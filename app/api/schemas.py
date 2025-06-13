from flask_restx import fields
from app.api import api_restx # Import the main Api object from app/api/__init__.py

# Define the model for Employee serialization (output)
employee_output_model = api_restx.model('EmployeeOutput', {
    'id': fields.Integer(readonly=True, description='The unique identifier of an employee'),
    'name': fields.String(required=True, description='Full name of the employee'),
    'job_title': fields.String(required=True, description='Job title'),
    'department': fields.String(required=True, description='Department'),
    'hire_date': fields.Date(description='Date of hire (YYYY-MM-DD)'),
    'date_of_birth': fields.Date(description='Date of birth (YYYY-MM-DD)'),
    'contact_number': fields.String(description='Contact phone number', allow_null=True), # Allow null for optional fields
    'emergency_contact': fields.String(description='Emergency contact name', allow_null=True),
    'emergency_phone': fields.String(description='Emergency contact phone number', allow_null=True),
    'created_at': fields.DateTime(description='Timestamp of creation', dt_format='iso8601', readonly=True),
    'updated_at': fields.DateTime(description='Timestamp of last update', dt_format='iso8601', readonly=True),
    # 'exposures_url': fields.Url('api.employee_exposures_list', absolute=True, description='Link to employee specific exposures'),
    # 'health_records_url': fields.Url('api.employee_health_records_list', absolute=True, description='Link to employee specific health records')
    # Example of how related resource URLs could be added later. 'api.employee_exposures_list' would be the endpoint name.
})

# Define the model for Employee input (creation/update)
employee_input_model = api_restx.model('EmployeeInput', {
    'name': fields.String(required=True, description='Full name of the employee', min_length=1, max_length=100),
    'job_title': fields.String(required=True, description='Job title', min_length=1, max_length=100),
    'department': fields.String(required=True, description='Department', min_length=1, max_length=100),
    'hire_date': fields.Date(description='Date of hire (YYYY-MM-DD)', required=False), # allow_null=True is implicit for Date if not required
    'date_of_birth': fields.Date(description='Date of birth (YYYY-MM-DD)', required=False),
    'contact_number': fields.String(description='Contact phone number', required=False, max_length=20),
    'emergency_contact': fields.String(description='Emergency contact name', required=False, max_length=100),
    'emergency_phone': fields.String(description='Emergency contact phone number', required=False, max_length=20),
})


# We can define other models here as needed, e.g., for Hazards, Exposures, HealthRecords
# For now, just the EmployeeOutput model as requested.

# Example for a minimal Hazard model (if we were doing more in this step)
# hazard_output_model = api_restx.model('HazardOutput', {
#     'id': fields.Integer(readonly=True),
#     'name': fields.String(required=True),
#     'category': fields.String(required=True),
#     'exposure_limit': fields.Float(required=True),
#     'unit': fields.String(required=True),
# })
