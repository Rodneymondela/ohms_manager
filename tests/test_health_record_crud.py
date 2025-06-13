import unittest
from datetime import date, datetime # datetime not used directly, but good for context
from flask import url_for
from urllib.parse import urlparse, parse_qs
from tests.test_config import BasicTests
from app import db
from app.models import User, Employee, HealthRecord, ROLE_USER, ROLE_ADMIN # Import roles

class TestHealthRecordCRUD(BasicTests):

    def setUp(self):
        super().setUp()
        self.test_user = User(username='testuser', email='testuser@example.com', role=ROLE_USER)
        self.test_user.set_password('TestPass123!')

        self.admin_user = User(username='adminuser', email='admin@example.com', role=ROLE_ADMIN)
        self.admin_user.set_password('AdminPass123!')

        self.employee1 = Employee(name='Alice Wonderland', job_title='Dreamer', department='Fantasy', hire_date=date(2023,1,1))
        self.employee2 = Employee(name='Bob The Builder', job_title='Constructor', department='Building', hire_date=date(2022,1,1))

        db.session.add_all([self.test_user, self.admin_user, self.employee1, self.employee2])
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

    def test_health_record_access_control_unauthenticated(self):
        # Log out the setup user first
        with self.client as c:
            c.get(url_for('auth.logout'), follow_redirects=True)

        endpoints_get = [
            url_for('health_records.list_health_records'),
            url_for('health_records.add_health_record'),
            url_for('health_records.edit_health_record', record_id=1),
        ]
        for endpoint in endpoints_get:
            response = self.client.get(endpoint, follow_redirects=False)
            self.assertEqual(response.status_code, 302)
            parsed_location = urlparse(response.location)
            expected_login_path = url_for('auth.login', _external=False)
            self.assertEqual(parsed_location.path, expected_login_path)
            endpoint_path = urlparse(endpoint).path
            if endpoint_path != expected_login_path:
                 query_params = parse_qs(parsed_location.query)
                 self.assertIn('next', query_params)
                 self.assertEqual(query_params['next'][0], endpoint_path)

        delete_endpoint_url = url_for('health_records.delete_health_record', record_id=1)
        delete_endpoint_path = urlparse(delete_endpoint_url).path
        response_post_delete = self.client.post(delete_endpoint_url, follow_redirects=False)
        self.assertEqual(response_post_delete.status_code, 302)
        parsed_location_post = urlparse(response_post_delete.location)
        expected_login_path_post = url_for('auth.login', _external=False)
        self.assertEqual(parsed_location_post.path, expected_login_path_post)
        query_params_post = parse_qs(parsed_location_post.query)
        self.assertIn('next', query_params_post)
        self.assertEqual(query_params_post['next'][0], delete_endpoint_path)

        # self._login_test_user() # Removed.

    def test_list_health_records(self):
        # Listing available to regular users
        self._login_test_user()
        response = self.client.get(url_for('health_records.list_health_records'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Manage Health Records', response.data)
        self.assertIn(b'No health records found.', response.data)

        record = HealthRecord(
            employee_id=self.employee1.id,
            test_type='Hearing Test',
            result='Normal',
            date=date(2023, 7, 10),
            recorded_by=self.test_user.id
        )
        db.session.add(record)
        db.session.commit()

        response = self.client.get(url_for('health_records.list_health_records'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.employee1.name.encode(), response.data)
        self.assertIn(b'Hearing Test', response.data)
        self.assertNotIn(b'No health records found.', response.data)

    def test_add_health_record_get_by_admin(self): # Renamed
        self._login_admin_user()
        response = self.client.get(url_for('health_records.add_health_record'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Add Health Record', response.data)
        self.assertIn(self.employee1.name.encode(), response.data)

    def test_add_health_record_get_by_regular_user_permission_denied(self):
        self._login_test_user()
        response = self.client.get(url_for('health_records.add_health_record'), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'You do not have permission to access this page.', response.data)
        self.assertEqual(urlparse(response.request.base_url).path, url_for('main.index', _external=False))

    def test_add_health_record_post_by_admin_success(self): # Renamed
        self._login_admin_user()
        record_data = {
            'employee': self.employee1.id,
            'test_type': 'Vision Test',
            'result': '20/20',
            'details': 'Annual checkup',
            'date': '2023-07-15',
            'next_test_date': '2024-07-15',
            'physician': 'Dr. Eyes',
            'facility': 'Optical Clinic'
        }
        response = self.client.post(url_for('health_records.add_health_record'), data=record_data, follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse(response.location).path, url_for('health_records.list_health_records', _external=False))

        redirect_response = self.client.get(response.location)
        self.assertIn(b'Health record added successfully.', redirect_response.data)

        record = HealthRecord.query.filter_by(test_type='Vision Test').first()
        self.assertIsNotNone(record)
        self.assertEqual(record.employee_id, self.employee1.id)
        self.assertEqual(record.result, '20/20')
        self.assertEqual(record.recorded_by, self.admin_user.id) # Admin recorded
        self.assertEqual(record.next_test_date, date(2024,7,15))

    def test_add_health_record_post_by_regular_user_permission_denied(self):
        self._login_test_user()
        record_data = {
            'employee': self.employee1.id, 'test_type': 'Vision Test NonAdmin', 'result': '20/20',
            'date': '2023-07-15', 'facility': 'Optical Clinic NonAdmin'
        }
        response = self.client.post(url_for('health_records.add_health_record'), data=record_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'You do not have permission to access this page.', response.data)
        self.assertEqual(urlparse(response.request.base_url).path, url_for('main.index', _external=False))
        self.assertIsNone(HealthRecord.query.filter_by(facility='Optical Clinic NonAdmin').first())

    def test_add_health_record_post_validation_error_by_admin(self): # Renamed
        self._login_admin_user() # Admin can submit invalid data
        # Missing employee
        response = self.client.post(url_for('health_records.add_health_record'), data={'test_type': 'Blood Test', 'result': 'OK', 'date': '2023-07-01'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Employee</label>', response.data)
        self.assertIn(b'This field is required.', response.data)

        # Missing test_type
        response = self.client.post(url_for('health_records.add_health_record'), data={'employee': self.employee1.id, 'result': 'OK', 'date': '2023-07-01'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Type</label>', response.data)
        self.assertIn(b'This field is required.', response.data)

        self.assertEqual(HealthRecord.query.count(), 0)

    def test_edit_health_record_get_by_admin(self): # Renamed and split
        self._login_admin_user()
        record = HealthRecord(
            employee_id=self.employee1.id, test_type='Flu Shot', result='Administered',
            date=date(2023,1,15), recorded_by=self.admin_user.id, physician="Dr. Arm" # Admin created
        )
        db.session.add(record)
        db.session.commit()
        record_id = record.id

        response_get = self.client.get(url_for('health_records.edit_health_record', record_id=record_id))
        self.assertEqual(response_get.status_code, 200)
        self.assertIn(b'Edit Health Record', response_get.data)
        self.assertIn(self.employee1.name.encode(), response_get.data)
        self.assertIn(b'Flu Shot', response_get.data)

    def test_edit_health_record_get_by_regular_user_permission_denied(self):
        self._login_test_user()
        record = HealthRecord(
            employee_id=self.employee1.id, test_type='Flu Shot Protected', result='Administered',
            date=date(2023,1,15), recorded_by=self.test_user.id, physician="Dr. Arm" # User created
        )
        db.session.add(record)
        db.session.commit()
        record_id = record.id

        response_get = self.client.get(url_for('health_records.edit_health_record', record_id=record_id), follow_redirects=True)
        self.assertEqual(response_get.status_code, 200) # Followed redirect
        self.assertIn(b'You do not have permission to access this page.', response_get.data)
        self.assertEqual(urlparse(response_get.request.base_url).path, url_for('main.index', _external=False))

    def test_edit_health_record_post_by_admin_success(self): # Renamed and split
        self._login_admin_user()
        record = HealthRecord(
            employee_id=self.employee1.id, test_type='Flu Shot Initial Admin', result='Administered',
            date=date(2023,1,15), recorded_by=self.admin_user.id, physician="Dr. Arm Initial"
        )
        db.session.add(record)
        db.session.commit()
        record_id = record.id

        updated_data = {
            'employee': self.employee2.id, 'test_type': 'Flu Shot - Annual Admin', 'result': 'Administered Updated Admin',
            'details': 'Admin Updated details', 'date': '2023-01-16', 'next_test_date': '',
            'physician': 'Dr. Shoulder Admin', 'facility': 'Community Clinic Admin'
        }
        response_post = self.client.post(url_for('health_records.edit_health_record', record_id=record_id), data=updated_data, follow_redirects=False)
        self.assertEqual(response_post.status_code, 302, f"POST request failed with data: {response_post.data.decode()}")
        self.assertEqual(urlparse(response_post.location).path, url_for('health_records.list_health_records', _external=False))

        redirect_response = self.client.get(response_post.location, follow_redirects=True)
        self.assertIn(b'Health record updated successfully.', redirect_response.data)

        updated_rec = HealthRecord.query.get(record_id)
        self.assertEqual(updated_rec.employee_id, self.employee2.id)
        self.assertEqual(updated_rec.test_type, 'Flu Shot - Annual Admin')
        self.assertEqual(updated_rec.physician, 'Dr. Shoulder Admin')
        self.assertIsNone(updated_rec.next_test_date)

    def test_edit_health_record_post_by_regular_user_permission_denied(self):
        self._login_test_user()
        original_test_type = "User Edit HR Original Type"
        record = HealthRecord(
            employee_id=self.employee1.id, test_type=original_test_type, result='Initial',
            date=date(2023,1,15), recorded_by=self.test_user.id
        )
        db.session.add(record)
        db.session.commit()
        record_id = record.id

        updated_data = {'test_type': 'User Edited HR Attempt Type', 'result': 'Attempted Update'}
        response_post = self.client.post(url_for('health_records.edit_health_record', record_id=record_id), data=updated_data, follow_redirects=True)

        self.assertEqual(response_post.status_code, 200)
        self.assertIn(b'You do not have permission to access this page.', response_post.data)
        self.assertEqual(urlparse(response_post.request.base_url).path, url_for('main.index', _external=False))

        unchanged_record = HealthRecord.query.get(record_id)
        self.assertEqual(unchanged_record.test_type, original_test_type)

    def test_edit_health_record_non_existent(self):
        self._login_admin_user() # Admin user
        response_get = self.client.get(url_for('health_records.edit_health_record', record_id=9999))
        self.assertEqual(response_get.status_code, 404)

        response_post = self.client.post(url_for('health_records.edit_health_record', record_id=9999), data={'test_type': 'NonExistent'})
        self.assertEqual(response_post.status_code, 404)

    def test_delete_health_record_by_admin(self): # Renamed
        self._login_admin_user() # Log in as admin
        record = HealthRecord(
            employee_id=self.employee1.id, test_type='TB Test', result='Negative',
            date=date(2023,3,20), recorded_by=self.admin_user.id # Admin created
        )
        db.session.add(record)
        db.session.commit()
        record_id = record.id

        response = self.client.post(url_for('health_records.delete_health_record', record_id=record_id), follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse(response.location).path, url_for('health_records.list_health_records', _external=False))

        redirect_response = self.client.get(response.location)
        self.assertIn(b'Health record deleted successfully.', redirect_response.data)

        self.assertIsNone(HealthRecord.query.get(record_id))

    def test_delete_health_record_by_regular_user_permission_denied(self):
        self._login_test_user() # Log in as regular user
        record_to_protect = HealthRecord(
            employee_id=self.employee1.id, test_type='Protected Test', result='Denied',
            date=date(2023,4,4), recorded_by=self.test_user.id
        )
        db.session.add(record_to_protect)
        db.session.commit()
        record_id = record_to_protect.id

        response = self.client.post(url_for('health_records.delete_health_record', record_id=record_id), follow_redirects=True)

        self.assertEqual(response.status_code, 200) # After redirect to main.index
        self.assertIn(b'You do not have permission to access this page.', response.data)
        self.assertEqual(urlparse(response.request.base_url).path, url_for('main.index', _external=False))

        still_exists_record = HealthRecord.query.get(record_id)
        self.assertIsNotNone(still_exists_record)

    def test_delete_health_record_non_existent(self):
        self._login_admin_user() # Admin user
        response = self.client.post(url_for('health_records.delete_health_record', record_id=9999))
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
