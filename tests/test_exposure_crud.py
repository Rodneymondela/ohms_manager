import unittest
from datetime import date, datetime
from tests.test_config import BasicTests
from app import db, app # Import db and app
from models import User, Employee, Hazard, Exposure

class TestExposureCRUD(BasicTests):

    def setUp(self):
        super().setUp()
        # Create a standard user for login in tests
        self.test_user = User(username='testuser', email='test@example.com')
        self.test_user.set_password('TestPass123!')
        db.session.add(self.test_user)

        # Create prerequisite Employee and Hazard objects
        self.employee1 = Employee(name='John Doe', job_title='Engineer', department='Tech', hire_date=date(2023,1,1))
        self.employee2 = Employee(name='Jane Smith', job_title='Developer', department='Engineering', hire_date=date(2022,1,1))
        self.hazard1 = Hazard(name='Noise', category='Physical', exposure_limit=85.0, unit='dB(A)')
        self.hazard2 = Hazard(name='Dust', category='Chemical', exposure_limit=10.0, unit='mg/m^3')

        db.session.add_all([self.employee1, self.employee2, self.hazard1, self.hazard2])
        db.session.commit()

        # Log in the test user
        self._login_test_user()

    def _login_test_user(self):
        return self.app.post('/login', data=dict(
            username='testuser',
            password='TestPass123!'
        ), follow_redirects=True)

    def test_exposure_access_control_unauthenticated(self):
        # Log out the setup user first
        with self.app as client: # Use client to maintain session for logout
            client.get('/logout', follow_redirects=True)

        endpoints = [
            '/exposures',
            '/exposure/add',
            '/exposure/1/edit',
        ]
        for endpoint in endpoints:
            response = self.app.get(endpoint, follow_redirects=False)
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.location.endswith('/login'))

        response_post_delete = self.app.post('/exposure/1/delete', follow_redirects=False)
        self.assertEqual(response_post_delete.status_code, 302)
        self.assertTrue(response_post_delete.location.endswith('/login'))

        # Log back in for subsequent tests if they rely on setUp's login
        # self._login_test_user() # Not needed if each test logs in or setUp logs in and isn't logged out

    def test_list_exposures(self):
        # User is logged in from setUp
        response = self.app.get('/exposures')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Manage Exposures', response.data)
        self.assertIn(b'No exposure records found.', response.data)

        exposure = Exposure(
            employee_id=self.employee1.id,
            hazard_id=self.hazard1.id,
            exposure_level=75.0,
            date=date(2023, 5, 15),
            recorded_by=self.test_user.id
        )
        db.session.add(exposure)
        db.session.commit()

        response = self.app.get('/exposures')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.employee1.name.encode(), response.data)
        self.assertIn(self.hazard1.name.encode(), response.data)
        self.assertIn(b'75.0', response.data)
        self.assertNotIn(b'No exposure records found.', response.data)

    def test_add_exposure_get(self):
        response = self.app.get('/exposure/add')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Add Exposure Record', response.data)
        self.assertIn(self.employee1.name.encode(), response.data) # Check if employee name is in choices
        self.assertIn(self.hazard1.name.encode(), response.data)   # Check if hazard name is in choices

    def test_add_exposure_post_success(self):
        exposure_data = {
            'employee': self.employee1.id,
            'hazard': self.hazard1.id,
            'exposure_level': '80.5',
            'duration': '8',
            'date': '2023-06-01',
            'location': 'Factory Floor',
            'notes': 'Routine check'
        }
        response = self.app.post('/exposure/add', data=exposure_data, follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith('/exposures'))

        redirect_response = self.app.get(response.location)
        self.assertIn(b'Exposure record added successfully.', redirect_response.data)

        exposure = Exposure.query.filter_by(location='Factory Floor').first()
        self.assertIsNotNone(exposure)
        self.assertEqual(exposure.employee_id, self.employee1.id)
        self.assertEqual(exposure.hazard_id, self.hazard1.id)
        self.assertEqual(exposure.exposure_level, 80.5)
        self.assertEqual(exposure.recorded_by, self.test_user.id)

    def test_add_exposure_post_validation_error(self):
        # Missing employee
        response = self.app.post('/exposure/add', data={'hazard': self.hazard1.id, 'exposure_level': '70', 'date': '2023-01-01'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Employee</label>', response.data) # Check for field label
        self.assertIn(b'This field is required.', response.data) # Error for employee

        # Invalid exposure level
        response = self.app.post('/exposure/add', data={'employee': self.employee1.id, 'hazard': self.hazard1.id, 'exposure_level': 'abc', 'date': '2023-01-01'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Not a valid float value', response.data)

        self.assertEqual(Exposure.query.count(), 0) # No exposure should be created

    def test_edit_exposure_get_and_post_success(self):
        exposure = Exposure(
            employee_id=self.employee1.id, hazard_id=self.hazard1.id,
            exposure_level=70.0, date=date(2023,1,10), recorded_by=self.test_user.id,
            location="Old Location"
        )
        db.session.add(exposure)
        db.session.commit()
        exposure_id = exposure.id

        response_get = self.app.get(f'/exposure/{exposure_id}/edit')
        self.assertEqual(response_get.status_code, 200)
        self.assertIn(b'Edit Exposure Record', response_get.data)
        self.assertIn(self.employee1.name.encode(), response_get.data) # Check pre-selection
        self.assertIn(b'Old Location', response_get.data)


        updated_data = {
            'employee': self.employee2.id, # Change employee
            'hazard': self.hazard2.id,   # Change hazard
            'exposure_level': '75.5',
            'duration': '4',
            'date': '2023-01-12',
            'location': 'New Location',
            'notes': 'Updated notes'
        }
        response_post = self.app.post(f'/exposure/{exposure_id}/edit', data=updated_data, follow_redirects=False)
        self.assertEqual(response_post.status_code, 302)
        self.assertTrue(response_post.location.endswith('/exposures'))

        redirect_response = self.app.get(response_post.location)
        self.assertIn(b'Exposure record updated successfully.', redirect_response.data)

        updated_exp = Exposure.query.get(exposure_id)
        self.assertEqual(updated_exp.employee_id, self.employee2.id)
        self.assertEqual(updated_exp.hazard_id, self.hazard2.id)
        self.assertEqual(updated_exp.exposure_level, 75.5)
        self.assertEqual(updated_exp.location, 'New Location')

    def test_edit_exposure_non_existent(self):
        response_get = self.app.get('/exposure/9999/edit')
        self.assertEqual(response_get.status_code, 404)

        response_post = self.app.post('/exposure/9999/edit', data={'exposure_level': '100'})
        self.assertEqual(response_post.status_code, 404)

    def test_delete_exposure_success(self):
        exposure = Exposure(
            employee_id=self.employee1.id, hazard_id=self.hazard1.id,
            exposure_level=60.0, date=date(2023,2,15), recorded_by=self.test_user.id
        )
        db.session.add(exposure)
        db.session.commit()
        exposure_id = exposure.id

        response = self.app.post(f'/exposure/{exposure_id}/delete', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith('/exposures'))

        redirect_response = self.app.get(response.location)
        self.assertIn(b'Exposure record deleted successfully.', redirect_response.data)

        self.assertIsNone(Exposure.query.get(exposure_id))

    def test_delete_exposure_non_existent(self):
        response = self.app.post('/exposure/9999/delete')
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
