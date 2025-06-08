import unittest
from flask_login import current_user
from tests.test_config import BasicTests
from app import db # Direct import of db from app
from models import User # User model
from datetime import datetime

class TestAuthRoutes(BasicTests):

    def test_get_register_page(self):
        response = self.app.get('/register', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Register', response.data) # Check for a keyword in the rendered page

    def test_get_login_page(self):
        response = self.app.get('/login', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data) # Check for a keyword

    def test_successful_registration(self):
        response = self.app.post('/register', data=dict(
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

        response = self.app.post('/register', data=dict(
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

        response = self.app.post('/register', data=dict(
            username='newusername',
            email='existingemail@example.com', # Same email
            password='NewPass123!',
            confirm_password='NewPass123!'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Stays on register page
        self.assertIn(b'Email already registered.', response.data) # Flash message
        self.assertIn(b'Register', response.data)

    def test_registration_password_too_short(self):
        response = self.app.post('/register', data=dict(
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
        response = self.app.post('/register', data=dict(
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
        response = self.app.post('/register', data=dict(
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

        response = self.app.post('/login', data=dict(
            username='loginuser',
            password='LoginPass123!'
        ), follow_redirects=False) # Important: check redirect before it's followed

        self.assertEqual(response.status_code, 302) # Should redirect
        self.assertTrue(response.location.endswith('/')) # Redirects to index

        # Follow redirect to check current_user status
        with self.app as client: # Use a new client context to ensure session persistence
            client.post('/login', data=dict(
                username='loginuser',
                password='LoginPass123!'
            ), follow_redirects=True) # This time follow for current_user check

            self.assertTrue(current_user.is_authenticated)
            self.assertEqual(current_user.username, 'loginuser')

        # Verify last_login was updated
        updated_user = User.query.filter_by(username='loginuser').first()
        self.assertIsNotNone(updated_user.last_login)
        if initial_last_login:
            self.assertGreater(updated_user.last_login, initial_last_login)
        else:
            self.assertIsInstance(updated_user.last_login, datetime)


    def test_login_invalid_username(self):
        response = self.app.post('/login', data=dict(
            username='nonexistentuser',
            password='anypassword'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Stays on login page
        self.assertIn(b'Login Unsuccessful. Please check username and password.', response.data)
        self.assertFalse(current_user.is_authenticated)

    def test_login_invalid_password(self):
        # Create a user
        test_user = User(username='loginuser2', email='login2@example.com')
        test_user.set_password('CorrectPass123!')
        db.session.add(test_user)
        db.session.commit()

        response = self.app.post('/login', data=dict(
            username='loginuser2',
            password='WrongPassword123!'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Stays on login page
        self.assertIn(b'Login Unsuccessful. Please check username and password.', response.data)
        self.assertFalse(current_user.is_authenticated)

    def test_login_empty_credentials_username(self):
        response = self.app.post('/login', data=dict(
            username='',
            password='somepassword'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Stays on login page
        self.assertIn(b'This field is required.', response.data) # WTForms error for username
        self.assertFalse(current_user.is_authenticated)

    def test_login_empty_credentials_password(self):
        response = self.app.post('/login', data=dict(
            username='someuser',
            password=''
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Stays on login page
        self.assertIn(b'This field is required.', response.data) # WTForms error for password
        self.assertFalse(current_user.is_authenticated)

    # --- Logout Test ---
    def test_logout(self):
        # 1. Create and login a user
        logout_user_obj = User(username='logoutuser', email='logout@example.com')
        logout_user_obj.set_password('LogoutPass123!')
        db.session.add(logout_user_obj)
        db.session.commit()

        login_response = self.app.post('/login', data=dict(
            username='logoutuser',
            password='LogoutPass123!'
        ), follow_redirects=True)
        self.assertEqual(login_response.status_code, 200) # Successfully on index page
        self.assertIn(b'Home', login_response.data) # Assuming 'Home' is on index for logged-in users
                                                     # or check for current_user.is_authenticated within a client context

        # 2. Perform logout
        # We need to use a client that maintains session state for logout
        with self.app as client:
            # First, ensure user is logged in this client's context
            client.post('/login', data=dict(username='logoutuser', password='LogoutPass123!'), follow_redirects=True)
            self.assertTrue(current_user.is_authenticated, "User should be authenticated before logout")

            logout_response = client.get('/logout', follow_redirects=False)
            self.assertEqual(logout_response.status_code, 302) # Redirects
            self.assertTrue(logout_response.location.endswith('/login'))

            # Follow redirect to check page content and current_user status
            final_page_response = client.get(logout_response.location, follow_redirects=True) # Get the login page
            self.assertEqual(final_page_response.status_code, 200)
            self.assertIn(b'You have been logged out.', final_page_response.data) # Flash message
            self.assertIn(b'Login', final_page_response.data) # Should be on login page

            self.assertFalse(current_user.is_authenticated, "User should be anonymous after logout")

            # 3. Try to access a protected page
            protected_page_response = client.get('/', follow_redirects=False) # Access index
            self.assertEqual(protected_page_response.status_code, 302) # Should redirect to login
            self.assertTrue(protected_page_response.location.endswith('/login'))


if __name__ == "__main__":
    unittest.main()
