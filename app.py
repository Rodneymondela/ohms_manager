import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError
from flask_wtf.csrf import CSRFProtect
from werkzeug.exceptions import abort # For 404 errors

from forms import RegistrationForm, LoginForm, EmployeeForm, HazardForm, ExposureForm, HealthRecordForm # Added HealthRecordForm

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'your_default_secret_key_here')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../instance/ohms.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
csrf = CSRFProtect()

db.init_app(app)
bcrypt.init_app(app)
login_manager.init_app(app)
csrf.init_app(app)

login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Import models
# Ensure models.py is in the same directory or adjust import path accordingly
from models import User, Employee, Hazard, Exposure, HealthRecord

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Context processors
@app.context_processor
def inject_nav_links():
    nav_links = []
    if current_user.is_authenticated:
        nav_links.extend([
            ('Home', 'index'),
            ('Employees', 'employees'),
            ('Hazards', 'hazards'),
            ('Exposures', 'exposures'),
            ('Health Records', 'health_records'), # Added Health Records link
            ('Logout', 'logout')
            # Add other authenticated user links here later
        ])
    else:
        nav_links.extend([
            ('Login', 'login'),
            ('Register', 'register')
        ])
    return dict(nav_links=nav_links)

# Routes
@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data

        user = User(username=username, email=email)
        try:
            # Model's set_password might have additional validation (e.g. complexity)
            user.set_password(password)
        except ValueError as e:
            flash(str(e), 'danger')
            return render_template('register.html', form=form)

        try:
            db.session.add(user)
            db.session.commit()
            flash('Your account has been created! You are now able to log in.', 'success')
            return redirect(url_for('login'))
        except IntegrityError:
            db.session.rollback()
            # Check if username or email already exists from form data
            existing_user_username = User.query.filter_by(username=form.username.data).first()
            existing_user_email = User.query.filter_by(email=form.email.data).first()
            if existing_user_username:
                flash('Username already exists. Please choose a different one.', 'danger')
            elif existing_user_email:
                flash('Email already registered. Please use a different one or log in.', 'danger')
            else:
                flash('An unexpected error occurred. Please try again.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {e}', 'danger')

    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        remember = form.remember.data

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating last login: {e}', 'warning')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Login Unsuccessful. Please check username and password.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback() # Rollback in case of DB errors leading to 500
    return render_template('500.html'), 500

# Employee CRUD Routes
@app.route('/employees')
@login_required
def employees():
    all_employees = Employee.query.all()
    return render_template('employees.html', employees=all_employees)

