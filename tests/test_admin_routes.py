import unittest
from flask import url_for
from urllib.parse import urlparse, parse_qs
from app import db, create_app
from app.models import User, ROLE_USER, ROLE_ADMIN, Employee, Hazard, Exposure # Added models
from tests.test_config import BasicTests
from datetime import date # Added date

class TestAdminUserManagementRoutes(BasicTests):

    def setUp(self):
        super().setUp()
        self.user_regular = User(username='reguser', email='reg@example.com', role=ROLE_USER)
        self.user_regular.set_password('UserPass123!')

        self.admin_user = User(username='admin', email='admin@example.com', role=ROLE_ADMIN)
        self.admin_user.set_password('AdminPass123!')

        db.session.add_all([self.user_regular, self.admin_user])
        db.session.commit()

    def _login_user(self, username, password):
        return self.client.post(url_for('auth.login'), data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def _login_regular_user(self):
        return self._login_user('reguser', 'UserPass123!')

    def _login_admin_user(self):
        return self._login_user('admin', 'AdminPass123!')

    # --- Access Control Tests ---
    def test_admin_pages_unauthenticated_redirect(self):
        # No login
        endpoints_to_check = [
            url_for('admin.list_users'),
            url_for('admin.edit_user_role_status', user_id=self.user_regular.id)
        ]
        for endpoint in endpoints_to_check:
            response = self.client.get(endpoint, follow_redirects=False)
            self.assertEqual(response.status_code, 302)
            parsed_location = urlparse(response.location)
            self.assertEqual(parsed_location.path, url_for('auth.login', _external=False))
            query_params = parse_qs(parsed_location.query)
            self.assertIn('next', query_params)
            # Compare relative paths for 'next'
            self.assertEqual(query_params['next'][0], urlparse(endpoint).path)

        # Check POST to delete for unauthenticated
        delete_unauth_response = self.client.post(url_for('admin.delete_user', user_id=self.user_regular.id), follow_redirects=False)
        self.assertEqual(delete_unauth_response.status_code, 302)
        self.assertTrue(urlparse(delete_unauth_response.location).path.startswith(url_for('auth.login', _external=False)))


    def test_admin_pages_regular_user_permission_denied(self):
        self._login_regular_user()
        endpoints_to_check_get = [
            url_for('admin.list_users'),
            url_for('admin.edit_user_role_status', user_id=self.admin_user.id) # Try to edit admin
        ]
        for endpoint in endpoints_to_check_get:
            response = self.client.get(endpoint, follow_redirects=True) # Follow redirect to check flash
            self.assertEqual(response.status_code, 200) # Should be on main.index
            self.assertIn(b'You must be an administrator to access this page.', response.data)
            self.assertEqual(urlparse(response.request.base_url).path, url_for('main.index', _external=False))

        # Test POST attempt for edit
        response_post_edit = self.client.post(
            url_for('admin.edit_user_role_status', user_id=self.admin_user.id),
            data={'role': ROLE_USER, 'is_active': True},
            follow_redirects=True
        )
        self.assertEqual(response_post_edit.status_code, 200) # Should be on main.index
        self.assertIn(b'You must be an administrator to access this page.', response_post_edit.data)

        # Test POST attempt for delete
        response_post_delete = self.client.post(
            url_for('admin.delete_user', user_id=self.admin_user.id), # Attempt to delete admin user
            follow_redirects=True
        )
        self.assertEqual(response_post_delete.status_code, 200) # Should be on main.index
        self.assertIn(b'You must be an administrator to access this page.', response_post_delete.data)


    # --- List Users Page Tests ---
    def test_list_users_page_admin_access(self):
        self._login_admin_user()
        response = self.client.get(url_for('admin.list_users'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'User Management', response.data)
        self.assertIn(self.user_regular.username.encode(), response.data)
        self.assertIn(self.admin_user.username.encode(), response.data)

    # --- Edit User Role/Status Tests ---
    def test_edit_user_get_by_admin(self):
        self._login_admin_user()
        response = self.client.get(url_for('admin.edit_user_role_status', user_id=self.user_regular.id))
        self.assertEqual(response.status_code, 200)
        self.assertIn(f"Edit User: {self.user_regular.username}".encode(), response.data)
        # Check form pre-population (example for role)
        self.assertIn(f'<option value="{ROLE_USER}" selected>{ROLE_USER.title()}</option>'.encode(), response.data)
        self.assertIn(b'name="is_active" type="checkbox" checked', response.data) # Assuming default is_active is True

    def test_edit_user_post_by_admin_success(self):
        self._login_admin_user()

        # Ensure user_regular is initially active and user role
        self.user_regular.is_active = True
        self.user_regular.role = ROLE_USER
        db.session.commit()

        response = self.client.post(url_for('admin.edit_user_role_status', user_id=self.user_regular.id), data={
            'role': ROLE_ADMIN,
            'is_active': False # This will uncheck the checkbox
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200) # After redirect to list_users
        self.assertIn(f"User '{self.user_regular.username}' (ID: {self.user_regular.id}) has been updated.".encode(), response.data)

        updated_user = User.query.get(self.user_regular.id)
        self.assertEqual(updated_user.role, ROLE_ADMIN)
        self.assertFalse(updated_user.is_active)

    def test_edit_user_admin_cannot_deactivate_self(self):
        self._login_admin_user()
        initial_is_active = self.admin_user.is_active # Should be True

        response = self.client.post(url_for('admin.edit_user_role_status', user_id=self.admin_user.id), data={
            'role': ROLE_ADMIN, # Keep role as admin
            'is_active': False # Attempt to uncheck (deactivate)
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200) # Redirected to list_users
        self.assertIn(b'You cannot deactivate your own account.', response.data)

        admin_still_active = User.query.get(self.admin_user.id)
        self.assertEqual(admin_still_active.is_active, initial_is_active) # Should not have changed

    def test_edit_user_admin_cannot_remove_own_admin_role(self):
        self._login_admin_user()
        initial_role = self.admin_user.role # Should be ROLE_ADMIN

        response = self.client.post(url_for('admin.edit_user_role_status', user_id=self.admin_user.id), data={
            'role': ROLE_USER, # Attempt to change role to user
            'is_active': True  # Keep active
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200) # Redirected to list_users
        self.assertIn(b'You cannot remove your own admin role.', response.data)

        admin_still_admin = User.query.get(self.admin_user.id)
        self.assertEqual(admin_still_admin.role, initial_role) # Role should not have changed

    def test_edit_user_admin_can_update_own_role_if_still_admin(self):
        self._login_admin_user()
        # This test ensures that if an admin submits the form for themselves
        # without attempting to change their role from admin or deactivate themselves,
        # it still processes correctly (e.g., resaving their role as admin).
        response = self.client.post(url_for('admin.edit_user_role_status', user_id=self.admin_user.id), data={
            'role': ROLE_ADMIN, # Keeping role as admin
            'is_active': True   # Keeping active
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200) # Redirected to list_users
        self.assertIn(f"User '{self.admin_user.username}' (ID: {self.admin_user.id}) has been updated.".encode(), response.data)

        admin_unchanged = User.query.get(self.admin_user.id)
        self.assertEqual(admin_unchanged.role, ROLE_ADMIN)
        self.assertTrue(admin_unchanged.is_active)

    # --- 404 Test for Edit ---
    def test_edit_nonexistent_user_by_admin(self):
        self._login_admin_user()
        response = self.client.get(url_for('admin.edit_user_role_status', user_id=99999)) # Non-existent ID
        self.assertEqual(response.status_code, 404)

        response_post = self.client.post(url_for('admin.edit_user_role_status', user_id=99999), data={
            'role': ROLE_ADMIN, 'is_active': True
        })
        self.assertEqual(response_post.status_code, 404)

    # --- Delete User Tests ---
    def test_delete_user_by_admin_success_and_on_delete_set_null(self):
        self._login_admin_user()

        # Create an Employee, Hazard, and an Exposure recorded by the regular user
        test_employee = Employee(name="Test Employee for Deletion Check", job_title="Test Job", department="Test Dept")
        db.session.add(test_employee)
        test_hazard = Hazard(name="Test Hazard for Deletion Check", category="Test Cat", exposure_limit=1.0, unit="ppm")
        db.session.add(test_hazard)
        db.session.commit() # Commit employee and hazard to get their IDs

        exposure_to_check = Exposure(
            employee_id=test_employee.id,
            hazard_id=test_hazard.id,
            exposure_level=5.0,
            date=date(2024, 1, 1),
            recorded_by=self.user_regular.id # Linked to the user we will delete
        )
        db.session.add(exposure_to_check)
        db.session.commit()
        exposure_id = exposure_to_check.id
        user_to_delete_id = self.user_regular.id
        user_to_delete_username = self.user_regular.username

        response = self.client.post(url_for('admin.delete_user', user_id=user_to_delete_id), follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Redirected to list_users
        expected_flash_message = f"User {user_to_delete_username} (ID: {user_to_delete_id}) has been deleted."
        self.assertIn(expected_flash_message.encode(), response.data) # Check for part of the message

        self.assertIsNone(User.query.get(user_to_delete_id))

        updated_exposure = Exposure.query.get(exposure_id)
        self.assertIsNotNone(updated_exposure)
        self.assertIsNone(updated_exposure.recorded_by)

    def test_delete_user_admin_cannot_delete_self(self):
        self._login_admin_user()
        admin_id_before_attempt = self.admin_user.id

        response = self.client.post(url_for('admin.delete_user', user_id=self.admin_user.id), follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Redirected to list_users
        self.assertIn(b'You cannot delete your own administrator account.', response.data)

        self.assertIsNotNone(User.query.get(admin_id_before_attempt))

    def test_delete_user_by_regular_user_permission_denied(self):
        self._login_regular_user()
        # Attempt to delete the admin user (or any other user)
        response = self.client.post(url_for('admin.delete_user', user_id=self.admin_user.id), follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Redirected to main.index
        self.assertIn(b'You must be an administrator to access this page.', response.data)
        self.assertIsNotNone(User.query.get(self.admin_user.id)) # Admin user should still exist

    def test_delete_nonexistent_user_by_admin(self):
        self._login_admin_user()
        response = self.client.post(url_for('admin.delete_user', user_id=99999)) # Non-existent ID
        self.assertEqual(response.status_code, 404)


if __name__ == '__main__':
    unittest.main()
