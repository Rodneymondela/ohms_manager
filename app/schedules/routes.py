from flask import render_template, redirect, url_for, flash, request, get_flashed_messages
from app import db
from app.models import HEG, SamplingSchedule
from .forms import HEGForm, ScheduleForm
from . import schedules_bp
from datetime import datetime

@schedules_bp.route('/')
@schedules_bp.route('/index')
def index():
    hegs = HEG.query.all()
    return render_template('schedules/index.html', hegs=hegs)

@schedules_bp.route('/add_heg', methods=['GET', 'POST'])
def add_heg():
    form = HEGForm()
    if form.validate_on_submit():
        existing_heg = HEG.query.filter_by(heg_number=form.heg_number.data).first()
        if existing_heg:
            flash('HEG Number already exists. Please choose a different one.', 'error')
        else:
            heg = HEG(heg_number=form.heg_number.data, job_title=form.job_title.data, department=form.department.data, exposure_agents=form.exposure_agents.data, risk_level=form.risk_level.data)
            db.session.add(heg)
            db.session.commit()
            flash('HEG added successfully!', 'success')
            return redirect(url_for('schedules_bp.index'))
    return render_template('schedules/add_heg.html', form=form)

@schedules_bp.route('/edit_heg/<int:heg_id>', methods=['GET', 'POST'])
def edit_heg(heg_id):
    heg = HEG.query.get_or_404(heg_id)
    form = HEGForm(obj=heg) # Populate form with existing HEG data for GET
    if form.validate_on_submit():
        if heg.heg_number != form.heg_number.data: # If heg_number changed
            existing_heg = HEG.query.filter_by(heg_number=form.heg_number.data).first()
            if existing_heg:
                flash('HEG Number already exists. Please choose a different one.', 'error')
                return render_template('schedules/edit_heg.html', form=form, heg=heg) # Re-render with error

        form.populate_obj(heg)
        db.session.commit()
        flash('HEG updated successfully!', 'success')
        return redirect(url_for('schedules_bp.index'))

    return render_template('schedules/edit_heg.html', form=form, heg=heg)

@schedules_bp.route('/delete_heg/<int:heg_id>', methods=['GET', 'POST'])
def delete_heg(heg_id):
    heg = HEG.query.get_or_404(heg_id)
    db.session.delete(heg)
    db.session.commit()
    flash('HEG and its schedules deleted successfully!', 'success')
    return redirect(url_for('schedules_bp.index'))

@schedules_bp.route('/add_schedule/<int:heg_id>', methods=['GET', 'POST'])
def add_schedule(heg_id):
    heg = HEG.query.get_or_404(heg_id)
    form = ScheduleForm()
    if form.validate_on_submit():
        schedule = SamplingSchedule(heg_id=heg.id)
        form.populate_obj(schedule)
        schedule.set_next_sample_due()
        db.session.add(schedule)
        db.session.commit()
        flash('Sampling schedule added successfully!', 'success')
        return redirect(url_for('schedules_bp.index'))
    return render_template('schedules/add_schedule.html', form=form, heg=heg)

@schedules_bp.route('/edit_schedule/<int:schedule_id>', methods=['GET', 'POST'])
def edit_schedule(schedule_id):
    schedule = SamplingSchedule.query.get_or_404(schedule_id)
    heg = schedule.heg
    form = ScheduleForm(obj=schedule)
    if form.validate_on_submit():
        form.populate_obj(schedule)
        schedule.set_next_sample_due()
        db.session.commit()
        flash('Sampling schedule updated successfully!', 'success')
        return redirect(url_for('schedules_bp.index'))
    return render_template('schedules/edit_schedule.html', form=form, schedule=schedule, heg=heg)

@schedules_bp.route('/delete_schedule/<int:schedule_id>', methods=['GET', 'POST'])
def delete_schedule(schedule_id):
    schedule = SamplingSchedule.query.get_or_404(schedule_id)
    db.session.delete(schedule)
    db.session.commit()
    flash('Schedule deleted successfully!', 'success')
    return redirect(url_for('schedules_bp.index'))
