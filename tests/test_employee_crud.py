import unittest
from datetime import date
from flask import url_for # For checking redirects more robustly
from tests.test_config import BasicTests
from app import db # Import db from app package
from app.models import User, Employee
# from app.forms import EmployeeForm # Not strictly needed if testing through routes

class TestEmployeeCRUD(BasicTests):

    def setUp(self):
        super().setUp()
        # Create a standard user for login in tests
        self.test_user = User(username='testuser', email='test@example.com')
        self.test_user.set_password('TestPass123!')
        db.session.add(self.test_user)
        db.session.commit()

    def _login_test_user(self):
        # URLs for login are now under /auth blueprint
        return self.client.post(url_for('auth.login'), data=dict(
            username='testuser',
            password='TestPass123!'
        ), follow_redirects=True)

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
            self.assertTrue(response.location.endswith(url_for('auth.login')), f"Endpoint {endpoint} did not redirect to login.")

        # Test POST separately for delete
        response_post_delete = self.client.post(url_for('employees.delete_employee', employee_id=1), follow_redirects=False)
        self.assertEqual(response_post_delete.status_code, 302)
        self.assertTrue(response_post_delete.location.endswith(url_for('auth.login')))

        # Log back in the test_user for subsequent tests if they don't log in themselves
        self._login_test_user()


    def test_list_employees(self):
        # self._login_test_user() # User is logged in via setUp or previous test's re-login
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

    def test_add_employee_get(self):
        # self._login_test_user()
        response = self.client.get(url_for('employees.add_employee'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Add Employee', response.data)

    def test_add_employee_post_success(self):
        # self._login_test_user()
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
        self.assertTrue(response.location.endswith(url_for('employees.list_employees')), f"Redirected to {response.location} instead of employees list")

        # Check flash message after redirect
        redirect_response = self.client.get(response.location, follow_redirects=True)
        self.assertIn(b'Employee added successfully.', redirect_response.data)

        # Verify employee in DB
        employee = Employee.query.filter_by(name='Jane Smith').first()
        self.assertIsNotNone(employee)
        self.assertEqual(employee.job_title, 'Developer')
        self.assertEqual(employee.hire_date, date(2023,3,15)) # Compare with date object

    def test_add_employee_post_validation_error(self):
        # self._login_test_user()
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
    #     # self._login_test_user()
    #     response = self.client.post(url_for('employees.add_employee'), data={
    #         'name': 'Model Test', 'job_title': 'Model Job', 'department': 'Model Dept',
    #         'contact_number': 'Invalid Phone Format That Is Too Long For Column Or Fails Regex'
    #     }, follow_redirects=True)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertIn(b'Error adding employee: Invalid phone number format', response.data) # Assuming this flash message

    def test_edit_employee_get_and_post_success(self):
        # self._login_test_user()
        emp = Employee(name='Edit Me', job_title='Old Title', department='Old Dept', hire_date=date(2022,1,1))
        db.session.add(emp)
        db.session.commit()
        employee_id = emp.id

        # GET request
        response_get = self.client.get(url_for('employees.edit_employee', employee_id=employee_id))
        self.assertEqual(response_get.status_code, 200)
        self.assertIn(b'Edit Employee', response_get.data)
        self.assertIn(b'Edit Me', response_get.data) # Check if current name is in form

        # POST request (success)
        updated_data = {
            'name': 'Edited Name',
            'job_title': 'New Title',
            'department': 'New Dept',
            'hire_date': '2022-02-01',
            'date_of_birth': emp.date_of_birth.strftime('%Y-%m-%d') if emp.date_of_birth else '',
            'contact_number': emp.contact_number or '',
            'emergency_contact': emp.emergency_contact or '',
            'emergency_phone': emp.emergency_phone or ''
        }
        response_post = self.client.post(url_for('employees.edit_employee', employee_id=employee_id), data=updated_data, follow_redirects=False)
        self.assertEqual(response_post.status_code, 302)
        self.assertTrue(response_post.location.endswith(url_for('employees.list_employees')))

        # Check flash message
        redirect_response = self.client.get(response_post.location)
        self.assertIn(b'Employee updated successfully.', redirect_response.data)

        # Verify update in DB
        updated_emp = Employee.query.get(employee_id)
        self.assertEqual(updated_emp.name, 'Edited Name')
        self.assertEqual(updated_emp.job_title, 'New Title')

    def test_edit_employee_non_existent(self):
        # self._login_test_user()
        response_get = self.client.get(url_for('employees.edit_employee', employee_id=9999)) # Non-existent ID
        self.assertEqual(response_get.status_code, 404)

        response_post = self.client.post(url_for('employees.edit_employee', employee_id=9999), data={'name': 'TryingToEdit'})
        self.assertEqual(response_post.status_code, 404)


    def test_delete_employee_success(self):
        # self._login_test_user()
        emp = Employee(name='Delete Me', job_title='Deleter', department='HR', hire_date=date(2021,1,1))
        db.session.add(emp)
        db.session.commit()
        employee_id = emp.id

        response = self.client.post(url_for('employees.delete_employee', employee_id=employee_id), follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith(url_for('employees.list_employees')))

        # Check flash message
        redirect_response = self.client.get(response.location)
        self.assertIn(b'Employee deleted successfully.', redirect_response.data)

        # Verify deletion from DB
        deleted_emp = Employee.query.get(employee_id)
        self.assertIsNone(deleted_emp)

    def test_delete_employee_non_existent(self):
        # self._login_test_user()
        response = self.client.post(url_for('employees.delete_employee', employee_id=9999)) # Non-existent ID
        self.assertEqual(response.status_code, 404)


if __name__ == '__main__':
    unittest.main()
