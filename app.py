from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, Response
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from models import db, Employee, Hazard, Exposure, HealthRecord, User, bcrypt
from datetime import datetime
from functools import wraps
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import os
import csv

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ohms.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or os.urandom(24)
app.config['PER_PAGE'] = 10

db.init_app(app)
bcrypt.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

def limit_api_calls(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated

@app.context_processor
def inject_nav_links():
    return dict(
        nav_links=[
            ("Home", 'index'),
            ("Employees", 'manage_employees'),
            ("Hazards", 'manage_hazards'),
            ("Exposures", 'manage_exposures'),
            ("Health", 'manage_health'),
            ("Logout", 'logout')
        ] if current_user.is_authenticated else [
            ("Login", 'login'),
            ("Register", 'register')
        ]
    )

@app.route('/')
@login_required
def index():
    return render_template('index.html')

# --- Authentication Routes ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        email = request.form.get('email')

        errors = False
        if not username or not password:
            flash('Username and password are required.', 'error')
            errors = True
        if len(password) < 8 or not any(c.isdigit() for c in password):
            flash('Password must be at least 8 characters and include a number.', 'error')
            errors = True
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            errors = True
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            errors = True
        if email and User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            errors = True

        if errors:
            return redirect(url_for('register'))

        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            db.session.commit()
            return redirect(url_for('index'))
        flash('Invalid login.', 'error')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# --- Employee Management ---
@app.route('/employees', methods=['GET', 'POST'])
@login_required
def manage_employees():
    if request.method == 'POST':
        name = request.form.get('name')
        job_title = request.form.get('job_title')
        department = request.form.get('department')
        contact_number = request.form.get('contact_number')

        if not all([name, job_title, department]):
            flash('All fields except contact number are required.', 'error')
        else:
            employee = Employee(name=name, job_title=job_title, department=department, contact_number=contact_number)
            db.session.add(employee)
            db.session.commit()
            flash('Employee added successfully.', 'success')
        return redirect(url_for('manage_employees'))

    employees = Employee.query.order_by(Employee.name).all()
    return render_template('employees.html', employees=employees)

@app.route('/employees/edit/<int:emp_id>', methods=['GET', 'POST'])
@login_required
def edit_employee(emp_id):
    employee = Employee.query.get_or_404(emp_id)
    if request.method == 'POST':
        employee.name = request.form.get('name')
        employee.job_title = request.form.get('job_title')
        employee.department = request.form.get('department')
        employee.contact_number = request.form.get('contact_number')
        db.session.commit()
        flash('Employee updated successfully.', 'success')
        return redirect(url_for('manage_employees'))
    return render_template('edit_employee.html', employee=employee)

@app.route('/employees/delete/<int:emp_id>')
@login_required
def delete_employee(emp_id):
    employee = Employee.query.get_or_404(emp_id)
    db.session.delete(employee)
    db.session.commit()
    flash('Employee deleted.', 'info')
    return redirect(url_for('manage_employees'))

# --- Hazard Management ---
@app.route('/hazards', methods=['GET', 'POST'])
@login_required
def manage_hazards():
    if request.method == 'POST':
        name = request.form.get('name')
        category = request.form.get('category')
        exposure_limit = request.form.get('exposure_limit')
        unit = request.form.get('unit')
        safety_measures = request.form.get('safety_measures')

        if not all([name, category, exposure_limit]):
            flash('Name, category, and exposure limit are required.', 'error')
        else:
            try:
                hazard = Hazard(name=name, category=category, exposure_limit=float(exposure_limit),
                                unit=unit or 'mg/m³', safety_measures=safety_measures)
                db.session.add(hazard)
                db.session.commit()
                flash('Hazard added.', 'success')
            except ValueError:
                flash('Exposure limit must be a number.', 'error')
        return redirect(url_for('manage_hazards'))

    hazards = Hazard.query.order_by(Hazard.name).all()
    return render_template('hazards.html', hazards=hazards)

@app.route('/hazards/edit/<int:hazard_id>', methods=['GET', 'POST'])
@login_required
def edit_hazard(hazard_id):
    hazard = Hazard.query.get_or_404(hazard_id)
    if request.method == 'POST':
        hazard.name = request.form.get('name')
        hazard.category = request.form.get('category')
        hazard.unit = request.form.get('unit')
        hazard.safety_measures = request.form.get('safety_measures')
        try:
            hazard.exposure_limit = float(request.form.get('exposure_limit'))
            db.session.commit()
            flash('Hazard updated.', 'success')
        except ValueError:
            flash('Exposure limit must be a number.', 'error')
        return redirect(url_for('manage_hazards'))
    return render_template('edit_hazard.html', hazard=hazard)

@app.route('/hazards/delete/<int:hazard_id>')
@login_required
def delete_hazard(hazard_id):
    hazard = Hazard.query.get_or_404(hazard_id)
    db.session.delete(hazard)
    db.session.commit()
    flash('Hazard deleted.', 'info')
    return redirect(url_for('manage_hazards'))

# --- Exposure Management ---
@app.route('/exposures', methods=['GET', 'POST'])
@login_required
def manage_exposures():
    employees = Employee.query.order_by(Employee.name).all()
    hazards = Hazard.query.order_by(Hazard.name).all()

    if request.method == 'POST':
        try:
            exposure = Exposure(
                employee_id=request.form.get('employee_id'),
                hazard_id=request.form.get('hazard_id'),
                exposure_level=float(request.form.get('exposure_level')),
                duration=float(request.form.get('duration')) if request.form.get('duration') else None,
                location=request.form.get('location'),
                notes=request.form.get('notes'),
                recorded_by=current_user.id
            )
            db.session.add(exposure)
            db.session.commit()
            flash('Exposure recorded.', 'success')
        except ValueError:
            flash('Exposure level and duration must be numbers.', 'error')
        return redirect(url_for('manage_exposures'))

    exposures = Exposure.query.order_by(Exposure.date.desc()).all()
    return render_template('exposures.html', employees=employees, hazards=hazards, exposures=exposures)

@app.route('/exposures/edit/<int:exposure_id>', methods=['GET', 'POST'])
@login_required
def edit_exposure(exposure_id):
    exposure = Exposure.query.get_or_404(exposure_id)
    employees = Employee.query.order_by(Employee.name).all()
    hazards = Hazard.query.order_by(Hazard.name).all()

    if request.method == 'POST':
        try:
            exposure.employee_id = request.form.get('employee_id')
            exposure.hazard_id = request.form.get('hazard_id')
            exposure.exposure_level = float(request.form.get('exposure_level'))
            exposure.duration = float(request.form.get('duration')) if request.form.get('duration') else None
            exposure.location = request.form.get('location')
            exposure.notes = request.form.get('notes')
            db.session.commit()
            flash('Exposure updated.', 'success')
            return redirect(url_for('manage_exposures'))
        except ValueError:
            flash('Exposure level and duration must be numeric.', 'error')

    return render_template('edit_exposure.html', exposure=exposure, employees=employees, hazards=hazards)

@app.route('/exposures/delete/<int:exposure_id>')
@login_required
def delete_exposure(exposure_id):
    exposure = Exposure.query.get_or_404(exposure_id)
    db.session.delete(exposure)
    db.session.commit()
    flash('Exposure deleted.', 'info')
    return redirect(url_for('manage_exposures'))

# --- Health Management ---
@app.route('/health', methods=['GET', 'POST'])
@login_required
def manage_health():
    employees = Employee.query.order_by(Employee.name).all()

    if request.method == 'POST':
        record = HealthRecord(
            employee_id=request.form.get('employee_id'),
            test_type=request.form.get('test_type'),
            result=request.form.get('result'),
            details=request.form.get('details'),
            date=datetime.strptime(request.form.get('date'), '%Y-%m-%d'),
            next_test_date=datetime.strptime(request.form.get('next_test_date'), '%Y-%m-%d') if request.form.get('next_test_date') else None,
            physician=request.form.get('physician'),
            facility=request.form.get('facility'),
            recorded_by=current_user.id
        )
        db.session.add(record)
        db.session.commit()
        flash('Health record added.', 'success')
        return redirect(url_for('manage_health'))

    records = HealthRecord.query.order_by(HealthRecord.date.desc()).all()
    return render_template('health.html', employees=employees, records=records)

@app.route('/health/edit/<int:record_id>', methods=['GET', 'POST'])
@login_required
def edit_health(record_id):
    record = HealthRecord.query.get_or_404(record_id)
    employees = Employee.query.order_by(Employee.name).all()

    if request.method == 'POST':
        record.employee_id = request.form.get('employee_id')
        record.test_type = request.form.get('test_type')
        record.result = request.form.get('result')
        record.details = request.form.get('details')
        record.date = datetime.strptime(request.form.get('date'), '%Y-%m-%d')
        record.next_test_date = datetime.strptime(request.form.get('next_test_date'), '%Y-%m-%d') if request.form.get('next_test_date') else None
        record.physician = request.form.get('physician')
        record.facility = request.form.get('facility')
        db.session.commit()
        flash('Health record updated.', 'success')
        return redirect(url_for('manage_health'))

    return render_template('edit_health.html', record=record, employees=employees)

@app.route('/health/delete/<int:record_id>')
@login_required
def delete_health(record_id):
    record = HealthRecord.query.get_or_404(record_id)
    db.session.delete(record)
    db.session.commit()
    flash('Health record deleted.', 'info')
    return redirect(url_for('manage_health'))
@app.route('/init_db')
def init_db():
    db.create_all()
    return 'Database initialized!'
# Temporary route to initialize database manually
@app.route('/init_db')
def init_db():
    with app.app_context():
        db.create_all()
    return "Database initialized successfully!"

# --- Run ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
