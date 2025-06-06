import unittest
from datetime import date, timedelta
from models import User, Employee, Hazard, Exposure, db # Assuming models.py is in the same directory or accessible
from flask import Flask

# Flask app setup for testing
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

class BaseTestCase(unittest.TestCase):
    def setUp(self):
        # Establish an application context before running the tests.
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

class TestUserModel(BaseTestCase):
    def test_set_password_valid(self):
        user = User(username="testuser")
        user.set_password("ValidPass123")
        self.assertIsNotNone(user.password_hash)

    def test_set_password_too_short(self):
        user = User(username="testuser")
        with self.assertRaisesRegex(ValueError, "Password must be at least 8 characters long"):
            user.set_password("Short1")

    def test_set_password_no_number(self):
        user = User(username="testuser")
        with self.assertRaisesRegex(ValueError, "Password must contain at least one number"):
            user.set_password("NoNumberPass")

    def test_set_password_no_uppercase(self):
        user = User(username="testuser")
        with self.assertRaisesRegex(ValueError, "Password must contain at least one uppercase letter"):
            user.set_password("nouppercase1")

    def test_set_password_no_lowercase(self):
        user = User(username="testuser")
        with self.assertRaisesRegex(ValueError, "Password must contain at least one lowercase letter"):
            user.set_password("NOLOWERCASE1")

    def test_validate_email_valid(self):
        user = User(username="testuser", email="test@example.com")
        user.set_password("ValidPass123") # Add this line
        db.session.add(user)
        db.session.commit() # Commit to trigger validation
        self.assertEqual(user.email, "test@example.com")

    def test_validate_email_invalid(self):
        with self.assertRaisesRegex(ValueError, "Invalid email address"):
            User(username="testuser", email="invalid-email")
            # Validation can be triggered on construction or explicitly by ORM events
            # For this setup, direct instantiation might not trigger @validates if not committed
            # So, we might need to commit or call validate explicitly if User constructor doesn't.
            # However, SQLAlchemy often calls validators before commit during attribute assignment.
            # Let's assume direct assignment triggers it for now. If not, adjust test.


class TestEmployeeModel(BaseTestCase):
    def test_validate_phone_valid(self):
        employee = Employee(name="John Doe", job_title="Engineer", department="Tech", contact_number="123-456-7890")
        db.session.add(employee)
        db.session.commit()
        self.assertEqual(employee.contact_number, "123-456-7890")

    def test_validate_phone_invalid(self):
        with self.assertRaisesRegex(ValueError, "Invalid phone number format"):
            Employee(name="Jane Doe", job_title="Analyst", department="HR", contact_number="123")

    def test_validate_date_of_birth_valid(self):
        valid_dob = date.today() - timedelta(days=20*365) # 20 years old
        employee = Employee(name="Old Enough", job_title="Worker", department="Any", date_of_birth=valid_dob)
        db.session.add(employee)
        db.session.commit()
        self.assertEqual(employee.date_of_birth, valid_dob)

    def test_validate_date_of_birth_future(self):
        future_dob = date.today() + timedelta(days=10)
        with self.assertRaisesRegex(ValueError, "Date of birth cannot be in the future."):
            Employee(name="Future Kid", job_title="Intern", department="Future", date_of_birth=future_dob)
            # db.session.add(e) # Add and commit if validation is only on flush
            # db.session.commit()

    def test_validate_date_of_birth_underage(self):
        underage_dob = date.today() - timedelta(days=17*365) # 17 years old
        with self.assertRaisesRegex(ValueError, "Employee must be at least 18 years old."):
            Employee(name="Too Young", job_title="Intern", department="Youth", date_of_birth=underage_dob)

    def test_validate_hire_date_valid(self):
        valid_hire_date = date.today() - timedelta(days=100)
        employee = Employee(name="Current Employee", job_title="Staff", department="Ops", hire_date=valid_hire_date)
        db.session.add(employee)
        db.session.commit()
        self.assertEqual(employee.hire_date, valid_hire_date)

    def test_validate_hire_date_future(self):
        future_hire_date = date.today() + timedelta(days=1)
        with self.assertRaisesRegex(ValueError, "Hire date cannot be in the future."):
            Employee(name="Future Hire", job_title="Trainee", department="Planning", hire_date=future_hire_date)


class TestHazardModel(BaseTestCase):
    def test_validate_exposure_limit_valid(self):
        hazard = Hazard(name="Noise", category="Physical", exposure_limit=85.5)
        db.session.add(hazard)
        db.session.commit()
        self.assertEqual(hazard.exposure_limit, 85.5)

    def test_validate_exposure_limit_zero(self):
        with self.assertRaisesRegex(ValueError, "Exposure limit must be positive"):
            Hazard(name="Dust", category="Chemical", exposure_limit=0)

    def test_validate_exposure_limit_negative(self):
        with self.assertRaisesRegex(ValueError, "Exposure limit must be positive"):
            Hazard(name="Vibration", category="Physical", exposure_limit=-10)


class TestExposureModel(BaseTestCase):
    def setUp(self):
        super().setUp()
        # Need a user and hazard for foreign key constraints
        self.user = User(username="testrecorder")
        self.user.set_password("TestPass123")
        self.employee = Employee(name="Test Employee", job_title="Tester", department="QA", date_of_birth=date(1990,1,1), hire_date=date(2020,1,1))
        self.hazard = Hazard(name="Test Hazard", category="Test", exposure_limit=10.0)
        db.session.add_all([self.user, self.employee, self.hazard])
        db.session.commit()


    def test_validate_exposure_level_valid(self):
        exposure = Exposure(employee_id=self.employee.id, hazard_id=self.hazard.id, exposure_level=5.0, recorded_by=self.user.id)
        db.session.add(exposure)
        db.session.commit()
        self.assertEqual(exposure.exposure_level, 5.0)

    def test_validate_exposure_level_zero(self):
        with self.assertRaisesRegex(ValueError, "Exposure level must be positive"):
            Exposure(employee_id=self.employee.id, hazard_id=self.hazard.id, exposure_level=0, recorded_by=self.user.id)

    def test_validate_exposure_level_negative(self):
        with self.assertRaisesRegex(ValueError, "Exposure level must be positive"):
            Exposure(employee_id=self.employee.id, hazard_id=self.hazard.id, exposure_level=-5.0, recorded_by=self.user.id)


if __name__ == '__main__':
    # No need to create_all here if BaseTestCase handles it per test run
    # However, if some setup outside test classes is needed, it could go here.
    # For a clean test environment, it's usually best handled in setUp/tearDown.
    # The original instruction had db.create_all() here, which might be for a global setup.
    # Let's keep it if it serves a purpose for the test runner not managed by unittest.
    with app.app_context():
        db.create_all() # This ensures tables are there if tests are run directly and not via a test runner that calls setUpClass
    unittest.main()
