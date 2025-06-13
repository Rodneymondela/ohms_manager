import unittest
from datetime import date
from flask import url_for # For checking redirects more robustly
from urllib.parse import urlparse, parse_qs
from tests.test_config import BasicTests
from app import db
from app.models import User, Hazard, Employee, Exposure, ROLE_USER, ROLE_ADMIN # Import roles

class TestHazardCRUD(BasicTests):

    def setUp(self):
        super().setUp()
        self.test_user = User(username='testuser', email='testuser@example.com', role=ROLE_USER)
        self.test_user.set_password('TestPass123!')

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

    def test_hazard_access_control_unauthenticated(self):
        # Log out the setup user first
        with self.client as c:
             c.get(url_for('auth.logout'), follow_redirects=True)

        endpoints_get = [
            url_for('hazards.list_hazards'),
            url_for('hazards.add_hazard'),
            url_for('hazards.edit_hazard', hazard_id=1),
        ]
        for endpoint in endpoints_get:
            response = self.client.get(endpoint, follow_redirects=False)
            self.assertEqual(response.status_code, 302, f"Endpoint {endpoint} did not redirect.")
            parsed_location = urlparse(response.location)
            expected_login_path = url_for('auth.login', _external=False)
            self.assertEqual(parsed_location.path, expected_login_path)
            endpoint_path = urlparse(endpoint).path
            if endpoint_path != expected_login_path:
                 query_params = parse_qs(parsed_location.query)
                 self.assertIn('next', query_params)
                 self.assertEqual(query_params['next'][0], endpoint_path)

        delete_endpoint_url = url_for('hazards.delete_hazard', hazard_id=1)
        delete_endpoint_path = urlparse(delete_endpoint_url).path
        response_post_delete = self.client.post(delete_endpoint_url, follow_redirects=False)
        self.assertEqual(response_post_delete.status_code, 302)
        parsed_location_post = urlparse(response_post_delete.location)
        expected_login_path_post = url_for('auth.login', _external=False)
        self.assertEqual(parsed_location_post.path, expected_login_path_post)
        query_params_post = parse_qs(parsed_location_post.query)
        self.assertIn('next', query_params_post)
        self.assertEqual(query_params_post['next'][0], delete_endpoint_path)

        # self._login_test_user() # Removed, each test will call it.

    def test_list_hazards(self):
        # Listing available to regular users
        self._login_test_user()
        response = self.client.get(url_for('hazards.list_hazards'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Manage Hazards', response.data)
        self.assertIn(b'No hazards found.', response.data) # Initially empty

        # Add a hazard and check again
        hazard = Hazard(name='Noise', category='Physical', exposure_limit=85.0, unit='dB(A)')
        db.session.add(hazard)
        db.session.commit()

        response = self.client.get(url_for('hazards.list_hazards'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Noise', response.data)
        self.assertNotIn(b'No hazards found.', response.data)

    def test_add_hazard_get_by_admin(self): # Renamed
        self._login_admin_user()
        response = self.client.get(url_for('hazards.add_hazard'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Add Hazard', response.data)

    def test_add_hazard_get_by_regular_user_permission_denied(self):
        self._login_test_user()
        response = self.client.get(url_for('hazards.add_hazard'), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'You do not have permission to access this page.', response.data)
        self.assertEqual(urlparse(response.request.base_url).path, url_for('main.index', _external=False))

    def test_add_hazard_post_by_admin_success(self): # Renamed
        self._login_admin_user()
        hazard_data = {
            'name': 'Chemical Fumes',
            'category': 'Chemical',
            'exposure_limit': '10.0', # String as from form
            'unit': 'ppm',
            'description': 'Volatile organic compounds',
            'safety_measures': 'Use respirators and ventilation'
        }
        response = self.client.post(url_for('hazards.add_hazard'), data=hazard_data, follow_redirects=False)

        self.assertEqual(response.status_code, 302, "Form submission did not redirect.")
        self.assertEqual(urlparse(response.location).path, url_for('hazards.list_hazards', _external=False))

        redirect_response = self.client.get(response.location, follow_redirects=True)
        self.assertIn(b'Hazard added successfully.', redirect_response.data)

        hazard = Hazard.query.filter_by(name='Chemical Fumes').first()
        self.assertIsNotNone(hazard)
        self.assertEqual(hazard.category, 'Chemical')
        self.assertEqual(hazard.exposure_limit, 10.0)

    def test_add_hazard_post_by_regular_user_permission_denied(self):
        self._login_test_user()
        hazard_data = {
            'name': 'Chemical Fumes NonAdmin', 'category': 'Chemical', 'exposure_limit': '10.0', 'unit': 'ppm',
            'description': 'Volatile organic compounds', 'safety_measures': 'Use respirators and ventilation'
        }
        response = self.client.post(url_for('hazards.add_hazard'), data=hazard_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'You do not have permission to access this page.', response.data)
        self.assertEqual(urlparse(response.request.base_url).path, url_for('main.index', _external=False))
        self.assertIsNone(Hazard.query.filter_by(name='Chemical Fumes NonAdmin').first())

    def test_add_hazard_post_validation_error_empty_name_by_admin(self): # Renamed
        self._login_admin_user()
        response = self.client.post(url_for('hazards.add_hazard'), data={
            'name': '', # Name is required
            'category': 'Test Category',
            'exposure_limit': '50.0',
            'unit': 'units'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Stays on form page
        self.assertIn(b'This field is required.', response.data)

        hazard = Hazard.query.filter_by(category='Test Category').first()
        self.assertIsNone(hazard)

    def test_add_hazard_post_validation_error_invalid_exposure_limit_by_admin(self): # Renamed
        self._login_admin_user()
        response = self.client.post(url_for('hazards.add_hazard'), data={
            'name': 'Bad Limit Hazard',
            'category': 'Test',
            'exposure_limit': 'not-a-number', # Invalid float
            'unit': 'units'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Not a valid float value', response.data) # WTForms error

        response_negative = self.client.post(url_for('hazards.add_hazard'), data={
            'name': 'Negative Limit Hazard',
            'category': 'Test',
            'exposure_limit': '-10.0', # Negative, fails NumberRange
            'unit': 'units'
        }, follow_redirects=True)
        self.assertEqual(response_negative.status_code, 200)
        self.assertIn(b'Number must be at least 1e-06.', response_negative.data) # Corrected assertion

    def test_edit_hazard_get_by_admin(self): # Renamed and split
        self._login_admin_user()
        hazard = Hazard(name='Vibration', category='Physical', exposure_limit=5.0, unit='m/s^2')
        db.session.add(hazard)
        db.session.commit()
        hazard_id = hazard.id

        response_get = self.client.get(url_for('hazards.edit_hazard', hazard_id=hazard_id))
        self.assertEqual(response_get.status_code, 200)
        self.assertIn(b'Edit Hazard', response_get.data)
        self.assertIn(b'Vibration', response_get.data)

    def test_edit_hazard_get_by_regular_user_permission_denied(self):
        self._login_test_user()
        hazard = Hazard(name='Vibration Protected', category='Physical', exposure_limit=5.0, unit='m/s^2')
        db.session.add(hazard)
        db.session.commit()
        hazard_id = hazard.id

        response_get = self.client.get(url_for('hazards.edit_hazard', hazard_id=hazard_id), follow_redirects=True)
        self.assertEqual(response_get.status_code, 200)
        self.assertIn(b'You do not have permission to access this page.', response_get.data)
        self.assertEqual(urlparse(response_get.request.base_url).path, url_for('main.index', _external=False))

    def test_edit_hazard_post_by_admin_success(self): # Renamed and split
        self._login_admin_user()
        hazard = Hazard(name='To Be Edited Hazard', category='Initial', exposure_limit=15.0, unit='old_units')
        db.session.add(hazard)
        db.session.commit()
        hazard_id = hazard.id

        updated_data = {
            'name': 'Admin Edited Hazard', 'category': 'Admin Updated', 'exposure_limit': '12.5',
            'unit': 'new_units', 'description': 'New desc', 'safety_measures': 'New measures'
        }
        response_post = self.client.post(url_for('hazards.edit_hazard', hazard_id=hazard_id), data=updated_data, follow_redirects=False)
        self.assertEqual(response_post.status_code, 302)
        self.assertEqual(urlparse(response_post.location).path, url_for('hazards.list_hazards', _external=False))

        redirect_response = self.client.get(response_post.location, follow_redirects=True)
        self.assertIn(b'Hazard updated successfully.', redirect_response.data)

        updated_hazard = Hazard.query.get(hazard_id)
        self.assertEqual(updated_hazard.name, 'Admin Edited Hazard')
        self.assertEqual(updated_hazard.category, 'Admin Updated')

    def test_edit_hazard_post_by_regular_user_permission_denied(self):
        self._login_test_user()
        original_name = "User Edit Hazard Original"
        hazard = Hazard(name=original_name, category='User Initial', exposure_limit=1.0, unit='test')
        db.session.add(hazard)
        db.session.commit()
        hazard_id = hazard.id

        updated_data = {'name': 'User Edited Hazard Attempt', 'category': 'User New Attempt'}
        response_post = self.client.post(url_for('hazards.edit_hazard', hazard_id=hazard_id), data=updated_data, follow_redirects=True)

        self.assertEqual(response_post.status_code, 200)
        self.assertIn(b'You do not have permission to access this page.', response_post.data)
        self.assertEqual(urlparse(response_post.request.base_url).path, url_for('main.index', _external=False))

        unchanged_hazard = Hazard.query.get(hazard_id)
        self.assertEqual(unchanged_hazard.name, original_name)


    def test_edit_hazard_non_existent(self):
        self._login_admin_user() # Admin user
        response_get = self.client.get(url_for('hazards.edit_hazard', hazard_id=9999))
        self.assertEqual(response_get.status_code, 404)

        response_post = self.client.post(url_for('hazards.edit_hazard', hazard_id=9999), data={'name': 'TryingToEdit'})
        self.assertEqual(response_post.status_code, 404)

    def test_delete_hazard_by_admin(self): # Renamed
        self._login_admin_user() # Log in as admin
        hazard = Hazard(name='Radiation', category='Physical', exposure_limit=1.0, unit='mSv')
        db.session.add(hazard)
        db.session.commit()
        hazard_id = hazard.id

        response = self.client.post(url_for('hazards.delete_hazard', hazard_id=hazard_id), follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse(response.location).path, url_for('hazards.list_hazards', _external=False))

        redirect_response = self.client.get(response.location, follow_redirects=True)
        self.assertIn(b'Hazard deleted successfully.', redirect_response.data)

        deleted_hazard = Hazard.query.get(hazard_id)
        self.assertIsNone(deleted_hazard)

    def test_delete_hazard_by_regular_user_permission_denied(self):
        self._login_test_user() # Log in as regular user
        hazard_to_protect = Hazard(name='Protected Hazard', category='Secret', exposure_limit=1.0, unit='units')
        db.session.add(hazard_to_protect)
        db.session.commit()
        hazard_id = hazard_to_protect.id

        response = self.client.post(url_for('hazards.delete_hazard', hazard_id=hazard_id), follow_redirects=True)

        self.assertEqual(response.status_code, 200) # After redirect to main.index
        self.assertIn(b'You do not have permission to access this page.', response.data)
        self.assertEqual(urlparse(response.request.base_url).path, url_for('main.index', _external=False))

        still_exists_hazard = Hazard.query.get(hazard_id)
        self.assertIsNotNone(still_exists_hazard)

    def test_delete_hazard_non_existent(self):
        self._login_admin_user() # Admin user
        response = self.client.post(url_for('hazards.delete_hazard', hazard_id=9999))
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
        response = self.client.post(url_for('hazards.delete_hazard', hazard_id=hazard_id), follow_redirects=True)
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
