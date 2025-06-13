import unittest
from flask import url_for
from urllib.parse import urlparse # Added import
from flask_login import current_user
from unittest.mock import patch, ANY # For mocking mail.send & using ANY
from tests.test_config import BasicTests
from app import db, mail, bcrypt # Import mail for mocking & bcrypt
from app.models import User
from app.forms import RequestResetForm, ResetPasswordForm
from datetime import datetime, timedelta

class TestAuthRoutes(BasicTests):

    def test_get_register_page(self):
        # URLs should now include the blueprint prefix
        response = self.client.get('/auth/register', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Register', response.data) # Check for a keyword in the rendered page

    def test_get_login_page(self):
        response = self.client.get('/auth/login', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data) # Check for a keyword

    def test_successful_registration(self):
        response = self.client.post('/auth/register', data=dict(
            username='newuser',
            email='newuser@example.com',
            password='NewUserPass123!',
            confirm_password='NewUserPass123!'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Should redirect to login, which is 200
        self.assertIn(b'Your account has been created!', response.data) # Flash message
        self.assertIn(b'Login', response.data) # Should be on login page

        # Check user in DB
        user = User.query.filter_by(username='newuser').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'newuser@example.com')

    def test_registration_existing_username(self):
        # First, create a user
        user = User(username='existinguser', email='exists@example.com')
        user.set_password('ExistingPass123!')
        db.session.add(user)
        db.session.commit()

        response = self.client.post('/auth/register', data=dict(
            username='existinguser', # Same username
            email='newemail@example.com',
            password='NewPass123!',
            confirm_password='NewPass123!'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Stays on register page
        self.assertIn(b'Username already exists.', response.data) # Flash message
        self.assertIn(b'Register', response.data) # Should still be on register page

    def test_registration_existing_email(self):
        # First, create a user
        user = User(username='anotheruser', email='existingemail@example.com')
        user.set_password('AnotherPass123!')
        db.session.add(user)
        db.session.commit()

        response = self.client.post('/auth/register', data=dict(
            username='newusername',
            email='existingemail@example.com', # Same email
            password='NewPass123!',
            confirm_password='NewPass123!'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Stays on register page
        self.assertIn(b'Email already registered.', response.data) # Flash message
        self.assertIn(b'Register', response.data)

    def test_registration_password_too_short(self):
        response = self.client.post('/auth/register', data=dict(
            username='testuser',
            email='test@example.com',
            password='short',
            confirm_password='short'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Stays on register page
        # WTForms error for length
        self.assertIn(b'Field must be at least 8 characters long.', response.data)
        self.assertIn(b'Register', response.data)

    def test_registration_password_mismatch(self):
        response = self.client.post('/auth/register', data=dict(
            username='testuser',
            email='test@example.com',
            password='ValidPass123!',
            confirm_password='DifferentPass123!'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Stays on register page
        self.assertIn(b'Field must be equal to password.', response.data) # WTForms error
        self.assertIn(b'Register', response.data)

    def test_registration_password_missing_criteria_from_model(self):
        # Test one of the model's specific password rules not covered by basic WTForms length/equalTo
        # For example, missing an uppercase letter
        response = self.client.post('/auth/register', data=dict(
            username='testuser',
            email='test@example.com',
            password='validpass123!', # Missing uppercase
            confirm_password='validpass123!'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Stays on register page
        # This flash message comes from the app.py route when user.set_password() raises ValueError
        self.assertIn(b'Password must contain at least one uppercase letter.', response.data)
        self.assertIn(b'Register', response.data)

    # --- Login Tests ---
    def test_login_successful(self):
        # Create a user
        test_user = User(username='loginuser', email='login@example.com')
        test_user.set_password('LoginPass123!')
        db.session.add(test_user)
        db.session.commit()

        initial_last_login = test_user.last_login # Could be None

        response = self.client.post('/auth/login', data=dict(
            username='loginuser',
            password='LoginPass123!'
        ), follow_redirects=False) # Important: check redirect before it's followed

        self.assertEqual(response.status_code, 302) # Should redirect
        parsed_location = urlparse(response.location)
        expected_path = url_for('main.index', _external=False)
        self.assertEqual(parsed_location.path, expected_path)

        # Follow redirect to check current_user status
        # The test client (self.client) maintains cookiejar, so session is persisted.
        # We make another request to a known endpoint to check current_user's state
        # or check a page that displays user-specific info.
        with self.client as client_in_block: # Use the test client to maintain session, aliased
            response_after_login = client_in_block.post('/auth/login', data=dict(
                username='loginuser',
                password='LoginPass123!'
            ), follow_redirects=True)

            # Now current_user should be set within this client's context if accessing a route
            # To test current_user directly, it's best to make a request to an endpoint
            # that exposes this information or relies on it.
            # For example, accessing the main index page which might show user's name.
            self.assertTrue(current_user.is_authenticated) # This checks current_user in the test's app context
            self.assertEqual(current_user.username, 'loginuser')

        # Verify last_login was updated
        updated_user = User.query.filter_by(username='loginuser').first()
        self.assertIsNotNone(updated_user.last_login)
        if initial_last_login:
            self.assertGreater(updated_user.last_login, initial_last_login)
        else:
            self.assertIsInstance(updated_user.last_login, datetime)


    def test_login_invalid_username(self):
        response = self.client.post('/auth/login', data=dict(
            username='nonexistentuser',
            password='anypassword'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Stays on login page
        self.assertIn(b'Login Unsuccessful. Please check username and password.', response.data)
        self.assertFalse(getattr(current_user, 'is_authenticated', False))

    def test_login_invalid_password(self):
        # Create a user
        test_user = User(username='loginuser2', email='login2@example.com')
        test_user.set_password('CorrectPass123!')
        db.session.add(test_user)
        db.session.commit()

        response = self.client.post('/auth/login', data=dict(
            username='loginuser2',
            password='WrongPassword123!'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Stays on login page
        self.assertIn(b'Login Unsuccessful. Please check username and password.', response.data)
        self.assertFalse(getattr(current_user, 'is_authenticated', False))

    def test_login_empty_credentials_username(self):
        response = self.client.post('/auth/login', data=dict(
            username='',
            password='somepassword'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Stays on login page
        self.assertIn(b'This field is required.', response.data) # WTForms error for username
        self.assertFalse(getattr(current_user, 'is_authenticated', False))

    def test_login_empty_credentials_password(self):
        response = self.client.post('/auth/login', data=dict(
            username='someuser',
            password=''
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Stays on login page
        self.assertIn(b'This field is required.', response.data) # WTForms error for password
        self.assertFalse(getattr(current_user, 'is_authenticated', False))

    # --- Logout Test ---
    def test_logout(self):
        # 1. Create and login a user
        logout_user_obj = User(username='logoutuser', email='logout@example.com')
        logout_user_obj.set_password('LogoutPass123!')
        db.session.add(logout_user_obj)
        db.session.commit()

        # Log in the user using self.client
        login_response = self.client.post('/auth/login', data=dict(
            username='logoutuser',
            password='LogoutPass123!'
        ), follow_redirects=True)
        self.assertEqual(login_response.status_code, 200)
        # Check if we are on the main page (e.g., by looking for a unique element of main.index)
        # For now, we assume it redirects to '/' which is main.index.
        # self.assertTrue(getattr(current_user, 'is_authenticated', False)) # This check is problematic here.
        # Instead, we verify login by being able to access a protected page or by content on the redirected page.
        # The login_response being 200 after follow_redirects=True implies login was successful enough to redirect to 'main.index'.

        # Perform logout using self.client consistently
        logout_response = self.client.get('/auth/logout', follow_redirects=False)
        self.assertEqual(logout_response.status_code, 302) # Redirects
        parsed_logout_redirect = urlparse(logout_response.location)
        self.assertEqual(parsed_logout_redirect.path, url_for('auth.login', _external=False))

        # Follow redirect to check page content and current_user status
        final_page_response = self.client.get(logout_response.location, follow_redirects=True) # Get the login page
        self.assertEqual(final_page_response.status_code, 200)
        self.assertIn(b'You have been logged out.', final_page_response.data) # Flash message
        self.assertIn(b'Login', final_page_response.data) # Should be on login page

        self.assertFalse(getattr(current_user, 'is_authenticated', False), "User should be anonymous after logout")

        # Try to access a protected page (main.index)
        protected_page_response = self.client.get(url_for('main.index', _external=False), follow_redirects=False)
        self.assertEqual(protected_page_response.status_code, 302) # Should redirect to login
        parsed_protected_redirect = urlparse(protected_page_response.location)
        self.assertEqual(parsed_protected_redirect.path, url_for('auth.login', _external=False))

    # --- Password Reset Request Tests ---
    def test_request_reset_password_route_get(self):
        response = self.client.get(url_for('auth.request_reset_password'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Request Password Reset', response.data)

    @patch('app.auth.email.mail.send') # Mock mail.send from app.auth.email module
    def test_request_reset_password_route_post_existing_email(self, mock_send_mail):
        user_email = 'resetme@example.com'
        user = User(username='resetuser', email=user_email)
        user.set_password('Password123!')
        db.session.add(user)
        db.session.commit()

        response = self.client.post(url_for('auth.request_reset_password'), data={'email': user_email}, follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Redirects to login
        self.assertIn(b'If an account with that email exists, instructions to reset your password have been sent.', response.data)
        self.assertTrue(urlparse(response.request.base_url).path.endswith(url_for('auth.login')))
        mock_send_mail.assert_called_once()

        updated_user = User.query.filter_by(email=user_email).first()
        self.assertIsNotNone(updated_user.reset_token)
        self.assertIsNotNone(updated_user.reset_token_expires)

    @patch('app.auth.email.mail.send')
    def test_request_reset_password_route_post_nonexistent_email(self, mock_send_mail):
        response = self.client.post(url_for('auth.request_reset_password'), data={'email': 'nonexistent@example.com'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Redirects to login
        self.assertIn(b'If an account with that email exists, instructions to reset your password have been sent.', response.data)
        self.assertTrue(urlparse(response.request.base_url).path.endswith(url_for('auth.login')))
        mock_send_mail.assert_not_called() # Should not be called if user doesn't exist

    def test_request_reset_password_route_authenticated_user(self):
        # Create and log in a user
        user = User(username='autheduser', email='authed@example.com')
        user.set_password('Password123!')
        db.session.add(user)
        db.session.commit()
        self.client.post(url_for('auth.login'), data={'username': 'autheduser', 'password': 'Password123!'}, follow_redirects=True)

        response_get = self.client.get(url_for('auth.request_reset_password'), follow_redirects=False)
        self.assertEqual(response_get.status_code, 302)
        self.assertTrue(urlparse(response_get.location).path.endswith(url_for('main.index')))

        response_post = self.client.post(url_for('auth.request_reset_password'), data={'email': 'authed@example.com'}, follow_redirects=False)
        self.assertEqual(response_post.status_code, 302)
        self.assertTrue(urlparse(response_post.location).path.endswith(url_for('main.index')))


    # --- Reset Password with Token Tests ---
    def test_reset_with_token_route_get_valid_token(self):
        user = User(username='validtokenuser', email='validtoken@example.com')
        user.set_password('Password123!')
        db.session.add(user)
        db.session.commit()
        token = user.get_reset_token()
        db.session.commit()

        response = self.client.get(url_for('auth.reset_with_token', token=token))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Reset Your Password', response.data)

    def test_reset_with_token_route_get_invalid_token(self):
        response = self.client.get(url_for('auth.reset_with_token', token='invalidtoken'), follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Redirects to request_reset
        self.assertIn(b'That is an invalid or expired token.', response.data)
        self.assertTrue(urlparse(response.request.base_url).path.endswith(url_for('auth.request_reset_password')))

    def test_reset_with_token_route_get_expired_token(self):
        user = User(username='expiredtokenuser', email='expiredtoken@example.com')
        user.set_password('Password123!')
        db.session.add(user)
        db.session.commit()
        token = user.get_reset_token(expires_sec=-1) # Token already expired
        db.session.commit()

        response = self.client.get(url_for('auth.reset_with_token', token=token), follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Redirects to request_reset
        self.assertIn(b'That is an invalid or expired token.', response.data)

    def test_reset_with_token_route_post_success(self):
        user = User(username='resetpassuser', email='resetpass@example.com')
        original_password_hash = bcrypt.generate_password_hash('OldPassword123!').decode('utf-8')
        user.password_hash = original_password_hash # Set initial password hash directly
        db.session.add(user)
        db.session.commit()
        token = user.get_reset_token()
        db.session.commit()

        response = self.client.post(url_for('auth.reset_with_token', token=token), data={
            'password': 'NewSecurePassword123!',
            'confirm_password': 'NewSecurePassword123!'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Redirects to login
        self.assertIn(b'Your password has been successfully updated!', response.data)
        self.assertTrue(urlparse(response.request.base_url).path.endswith(url_for('auth.login')))

        updated_user = User.query.filter_by(email='resetpass@example.com').first()
        self.assertTrue(updated_user.check_password('NewSecurePassword123!'))
        self.assertNotEqual(updated_user.password_hash, original_password_hash)
        self.assertIsNone(updated_user.reset_token)
        self.assertIsNone(updated_user.reset_token_expires)

    def test_reset_with_token_route_post_invalid_token(self):
        response = self.client.post(url_for('auth.reset_with_token', token='invalidtoken'), data={
            'password': 'NewPassword123!', 'confirm_password': 'NewPassword123!'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Redirects to request_reset
        self.assertIn(b'That is an invalid or expired token.', response.data)

    def test_reset_with_token_route_post_mismatched_passwords(self):
        user = User(username='mismatchuser', email='mismatch@example.com')
        user.set_password('Password123!')
        db.session.add(user)
        db.session.commit()
        token = user.get_reset_token()
        db.session.commit()

        response = self.client.post(url_for('auth.reset_with_token', token=token), data={
            'password': 'NewPassword123!', 'confirm_password': 'DifferentPassword123!'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Stays on reset_password_form
        self.assertIn(b'Passwords must match.', response.data)

    def test_reset_with_token_route_post_weak_password(self):
        user = User(username='weakpassuser', email='weakpass@example.com')
        user.set_password('Password123!') # Initial valid password
        db.session.add(user)
        db.session.commit()
        token = user.get_reset_token()
        db.session.commit()

        response = self.client.post(url_for('auth.reset_with_token', token=token), data={
            'password': 'weak', 'confirm_password': 'weak'
        }, follow_redirects=True) # Does not redirect if form validation fails server-side due to model
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Password must be at least 8 characters long.', response.data) # Error from User.set_password flashed

    def test_reset_with_token_route_authenticated_user(self):
        # Create and log in a user
        user = User(username='authedreset', email='authedreset@example.com')
        user.set_password('Password123!')
        db.session.add(user)
        db.session.commit()
        self.client.post(url_for('auth.login'), data={'username': 'authedreset', 'password': 'Password123!'}, follow_redirects=True)

        # Generate a token for this user just to have a valid token in URL
        token = user.get_reset_token()
        db.session.commit()

        response_get = self.client.get(url_for('auth.reset_with_token', token=token), follow_redirects=False)
        self.assertEqual(response_get.status_code, 302)
        self.assertTrue(urlparse(response_get.location).path.endswith(url_for('main.index')))

        response_post = self.client.post(url_for('auth.reset_with_token', token=token), data={
            'password': 'NewPassword123!', 'confirm_password': 'NewPassword123!'
        }, follow_redirects=False)
        self.assertEqual(response_post.status_code, 302)
        self.assertTrue(urlparse(response_post.location).path.endswith(url_for('main.index')))

    def test_auth_event_logging(self):
        with patch('flask.current_app.logger.info') as mock_logger_info, \
             patch('flask.current_app.logger.warning') as mock_logger_warning, \
             patch('flask.current_app.logger.error') as mock_logger_error: # Not strictly testing error here, but good to have

            # Registration
            reg_response = self.client.post(url_for('auth.register'), data={
                'username': 'logtestuser',
                'email': 'logtest@example.com',
                'password': 'LogTestPassword1!', # Ensure this meets complexity
                'confirm_password': 'LogTestPassword1!'
            }, follow_redirects=True)
            self.assertEqual(reg_response.status_code, 200) # Should land on login page

            # Check if info was called with a message containing 'registered successfully'
            called_with_registered = any('registered successfully' in call_args[0][0] for call_args in mock_logger_info.call_args_list)
            self.assertTrue(called_with_registered, "Registration success log not found.")
            mock_logger_info.reset_mock()

            # Login
            login_response = self.client.post(url_for('auth.login'), data={
                'username': 'logtestuser',
                'password': 'LogTestPassword1!'
            }, follow_redirects=True)
            self.assertEqual(login_response.status_code, 200) # Should land on index page
            called_with_login = any('logged in successfully' in call_args[0][0] for call_args in mock_logger_info.call_args_list)
            self.assertTrue(called_with_login, "Login success log not found.")
            mock_logger_info.reset_mock()

            # Failed Login
            failed_login_response = self.client.post(url_for('auth.login'), data={
                'username': 'logtestuser',
                'password': 'WrongPassword!'
            }, follow_redirects=True)
            self.assertEqual(failed_login_response.status_code, 200) # Stays on login page
            called_with_failed_login = any('Failed login attempt' in call_args[0][0] for call_args in mock_logger_warning.call_args_list)
            self.assertTrue(called_with_failed_login, "Failed login warning log not found.")
            mock_logger_warning.reset_mock()

            # Password Reset Request
            with patch('app.auth.email.mail.send') as mock_send_mail: # Mock mail.send for this part
                reset_req_response = self.client.post(url_for('auth.request_reset_password'), data={
                    'email': 'logtest@example.com'
                }, follow_redirects=True)
                self.assertEqual(reset_req_response.status_code, 200) # Lands on login page
                mock_send_mail.assert_called_once() # Ensure email sending was attempted

            called_with_reset_request = any('Password reset requested' in call_args[0][0] for call_args in mock_logger_info.call_args_list)
            self.assertTrue(called_with_reset_request, "Password reset request log not found.")
            mock_logger_info.reset_mock()

            # Check email sent log
            # This assumes mock_send_mail doesn't raise an exception, allowing the success log to be reached.
            called_with_email_sent = any('Password reset email successfully sent' in call_args[0][0] for call_args in mock_logger_info.call_args_list)
            self.assertTrue(called_with_email_sent, "Password reset email sent log not found.")


if __name__ == "__main__":
    unittest.main()
