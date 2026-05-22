"""
Field Sheet endpoints  —  /api/field-sheets/*

Scan files are stored in Cloudinary (persistent across Heroku dyno restarts).
Falls back to local disk when CLOUDINARY_URL is not set (local dev without addon).
All queries are scoped to the current user's operation.
"""

import os
from datetime import datetime
from flask import request, jsonify, redirect
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import cloudinary
import cloudinary.uploader
import cloudinary.api
from app.api import api_bp
from app import db
from app.schedules.models import FieldSheet


ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'tif', 'tiff'}


def _allowed(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _parse_date(s):
    if not s:
        return None
    try:
        return datetime.strptime(s, '%Y-%m-%d').date()
    except ValueError:
        return None


def _op_id():
    if current_user.role == 'super_admin':
        return None
    return current_user.operation_id


def _owns(sheet):
    if current_user.role == 'super_admin':
        return None
    if sheet.operation_id != current_user.operation_id:
        return jsonify({'error': 'Access denied'}), 403
    return None


def _apply(sheet, data):
    """Apply JSON fields onto a FieldSheet instance."""
    for key in (
        'mine_site', 'heg', 'sampling_quarter', 'survey_number',
        'employee_name', 'coy_number', 'job_title', 'company_name',
        'shift_sampled', 'purpose',
        'wind_speed',
        'noise_sources', 'noise_control_types', 'noise_demarcated', 'noise_hpd_provided',
        'noise_dbadge_serial', 'noise_method', 'noise_pre_cal', 'noise_post_cal',
        'noise_time_on', 'noise_time_off',
        'air_contaminant', 'air_control_types', 'air_personal_sample', 'air_area_sample',
        'air_pump_serial', 'air_filter_number', 'air_method',
        'air_time_on', 'air_time_off',
        'wearer_signature', 'sampled_by', 'sampled_designation', 'verified_by',
        'activity_area', 'occupation_group',
    ):
        if key in data:
            setattr(sheet, key, data[key] or None)

    for key in (
        'weather_wet', 'weather_dry', 'weather_hot', 'weather_warm', 'weather_cold',
        'indoor_ac', 'indoor_lev', 'cabin_ac',
        'brief_1', 'brief_2', 'brief_3', 'brief_4', 'brief_5', 'brief_6',
    ):
        if key in data:
            setattr(sheet, key, bool(data[key]))

    for key in ('noise_run_time', 'air_run_time'):
        if key in data and data[key] not in (None, ''):
            try:
                setattr(sheet, key, int(data[key]))
            except (ValueError, TypeError):
                pass

    for key in ('noise_laeq', 'air_pre_cal_flow', 'air_post_cal_flow',
                'result_mn_twa', 'result_si_twa', 'result_pnoc_twa'):
        if key in data and data[key] not in (None, ''):
            try:
                setattr(sheet, key, float(data[key]))
            except (ValueError, TypeError):
                pass
        elif key in data and data[key] in (None, ''):
            setattr(sheet, key, None)

    for key in ('sampling_date', 'noise_cal_date', 'air_cal_date', 'sampled_date'):
        if key in data:
            setattr(sheet, key, _parse_date(data[key]))


def _cloudinary_public_id(sheet_id, filename):
    """Stable Cloudinary public_id for a field sheet scan."""
    name = secure_filename(filename).rsplit('.', 1)[0]
    return f"ohms/field_sheets/{sheet_id}/{name}"


@api_bp.route('/field-sheets', methods=['GET'])
@login_required
def list_field_sheets():
    q = FieldSheet.query
    op = _op_id()
    if op is not None:
        q = q.filter(FieldSheet.operation_id == op)
    sheets = q.order_by(FieldSheet.created_at.desc()).all()
    return jsonify([s.to_dict() for s in sheets])


@api_bp.route('/field-sheets', methods=['POST'])
@login_required
def create_field_sheet():
    data = request.get_json(silent=True) or {}
    sheet = FieldSheet(operation_id=current_user.operation_id)
    _apply(sheet, data)
    db.session.add(sheet)
    db.session.commit()
    return jsonify(sheet.to_dict()), 201


@api_bp.route('/field-sheets/<int:sid>', methods=['GET'])
@login_required
def get_field_sheet(sid):
    sheet = FieldSheet.query.get_or_404(sid)
    err = _owns(sheet)
    if err:
        return err
    return jsonify(sheet.to_dict())


@api_bp.route('/field-sheets/<int:sid>', methods=['PUT'])
@login_required
def update_field_sheet(sid):
    sheet = FieldSheet.query.get_or_404(sid)
    err = _owns(sheet)
    if err:
        return err
    data = request.get_json(silent=True) or {}
    _apply(sheet, data)
    db.session.commit()
    return jsonify(sheet.to_dict())


@api_bp.route('/field-sheets/<int:sid>', methods=['DELETE'])
@login_required
def delete_field_sheet(sid):
    sheet = FieldSheet.query.get_or_404(sid)
    err = _owns(sheet)
    if err:
        return err
    if sheet.scan_filename:
        try:
            public_id = _cloudinary_public_id(sheet.id, sheet.scan_filename)
            cloudinary.api.delete_resources([public_id], resource_type='raw')
            cloudinary.api.delete_resources([public_id], resource_type='image')
        except Exception:
            pass
    db.session.delete(sheet)
    db.session.commit()
    return jsonify({'deleted': sid})


@api_bp.route('/field-sheets/<int:sid>/scan', methods=['POST'])
@login_required
def upload_scan(sid):
    sheet = FieldSheet.query.get_or_404(sid)
    err = _owns(sheet)
    if err:
        return err
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    f = request.files['file']
    if not f.filename:
        return jsonify({'error': 'Empty filename'}), 400
    if not _allowed(f.filename):
        return jsonify({'error': 'File type not allowed. Use PDF, PNG, JPG, or TIFF.'}), 400

    ext = f.filename.rsplit('.', 1)[1].lower()
    resource_type = 'raw' if ext == 'pdf' else 'image'
    public_id = _cloudinary_public_id(sid, f.filename)

    if sheet.scan_filename:
        old_id = _cloudinary_public_id(sid, sheet.scan_filename)
        old_ext = sheet.scan_filename.rsplit('.', 1)[-1].lower()
        old_rt = 'raw' if old_ext == 'pdf' else 'image'
        try:
            cloudinary.api.delete_resources([old_id], resource_type=old_rt)
        except Exception:
            pass

    result = cloudinary.uploader.upload(
        f,
        public_id=public_id,
        resource_type=resource_type,
        overwrite=True,
    )

    sheet.scan_filename = f.filename
    sheet.scan_url_external = result.get('secure_url')
    db.session.commit()
    return jsonify(sheet.to_dict())


@api_bp.route('/field-sheets/dmpr-data', methods=['GET'])
@login_required
def field_sheets_dmpr_data():
    """
    Aggregate field sheet lab results into the DMPR quarterly structure.
    Groups by activity_area → occupation_group → sampling_quarter → pollutant.
    Returns averaged TWA values for each combination.
    """
    q = FieldSheet.query
    op = _op_id()
    if op is not None:
        q = q.filter(FieldSheet.operation_id == op)

    sheets = q.filter(
        FieldSheet.activity_area.isnot(None),
        FieldSheet.occupation_group.isnot(None),
        FieldSheet.sampling_quarter.isnot(None),
    ).all()

    # quarter label → lowercase key
    q_map = {'Q1': 'q1', 'Q2': 'q2', 'Q3': 'q3', 'Q4': 'q4'}

    # acc: area → occ → q_key → code → [values]
    acc = {}
    for s in sheets:
        area = (s.activity_area or '').strip()
        occ  = (s.occupation_group or '').strip()
        q_key = q_map.get((s.sampling_quarter or '').strip().upper())
        if not area or not occ or not q_key:
            continue

        acc.setdefault(area, {}).setdefault(occ, {}).setdefault(q_key, {})
        for code, val in [('378', s.result_mn_twa), ('522', s.result_si_twa), ('459', s.result_pnoc_twa)]:
            if val is not None and val > 0:
                acc[area][occ][q_key].setdefault(code, []).append(val)

    result = []
    for area_name, occs in acc.items():
        occ_list = []
        for occ_name, quarters in occs.items():
            poll_map = {}
            for q_key, codes in quarters.items():
                for code, vals in codes.items():
                    if code not in poll_map:
                        poll_map[code] = {'q1': '', 'q2': '', 'q3': '', 'q4': ''}
                    avg = sum(vals) / len(vals)
                    poll_map[code][q_key] = f'{avg:.4f}'
            occ_list.append({'name': occ_name, 'pollutants': poll_map})
        result.append({'name': area_name, 'occupations': occ_list})

    return jsonify({'areas': result, 'rowCount': len(sheets)})


@api_bp.route('/field-sheets/<int:sid>/scan', methods=['GET'])
@login_required
def download_scan(sid):
    sheet = FieldSheet.query.get_or_404(sid)
    err = _owns(sheet)
    if err:
        return err
    if not sheet.scan_filename or not sheet.scan_url_external:
        return jsonify({'error': 'No scan uploaded'}), 404
    return redirect(sheet.scan_url_external)
