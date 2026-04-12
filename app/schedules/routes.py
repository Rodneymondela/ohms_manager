"""
Occupational Hygiene Sampling Schedule Routes
=============================================
Blueprint prefix: /schedules
"""

from flask import (
    render_template, redirect, url_for,
    flash, request, jsonify, abort
)
from app import db
from app.schedules import schedules_bp
from app.schedules.models import HEG, Stressor, HEGStressor, SamplingSchedule, calculate_next_due
from app.schedules.forms import HEGForm, HEGStressorForm, SamplingScheduleForm, StressorForm


# ── Helper ──────────────────────────────────────────────────────────────────

def _active_stressors():
    return Stressor.query.filter_by(is_active=True).order_by(Stressor.name).all()

def _all_hegs():
    return HEG.query.order_by(HEG.heg_number).all()


# ══════════════════════════════════════════════════════════════════════════════
# HEG VIEWS
# ══════════════════════════════════════════════════════════════════════════════

@schedules_bp.route('/')
@schedules_bp.route('/hegs')
def heg_list():
    """List all HEGs with their linked stressors and schedule summary."""
    hegs = HEG.query.order_by(HEG.heg_number).all()
    return render_template('schedules/heg_list.html', hegs=hegs)


@schedules_bp.route('/hegs/add', methods=['GET', 'POST'])
def heg_add():
    form = HEGForm()
    if form.validate_on_submit():
        # Ensure HEG number is unique
        if HEG.query.filter_by(heg_number=form.heg_number.data.strip()).first():
            flash(f'HEG number "{form.heg_number.data}" already exists.', 'danger')
        else:
            heg = HEG(
                heg_number  = form.heg_number.data.strip().upper(),
                job_title   = form.job_title.data.strip(),
                department  = form.department.data.strip(),
                risk_level  = form.risk_level.data,
                description = form.description.data,
            )
            db.session.add(heg)
            db.session.commit()
            flash(f'HEG {heg.heg_number} created successfully.', 'success')
            return redirect(url_for('schedules.heg_list'))
    return render_template('schedules/heg_form.html', form=form, title='Add HEG', editing=False)


@schedules_bp.route('/hegs/<int:heg_id>/edit', methods=['GET', 'POST'])
def heg_edit(heg_id):
    heg  = HEG.query.get_or_404(heg_id)
    form = HEGForm(obj=heg)
    if form.validate_on_submit():
        existing = HEG.query.filter_by(heg_number=form.heg_number.data.strip().upper()).first()
        if existing and existing.id != heg.id:
            flash(f'HEG number "{form.heg_number.data}" already exists.', 'danger')
        else:
            heg.heg_number  = form.heg_number.data.strip().upper()
            heg.job_title   = form.job_title.data.strip()
            heg.department  = form.department.data.strip()
            heg.risk_level  = form.risk_level.data
            heg.description = form.description.data
            db.session.commit()
            flash(f'HEG {heg.heg_number} updated.', 'success')
            return redirect(url_for('schedules.heg_list'))
    return render_template('schedules/heg_form.html', form=form, title='Edit HEG', editing=True, heg=heg)


@schedules_bp.route('/hegs/<int:heg_id>/delete', methods=['POST'])
def heg_delete(heg_id):
    heg = HEG.query.get_or_404(heg_id)
    db.session.delete(heg)
    db.session.commit()
    flash(f'HEG {heg.heg_number} deleted.', 'warning')
    return redirect(url_for('schedules.heg_list'))


# ══════════════════════════════════════════════════════════════════════════════
# HEG STRESSOR ASSIGNMENT
# ══════════════════════════════════════════════════════════════════════════════

@schedules_bp.route('/hegs/<int:heg_id>/stressors/add', methods=['GET', 'POST'])
def heg_stressor_add(heg_id):
    heg  = HEG.query.get_or_404(heg_id)
    form = HEGStressorForm()

    # Only show stressors not already linked to this HEG
    linked_ids = [hs.stressor_id for hs in heg.heg_stressors]
    available  = [s for s in _active_stressors() if s.id not in linked_ids]
    form.set_stressor_choices(available)

    if form.validate_on_submit():
        hs = HEGStressor(
            heg_id              = heg.id,
            stressor_id         = form.stressor_id.data,
            monitoring_priority = form.monitoring_priority.data,
            exposure_notes      = form.exposure_notes.data,
        )
        db.session.add(hs)
        db.session.commit()
        stressor = Stressor.query.get(form.stressor_id.data)
        flash(f'Stressor "{stressor.name}" assigned to {heg.heg_number}.', 'success')
        return redirect(url_for('schedules.heg_list'))

    stressor_data = {
        s.id: {
            'oel_display': s.oel_display(),
            'oel_reference': s.oel_reference or '',
            'sampling_method': s.sampling_method or '',
            'category': s.category,
        }
        for s in _active_stressors()
    }
    return render_template('schedules/heg_stressor_form.html',
                           form=form, heg=heg, stressor_data=stressor_data)


