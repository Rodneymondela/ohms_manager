"""
Field Sheet endpoints  —  /api/field-sheets/*
"""

import os
from datetime import datetime
from flask import request, jsonify, send_file, current_app
from flask_login import login_required
from werkzeug.utils import secure_filename
from app.api import api_bp
from app import db
from app.schedules.models import FieldSheet


ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'tif', 'tiff'}


def _uploads_dir():
    path = os.path.join(current_app.instance_path, 'uploads', 'field_sheets')
    os.makedirs(path, exist_ok=True)
    return path


def _allowed(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _parse_date(s):
    if not s:
        return None
    try:
        return datetime.strptime(s, '%Y-%m-%d').date()
    except ValueError:
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

    for key in ('noise_laeq', 'air_pre_cal_flow', 'air_post_cal_flow'):
        if key in data and data[key] not in (None, ''):
            try:
                setattr(sheet, key, float(data[key]))
            except (ValueError, TypeError):
                pass

    for key in ('sampling_date', 'noise_cal_date', 'air_cal_date', 'sampled_date'):
        if key in data:
            setattr(sheet, key, _parse_date(data[key]))


@api_bp.route('/field-sheets', methods=['GET'])
@login_required
def list_field_sheets():
    sheets = FieldSheet.query.order_by(FieldSheet.created_at.desc()).all()
    return jsonify([s.to_dict() for s in sheets])


@api_bp.route('/field-sheets', methods=['POST'])
@login_required
def create_field_sheet():
    data = request.get_json(silent=True) or {}
    sheet = FieldSheet()
    _apply(sheet, data)
    db.session.add(sheet)
    db.session.commit()
    return jsonify(sheet.to_dict()), 201


@api_bp.route('/field-sheets/<int:sid>', methods=['GET'])
@login_required
def get_field_sheet(sid):
    sheet = FieldSheet.query.get_or_404(sid)
    return jsonify(sheet.to_dict())


@api_bp.route('/field-sheets/<int:sid>', methods=['PUT'])
@login_required
def update_field_sheet(sid):
    sheet = FieldSheet.query.get_or_404(sid)
    data = request.get_json(silent=True) or {}
    _apply(sheet, data)
    db.session.commit()
    return jsonify(sheet.to_dict())


@api_bp.route('/field-sheets/<int:sid>', methods=['DELETE'])
@login_required
def delete_field_sheet(sid):
    sheet = FieldSheet.query.get_or_404(sid)
    # Remove scan file if present
    if sheet.scan_filename:
        path = os.path.join(_uploads_dir(), str(sheet.id), sheet.scan_filename)
        if os.path.exists(path):
            os.remove(path)
    db.session.delete(sheet)
    db.session.commit()
    return jsonify({'deleted': sid})


@api_bp.route('/field-sheets/<int:sid>/scan', methods=['POST'])
@login_required
def upload_scan(sid):
    sheet = FieldSheet.query.get_or_404(sid)
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    f = request.files['file']
    if not f.filename:
        return jsonify({'error': 'Empty filename'}), 400
    if not _allowed(f.filename):
        return jsonify({'error': 'File type not allowed. Use PDF, PNG, JPG, or TIFF.'}), 400

    folder = os.path.join(_uploads_dir(), str(sheet.id))
    os.makedirs(folder, exist_ok=True)

    # Remove old scan
    if sheet.scan_filename:
        old = os.path.join(folder, sheet.scan_filename)
        if os.path.exists(old):
            os.remove(old)

    filename = secure_filename(f.filename)
    f.save(os.path.join(folder, filename))
    sheet.scan_filename = filename
    db.session.commit()
    return jsonify(sheet.to_dict())


@api_bp.route('/field-sheets/<int:sid>/scan', methods=['GET'])
@login_required
def download_scan(sid):
    sheet = FieldSheet.query.get_or_404(sid)
    if not sheet.scan_filename:
        return jsonify({'error': 'No scan uploaded'}), 404
    path = os.path.join(_uploads_dir(), str(sheet.id), sheet.scan_filename)
    if not os.path.exists(path):
        return jsonify({'error': 'File not found on disk'}), 404
    return send_file(path, as_attachment=False)
