"""
REST JSON API  —  /api/*
Consumed by the React OHMS Manager frontend.
No session auth required; CORS is configured in create_app().
"""

from datetime import date, datetime
from flask import request, jsonify
from flask_login import login_required
from app import db
from app.api import api_bp
from app.schedules.models import (
    Stressor, HEG, SamplingSchedule,
    ExposureReading, EmployeeExposure,
    MedicalRecord,
)
from app.employees.models import Employee


# ── helpers ──────────────────────────────────────────────────────────────────

def _parse_date(s):
    if not s:
        return None
    try:
        return datetime.strptime(s, '%Y-%m-%d').date()
    except ValueError:
        return None


def _err(msg, code=400):
    return jsonify({'error': msg}), code


# ══════════════════════════════════════════════════════════════════════════════
# STRESSORS  (Hazards in the React UI)
# ══════════════════════════════════════════════════════════════════════════════

@api_bp.route('/stressors', methods=['GET'])
@login_required
def list_stressors():
    stressors = Stressor.query.filter_by(is_active=True).order_by(Stressor.name).all()
    return jsonify([s.to_api_dict() for s in stressors])


@api_bp.route('/stressors', methods=['POST'])
@login_required
def create_stressor():
    data = request.get_json(silent=True) or {}
    if not data.get('name'):
        return _err('name is required')
    if not data.get('category'):
        return _err('category is required')

    oel_value = data.get('oelValue')
    if oel_value is not None:
        try:
            oel_value = float(oel_value)
        except (TypeError, ValueError):
            oel_value = None

    s = Stressor(
        name               = data['name'].strip(),
        category           = data['category'],
        oel_value          = oel_value,
        oel_unit           = data.get('unit') or None,
        oel_text           = data.get('oel') or None,
        description        = data.get('description') or None,
        health_effects     = data.get('healthEffects') or None,
        linked_test        = data.get('linkedTest') or None,
        default_frequency  = data.get('frequency') or 'Annual',
    )
    db.session.add(s)
    db.session.commit()
    return jsonify(s.to_api_dict()), 201


@api_bp.route('/stressors/<int:sid>', methods=['PUT'])
@login_required
def update_stressor(sid):
    s = Stressor.query.get_or_404(sid)
    data = request.get_json(silent=True) or {}

    if 'name'          in data: s.name              = data['name'].strip()
    if 'category'      in data: s.category          = data['category']
    if 'description'   in data: s.description       = data['description'] or None
    if 'healthEffects' in data: s.health_effects     = data['healthEffects'] or None
    if 'linkedTest'    in data: s.linked_test        = data['linkedTest'] or None
    if 'frequency'     in data: s.default_frequency  = data['frequency'] or None
    if 'unit'          in data: s.oel_unit           = data['unit'] or None
    if 'oel'           in data: s.oel_text           = data['oel'] or None
    if 'oelValue'      in data:
        try:
            s.oel_value = float(data['oelValue']) if data['oelValue'] not in (None, '') else None
        except (TypeError, ValueError):
            pass

    db.session.commit()
    return jsonify(s.to_api_dict())


@api_bp.route('/stressors/<int:sid>', methods=['DELETE'])
@login_required
def delete_stressor(sid):
    s = Stressor.query.get_or_404(sid)
    s.is_active = False   # soft-delete
    db.session.commit()
    return jsonify({'deleted': sid})


# ══════════════════════════════════════════════════════════════════════════════
# EMPLOYEES
# ══════════════════════════════════════════════════════════════════════════════

@api_bp.route('/employees', methods=['GET'])
@login_required
def list_employees():
    emps = Employee.query.filter_by(is_active=True).order_by(Employee.name).all()
    return jsonify([e.to_api_dict() for e in emps])


def _apply_employee_data(emp, data):
    """Apply JSON payload fields onto an Employee instance."""
    if 'name'       in data: emp.name       = data['name'].strip()
    if 'jobTitle'   in data: emp.job_title   = data['jobTitle'].strip()
    if 'department' in data: emp.department  = data['department']
    if 'heg'        in data: emp.heg_number  = data['heg'] or None

    if 'hazardIds' in data:
        ids = [int(i) for i in data['hazardIds']] if data['hazardIds'] else []
        stressors = Stressor.query.filter(Stressor.id.in_(ids)).all() if ids else []
        emp.stressors = stressors


@api_bp.route('/employees', methods=['POST'])
@login_required
def create_employee():
    data = request.get_json(silent=True) or {}
    if not data.get('name'):
        return _err('name is required')
    if not data.get('jobTitle'):
        return _err('jobTitle is required')

    emp = Employee(
        name       = data['name'].strip(),
        job_title  = data.get('jobTitle', '').strip(),
        department = data.get('department', ''),
        heg_number = data.get('heg') or None,
    )
    _apply_employee_data(emp, data)
    db.session.add(emp)
    db.session.commit()
    return jsonify(emp.to_api_dict()), 201


