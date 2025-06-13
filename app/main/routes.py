from flask import render_template
from flask_login import login_required
from app.models import Employee, Hazard, Exposure, HealthRecord # Import models
from . import main_bp

@main_bp.route('/')
@login_required
def index():
    employee_count = Employee.query.count()
    hazard_count = Hazard.query.count()
    exposure_count = Exposure.query.count()
    health_record_count = HealthRecord.query.count()

    return render_template('main/index.html',
                           title='Home',
                           employee_count=employee_count,
                           hazard_count=hazard_count,
                           exposure_count=exposure_count,
                           health_record_count=health_record_count)
