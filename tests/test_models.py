import unittest
from datetime import datetime, timedelta # Added imports
import time # For time.sleep if needed for expiry test, though manual setting is better
from app import db
from app.models import User
from tests.test_config import BasicTests

class TestUserModel(BasicTests):

    def test_set_password_success(self):
        user = User(username="testuser", email="test@example.com")
        try:
            user.set_password("ValidPass123!")
            self.assertIsNotNone(user.password_hash)
            self.assertTrue(user.check_password("ValidPass123!"))
        except ValueError:
            self.fail("set_password raised ValueError unexpectedly for a valid password.")

    def test_set_password_too_short(self):
        user = User(username="testuser", email="test@example.com")
        with self.assertRaisesRegex(ValueError, "Password must be at least 8 characters long."):
            user.set_password("Vp1!")

    def test_set_password_no_digit(self):
        user = User(username="testuser", email="test@example.com")
        with self.assertRaisesRegex(ValueError, "Password must contain at least one number."):
            user.set_password("ValidPass!")

    def test_set_password_no_uppercase(self):
        user = User(username="testuser", email="test@example.com")
        with self.assertRaisesRegex(ValueError, "Password must contain at least one uppercase letter."):
            user.set_password("validpass1!")

    def test_set_password_no_lowercase(self):
        user = User(username="testuser", email="test@example.com")
        with self.assertRaisesRegex(ValueError, "Password must contain at least one lowercase letter."):
            user.set_password("VALIDPASS1!")

    def test_set_password_no_special_char(self):
        user = User(username="testuser", email="test@example.com")
        with self.assertRaisesRegex(ValueError, "Password must contain at least one special character"):
            user.set_password("ValidPass123")

    def test_validate_email_success(self):
        try:
            user = User(username="testuser", email="valid@example.com")
            db.session.add(user) # Temporarily add to session to trigger validation if it's on assignment
                                 # and not only on flush/commit, or if @validates needs it.
                                 # For @validates, direct assignment is usually enough.
            self.assertEqual(user.email, "valid@example.com")
        except ValueError:
            self.fail("User email validation failed unexpectedly for a valid email.")

    def test_validate_email_invalid_no_at(self):
        with self.assertRaisesRegex(ValueError, "Invalid email address"):
            User(username="testuser", email="invalidexample.com")

    def test_validate_email_invalid_no_domain(self):
        with self.assertRaisesRegex(ValueError, "Invalid email address"):
            User(username="testuser", email="invalid@")

    def test_validate_email_invalid_no_user(self):
        with self.assertRaisesRegex(ValueError, "Invalid email address"):
            User(username="testuser", email="@example.com")

    def test_check_password_correct(self):
        user = User(username="testuser", email="test@example.com")
        user.set_password("ValidPass123!")
        self.assertTrue(user.check_password("ValidPass123!"))

    def test_check_password_incorrect(self):
        user = User(username="testuser", email="test@example.com")
        user.set_password("ValidPass123!")
        self.assertFalse(user.check_password("WrongPass123!"))

    # --- Password Reset Token Tests ---
    def test_get_password_reset_token(self):
        user = User(username="tokenuser", email="token@example.com")
        user.set_password("Password123!") # Needs to be a valid password
        db.session.add(user)
        db.session.commit() # User needs to be in DB for some ORM operations if not already

        token = user.get_reset_token()
        self.assertIsNotNone(user.reset_token)
        self.assertIsInstance(user.reset_token, str)
        self.assertEqual(user.reset_token, token)

        self.assertIsNotNone(user.reset_token_expires)
        self.assertIsInstance(user.reset_token_expires, datetime)

        # Check expiry time is roughly correct (e.g., default 1800 seconds)
        # It should be greater than now + 1700 and less than now + 1900
        # Allow a small buffer for execution time.
        expected_expiry_min = datetime.utcnow() + timedelta(seconds=1800 - 60) # 1 min buffer
        expected_expiry_max = datetime.utcnow() + timedelta(seconds=1800 + 60) # 1 min buffer
        self.assertTrue(expected_expiry_min < user.reset_token_expires < expected_expiry_max)

    def test_verify_password_reset_token_valid(self):
        user = User(username="verifyuser", email="verify@example.com")
        user.set_password("Password123!")
        db.session.add(user)
        db.session.commit() # User must be in DB for token generation and commit

        token = user.get_reset_token()
        db.session.commit() # Commit token and expiry to DB

        verified_user = User.verify_reset_token(token)
        self.assertIsNotNone(verified_user)
        self.assertEqual(verified_user.id, user.id)

    def test_verify_password_reset_token_expired(self):
        user = User(username="expireduser", email="expired@example.com")
        user.set_password("Password123!")
        db.session.add(user)
        db.session.commit()

        token = user.get_reset_token()
        # Manually set token expiry to the past
        user.reset_token_expires = datetime.utcnow() - timedelta(seconds=3600) # Expired 1 hour ago
        db.session.commit()

        verified_user = User.verify_reset_token(token)
        self.assertIsNone(verified_user)

    def test_verify_password_reset_token_invalid(self):
        # No user setup needed, just verifying an invalid token string
        verified_user = User.verify_reset_token("completelyinvalidtokenstring")
        self.assertIsNone(verified_user)

        # Test with a token from a user that was never saved (or token cleared)
        user_not_saved_token = User(username="notsaved", email="notsaved@example.com")
        user_not_saved_token.set_password("Password123!")
        # db.session.add(user_not_saved_token) # Not adding or committing
        token_never_in_db = user_not_saved_token.get_reset_token()
        # (token is on instance but not in DB)

        verified_user_for_unsaved_token = User.verify_reset_token(token_never_in_db)
        self.assertIsNone(verified_user_for_unsaved_token)


if __name__ == "__main__":
    unittest.main()
