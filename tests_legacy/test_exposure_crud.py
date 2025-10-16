import unittest
from datetime import date, datetime # Not used directly, but good for context
from flask import url_for, current_app # Added current_app (implicitly used by url_for in app context)
from urllib.parse import urlparse, parse_qs
from unittest.mock import patch # Added patch
from tests.test_config import BasicTests
from app import db
from app.models import User, Employee, Hazard, Exposure, ROLE_USER, ROLE_ADMIN

class TestExposureCRUD(BasicTests):

    def setUp(self):
        super().setUp()
        self.test_user = User(username='testuser', email='testuser@example.com', role=ROLE_USER)
        self.test_user.set_password('TestPass123!')

        self.admin_user = User(username='adminuser', email='admin@example.com', role=ROLE_ADMIN)
        self.admin_user.set_password('AdminPass123!')

        self.employee1 = Employee(name='John Doe', job_title='Engineer', department='Tech', hire_date=date(2023,1,1))
        self.employee2 = Employee(name='Jane Smith', job_title='Developer', department='Engineering', hire_date=date(2022,1,1))
        self.hazard1 = Hazard(name='Noise', category='Physical', exposure_limit=85.0, unit='dB(A)')
        self.hazard2 = Hazard(name='Dust', category='Chemical', exposure_limit=10.0, unit='mg/m^3')

        db.session.add_all([self.test_user, self.admin_user, self.employee1, self.employee2, self.hazard1, self.hazard2])
        db.session.commit() # Commit users, employees, hazards first to get IDs

        self.exposure1 = Exposure(
            employee_id=self.employee1.id,
            hazard_id=self.hazard1.id,
            exposure_level=90.0,
            duration=8,
            date=date(2023, 10, 15),
            location="Main Factory Floor",
            notes="Annual checkup, near machine A.",
            recorded_by=self.admin_user.id # Or test_user, depending on who should create initial test data
        )
        db.session.add(self.exposure1)
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

    def test_exposure_access_control_unauthenticated(self):
        # Log out the setup user first
        with self.client as c:
            c.get(url_for('auth.logout'), follow_redirects=True)

        endpoints_get = [
            url_for('exposures.list_exposures'),
            url_for('exposures.add_exposure'),
            url_for('exposures.edit_exposure', exposure_id=1),
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

        delete_endpoint_url = url_for('exposures.delete_exposure', exposure_id=1)
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

    def test_list_exposures(self):
        # Listing available to regular users
        self._login_test_user()
        response = self.client.get(url_for('exposures.list_exposures'))
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

        response = self.client.get(url_for('exposures.list_exposures'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.employee1.name.encode(), response.data)
        self.assertIn(self.hazard1.name.encode(), response.data)
        self.assertIn(b'75.0', response.data)
        self.assertNotIn(b'No exposure records found.', response.data)

    def test_add_exposure_get_by_admin(self): # Renamed
        self._login_admin_user()
        response = self.client.get(url_for('exposures.add_exposure'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Add Exposure Record', response.data)
        self.assertIn(self.employee1.name.encode(), response.data)
        self.assertIn(self.hazard1.name.encode(), response.data)

    def test_add_exposure_get_by_regular_user_permission_denied(self):
        self._login_test_user()
        response = self.client.get(url_for('exposures.add_exposure'), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'You do not have permission to access this page.', response.data)
        self.assertEqual(urlparse(response.request.base_url).path, url_for('main.index', _external=False))

    def test_add_exposure_post_by_admin_success(self): # Renamed
        self._login_admin_user()
        exposure_data = {
            'employee': self.employee1.id,
            'hazard': self.hazard1.id,
            'exposure_level': '80.5',
            'duration': '8',
            'date': '2023-06-01',
            'location': 'Factory Floor',
            'notes': 'Routine check'
        }
        response = self.client.post(url_for('exposures.add_exposure'), data=exposure_data, follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse(response.location).path, url_for('exposures.list_exposures', _external=False))

        redirect_response = self.client.get(response.location)
        self.assertIn(b'Exposure record added successfully.', redirect_response.data)

        exposure = Exposure.query.filter_by(location='Factory Floor').first()
        self.assertIsNotNone(exposure)
        self.assertEqual(exposure.employee_id, self.employee1.id)
        self.assertEqual(exposure.hazard_id, self.hazard1.id)
        self.assertEqual(exposure.exposure_level, 80.5)
        self.assertEqual(exposure.recorded_by, self.admin_user.id) # Should be admin

    def test_add_exposure_post_by_regular_user_permission_denied(self):
        self._login_test_user()
        exposure_data = {
            'employee': self.employee1.id, 'hazard': self.hazard1.id,
            'exposure_level': '80.5', 'date': '2023-06-01', 'location': 'Factory Floor NonAdmin'
        }
        response = self.client.post(url_for('exposures.add_exposure'), data=exposure_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'You do not have permission to access this page.', response.data)
        self.assertEqual(urlparse(response.request.base_url).path, url_for('main.index', _external=False))
        self.assertIsNone(Exposure.query.filter_by(location='Factory Floor NonAdmin').first())

    def test_add_exposure_post_validation_error_by_admin(self): # Renamed
        self._login_admin_user() # Admin can submit invalid data
        # Missing employee
        response = self.client.post(url_for('exposures.add_exposure'), data={'hazard': self.hazard1.id, 'exposure_level': '70', 'date': '2023-01-01'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Employee</label>', response.data) # Check for field label
        self.assertIn(b'This field is required.', response.data) # Error for employee

        # Invalid exposure level
        response = self.client.post(url_for('exposures.add_exposure'), data={'employee': self.employee1.id, 'hazard': self.hazard1.id, 'exposure_level': 'abc', 'date': '2023-01-01'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Not a valid float value', response.data)

        self.assertEqual(Exposure.query.count(), 0) # No exposure should be created

    def test_edit_exposure_get_by_admin(self): # Renamed and split
        self._login_admin_user()
        exposure = Exposure(
            employee_id=self.employee1.id, hazard_id=self.hazard1.id,
            exposure_level=70.0, date=date(2023,1,10), recorded_by=self.admin_user.id, # Use admin for creation
            location="Old Location"
        )
        db.session.add(exposure)
        db.session.commit()
        exposure_id = exposure.id

        response_get = self.client.get(url_for('exposures.edit_exposure', exposure_id=exposure_id))
        self.assertEqual(response_get.status_code, 200)
        self.assertIn(b'Edit Exposure Record', response_get.data)
        self.assertIn(self.employee1.name.encode(), response_get.data)
        self.assertIn(b'Old Location', response_get.data)

    def test_edit_exposure_get_by_regular_user_permission_denied(self):
        self._login_test_user()
        exposure = Exposure(
            employee_id=self.employee1.id, hazard_id=self.hazard1.id,
            exposure_level=70.0, date=date(2023,1,10), recorded_by=self.test_user.id, # Can be created by test_user for this check
            location="Protected Location"
        )
        db.session.add(exposure)
        db.session.commit()
        exposure_id = exposure.id

        response_get = self.client.get(url_for('exposures.edit_exposure', exposure_id=exposure_id), follow_redirects=True)
        self.assertEqual(response_get.status_code, 200)
        self.assertIn(b'You do not have permission to access this page.', response_get.data)
        self.assertEqual(urlparse(response_get.request.base_url).path, url_for('main.index', _external=False))

    def test_edit_exposure_post_by_admin_success(self): # Renamed and split
        self._login_admin_user()
        exposure = Exposure(
            employee_id=self.employee1.id, hazard_id=self.hazard1.id,
            exposure_level=70.0, date=date(2023,1,10), recorded_by=self.admin_user.id, # Admin created
            location="Admin Edit Initial Location"
        )
        db.session.add(exposure)
        db.session.commit()
        exposure_id = exposure.id

        updated_data = {
            'employee': self.employee2.id, 'hazard': self.hazard2.id, 'exposure_level': '75.5',
            'duration': '4', 'date': '2023-01-12', 'location': 'Admin New Location', 'notes': 'Admin updated notes'
        }
        response_post = self.client.post(url_for('exposures.edit_exposure', exposure_id=exposure_id), data=updated_data, follow_redirects=False)
        self.assertEqual(response_post.status_code, 302)
        self.assertEqual(urlparse(response_post.location).path, url_for('exposures.list_exposures', _external=False))

        redirect_response = self.client.get(response_post.location, follow_redirects=True)
        self.assertIn(b'Exposure record updated successfully.', redirect_response.data)

        updated_exp = Exposure.query.get(exposure_id)
        self.assertEqual(updated_exp.employee_id, self.employee2.id)
        self.assertEqual(updated_exp.hazard_id, self.hazard2.id)
        self.assertEqual(updated_exp.location, 'Admin New Location')

    def test_edit_exposure_post_by_regular_user_permission_denied(self):
        self._login_test_user()
        original_location = "User Edit Exposure Original Loc"
        exposure = Exposure(
            employee_id=self.employee1.id, hazard_id=self.hazard1.id,
            exposure_level=70.0, date=date(2023,1,10), recorded_by=self.test_user.id, # Can be created by test_user
            location=original_location
        )
        db.session.add(exposure)
        db.session.commit()
        exposure_id = exposure.id

        updated_data = {'location': 'User Edited Exposure Attempt Loc', 'exposure_level': '99.9'}
        response_post = self.client.post(url_for('exposures.edit_exposure', exposure_id=exposure_id), data=updated_data, follow_redirects=True)

        self.assertEqual(response_post.status_code, 200)
        self.assertIn(b'You do not have permission to access this page.', response_post.data)
        self.assertEqual(urlparse(response_post.request.base_url).path, url_for('main.index', _external=False))

        unchanged_exposure = Exposure.query.get(exposure_id)
        self.assertEqual(unchanged_exposure.location, original_location)


    def test_edit_exposure_non_existent(self):
        self._login_admin_user() # Admin user
        response_get = self.client.get(url_for('exposures.edit_exposure', exposure_id=9999))
        self.assertEqual(response_get.status_code, 404)

        response_post = self.client.post(url_for('exposures.edit_exposure', exposure_id=9999), data={'exposure_level': '100'})
        self.assertEqual(response_post.status_code, 404)

    def test_delete_exposure_by_admin(self): # Renamed
        self._login_admin_user() # Log in as admin
        exposure = Exposure(
            employee_id=self.employee1.id, hazard_id=self.hazard1.id,
            exposure_level=60.0, date=date(2023,2,15), recorded_by=self.test_user.id
        )
        db.session.add(exposure)
        db.session.commit()
        exposure_id = exposure.id

        response = self.client.post(url_for('exposures.delete_exposure', exposure_id=exposure_id), follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse(response.location).path, url_for('exposures.list_exposures', _external=False))

        redirect_response = self.client.get(response.location)
        self.assertIn(b'Exposure record deleted successfully.', redirect_response.data)

        self.assertIsNone(Exposure.query.get(exposure_id))

    def test_delete_exposure_by_regular_user_permission_denied(self):
        self._login_test_user() # Log in as regular user
        exposure_to_protect = Exposure(
            employee_id=self.employee1.id, hazard_id=self.hazard1.id,
            exposure_level=50.0, date=date(2023,3,3), recorded_by=self.test_user.id
        )
        db.session.add(exposure_to_protect)
        db.session.commit()
        exposure_id = exposure_to_protect.id

        response = self.client.post(url_for('exposures.delete_exposure', exposure_id=exposure_id), follow_redirects=True)

        self.assertEqual(response.status_code, 200) # After redirect to main.index
        self.assertIn(b'You do not have permission to access this page.', response.data)
        self.assertEqual(urlparse(response.request.base_url).path, url_for('main.index', _external=False))

        still_exists_exposure = Exposure.query.get(exposure_id)
        self.assertIsNotNone(still_exists_exposure)

    def test_delete_exposure_non_existent(self):
        self._login_admin_user() # Admin user
        response = self.client.post(url_for('exposures.delete_exposure', exposure_id=9999))
        self.assertEqual(response.status_code, 404)

    # --- PDF Generation Tests ---
    def test_print_exposure_pdf_unauthenticated(self):
        # Log out any logged-in user from setUp
        with self.client as c:
            c.get(url_for('auth.logout'), follow_redirects=True)

        response = self.client.get(url_for('exposures.print_exposure_pdf', exposure_id=self.exposure1.id))
        self.assertEqual(response.status_code, 302) # Redirect to login
        self.assertTrue(urlparse(response.location).path.startswith(url_for('auth.login', _external=False)))

    def test_print_exposure_pdf_authenticated_success(self):
        self._login_regular_user() # Any logged-in user can print
        response = self.client.get(url_for('exposures.print_exposure_pdf', exposure_id=self.exposure1.id))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/pdf')
        self.assertIn(f'inline; filename=exposure_record_{self.exposure1.id}.pdf', response.headers['Content-Disposition'])
        self.assertTrue(response.data.startswith(b'%PDF-'))

    def test_print_exposure_pdf_nonexistent_exposure(self):
        self._login_regular_user()
        response = self.client.get(url_for('exposures.print_exposure_pdf', exposure_id=99999))
        self.assertEqual(response.status_code, 404)

    @patch('app.utils.pdf_generator.generate_exposure_pdf')
    def test_print_exposure_pdf_generation_error_handling(self, mock_generate_pdf):
        self._login_regular_user()
        mock_generate_pdf.side_effect = Exception("Simulated PDF generation error")

        response = self.client.get(url_for('exposures.print_exposure_pdf', exposure_id=self.exposure1.id), follow_redirects=True)

        self.assertEqual(response.status_code, 200) # Follows redirect to list page
        self.assertIn(b'Error generating PDF for this exposure record.', response.data)
        self.assertEqual(urlparse(response.request.base_url).path, url_for('exposures.list_exposures', _external=False))


if __name__ == '__main__':
    unittest.main()
