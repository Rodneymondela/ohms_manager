import unittest
from datetime import date, datetime
from tests.test_config import BasicTests
from app import db, app # Import db and app
from models import User, Employee, HealthRecord # Added HealthRecord

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
        return self.app.post('/login', data=dict(
            username='testuser',
            password='TestPass123!'
        ), follow_redirects=True)

    def test_health_record_access_control_unauthenticated(self):
        # Log out the setup user first
        with self.app as client:
            client.get('/logout', follow_redirects=True)

        endpoints = [
            '/health_records',
            '/health_record/add',
            '/health_record/1/edit',
        ]
        for endpoint in endpoints:
            response = self.app.get(endpoint, follow_redirects=False)
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.location.endswith('/login'))

        response_post_delete = self.app.post('/health_record/1/delete', follow_redirects=False)
        self.assertEqual(response_post_delete.status_code, 302)
        self.assertTrue(response_post_delete.location.endswith('/login'))

    def test_list_health_records(self):
        response = self.app.get('/health_records')
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

        response = self.app.get('/health_records')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.employee1.name.encode(), response.data)
        self.assertIn(b'Hearing Test', response.data)
        self.assertNotIn(b'No health records found.', response.data)

    def test_add_health_record_get(self):
        response = self.app.get('/health_record/add')
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
        response = self.app.post('/health_record/add', data=record_data, follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith('/health_records'))

        redirect_response = self.app.get(response.location)
        self.assertIn(b'Health record added successfully.', redirect_response.data)

        record = HealthRecord.query.filter_by(test_type='Vision Test').first()
        self.assertIsNotNone(record)
        self.assertEqual(record.employee_id, self.employee1.id)
        self.assertEqual(record.result, '20/20')
        self.assertEqual(record.recorded_by, self.test_user.id)
        self.assertEqual(record.next_test_date, date(2024,7,15))


    def test_add_health_record_post_validation_error(self):
        # Missing employee
        response = self.app.post('/health_record/add', data={'test_type': 'Blood Test', 'result': 'OK', 'date': '2023-07-01'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Employee</label>', response.data)
        self.assertIn(b'This field is required.', response.data)

        # Missing test_type
        response = self.app.post('/health_record/add', data={'employee': self.employee1.id, 'result': 'OK', 'date': '2023-07-01'}, follow_redirects=True)
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

        response_get = self.app.get(f'/health_record/{record_id}/edit')
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
        response_post = self.app.post(f'/health_record/{record_id}/edit', data=updated_data, follow_redirects=False)
        self.assertEqual(response_post.status_code, 302, f"POST request failed with data: {response_post.data.decode()}")
        self.assertTrue(response_post.location.endswith('/health_records'))

        redirect_response = self.app.get(response_post.location)
        self.assertIn(b'Health record updated successfully.', redirect_response.data)

        updated_rec = HealthRecord.query.get(record_id)
        self.assertEqual(updated_rec.employee_id, self.employee2.id)
        self.assertEqual(updated_rec.test_type, 'Flu Shot - Annual')
        self.assertEqual(updated_rec.physician, 'Dr. Shoulder')
        self.assertIsNone(updated_rec.next_test_date) # Check if cleared

    def test_edit_health_record_non_existent(self):
        response_get = self.app.get('/health_record/9999/edit')
        self.assertEqual(response_get.status_code, 404)

        response_post = self.app.post('/health_record/9999/edit', data={'test_type': 'NonExistent'})
        self.assertEqual(response_post.status_code, 404)

    def test_delete_health_record_success(self):
        record = HealthRecord(
            employee_id=self.employee1.id, test_type='TB Test', result='Negative',
            date=date(2023,3,20), recorded_by=self.test_user.id
        )
        db.session.add(record)
        db.session.commit()
        record_id = record.id

        response = self.app.post(f'/health_record/{record_id}/delete', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith('/health_records'))

        redirect_response = self.app.get(response.location)
        self.assertIn(b'Health record deleted successfully.', redirect_response.data)

        self.assertIsNone(HealthRecord.query.get(record_id))

    def test_delete_health_record_non_existent(self):
        response = self.app.post('/health_record/9999/delete')
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