@api_bp.route('/employees/bulk', methods=['POST'])
@login_required
def bulk_create_employees():
    items = request.get_json(silent=True) or []
    if not isinstance(items, list):
        return _err('expected a JSON array')

    created = []
    for data in items:
        if not data.get('name') or not data.get('jobTitle'):
            continue
        emp = Employee(
            name       = data['name'].strip(),
            job_title  = data.get('jobTitle', '').strip(),
            department = data.get('department', ''),
            heg_number = data.get('heg') or None,
        )
        _apply_employee_data(emp, data)
        db.session.add(emp)
        created.append(emp)

    db.session.commit()
    return jsonify([e.to_api_dict() for e in created]), 201


@api_bp.route('/employees/<int:eid>', methods=['PUT'])
@login_required
def update_employee(eid):
    emp = Employee.query.get_or_404(eid)
    data = request.get_json(silent=True) or {}
    _apply_employee_data(emp, data)
    db.session.commit()
    return jsonify(emp.to_api_dict())


@api_bp.route('/employees/<int:eid>', methods=['DELETE'])
@login_required
def delete_employee(eid):
    emp = Employee.query.get_or_404(eid)
    emp.is_active = False
    db.session.commit()
    return jsonify({'deleted': eid})


# ══════════════════════════════════════════════════════════════════════════════
# HEG GROUPS  (dropdown list for the UI)
# ══════════════════════════════════════════════════════════════════════════════

@api_bp.route('/heg-groups', methods=['GET'])
@login_required
def list_heg_groups():
    hegs = HEG.query.order_by(HEG.heg_number).all()
    return jsonify([f"{h.heg_number}: {h.job_title}" for h in hegs])


@api_bp.route('/hegs', methods=['GET'])
@login_required
def list_hegs():
    hegs = HEG.query.order_by(HEG.heg_number).all()
    return jsonify([{
        'id':          h.id,
        'heg_number':  h.heg_number,
        'job_title':   h.job_title,
        'department':  h.department,
        'occupations': h.occupations or [],
    } for h in hegs])


# ══════════════════════════════════════════════════════════════════════════════
# DEPARTMENTS  (dropdown list for the UI)
# ══════════════════════════════════════════════════════════════════════════════

@api_bp.route('/departments', methods=['GET'])
@login_required
def list_departments():
    rows = db.session.query(Employee.department)\
               .filter_by(is_active=True)\
               .distinct()\
               .order_by(Employee.department)\
               .all()
    depts = [r[0] for r in rows if r[0]]
    # Always include a sensible default set
    defaults = ['Mining', 'Metallurgy', 'Engineering', 'Processing', 'HSE', 'Laboratory']
    merged = sorted(set(defaults) | set(depts))
    return jsonify(merged)


# ══════════════════════════════════════════════════════════════════════════════
# EXPOSURE READINGS
# ══════════════════════════════════════════════════════════════════════════════

@api_bp.route('/exposure-readings', methods=['GET'])
@login_required
def list_exposure_readings():
    readings = ExposureReading.query.order_by(ExposureReading.date.desc()).all()
    return jsonify([r.to_api_dict() for r in readings])


@api_bp.route('/exposure-readings', methods=['POST'])
@login_required
def create_exposure_reading():
    data = request.get_json(silent=True) or {}
    if not data.get('hazardId'):
        return _err('hazardId is required')

    stressor = Stressor.query.get(int(data['hazardId']))
    if not stressor:
        return _err('stressor not found', 404)

    reading = ExposureReading(
        stressor_id    = stressor.id,
        location       = data.get('location', '').strip(),
        measured_value = float(data.get('measuredValue', 0)),
        oel_value      = stressor.oel_value,
        oel_unit       = stressor.oel_unit,
        date           = _parse_date(data.get('date')) or date.today(),
    )
    db.session.add(reading)
    db.session.flush()   # get reading.id before adding associations

    emp_ids = [int(i) for i in (data.get('employeeIds') or [])]
    for eid in emp_ids:
        if Employee.query.get(eid):
            db.session.add(EmployeeExposure(reading_id=reading.id, employee_id=eid))

    db.session.commit()
    return jsonify(reading.to_api_dict()), 201


@api_bp.route('/exposure-readings/<int:rid>', methods=['DELETE'])
@login_required
def delete_exposure_reading(rid):
    reading = ExposureReading.query.get_or_404(rid)
    db.session.delete(reading)
    db.session.commit()
    return jsonify({'deleted': rid})


# ══════════════════════════════════════════════════════════════════════════════
# MEDICAL RECORDS
# ══════════════════════════════════════════════════════════════════════════════

@api_bp.route('/medical-records', methods=['GET'])
@login_required
def list_medical_records():
    records = MedicalRecord.query.order_by(MedicalRecord.id).all()
    return jsonify([r.to_api_dict() for r in records])


