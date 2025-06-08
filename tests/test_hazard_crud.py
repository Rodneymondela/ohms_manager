import unittest
from datetime import date
from tests.test_config import BasicTests
from app import db, app # Import db and app
from models import User, Hazard, Employee, Exposure # Added Employee and Exposure

class TestHazardCRUD(BasicTests):

    def setUp(self):
        super().setUp()
        # Create a standard user for login in tests
        self.test_user = User(username='testuser', email='test@example.com')
        self.test_user.set_password('TestPass123!')
        db.session.add(self.test_user)
        db.session.commit()

    def _login_test_user(self):
        return self.app.post('/login', data=dict(
            username='testuser',
            password='TestPass123!'
        ), follow_redirects=True)

    def test_hazard_access_control_unauthenticated(self):
        endpoints = [
            '/hazards',
            '/hazard/add',
            '/hazard/1/edit', # Assumes a hazard with ID 1 might exist or route structure
        ]
        for endpoint in endpoints:
            response = self.app.get(endpoint, follow_redirects=False)
            self.assertEqual(response.status_code, 302, f"Endpoint {endpoint} did not redirect.")
            self.assertTrue(response.location.endswith('/login'), f"Endpoint {endpoint} did not redirect to login.")

        response_post_delete = self.app.post('/hazard/1/delete', follow_redirects=False)
        self.assertEqual(response_post_delete.status_code, 302)
        self.assertTrue(response_post_delete.location.endswith('/login'))

    def test_list_hazards(self):
        self._login_test_user()
        response = self.app.get('/hazards')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Manage Hazards', response.data)
        self.assertIn(b'No hazards found.', response.data) # Initially empty

        # Add a hazard and check again
        hazard = Hazard(name='Noise', category='Physical', exposure_limit=85.0, unit='dB(A)')
        db.session.add(hazard)
        db.session.commit()

        response = self.app.get('/hazards')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Noise', response.data)
        self.assertNotIn(b'No hazards found.', response.data)

    def test_add_hazard_get(self):
        self._login_test_user()
        response = self.app.get('/hazard/add')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Add Hazard', response.data)

    def test_add_hazard_post_success(self):
        self._login_test_user()
        hazard_data = {
            'name': 'Chemical Fumes',
            'category': 'Chemical',
            'exposure_limit': '10.0', # String as from form
            'unit': 'ppm',
            'description': 'Volatile organic compounds',
            'safety_measures': 'Use respirators and ventilation'
        }
        response = self.app.post('/hazard/add', data=hazard_data, follow_redirects=False)

        self.assertEqual(response.status_code, 302, "Form submission did not redirect.")
        self.assertTrue(response.location.endswith('/hazards'), f"Redirected to {response.location} instead of /hazards")

        redirect_response = self.app.get(response.location, follow_redirects=True)
        self.assertIn(b'Hazard added successfully.', redirect_response.data)

        hazard = Hazard.query.filter_by(name='Chemical Fumes').first()
        self.assertIsNotNone(hazard)
        self.assertEqual(hazard.category, 'Chemical')
        self.assertEqual(hazard.exposure_limit, 10.0)

    def test_add_hazard_post_validation_error_empty_name(self):
        self._login_test_user()
        response = self.app.post('/hazard/add', data={
            'name': '', # Name is required
            'category': 'Test Category',
            'exposure_limit': '50.0',
            'unit': 'units'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Stays on form page
        self.assertIn(b'This field is required.', response.data)

        hazard = Hazard.query.filter_by(category='Test Category').first()
        self.assertIsNone(hazard)

    def test_add_hazard_post_validation_error_invalid_exposure_limit(self):
        self._login_test_user()
        response = self.app.post('/hazard/add', data={
            'name': 'Bad Limit Hazard',
            'category': 'Test',
            'exposure_limit': 'not-a-number', # Invalid float
            'unit': 'units'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Not a valid float value', response.data) # WTForms error

        response_negative = self.app.post('/hazard/add', data={
            'name': 'Negative Limit Hazard',
            'category': 'Test',
            'exposure_limit': '-10.0', # Negative, fails NumberRange
            'unit': 'units'
        }, follow_redirects=True)
        self.assertEqual(response_negative.status_code, 200)
        self.assertIn(b'Number must be greater than or equal to 1e-06.', response_negative.data)


    def test_edit_hazard_get_and_post_success(self):
        self._login_test_user()
        hazard = Hazard(name='Vibration', category='Physical', exposure_limit=5.0, unit='m/s^2')
        db.session.add(hazard)
        db.session.commit()
        hazard_id = hazard.id

        response_get = self.app.get(f'/hazard/{hazard_id}/edit')
        self.assertEqual(response_get.status_code, 200)
        self.assertIn(b'Edit Hazard', response_get.data)
        self.assertIn(b'Vibration', response_get.data)

        updated_data = {
            'name': 'Edited Vibration',
            'category': 'Physical Updated',
            'exposure_limit': '2.5',
            'unit': 'm/s^2 new',
            'description': hazard.description or '',
            'safety_measures': hazard.safety_measures or ''
        }
        response_post = self.app.post(f'/hazard/{hazard_id}/edit', data=updated_data, follow_redirects=False)
        self.assertEqual(response_post.status_code, 302)
        self.assertTrue(response_post.location.endswith('/hazards'))

        redirect_response = self.app.get(response_post.location)
        self.assertIn(b'Hazard updated successfully.', redirect_response.data)

        updated_hazard = Hazard.query.get(hazard_id)
        self.assertEqual(updated_hazard.name, 'Edited Vibration')
        self.assertEqual(updated_hazard.exposure_limit, 2.5)

    def test_edit_hazard_non_existent(self):
        self._login_test_user()
        response_get = self.app.get('/hazard/9999/edit')
        self.assertEqual(response_get.status_code, 404)

        response_post = self.app.post('/hazard/9999/edit', data={'name': 'TryingToEdit'})
        self.assertEqual(response_post.status_code, 404)

    def test_delete_hazard_success(self):
        self._login_test_user()
        hazard = Hazard(name='Radiation', category='Physical', exposure_limit=1.0, unit='mSv')
        db.session.add(hazard)
        db.session.commit()
        hazard_id = hazard.id

        response = self.app.post(f'/hazard/{hazard_id}/delete', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith('/hazards'))

        redirect_response = self.app.get(response.location)
        self.assertIn(b'Hazard deleted successfully.', redirect_response.data)

        deleted_hazard = Hazard.query.get(hazard_id)
        self.assertIsNone(deleted_hazard)

    def test_delete_hazard_non_existent(self):
        self._login_test_user()
        response = self.app.post('/hazard/9999/delete')
        self.assertEqual(response.status_code, 404)

    def test_delete_hazard_with_exposure_cascade(self):
        self._login_test_user()
        # Create an employee
        emp = Employee(name='Test Emp For Exposure', job_title='Tester', department='QA', hire_date=date(2023,1,1))
        db.session.add(emp)
        db.session.commit()

        # Create a hazard
        hazard_to_delete = Hazard(name='Dust', category='Chemical', exposure_limit=10.0, unit='mg/m^3')
        db.session.add(hazard_to_delete)
        db.session.commit()
        hazard_id = hazard_to_delete.id

        # Create an exposure linking them
        exposure = Exposure(employee_id=emp.id, hazard_id=hazard_id, exposure_level=5.0, date=date(2023,1,1))
        db.session.add(exposure)
        db.session.commit()
        exposure_id = exposure.id

        self.assertIsNotNone(Exposure.query.get(exposure_id), "Exposure record should exist before hazard deletion.")

        # Delete the hazard
        response = self.app.post(f'/hazard/{hazard_id}/delete', follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Should be on hazards page
        self.assertIn(b'Hazard deleted successfully.', response.data)

        # Verify hazard is deleted
        deleted_hazard = Hazard.query.get(hazard_id)
        self.assertIsNone(deleted_hazard, "Hazard should be deleted.")

        # Verify the associated exposure is also deleted due to cascade
        # In models.py, Hazard.exposures = relationship('Exposure', backref='hazard', lazy=True, cascade='all, delete-orphan')
        deleted_exposure = Exposure.query.get(exposure_id)
        self.assertIsNone(deleted_exposure, "Associated exposure should be deleted by cascade.")

if __name__ == '__main__':
    unittest.main()
