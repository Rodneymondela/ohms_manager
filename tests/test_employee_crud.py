import unittest
from datetime import date
from flask import url_for
from urllib.parse import urlparse, parse_qs
from tests.test_config import BasicTests
from app import db
from app.models import User, Employee, ROLE_USER, ROLE_ADMIN # Import roles
# from app.forms import EmployeeForm # Not strictly needed if testing through routes

class TestEmployeeCRUD(BasicTests):

    def setUp(self):
        super().setUp()
        # Create a standard user (default role is ROLE_USER)
        self.test_user = User(username='testuser', email='testuser@example.com')
        self.test_user.set_password('TestPass123!')

        # Create an admin user
        self.admin_user = User(username='adminuser', email='admin@example.com', role=ROLE_ADMIN)
        self.admin_user.set_password('AdminPass123!')

        db.session.add_all([self.test_user, self.admin_user])
        db.session.commit()

    def _login_user(self, username, password):
        return self.client.post(url_for('auth.login'), data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def _login_test_user(self): # Regular user
        return self._login_user('testuser', 'TestPass123!')

    def _login_admin_user(self): # Admin user
        return self._login_user('adminuser', 'AdminPass123!')

    def test_access_control_unauthenticated(self):
        # Log out the setup user first
        with self.client as c: # Use client to maintain session for logout
             c.get(url_for('auth.logout'), follow_redirects=True)

        endpoints_get = [
            url_for('employees.list_employees'),
            url_for('employees.add_employee'),
            url_for('employees.edit_employee', employee_id=1), # Assumes an employee with ID 1
        ]
        for endpoint in endpoints_get:
            response = self.client.get(endpoint, follow_redirects=False)
            self.assertEqual(response.status_code, 302, f"Endpoint {endpoint} did not redirect.")
            parsed_location = urlparse(response.location)
            expected_login_path = url_for('auth.login', _external=False)
            self.assertEqual(parsed_location.path, expected_login_path)

            # endpoint is absolute, query_params['next'][0] is relative.
            # We need to compare relative paths.
            endpoint_path = urlparse(endpoint).path
            if endpoint_path != expected_login_path:
                 query_params = parse_qs(parsed_location.query)
                 self.assertIn('next', query_params)
                 self.assertEqual(query_params['next'][0], endpoint_path)


        # Test POST separately for delete
        delete_endpoint_url = url_for('employees.delete_employee', employee_id=1) # This is absolute
        delete_endpoint_path = urlparse(delete_endpoint_url).path # Get relative path
        response_post_delete = self.client.post(delete_endpoint_url, follow_redirects=False)
        self.assertEqual(response_post_delete.status_code, 302)
        parsed_location_post = urlparse(response_post_delete.location)
        expected_login_path_post = url_for('auth.login', _external=False)
        self.assertEqual(parsed_location_post.path, expected_login_path_post)
        query_params_post = parse_qs(parsed_location_post.query)
        self.assertIn('next', query_params_post)
        self.assertEqual(query_params_post['next'][0], delete_endpoint_path)

        # No re-login here, each test handles its own


    def test_list_employees(self):
        # Listing should be available to regular logged-in users too.
        self._login_test_user()
        response = self.client.get(url_for('employees.list_employees'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Manage Employees', response.data)
        self.assertIn(b'No employees found.', response.data) # Initially empty

        # Add an employee and check again
        emp = Employee(name='John Doe', job_title='Engineer', department='Tech', hire_date=date(2023,1,1))
        db.session.add(emp)
        db.session.commit()

        response = self.client.get(url_for('employees.list_employees'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'John Doe', response.data)
        self.assertNotIn(b'No employees found.', response.data)

    def test_add_employee_get_by_admin(self): # Renamed
        self._login_admin_user()
        response = self.client.get(url_for('employees.add_employee'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Add Employee', response.data)

    def test_add_employee_get_by_regular_user_permission_denied(self):
        self._login_test_user()
        response = self.client.get(url_for('employees.add_employee'), follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Followed redirect
        self.assertIn(b'You do not have permission to access this page.', response.data)
        self.assertEqual(urlparse(response.request.base_url).path, url_for('main.index', _external=False))

    def test_add_employee_post_by_admin_success(self): # Renamed
        self._login_admin_user()
        employee_data = {
            'name': 'Jane Smith',
            'job_title': 'Developer',
            'department': 'Engineering',
            'hire_date': '2023-03-15', # String format as it comes from form
            'date_of_birth': '1990-05-20',
            'contact_number': '1234567890',
            'emergency_contact': 'Emergency Jane',
            'emergency_phone': '0987654321'
        }
        response = self.client.post(url_for('employees.add_employee'), data=employee_data, follow_redirects=False)

        self.assertEqual(response.status_code, 302, "Form submission did not redirect.")
        self.assertEqual(urlparse(response.location).path, url_for('employees.list_employees', _external=False))

        # Check flash message after redirect
        redirect_response = self.client.get(response.location, follow_redirects=True)
        self.assertIn(b'Employee added successfully.', redirect_response.data)

        # Verify employee in DB
        employee = Employee.query.filter_by(name='Jane Smith').first()
        self.assertIsNotNone(employee)
        self.assertEqual(employee.job_title, 'Developer')
        self.assertEqual(employee.hire_date, date(2023,3,15)) # Compare with date object

    def test_add_employee_post_by_regular_user_permission_denied(self):
        self._login_test_user()
        employee_data = {
            'name': 'Jane Smith NonAdmin', 'job_title': 'Developer', 'department': 'Engineering',
            'hire_date': '2023-03-15', 'date_of_birth': '1990-05-20',
            'contact_number': '1234567890', 'emergency_contact': 'Emergency Jane', 'emergency_phone': '0987654321'
        }
        response = self.client.post(url_for('employees.add_employee'), data=employee_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Followed redirect
        self.assertIn(b'You do not have permission to access this page.', response.data)
        self.assertEqual(urlparse(response.request.base_url).path, url_for('main.index', _external=False))
        self.assertIsNone(Employee.query.filter_by(name='Jane Smith NonAdmin').first())

    def test_add_employee_post_validation_error_by_admin(self): # Renamed
        self._login_admin_user() # Admin can still submit invalid data
        response = self.client.post(url_for('employees.add_employee'), data={
            'name': '', # Name is required
            'job_title': 'Tester',
            'department': 'QA'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Stays on form page
        self.assertIn(b'This field is required.', response.data) # WTForms error for name

        employee = Employee.query.filter_by(job_title='Tester').first()
        self.assertIsNone(employee) # Employee should not have been created

    # Test for model validation (e.g. phone number format) would require a specific setup
    # or a value known to trigger the model's validator if it's more specific than length.
    # For now, the form's length validation is what we primarily test for contact_number.
    # If app.py's add_employee route flashes a specific error for model's ValueError, we could test that.
    # Example:
    # def test_add_employee_post_model_validation_error(self):
    #     self._login_test_user() # Add this if test is uncommented
    #     response = self.client.post(url_for('employees.add_employee'), data={
    #         'name': 'Model Test', 'job_title': 'Model Job', 'department': 'Model Dept',
    #         'contact_number': 'Invalid Phone Format That Is Too Long For Column Or Fails Regex'
    #     }, follow_redirects=True)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertIn(b'Error adding employee: Invalid phone number format', response.data) # Assuming this flash message

    def test_edit_employee_get_by_admin(self): # Renamed and split
        self._login_admin_user()
        emp = Employee(name='Edit Me', job_title='Old Title', department='Old Dept', hire_date=date(2022,1,1))
        db.session.add(emp)
        db.session.commit()
        employee_id = emp.id

        response_get = self.client.get(url_for('employees.edit_employee', employee_id=employee_id))
        self.assertEqual(response_get.status_code, 200)
        self.assertIn(b'Edit Employee', response_get.data)
        self.assertIn(b'Edit Me', response_get.data)

    def test_edit_employee_get_by_regular_user_permission_denied(self):
        self._login_test_user()
        emp = Employee(name='Edit Me Protected', job_title='Old Title', department='Old Dept', hire_date=date(2022,1,1))
        db.session.add(emp)
        db.session.commit()
        employee_id = emp.id

        response_get = self.client.get(url_for('employees.edit_employee', employee_id=employee_id), follow_redirects=True)
        self.assertEqual(response_get.status_code, 200) # Followed redirect
        self.assertIn(b'You do not have permission to access this page.', response_get.data)
        self.assertEqual(urlparse(response_get.request.base_url).path, url_for('main.index', _external=False))

    def test_edit_employee_post_by_admin_success(self): # Renamed and split
        self._login_admin_user()
        emp = Employee(name='To Be Edited by Admin', job_title='Initial Title', department='Initial Dept', hire_date=date(2022,1,1))
        db.session.add(emp)
        db.session.commit()
        employee_id = emp.id

        updated_data = {
            'name': 'Admin Edited Name', 'job_title': 'Admin New Title', 'department': 'Admin New Dept',
            'hire_date': '2022-02-02', 'date_of_birth': '', 'contact_number': '',
            'emergency_contact': '', 'emergency_phone': ''
        }
        response_post = self.client.post(url_for('employees.edit_employee', employee_id=employee_id), data=updated_data, follow_redirects=False)
        self.assertEqual(response_post.status_code, 302)
        self.assertEqual(urlparse(response_post.location).path, url_for('employees.list_employees', _external=False))

        redirect_response = self.client.get(response_post.location, follow_redirects=True)
        self.assertIn(b'Employee updated successfully.', redirect_response.data)

        updated_emp = Employee.query.get(employee_id)
        self.assertEqual(updated_emp.name, 'Admin Edited Name')
        self.assertEqual(updated_emp.job_title, 'Admin New Title')

    def test_edit_employee_post_by_regular_user_permission_denied(self):
        self._login_test_user()
        emp_initial_name = 'User Edit Test Original'
        emp = Employee(name=emp_initial_name, job_title='User Initial Title', department='User Initial Dept', hire_date=date(2022,3,3))
        db.session.add(emp)
        db.session.commit()
        employee_id = emp.id

        updated_data = {'name': 'User Edited Name Attempt', 'job_title': 'User New Title Attempt'}
        response_post = self.client.post(url_for('employees.edit_employee', employee_id=employee_id), data=updated_data, follow_redirects=True)

        self.assertEqual(response_post.status_code, 200) # Followed redirect
        self.assertIn(b'You do not have permission to access this page.', response_post.data)
        self.assertEqual(urlparse(response_post.request.base_url).path, url_for('main.index', _external=False))

        # Verify data was not changed
        unchanged_emp = Employee.query.get(employee_id)
        self.assertEqual(unchanged_emp.name, emp_initial_name)


    def test_edit_employee_non_existent(self):
        self._login_admin_user() # Admin user for attempting to edit non-existent
        response_get = self.client.get(url_for('employees.edit_employee', employee_id=9999)) # Non-existent ID
        self.assertEqual(response_get.status_code, 404)

        response_post = self.client.post(url_for('employees.edit_employee', employee_id=9999), data={'name': 'TryingToEdit'})
        self.assertEqual(response_post.status_code, 404)

    def test_delete_employee_by_admin(self): # Renamed
        self._login_admin_user() # Log in as admin
        emp = Employee(name='Delete Me Admin', job_title='Deleter', department='HR', hire_date=date(2021,1,1))
        db.session.add(emp)
        db.session.commit()
        employee_id = emp.id

        response = self.client.post(url_for('employees.delete_employee', employee_id=employee_id), follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse(response.location).path, url_for('employees.list_employees', _external=False))

        redirect_response = self.client.get(response.location, follow_redirects=True) # Follow redirect to check flash
        self.assertIn(b'Employee deleted successfully.', redirect_response.data)

        deleted_emp = Employee.query.get(employee_id)
        self.assertIsNone(deleted_emp)

    def test_delete_employee_by_regular_user_permission_denied(self):
        self._login_test_user() # Log in as regular user
        emp_to_protect = Employee(name='Protected Emp', job_title='Survivor', department='Security', hire_date=date(2020,1,1))
        db.session.add(emp_to_protect)
        db.session.commit()
        employee_id = emp_to_protect.id

        response = self.client.post(url_for('employees.delete_employee', employee_id=employee_id), follow_redirects=True)

        # Should redirect to main.index and flash permission error
        self.assertEqual(response.status_code, 200) # After following redirect to main.index
        self.assertIn(b'You do not have permission to access this page.', response.data)
        # Check that the current URL is main.index after redirect
        self.assertEqual(urlparse(response.request.base_url).path, url_for('main.index', _external=False))

        # Verify employee still exists
        still_exists_emp = Employee.query.get(employee_id)
        self.assertIsNotNone(still_exists_emp)

    def test_delete_employee_non_existent(self):
        self._login_admin_user() # Admin user for attempting to delete non-existent
        response = self.client.post(url_for('employees.delete_employee', employee_id=9999)) # Non-existent ID
        self.assertEqual(response.status_code, 404)


if __name__ == '__main__':
    unittest.main()
