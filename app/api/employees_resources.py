from flask_restx import Resource, Namespace
from flask_login import login_required, current_user # Added current_user
from flask import current_app # Added current_app for logging
from app.models import Employee
from .schemas import employee_output_model, employee_input_model # Added employee_input_model
from app.api import api_restx
from app import db # Added db
from app.decorators import admin_required # Added admin_required
from sqlalchemy.exc import IntegrityError # Added IntegrityError

# Define the namespace for employee operations
# The path='/employees' here means the full path will be /api/v1/employees
# as api_bp has url_prefix='/api/v1' and api_restx is initialized with api_bp.
employee_ns = api_restx.namespace('employees',
                                  description='Employee related operations',
                                  path='/employees') # This path is relative to the Api object's root

@employee_ns.route('/') # Defines the route for this resource within the namespace (e.g., /api/v1/employees/)
class EmployeeListResource(Resource):
    # Apply decorators to all methods in a Resource using method_decorators
    # For this specific case, login_required is on the method.
    # method_decorators = [login_required]

    @login_required # Apply to specific method
    @employee_ns.doc('list_employees', description='List all employees')
    @employee_ns.marshal_list_with(employee_output_model)
    def get(self):
        """List all employees"""
        return Employee.query.order_by(Employee.name).all()

    @employee_ns.expect(employee_input_model, validate=True)
    @employee_ns.marshal_with(employee_output_model, code=201, description='Employee created successfully')
    @admin_required # This already implies @login_required
    def post(self):
        """Create a new employee"""
        data = employee_ns.payload

        new_employee = Employee(
            name=data['name'],
            job_title=data['job_title'],
            department=data['department'],
            hire_date=data.get('hire_date'),
            date_of_birth=data.get('date_of_birth'),
            contact_number=data.get('contact_number'),
            emergency_contact=data.get('emergency_contact'),
            emergency_phone=data.get('emergency_phone')
        )

        try:
            db.session.add(new_employee)
            db.session.commit()
            log_actor = current_user.username if current_user.is_authenticated else 'Unknown'
            current_app.logger.info(f"API: New employee '{new_employee.name}' (ID: {new_employee.id}) created by {log_actor}.")
            return new_employee, 201
        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.warning(f"API: IntegrityError creating employee '{data.get('name')}': {str(e)}", exc_info=True)
            employee_ns.abort(400, f"Database integrity error: {str(e.orig)}")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"API: Error creating employee '{data.get('name')}': {str(e)}", exc_info=True)
            employee_ns.abort(500, "Could not create employee due to an internal error.")

@employee_ns.route('/<int:employee_id>')
@employee_ns.response(404, 'Employee not found')
@employee_ns.param('employee_id', 'The employee identifier')
class EmployeeResource(Resource):
    # method_decorators = [login_required] # Could be used for class-wide protection

    @login_required # Apply to specific method
    @employee_ns.doc('get_employee', description='Get a specific employee by their ID')
    @employee_ns.marshal_with(employee_output_model) # Use marshal_with for a single object
    def get(self, employee_id):
        """Fetch a specific employee by their ID"""
        employee = Employee.query.get_or_404(employee_id)
        return employee

    @employee_ns.expect(employee_input_model, validate=True)
    @employee_ns.marshal_with(employee_output_model, description='Employee updated successfully')
    @admin_required # This also handles @login_required
    def put(self, employee_id):
        """Update an existing employee. Requires all fields to be sent (PUT semantics)."""
        employee_to_update = Employee.query.get_or_404(employee_id)
        data = employee_ns.payload

        # Update fields from payload.
        employee_to_update.name = data['name'] # Required field
        employee_to_update.job_title = data['job_title'] # Required field
        employee_to_update.department = data['department'] # Required field

        # Optional fields from input model
        employee_to_update.hire_date = data.get('hire_date')
        employee_to_update.date_of_birth = data.get('date_of_birth')
        employee_to_update.contact_number = data.get('contact_number')
        employee_to_update.emergency_contact = data.get('emergency_contact')
        employee_to_update.emergency_phone = data.get('emergency_phone')
        # updated_at is handled by SQLAlchemy's onupdate

        try:
            db.session.commit()
            log_actor = current_user.username if current_user.is_authenticated else 'Unknown'
            current_app.logger.info(f"API: Employee ID {employee_to_update.id} ('{employee_to_update.name}') updated by {log_actor}.")
            return employee_to_update
        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.warning(f"API: IntegrityError updating employee ID {employee_id}: {str(e)}", exc_info=True)
            # Provide a more specific error message if possible, e.g., from e.orig
            employee_ns.abort(400, f"Database integrity error: {str(e.orig)}")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"API: Error updating employee ID {employee_id}: {str(e)}", exc_info=True)
            employee_ns.abort(500, "Could not update employee due to an internal error.")

    @admin_required # This also handles @login_required
    @employee_ns.doc('delete_employee', description='Delete an existing employee. This will also delete associated exposure and health records due to cascading database rules.')
    @employee_ns.response(204, 'Employee (and associated exposures/health records) deleted successfully.')
    # @employee_ns.response(404, 'Employee not found.') # Already on class
    def delete(self, employee_id):
        """Delete an existing employee. Associated exposure and health records will also be deleted."""
        employee_to_delete = Employee.query.get_or_404(employee_id)

        # Safeguard against self-deletion for User model is in admin routes,
        # not directly applicable here unless Employees are also Users and can be admins.
        # For now, assume any admin can delete any employee.

        try:
            employee_name_for_log = employee_to_delete.name # Capture before deletion
            db.session.delete(employee_to_delete)
            db.session.commit()
            log_actor = current_user.username if current_user.is_authenticated else 'Unknown'
            current_app.logger.info(f"API: Employee ID {employee_id} ('{employee_name_for_log}') and associated records deleted by {log_actor}.")
            return '', 204 # Standard response for successful DELETE
        except IntegrityError as e: # Should be less likely with cascades, but good for other DB issues
            db.session.rollback()
            current_app.logger.error(f"API: IntegrityError deleting employee ID {employee_id}: {str(e)}", exc_info=True)
            employee_ns.abort(500, f"Could not delete employee due to a database integrity error: {str(e.orig)}")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"API: Error deleting employee ID {employee_id}: {str(e)}", exc_info=True)
            employee_ns.abort(500, "Could not delete employee due to an internal error.")
