import unittest
from app import create_app, db # Import create_app and the globally defined db instance

class BasicTests(unittest.TestCase):

    def setUp(self):
        self.app = create_app() # Create app instance using the factory

        # Configure the app for testing AFTER it's created by the factory
        # The factory might set defaults, these are test-specific overrides.
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['SECRET_KEY'] = 'test_secret_key_for_testing'
        self.app.config['SERVER_NAME'] = 'localhost.localdomain' # Added for url_for
        self.app.config['APPLICATION_ROOT'] = '/' # Often needed with SERVER_NAME
        self.app.config['PREFERRED_URL_SCHEME'] = 'http' # Often needed with SERVER_NAME
        # LOGIN_DISABLED can be useful if you want to bypass login for certain tests,
        # but generally, it's better to test the login flow.
        # self.app.config['LOGIN_DISABLED'] = True

        # self.client is the test client to make requests
        self.client = self.app.test_client()

        # Push an application context. This is crucial for db operations
        # and anything else that depends on the current application context.
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Create all database tables. db.create_all() needs an app context.
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

if __name__ == "__main__":
    unittest.main()
