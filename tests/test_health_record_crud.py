import unittest
from datetime import date, datetime # datetime not used directly, but good for context
from flask import url_for # For checking redirects more robustly
from tests.test_config import BasicTests
from app import db # Import db from app package
from app.models import User, Employee, HealthRecord # Models from app package

class TestHealthRecordCRUD(BasicTests):

    def setUp(self):
        super().setUp()
        # Create a standard user for login in tests
        self.test_user = User(username='testuser', email='test@example.com')
        self.test_user.set_password('TestPass123!')
        db.session.add(self.test_user)

        # Create prerequisite Employee objects
        self.employee1 = Employee(name='Alice Wonderland', job_title='Dreamer', department='Fantasy', hire_date=date(2023,1,1))
        self.employee2 = Employee(name='Bob The Builder', job_title='Constructor', department='Building', hire_date=date(2022,1,1))

        db.session.add_all([self.employee1, self.employee2])
        db.session.commit()

        # Log in the test user
        self._login_test_user()

    def _login_test_user(self):
        return self.client.post(url_for('auth.login'), data=dict(
            username='testuser',
            password='TestPass123!'
        ), follow_redirects=True)

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
            self.assertTrue(response.location.endswith(url_for('auth.login')))

        response_post_delete = self.client.post(url_for('health_records.delete_health_record', record_id=1), follow_redirects=False)
        self.assertEqual(response_post_delete.status_code, 302)
        self.assertTrue(response_post_delete.location.endswith(url_for('auth.login')))

        self._login_test_user() # Re-login

    def test_list_health_records(self):
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

    def test_add_health_record_get(self):
        response = self.client.get(url_for('health_records.add_health_record'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Add Health Record', response.data)
        self.assertIn(self.employee1.name.encode(), response.data) # Check if employee name is in choices

    def test_add_health_record_post_success(self):
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
        self.assertTrue(response.location.endswith(url_for('health_records.list_health_records')))

        redirect_response = self.client.get(response.location)
        self.assertIn(b'Health record added successfully.', redirect_response.data)

        record = HealthRecord.query.filter_by(test_type='Vision Test').first()
        self.assertIsNotNone(record)
        self.assertEqual(record.employee_id, self.employee1.id)
        self.assertEqual(record.result, '20/20')
        self.assertEqual(record.recorded_by, self.test_user.id)
        self.assertEqual(record.next_test_date, date(2024,7,15))


    def test_add_health_record_post_validation_error(self):
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

    def test_edit_health_record_get_and_post_success(self):
        record = HealthRecord(
            employee_id=self.employee1.id, test_type='Flu Shot', result='Administered',
            date=date(2023,1,15), recorded_by=self.test_user.id, physician="Dr. Arm"
        )
        db.session.add(record)
        db.session.commit()
        record_id = record.id

        response_get = self.client.get(url_for('health_records.edit_health_record', record_id=record_id))
        self.assertEqual(response_get.status_code, 200)
        self.assertIn(b'Edit Health Record', response_get.data)
        self.assertIn(self.employee1.name.encode(), response_get.data)
        self.assertIn(b'Flu Shot', response_get.data)

        updated_data = {
            'employee': self.employee2.id, # Change employee
            'test_type': 'Flu Shot - Annual',
            'result': 'Administered Updated',
            'details': 'Updated details',
            'date': '2023-01-16',
            'next_test_date': '', # Clear next test date
            'physician': 'Dr. Shoulder',
            'facility': 'Community Clinic'
        }
        response_post = self.client.post(url_for('health_records.edit_health_record', record_id=record_id), data=updated_data, follow_redirects=False)
        self.assertEqual(response_post.status_code, 302, f"POST request failed with data: {response_post.data.decode()}")
        self.assertTrue(response_post.location.endswith(url_for('health_records.list_health_records')))

        redirect_response = self.client.get(response_post.location)
        self.assertIn(b'Health record updated successfully.', redirect_response.data)

        updated_rec = HealthRecord.query.get(record_id)
        self.assertEqual(updated_rec.employee_id, self.employee2.id)
        self.assertEqual(updated_rec.test_type, 'Flu Shot - Annual')
        self.assertEqual(updated_rec.physician, 'Dr. Shoulder')
        self.assertIsNone(updated_rec.next_test_date) # Check if cleared

    def test_edit_health_record_non_existent(self):
        response_get = self.client.get(url_for('health_records.edit_health_record', record_id=9999))
        self.assertEqual(response_get.status_code, 404)

        response_post = self.client.post(url_for('health_records.edit_health_record', record_id=9999), data={'test_type': 'NonExistent'})
        self.assertEqual(response_post.status_code, 404)

    def test_delete_health_record_success(self):
        record = HealthRecord(
            employee_id=self.employee1.id, test_type='TB Test', result='Negative',
            date=date(2023,3,20), recorded_by=self.test_user.id
        )
        db.session.add(record)
        db.session.commit()
        record_id = record.id

        response = self.client.post(url_for('health_records.delete_health_record', record_id=record_id), follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith(url_for('health_records.list_health_records')))

        redirect_response = self.client.get(response.location)
        self.assertIn(b'Health record deleted successfully.', redirect_response.data)

        self.assertIsNone(HealthRecord.query.get(record_id))

    def test_delete_health_record_non_existent(self):
        response = self.client.post(url_for('health_records.delete_health_record', record_id=9999))
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
