from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db # Assuming db from app package
from app.models import HealthRecord, Employee
from app.forms import HealthRecordForm
from . import health_records_bp
from sqlalchemy.exc import IntegrityError

@health_records_bp.route('/')
@login_required
def list_health_records(): # Renamed from 'health_records'
    all_records = HealthRecord.query.order_by(HealthRecord.date.desc()).all()
    return render_template('health_records/health_records.html', health_records=all_records, title='Manage Health Records')

@health_records_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_health_record():
    form = HealthRecordForm()
    form.employee.choices = [(e.id, e.name) for e in Employee.query.order_by(Employee.name).all()]

    if form.validate_on_submit():
        try:
            record = HealthRecord(
                employee_id=form.employee.data,
                test_type=form.test_type.data,
                result=form.result.data,
                details=form.details.data,
                date=form.date.data,
                next_test_date=form.next_test_date.data,
                physician=form.physician.data,
                facility=form.facility.data,
                recorded_by=current_user.id
            )
            db.session.add(record)
            db.session.commit()
            flash('Health record added successfully.', 'success')
            return redirect(url_for('health_records.list_health_records'))
        except IntegrityError:
            db.session.rollback()
            flash('Error: Could not add health record due to a data conflict or missing related employee.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'An unexpected error occurred: {e}', 'danger')
    return render_template('health_records/health_record_form.html', form=form, title='Add Health Record')

@health_records_bp.route('/<int:record_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_health_record(record_id):
    record = HealthRecord.query.get_or_404(record_id)
    form = HealthRecordForm(obj=record)
    form.employee.choices = [(e.id, e.name) for e in Employee.query.order_by(Employee.name).all()]

    if request.method == 'GET':
        form.employee.data = record.employee_id
        # Date fields are usually handled correctly by obj=record for pre-population

    if form.validate_on_submit():
        try:
            record.employee_id = form.employee.data
            record.test_type = form.test_type.data
            record.result = form.result.data
            record.details = form.details.data
            record.date = form.date.data
            record.next_test_date = form.next_test_date.data
            record.physician = form.physician.data
            record.facility = form.facility.data
            # recorded_by typically doesn't change on edit

            db.session.commit()
            flash('Health record updated successfully.', 'success')
            return redirect(url_for('health_records.list_health_records'))
        except IntegrityError:
            db.session.rollback()
            flash('Error: Could not update health record due to a data conflict.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'An unexpected error occurred: {e}', 'danger')

    return render_template('health_records/health_record_form.html', form=form, title='Edit Health Record', record_id=record_id)

@health_records_bp.route('/<int:record_id>/delete', methods=['POST'])
@login_required
def delete_health_record(record_id):
    record = HealthRecord.query.get_or_404(record_id)
    try:
        db.session.delete(record)
        db.session.commit()
        flash('Health record deleted successfully.', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('Error: Could not delete health record due to a data conflict.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'An unexpected error occurred: {e}', 'danger')
    return redirect(url_for('health_records.list_health_records'))
