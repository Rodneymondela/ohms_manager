from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required # current_user might not be needed if not setting recorded_by
from app import db # Assuming db from app package
from app.models import Employee
from app.forms import EmployeeForm
from . import employees_bp
from sqlalchemy.exc import IntegrityError
# from werkzeug.exceptions import abort # Not strictly needed if using get_or_404

@employees_bp.route('/')
@login_required
def list_employees(): # Renamed from 'employees'
    all_employees = Employee.query.all()
    return render_template('employees/employees.html', employees=all_employees, title='Manage Employees')

@employees_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_employee():
    form = EmployeeForm()
    if form.validate_on_submit():
        try:
            employee = Employee(
                name=form.name.data,
                job_title=form.job_title.data,
                department=form.department.data,
                hire_date=form.hire_date.data,
                date_of_birth=form.date_of_birth.data,
                contact_number=form.contact_number.data,
                emergency_contact=form.emergency_contact.data,
                emergency_phone=form.emergency_phone.data
            )
            db.session.add(employee)
            db.session.commit()
            flash('Employee added successfully.', 'success')
            return redirect(url_for('employees.list_employees'))
        except ValueError as e:
            db.session.rollback()
            flash(f'Error adding employee: {e}', 'danger')
        except IntegrityError:
            db.session.rollback()
            flash('Error: An employee with similar critical details already exists.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'An unexpected error occurred: {e}', 'danger')
    return render_template('employees/employee_form.html', form=form, title='Add Employee')

@employees_bp.route('/<int:employee_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    form = EmployeeForm(obj=employee)

    if form.validate_on_submit():
        try:
            form.populate_obj(employee)
            db.session.commit()
            flash('Employee updated successfully.', 'success')
            return redirect(url_for('employees.list_employees'))
        except ValueError as e:
            db.session.rollback()
            flash(f'Error updating employee: {e}', 'danger')
        except IntegrityError:
            db.session.rollback()
            flash('Error: Could not update employee due to a data conflict.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'An unexpected error occurred: {e}', 'danger')

    return render_template('employees/employee_form.html', form=form, title='Edit Employee', employee_id=employee_id)

@employees_bp.route('/<int:employee_id>/delete', methods=['POST'])
@login_required
def delete_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    try:
        db.session.delete(employee)
        db.session.commit()
        flash('Employee deleted successfully.', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('Error: Cannot delete this employee as they have related records (e.g., exposures, health records). Please remove those first.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'An unexpected error occurred: {e}', 'danger')
    return redirect(url_for('employees.list_employees'))