@app.route('/employee/add', methods=['GET', 'POST'])
@login_required
def add_employee():
    form = EmployeeForm()
    if form.validate_on_submit():
        try:
            # DateFields are converted to datetime.date objects by WTForms
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
            return redirect(url_for('employees'))
        except ValueError as e: # Catch validation errors from model
            db.session.rollback()
            flash(f'Error adding employee: {e}', 'danger')
        except IntegrityError: # Should not happen if form validation is robust for unique fields (none here)
            db.session.rollback()
            flash('Error: An employee with similar critical details already exists.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'An unexpected error occurred: {e}', 'danger')
    return render_template('employee_form.html', form=form, title='Add Employee')

@app.route('/employee/<int:employee_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    form = EmployeeForm(obj=employee) # Populate form with existing data on GET

    if form.validate_on_submit():
        try:
            form.populate_obj(employee) # Update employee object with form data
            db.session.commit()
            flash('Employee updated successfully.', 'success')
            return redirect(url_for('employees'))
        except ValueError as e: # Catch validation errors from model
            db.session.rollback()
            flash(f'Error updating employee: {e}', 'danger')
        except IntegrityError:
            db.session.rollback()
            flash('Error: Could not update employee due to a data conflict.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'An unexpected error occurred: {e}', 'danger')

    # For GET request or if form validation fails, render the form again
    return render_template('employee_form.html', form=form, title='Edit Employee', employee_id=employee_id)

@app.route('/employee/<int:employee_id>/delete', methods=['POST'])
@login_required
def delete_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    try:
        db.session.delete(employee)
        db.session.commit()
        flash('Employee deleted successfully.', 'success')
    except IntegrityError: # If deletion violates foreign key constraints (e.g. employee has related records not set to cascade delete)
        db.session.rollback()
        flash('Error: Cannot delete this employee as they have related records (e.g., exposures, health records). Please remove those first.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'An unexpected error occurred: {e}', 'danger')
    return redirect(url_for('employees'))

# Hazard CRUD Routes
@app.route('/hazards')
@login_required
def hazards():
    all_hazards = Hazard.query.all()
    return render_template('hazards.html', hazards=all_hazards)

@app.route('/hazard/add', methods=['GET', 'POST'])
@login_required
def add_hazard():
    form = HazardForm()
    if form.validate_on_submit():
        try:
            hazard = Hazard(
                name=form.name.data,
                category=form.category.data,
                exposure_limit=form.exposure_limit.data,
                unit=form.unit.data,
                description=form.description.data,
                safety_measures=form.safety_measures.data
            )
            db.session.add(hazard)
            db.session.commit()
            flash('Hazard added successfully.', 'success')
            return redirect(url_for('hazards'))
        except ValueError as e: # Catch validation errors from model (e.g. exposure_limit < 0)
            db.session.rollback()
            flash(f'Error adding hazard: {e}', 'danger')
        except IntegrityError: # e.g. if hazard name had a unique constraint
            db.session.rollback()
            flash('Error: This hazard might already exist or conflicts with existing data.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'An unexpected error occurred: {e}', 'danger')
    return render_template('hazard_form.html', form=form, title='Add Hazard')

@app.route('/hazard/<int:hazard_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_hazard(hazard_id):
    hazard = Hazard.query.get_or_404(hazard_id)
    form = HazardForm(obj=hazard) # Populate form with existing data on GET

    if form.validate_on_submit():
        try:
            form.populate_obj(hazard) # Update hazard object with form data
            db.session.commit()
            flash('Hazard updated successfully.', 'success')
            return redirect(url_for('hazards'))
        except ValueError as e: # Catch validation errors from model
            db.session.rollback()
            flash(f'Error updating hazard: {e}', 'danger')
        except IntegrityError:
            db.session.rollback()
            flash('Error: Could not update hazard due to a data conflict.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'An unexpected error occurred: {e}', 'danger')

    return render_template('hazard_form.html', form=form, title='Edit Hazard', hazard_id=hazard_id)

@app.route('/hazard/<int:hazard_id>/delete', methods=['POST'])
@login_required
def delete_hazard(hazard_id):
    hazard = Hazard.query.get_or_404(hazard_id)
    try:
        db.session.delete(hazard)
        db.session.commit()
        flash('Hazard deleted successfully.', 'success')
    except IntegrityError: # If deletion violates foreign key constraints (e.g. hazard has related exposures)
        db.session.rollback()
        flash('Error: Cannot delete this hazard as it has related records (e.g., exposures). Please remove those first.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'An unexpected error occurred: {e}', 'danger')
    return redirect(url_for('hazards'))

# Exposure CRUD Routes
@app.route('/exposures')
@login_required
def exposures():
    all_exposures = Exposure.query.order_by(Exposure.date.desc()).all()
    # Consider joining with Employee and Hazard for efficiency if displaying names directly often
    # For now, template can access exposure.employee.name and exposure.hazard.name
    return render_template('exposures.html', exposures=all_exposures)

@app.route('/exposure/add', methods=['GET', 'POST'])
@login_required
def add_exposure():
    form = ExposureForm()
    form.employee.choices = [(e.id, e.name) for e in Employee.query.order_by(Employee.name).all()]
    form.hazard.choices = [(h.id, h.name) for h in Hazard.query.order_by(Hazard.name).all()]

    if form.validate_on_submit():
        try:
            exposure = Exposure(
                employee_id=form.employee.data,
                hazard_id=form.hazard.data,
                exposure_level=form.exposure_level.data,
                duration=form.duration.data,
                date=form.date.data,
                location=form.location.data,
                notes=form.notes.data,
                recorded_by=current_user.id
            )
            db.session.add(exposure)
            db.session.commit()
            flash('Exposure record added successfully.', 'success')
            return redirect(url_for('exposures'))
        except ValueError as e:
            db.session.rollback()
            flash(f'Error adding exposure record: {e}', 'danger')
        except IntegrityError:
            db.session.rollback()
            flash('Error: Could not add exposure record due to a data conflict or missing related record.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'An unexpected error occurred: {e}', 'danger')
    return render_template('exposure_form.html', form=form, title='Add Exposure Record')

@app.route('/exposure/<int:exposure_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_exposure(exposure_id):
    exposure = Exposure.query.get_or_404(exposure_id)
    form = ExposureForm(obj=exposure) # Populate form with existing data on GET

    # Populate choices for SelectFields
    form.employee.choices = [(e.id, e.name) for e in Employee.query.order_by(Employee.name).all()]
    form.hazard.choices = [(h.id, h.name) for h in Hazard.query.order_by(Hazard.name).all()]

    if request.method == 'GET':
        # Set the data for SelectFields explicitly if obj doesn't handle it perfectly for IDs
        form.employee.data = exposure.employee_id
        form.hazard.data = exposure.hazard_id
        # For other fields, obj=exposure should handle it. Date needs to be in correct object format.
        # form.date.data = exposure.date # WTForms DateField usually handles date objects well with obj

    if form.validate_on_submit():
        try:
            exposure.employee_id = form.employee.data
            exposure.hazard_id = form.hazard.data
            exposure.exposure_level = form.exposure_level.data
            exposure.duration = form.duration.data
            exposure.date = form.date.data
            exposure.location = form.location.data
            exposure.notes = form.notes.data
            # recorded_by typically doesn't change on edit, or it becomes "last_edited_by"

            db.session.commit()
            flash('Exposure record updated successfully.', 'success')
            return redirect(url_for('exposures'))
        except ValueError as e:
            db.session.rollback()
            flash(f'Error updating exposure record: {e}', 'danger')
        except IntegrityError:
            db.session.rollback()
            flash('Error: Could not update exposure record due to a data conflict.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'An unexpected error occurred: {e}', 'danger')

    return render_template('exposure_form.html', form=form, title='Edit Exposure Record', exposure_id=exposure_id)

@app.route('/exposure/<int:exposure_id>/delete', methods=['POST'])
@login_required
def delete_exposure(exposure_id):
    exposure = Exposure.query.get_or_404(exposure_id)
    try:
        db.session.delete(exposure)
        db.session.commit()
        flash('Exposure record deleted successfully.', 'success')
    except IntegrityError: # Should not typically happen for simple delete unless DB rules are very strict
        db.session.rollback()
        flash('Error: Could not delete exposure record due to a data conflict.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'An unexpected error occurred: {e}', 'danger')
    return redirect(url_for('exposures'))

# HealthRecord CRUD Routes
@app.route('/health_records')
@login_required
def health_records():
    all_records = HealthRecord.query.order_by(HealthRecord.date.desc()).all()
    return render_template('health_records.html', health_records=all_records)

@app.route('/health_record/add', methods=['GET', 'POST'])
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
            return redirect(url_for('health_records'))
        except IntegrityError:
            db.session.rollback()
            flash('Error: Could not add health record due to a data conflict or missing related employee.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'An unexpected error occurred: {e}', 'danger')
    return render_template('health_record_form.html', form=form, title='Add Health Record')

@app.route('/health_record/<int:record_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_health_record(record_id):
    record = HealthRecord.query.get_or_404(record_id)
    form = HealthRecordForm(obj=record)
    form.employee.choices = [(e.id, e.name) for e in Employee.query.order_by(Employee.name).all()]

    if request.method == 'GET':
        form.employee.data = record.employee_id
        # Date fields are usually handled correctly by obj=record

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
            return redirect(url_for('health_records'))
        except IntegrityError:
            db.session.rollback()
            flash('Error: Could not update health record due to a data conflict.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'An unexpected error occurred: {e}', 'danger')

    return render_template('health_record_form.html', form=form, title='Edit Health Record', record_id=record_id)

@app.route('/health_record/<int:record_id>/delete', methods=['POST'])
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
    return redirect(url_for('health_records'))

if __name__ == '__main__':
    # Create database and tables if they don't exist
    # This is generally better handled with Flask-Migrate for production apps
    with app.app_context():
        db.create_all()
    app.run(debug=True)