@api_bp.route('/medical-records', methods=['POST'])
@login_required
def create_medical_record():
    data = request.get_json(silent=True) or {}
    if not data.get('testName'):
        return _err('testName is required')
    if not data.get('employeeId'):
        return _err('employeeId is required')

    rec = MedicalRecord(
        employee_id = int(data['employeeId']),
        stressor_id = int(data['hazardId']) if data.get('hazardId') else None,
        test_name   = data['testName'].strip(),
        last_done   = _parse_date(data.get('lastDone')),
        next_due    = _parse_date(data.get('nextDue')),
        result      = data.get('result') or None,
        status      = data.get('status', 'scheduled'),
    )
    db.session.add(rec)
    db.session.commit()
    return jsonify(rec.to_api_dict()), 201


@api_bp.route('/medical-records/bulk', methods=['POST'])
@login_required
def bulk_create_medical_records():
    items = request.get_json(silent=True) or []
    if not isinstance(items, list):
        return _err('expected a JSON array')

    created = []
    for data in items:
        if not data.get('testName') or not data.get('employeeId'):
            continue
        rec = MedicalRecord(
            employee_id = int(data['employeeId']),
            stressor_id = int(data['hazardId']) if data.get('hazardId') else None,
            test_name   = data['testName'].strip(),
            last_done   = _parse_date(data.get('lastDone')),
            next_due    = _parse_date(data.get('nextDue')),
            result      = data.get('result') or None,
            status      = data.get('status', 'scheduled'),
        )
        db.session.add(rec)
        created.append(rec)

    db.session.commit()
    return jsonify([r.to_api_dict() for r in created]), 201


@api_bp.route('/medical-records/<int:mid>', methods=['PUT'])
@login_required
def update_medical_record(mid):
    rec = MedicalRecord.query.get_or_404(mid)
    data = request.get_json(silent=True) or {}

    if 'employeeId' in data: rec.employee_id = int(data['employeeId'])
    if 'hazardId'   in data: rec.stressor_id = int(data['hazardId']) if data['hazardId'] else None
    if 'testName'   in data: rec.test_name   = data['testName'].strip()
    if 'lastDone'   in data: rec.last_done   = _parse_date(data['lastDone'])
    if 'nextDue'    in data: rec.next_due    = _parse_date(data['nextDue'])
    if 'result'     in data: rec.result      = data['result'] or None
    if 'status'     in data: rec.status      = data['status']

    db.session.commit()
    return jsonify(rec.to_api_dict())


@api_bp.route('/medical-records/<int:mid>', methods=['DELETE'])
@login_required
def delete_medical_record(mid):
    rec = MedicalRecord.query.get_or_404(mid)
    db.session.delete(rec)
    db.session.commit()
    return jsonify({'deleted': mid})


# ══════════════════════════════════════════════════════════════════════════════
# SAMPLING SCHEDULES
# ══════════════════════════════════════════════════════════════════════════════

@api_bp.route('/sampling-schedules', methods=['GET'])
@login_required
def list_sampling_schedules():
    schedules = (SamplingSchedule.query
                 .join(HEG).join(Stressor)
                 .order_by(SamplingSchedule.next_sample_due)
                 .all())
    return jsonify([s.to_dict() for s in schedules])


@api_bp.route('/sampling-schedules', methods=['POST'])
@login_required
def create_sampling_schedule():
    data = request.get_json(silent=True) or {}
    if not data.get('hegId') or not data.get('stressorId') or not data.get('frequency'):
        return _err('hegId, stressorId and frequency are required')

    s = SamplingSchedule(
        heg_id            = int(data['hegId']),
        stressor_id       = int(data['stressorId']),
        occupation        = data.get('occupation') or None,
        sampling_type     = data.get('samplingType') or None,
        frequency         = data['frequency'],
        last_sampled_date = _parse_date(data.get('lastSampledDate')),
        remarks           = data.get('remarks') or None,
    )
    s.recalculate_next_due()
    db.session.add(s)
    db.session.commit()
    return jsonify(s.to_dict()), 201


@api_bp.route('/sampling-schedules/<int:sid>', methods=['PUT'])
@login_required
def update_sampling_schedule(sid):
    s = SamplingSchedule.query.get_or_404(sid)
    data = request.get_json(silent=True) or {}

    if 'hegId'           in data: s.heg_id            = int(data['hegId'])
    if 'stressorId'      in data: s.stressor_id       = int(data['stressorId'])
    if 'occupation'      in data: s.occupation        = data['occupation'] or None
    if 'samplingType'    in data: s.sampling_type     = data['samplingType'] or None
    if 'frequency'       in data: s.frequency         = data['frequency']
    if 'lastSampledDate' in data: s.last_sampled_date = _parse_date(data['lastSampledDate'])
    if 'remarks'         in data: s.remarks           = data['remarks'] or None
    s.recalculate_next_due()
    db.session.commit()
    return jsonify(s.to_dict())


@api_bp.route('/sampling-schedules/<int:sid>', methods=['DELETE'])
@login_required
def delete_sampling_schedule(sid):
    s = SamplingSchedule.query.get_or_404(sid)
    db.session.delete(s)
    db.session.commit()
    return jsonify({'deleted': sid})
