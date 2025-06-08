import unittest
from app import db  # db instance from your main app (SQLAlchemy())
from app.models import User # User model from app package
from tests.test_config import BasicTests # Base test class

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

if __name__ == "__main__":
    unittest.main()