@schedules_bp.route('/hegs/<int:heg_id>/stressors/<int:hs_id>/remove', methods=['POST'])
def heg_stressor_remove(heg_id, hs_id):
    hs = HEGStressor.query.get_or_404(hs_id)
    name = hs.stressor.name
    db.session.delete(hs)
    db.session.commit()
    flash(f'Stressor "{name}" removed from HEG.', 'warning')
    return redirect(url_for('schedules.heg_list'))


# ══════════════════════════════════════════════════════════════════════════════
# SAMPLING SCHEDULE VIEWS
# ══════════════════════════════════════════════════════════════════════════════

@schedules_bp.route('/schedules')
def schedule_list():
    """View all sampling schedules with optional filters."""
    stressor_id = request.args.get('stressor_id', type=int)
    department  = request.args.get('department', '').strip()
    risk_level  = request.args.get('risk_level', '').strip()
    status      = request.args.get('status', '').strip()

    query = SamplingSchedule.query.join(HEG).join(Stressor)

    if stressor_id:
        query = query.filter(SamplingSchedule.stressor_id == stressor_id)
    if department:
        query = query.filter(HEG.department.ilike(f'%{department}%'))
    if risk_level:
        query = query.filter(HEG.risk_level == risk_level)

    schedules = query.order_by(SamplingSchedule.next_sample_due).all()

    # Filter by computed status (can't do in DB since it's a property)
    if status:
        schedules = [s for s in schedules if s.computed_status == status]

    # For filter dropdowns
    stressors   = _active_stressors()
    departments = db.session.query(HEG.department).distinct().order_by(HEG.department).all()
    departments = [d[0] for d in departments]

    return render_template('schedules/schedule_list.html',
                           schedules=schedules,
                           stressors=stressors,
                           departments=departments,
                           filters={'stressor_id': stressor_id, 'department': department,
                                    'risk_level': risk_level, 'status': status})


@schedules_bp.route('/schedules/add', methods=['GET', 'POST'])
def schedule_add():
    form = SamplingScheduleForm()
    form.set_heg_choices(_all_hegs())
    form.set_stressor_choices(_active_stressors())

    # Pre-select HEG if passed via query string
    preselect_heg = request.args.get('heg_id', type=int)
    if preselect_heg and request.method == 'GET':
        form.heg_id.data = preselect_heg

    if form.validate_on_submit():
        schedule = SamplingSchedule(
            heg_id            = form.heg_id.data,
            stressor_id       = form.stressor_id.data,
            sampling_type     = form.sampling_type.data,
            frequency         = form.frequency.data,
            last_sampled_date = form.last_sampled_date.data,
            status            = form.status.data,
            remarks           = form.remarks.data,
        )
        schedule.recalculate_next_due()
        db.session.add(schedule)
        db.session.commit()
        flash('Sampling schedule created successfully.', 'success')
        return redirect(url_for('schedules.schedule_list'))

    stressor_data = {
        s.id: {
            'oel_display':     s.oel_display(),
            'oel_reference':   s.oel_reference or '',
            'sampling_method': s.sampling_method or '',
            'category':        s.category,
        }
        for s in _active_stressors()
    }
    return render_template('schedules/schedule_form.html',
                           form=form, title='Add Sampling Schedule',
                           editing=False, stressor_data=stressor_data)


@schedules_bp.route('/schedules/<int:schedule_id>/edit', methods=['GET', 'POST'])
def schedule_edit(schedule_id):
    schedule = SamplingSchedule.query.get_or_404(schedule_id)
    form     = SamplingScheduleForm(obj=schedule)
    form.set_heg_choices(_all_hegs())
    form.set_stressor_choices(_active_stressors())

    if form.validate_on_submit():
        schedule.heg_id            = form.heg_id.data
        schedule.stressor_id       = form.stressor_id.data
        schedule.sampling_type     = form.sampling_type.data
        schedule.frequency         = form.frequency.data
        schedule.last_sampled_date = form.last_sampled_date.data
        schedule.status            = form.status.data
        schedule.remarks           = form.remarks.data
        schedule.recalculate_next_due()
        db.session.commit()
        flash('Schedule updated successfully.', 'success')
        return redirect(url_for('schedules.schedule_list'))

    stressor_data = {
        s.id: {
            'oel_display':     s.oel_display(),
            'oel_reference':   s.oel_reference or '',
            'sampling_method': s.sampling_method or '',
            'category':        s.category,
        }
        for s in _active_stressors()
    }
    return render_template('schedules/schedule_form.html',
                           form=form, title='Edit Sampling Schedule',
                           editing=True, schedule=schedule, stressor_data=stressor_data)


