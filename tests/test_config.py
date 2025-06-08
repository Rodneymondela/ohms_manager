import unittest
from app import app, db, bcrypt, login_manager # Import necessary components from your app

class BasicTests(unittest.TestCase):

    def setUp(self):
        # Configure the app for testing
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for tests
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' # Use in-memory DB
        app.config['SECRET_KEY'] = 'test_secret_key'
        app.config['LOGIN_DISABLED'] = True # Optional: disable login for routes not being tested for auth

        # Create a test client
        self.app = app.test_client()

        # Push an application context
        self.app_context = app.app_context()
        self.app_context.push()

        # Initialize extensions with the app instance if not already done globally in a way that adapts
        # For tests, it's often good to ensure they are bound to the test app instance
        # However, if your app.py initializes them with 'app', this might be redundant
        # or require careful handling if 'app' is imported directly.
        # Let's assume app.py's 'app' object is what we're configuring.

        db.init_app(app) # Ensure db is initialized with the potentially reconfigured app
        bcrypt.init_app(app)
        login_manager.init_app(app)

        # Create all database tables
        db.create_all()

    def tearDown(self):
        # Remove the session and drop all tables
        db.session.remove()
        db.drop_all()

        # Pop the application context
        self.app_context.pop()

if __name__ == "__main__":
    unittest.main()
