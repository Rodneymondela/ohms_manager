"""
Lab Results (Master Sheet) endpoints  —  /api/lab-results/*

Each row represents one sample result returned by the lab.
Aggregated by the DMPR report: area → occupation → quarter → pollutant.
"""

from datetime import datetime
from flask import request, jsonify
from flask_login import login_required, current_user
from app.api import api_bp
from app import db
from app.schedules.models import LabResult


def _op_id():
    if current_user.role == 'super_admin':
        return None
    return current_user.operation_id


def _owns(record):
    if current_user.role == 'super_admin':
        return None
    if record.operation_id != current_user.operation_id:
        return jsonify({'error': 'Access denied'}), 403
    return None


def _parse_date(s):
    if not s:
        return None
    try:
        return datetime.strptime(s, '%Y-%m-%d').date()
    except ValueError:
        return None


def _apply(record, data):
    for key in ('activity_area', 'occupation', 'sampling_quarter',
                'survey_ref', 'lab_report_ref'):
        if key in data:
            setattr(record, key, data[key] or None)

    for key in ('result_mn_twa', 'result_si_twa', 'result_pnoc_twa', 'shift_duration'):
        if key in data:
            v = data[key]
            if v not in (None, ''):
                try:
                    setattr(record, key, float(v))
                except (ValueError, TypeError):
                    pass
            else:
                setattr(record, key, None)

    if 'sampling_duration' in data:
        v = data['sampling_duration']
        if v not in (None, ''):
            try:
                record.sampling_duration = int(v)
            except (ValueError, TypeError):
                pass
        else:
            record.sampling_duration = None

    if 'sampling_date' in data:
        record.sampling_date = _parse_date(data['sampling_date'])


@api_bp.route('/lab-results', methods=['GET'])
@login_required
def list_lab_results():
    q = LabResult.query
    op = _op_id()
    if op is not None:
        q = q.filter(LabResult.operation_id == op)
    records = q.order_by(LabResult.sampling_date.desc(), LabResult.created_at.desc()).all()
    return jsonify([r.to_dict() for r in records])


@api_bp.route('/lab-results', methods=['POST'])
@login_required
def create_lab_result():
    data = request.get_json(silent=True) or {}
    record = LabResult(operation_id=current_user.operation_id)
    _apply(record, data)
    db.session.add(record)
    db.session.commit()
    return jsonify(record.to_dict()), 201


@api_bp.route('/lab-results/<int:rid>', methods=['PUT'])
@login_required
def update_lab_result(rid):
    record = LabResult.query.get_or_404(rid)
    err = _owns(record)
    if err:
        return err
    data = request.get_json(silent=True) or {}
    _apply(record, data)
    db.session.commit()
    return jsonify(record.to_dict())


@api_bp.route('/lab-results/<int:rid>', methods=['DELETE'])
@login_required
def delete_lab_result(rid):
    record = LabResult.query.get_or_404(rid)
    err = _owns(record)
    if err:
        return err
    db.session.delete(record)
    db.session.commit()
    return jsonify({'deleted': rid})


@api_bp.route('/lab-results/sync-from-field-sheets', methods=['POST'])
@login_required
def sync_lab_results_from_field_sheets():
    """
    Create draft LabResult rows from FieldSheets that have activity_area +
    occupation_group set (airborne sampling).  Skips sheets already linked.
    """
    from app.schedules.models import FieldSheet

    op = _op_id()

    # Build a set of already-imported survey refs + dates to deduplicate
    # (avoids dependency on field_sheet_id column existing in DB)
    existing_keys = set()
    for r in LabResult.query.with_entities(
            LabResult.survey_ref, LabResult.sampling_date, LabResult.activity_area, LabResult.occupation
    ).all():
        existing_keys.add((r.survey_ref, str(r.sampling_date), r.activity_area, r.occupation))

    q = FieldSheet.query.filter(
        FieldSheet.activity_area.isnot(None),
        FieldSheet.occupation_group.isnot(None),
    )
    if op is not None:
        q = q.filter(FieldSheet.operation_id == op)

    sheets = q.all()
    created = skipped = 0
    try:
        for fs in sheets:
            key = (fs.survey_number, str(fs.sampling_date), fs.activity_area, fs.occupation_group)
            if key in existing_keys:
                skipped += 1
                continue
            quarter = fs.sampling_quarter
            if not quarter and fs.sampling_date:
                m = fs.sampling_date.month
                quarter = f'Q{(m - 1) // 3 + 1}'

            lr = LabResult(
                operation_id      = current_user.operation_id,
                sampling_date     = fs.sampling_date,
                sampling_quarter  = quarter,
                activity_area     = fs.activity_area,
                occupation        = fs.occupation_group,
                sampling_duration = fs.air_run_time,
                survey_ref        = fs.survey_number,
            )
            db.session.add(lr)
            created += 1

        if created:
            db.session.commit()
    except Exception as exc:
        db.session.rollback()
        return jsonify({'error': str(exc)}), 500

    return jsonify({'created': created, 'skipped': skipped, 'eligible': len(sheets)})


@api_bp.route('/lab-results/dmpr-data', methods=['GET'])
@login_required
def lab_results_dmpr_data():
    """
    Aggregate lab results into the DMPR quarterly structure.
    Groups: activity_area → occupation → sampling_quarter → pollutant.
    Returns averaged TWA values for each combination.
    """
    q = LabResult.query
    op = _op_id()
    if op is not None:
        q = q.filter(LabResult.operation_id == op)

    records = q.filter(
        LabResult.activity_area.isnot(None),
        LabResult.occupation.isnot(None),
        LabResult.sampling_quarter.isnot(None),
    ).all()

    q_map = {'Q1': 'q1', 'Q2': 'q2', 'Q3': 'q3', 'Q4': 'q4'}

    rejected = 0
    # acc: area → occ → q_key → code → [values]
    acc = {}
    for r in records:
        if not r.is_valid_sample:
            rejected += 1
            continue
        area  = (r.activity_area or '').strip()
        occ   = (r.occupation or '').strip()
        q_key = q_map.get((r.sampling_quarter or '').strip().upper())
        if not area or not occ or not q_key:
            continue
        acc.setdefault(area, {}).setdefault(occ, {}).setdefault(q_key, {})
        for code, val in [('378', r.result_mn_twa), ('522', r.result_si_twa), ('459', r.result_pnoc_twa)]:
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

    return jsonify({'areas': result, 'rowCount': len(records), 'rejectedCount': rejected})