@schedules_bp.route('/schedules/<int:schedule_id>/delete', methods=['POST'])
def schedule_delete(schedule_id):
    schedule = SamplingSchedule.query.get_or_404(schedule_id)
    db.session.delete(schedule)
    db.session.commit()
    flash('Schedule deleted.', 'warning')
    return redirect(url_for('schedules.schedule_list'))


# ══════════════════════════════════════════════════════════════════════════════
# STRESSOR MASTER LIST (Admin)
# ══════════════════════════════════════════════════════════════════════════════

@schedules_bp.route('/stressors')
def stressor_list():
    stressors = Stressor.query.order_by(Stressor.category, Stressor.name).all()
    return render_template('schedules/stressor_list.html', stressors=stressors)


@schedules_bp.route('/stressors/add', methods=['GET', 'POST'])
def stressor_add():
    form = StressorForm()
    if form.validate_on_submit():
        s = Stressor(
            name            = form.name.data.strip(),
            category        = form.category.data,
            oel_value       = form.oel_value.data,
            oel_unit        = form.oel_unit.data,
            oel_text        = form.oel_text.data,
            oel_reference   = form.oel_reference.data,
            sampling_method = form.sampling_method.data,
            is_active       = form.is_active.data,
        )
        db.session.add(s)
        db.session.commit()
        flash(f'Stressor "{s.name}" added.', 'success')
        return redirect(url_for('schedules.stressor_list'))
    return render_template('schedules/stressor_form.html', form=form, title='Add Stressor', editing=False)


@schedules_bp.route('/stressors/<int:stressor_id>/edit', methods=['GET', 'POST'])
def stressor_edit(stressor_id):
    s    = Stressor.query.get_or_404(stressor_id)
    form = StressorForm(obj=s)
    if form.validate_on_submit():
        s.name            = form.name.data.strip()
        s.category        = form.category.data
        s.oel_value       = form.oel_value.data
        s.oel_unit        = form.oel_unit.data
        s.oel_text        = form.oel_text.data
        s.oel_reference   = form.oel_reference.data
        s.sampling_method = form.sampling_method.data
        s.is_active       = form.is_active.data
        db.session.commit()
        flash(f'Stressor "{s.name}" updated.', 'success')
        return redirect(url_for('schedules.stressor_list'))
    return render_template('schedules/stressor_form.html', form=form, title='Edit Stressor', editing=True, stressor=s)


# ══════════════════════════════════════════════════════════════════════════════
# JSON API  — consumed by the React OHMS Manager UI
# ══════════════════════════════════════════════════════════════════════════════

@schedules_bp.route('/api/hegs')
def api_hegs():
    """Return all HEGs with their linked stressors as JSON."""
    hegs = HEG.query.order_by(HEG.heg_number).all()
    data = []
    for h in hegs:
        data.append({
            'id':          h.id,
            'heg_number':  h.heg_number,
            'job_title':   h.job_title,
            'department':  h.department,
            'risk_level':  h.risk_level,
            'description': h.description,
            'stressors': [
                {
                    'id':           hs.stressor.id,
                    'name':         hs.stressor.name,
                    'category':     hs.stressor.category,
                    'oel_display':  hs.stressor.oel_display(),
                    'oel_unit':     hs.stressor.oel_unit,
                    'oel_reference':hs.stressor.oel_reference,
                    'priority':     hs.monitoring_priority,
                }
                for hs in h.heg_stressors
            ],
        })
    resp = jsonify(data)
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


@schedules_bp.route('/api/schedules')
def api_schedules():
    """Return all sampling schedules as JSON for the React OHMS Manager UI."""
    schedules = SamplingSchedule.query.join(HEG).join(Stressor).order_by(
        SamplingSchedule.next_sample_due
    ).all()
    resp = jsonify([s.to_dict() for s in schedules])
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


@schedules_bp.route('/api/stressors')
def api_stressors():
    """Return master stressor list as JSON."""
    stressors = _active_stressors()
    data = [
        {
            'id':             s.id,
            'name':           s.name,
            'category':       s.category,
            'oel_display':    s.oel_display(),
            'oel_value':      s.oel_value,
            'oel_unit':       s.oel_unit,
            'oel_reference':  s.oel_reference,
            'sampling_method':s.sampling_method,
        }
        for s in stressors
    ]
    resp = jsonify(data)
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp
