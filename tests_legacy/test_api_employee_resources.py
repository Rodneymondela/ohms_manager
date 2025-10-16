import unittest
import json
from flask import url_for, current_app
from urllib.parse import urlparse
from tests.test_config import BasicTests
from app import db
from app.models import User, Employee, ROLE_USER, ROLE_ADMIN, Hazard, Exposure, HealthRecord # Added Hazard, Exposure, HealthRecord
from datetime import date, datetime # Added datetime

class TestEmployeeAPI(BasicTests):

    def setUp(self):
        super().setUp() # Sets up app context, client, and db

        self.user_regular = User(username='apiuser', email='apiuser@example.com', role=ROLE_USER)
        self.user_regular.set_password('ApiUserPass1!')

        self.admin_user = User(username='apiadmin', email='apiadmin@example.com', role=ROLE_ADMIN)
        self.admin_user.set_password('ApiAdminPass1!')

        self.employee1 = Employee(name='Alice API', job_title='API Tester', department='Tech', hire_date=date(2023,1,1))
        self.employee2 = Employee(name='Bob JSON', job_title='Data Specialist', department='Analytics', hire_date=date(2022,2,2))

        db.session.add_all([self.user_regular, self.admin_user, self.employee1, self.employee2])
        db.session.commit()

    def _login_user(self, username, password):
        return self.client.post(url_for('auth.login'), data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def _login_regular_user(self):
        return self._login_user('apiuser', 'ApiUserPass1!')

    def _login_admin_user(self):
        return self._login_user('apiadmin', 'ApiAdminPass1!')

    # --- Test GET /api/v1/employees/ (List Employees) ---
    def test_get_employee_list_unauthenticated(self):
        # Attempt to access without logging in
        response = self.client.get(url_for('api.employees_employee_list_resource'))
        # Flask-Login's @login_required redirects to HTML login page (302)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.startswith(url_for('auth.login', _external=False)))

    def test_get_employee_list_authenticated(self):
        self._login_regular_user() # Any authenticated user should be able to list
        response = self.client.get(url_for('api.employees_employee_list_resource'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        data = json.loads(response.data.decode('utf-8'))
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2) # Based on setUp

        # Check for presence of employee names (more robust check would be full data)
        employee_names = [emp['name'] for emp in data]
        self.assertIn(self.employee1.name, employee_names)
        self.assertIn(self.employee2.name, employee_names)

        # Check structure of one item
        if data:
            item = next((emp for emp in data if emp['id'] == self.employee1.id), None)
            self.assertIsNotNone(item)
            self.assertEqual(item['name'], self.employee1.name)
            self.assertEqual(item['job_title'], self.employee1.job_title)
            self.assertEqual(item['department'], self.employee1.department)
            self.assertEqual(item['hire_date'], self.employee1.hire_date.isoformat())


    # --- Test GET /api/v1/employees/<employee_id> (Get Specific Employee) ---
    def test_get_employee_detail_unauthenticated(self):
        response = self.client.get(url_for('api.employees_employee_resource', employee_id=self.employee1.id))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.startswith(url_for('auth.login', _external=False)))

    def test_get_employee_detail_authenticated_success(self):
        self._login_regular_user()
        response = self.client.get(url_for('api.employees_employee_resource', employee_id=self.employee1.id))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        data = json.loads(response.data.decode('utf-8'))
        self.assertIsInstance(data, dict)
        self.assertEqual(data['id'], self.employee1.id)
        self.assertEqual(data['name'], self.employee1.name)
        self.assertEqual(data['job_title'], self.employee1.job_title)
        self.assertEqual(data['department'], self.employee1.department)
        self.assertEqual(data['hire_date'], self.employee1.hire_date.isoformat() if self.employee1.hire_date else None)
        self.assertIn('created_at', data) # Check presence of datetime fields
        self.assertIn('updated_at', data)

    def test_get_employee_detail_not_found(self):
        self._login_regular_user()
        non_existent_id = 99999
        response = self.client.get(url_for('api.employees_employee_resource', employee_id=non_existent_id))
        # Flask-RESTX and get_or_404 should result in a 404
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content_type, 'application/json') # RESTX usually returns JSON error
        data = json.loads(response.data.decode('utf-8'))
        self.assertIn('message', data) # Check for error message

    # --- Test POST /api/v1/employees/ (Create Employee) ---
    def test_create_employee_by_admin_success(self):
        self._login_admin_user()
        employee_data = {
            'name': 'Charlie New',
            'job_title': 'Intern',
            'department': 'Development',
            'hire_date': '2024-01-01',
            'contact_number': '555-0101'
        }
        response = self.client.post(url_for('api.employees_employee_list_resource'), json=employee_data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content_type, 'application/json')
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['name'], employee_data['name'])
        self.assertEqual(data['job_title'], employee_data['job_title'])
        self.assertTrue(Employee.query.filter_by(name=employee_data['name']).first() is not None)

    def test_create_employee_by_regular_user_permission_denied(self):
        self._login_regular_user()
        employee_data = {'name': 'Denied User', 'job_title': 'Tester', 'department': 'QA'}
        response = self.client.post(url_for('api.employees_employee_list_resource'), json=employee_data, follow_redirects=True)
        # The admin_required decorator redirects to main.index and flashes a message
        self.assertEqual(response.status_code, 200) # After redirect
        self.assertTrue(urlparse(response.request.base_url).path.endswith(url_for('main.index', _external=False)))
        self.assertIn(b'You must be an administrator to access this page.', response.data)


    def test_create_employee_missing_required_field_by_admin(self):
        self._login_admin_user()
        employee_data = {'job_title': 'Missing Name', 'department': 'Mystery'} # Name is missing
        response = self.client.post(url_for('api.employees_employee_list_resource'), json=employee_data)
        self.assertEqual(response.status_code, 400) # Flask-RESTX .expect handles this
        data = json.loads(response.data.decode('utf-8'))
        self.assertIn('errors', data)
        self.assertIn('name', data['errors'])


    # --- Test PUT /api/v1/employees/<employee_id> (Update Employee) ---
    def test_update_employee_by_admin_success(self):
        self._login_admin_user()
        update_data = {'name': self.employee1.name, 'job_title': 'Senior API Tester', 'department': 'Advanced Tech'}
        response = self.client.put(url_for('api.employees_employee_resource', employee_id=self.employee1.id), json=update_data)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['job_title'], 'Senior API Tester')
        self.assertEqual(data['department'], 'Advanced Tech')
        db.session.refresh(self.employee1) # Refresh from DB
        self.assertEqual(self.employee1.job_title, 'Senior API Tester')

    def test_update_employee_by_regular_user_permission_denied(self):
        self._login_regular_user()
        update_data = {'name': self.employee1.name, 'job_title': 'Attempted Update', 'department': self.employee1.department}
        response = self.client.put(url_for('api.employees_employee_resource', employee_id=self.employee1.id), json=update_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200) # After redirect
        self.assertTrue(urlparse(response.request.base_url).path.endswith(url_for('main.index', _external=False)))
        self.assertIn(b'You must be an administrator to access this page.', response.data)


    def test_update_employee_invalid_data_by_admin(self):
        self._login_admin_user()
        update_data = {'name': '', 'job_title': 'No Name Job', 'department': 'Validation Test'} # Empty name
        response = self.client.put(url_for('api.employees_employee_resource', employee_id=self.employee1.id), json=update_data)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode('utf-8'))
        self.assertIn('errors', data)
        self.assertIn('name', data['errors'])

    def test_update_nonexistent_employee_by_admin(self):
        self._login_admin_user()
        update_data = {'name': 'Ghost', 'job_title': 'Phantom', 'department': 'Ectoplasm'}
        response = self.client.put(url_for('api.employees_employee_resource', employee_id=99999), json=update_data)
        self.assertEqual(response.status_code, 404)

    # --- Test DELETE /api/v1/employees/<employee_id> (Delete Employee) ---
    def test_delete_employee_by_admin_success(self):
        self._login_admin_user()
        # Create related records to test cascade delete
        hazard = Hazard(name='API Test Hazard', category='API', exposure_limit=1, unit='api_unit')
        db.session.add(hazard)
        db.session.commit()

        exposure = Exposure(employee_id=self.employee1.id, hazard_id=hazard.id, exposure_level=1, date=date(2024,1,1), recorded_by=self.admin_user.id)
        health_record = HealthRecord(employee_id=self.employee1.id, test_type='API Deletion Test', result='Pending', date=date(2024,1,1), recorded_by=self.admin_user.id)
        db.session.add_all([exposure, health_record])
        db.session.commit()

        exposure_id = exposure.id
        health_record_id = health_record.id
        employee1_id = self.employee1.id

        response = self.client.delete(url_for('api.employees_employee_resource', employee_id=employee1_id))
        self.assertEqual(response.status_code, 204)
        self.assertIsNone(Employee.query.get(employee1_id))
        self.assertIsNone(Exposure.query.get(exposure_id), "Cascade delete failed for Exposure")
        self.assertIsNone(HealthRecord.query.get(health_record_id), "Cascade delete failed for HealthRecord")


    def test_delete_employee_by_regular_user_permission_denied(self):
        self._login_regular_user()
        response = self.client.delete(url_for('api.employees_employee_resource', employee_id=self.employee1.id), follow_redirects=True)
        self.assertEqual(response.status_code, 200) # After redirect
        self.assertTrue(urlparse(response.request.base_url).path.endswith(url_for('main.index', _external=False)))
        self.assertIn(b'You must be an administrator to access this page.', response.data)
        self.assertIsNotNone(Employee.query.get(self.employee1.id))


    def test_delete_nonexistent_employee_by_admin(self):
        self._login_admin_user()
        response = self.client.delete(url_for('api.employees_employee_resource', employee_id=99999))
        self.assertEqual(response.status_code, 404)


if __name__ == '__main__':
    unittest.main()
