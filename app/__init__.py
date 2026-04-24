import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_wtf import CSRFProtect
from flask_cors import CORS

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)

    from config import Config
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)

    # Return JSON 401 instead of redirecting to HTML login page
    @login_manager.unauthorized_handler
    def unauthorized():
        return jsonify({'error': 'Authentication required'}), 401

    # Allow the React frontend (dev + production) to reach the API with session cookies
    allowed = [
        'http://localhost:5173', 'http://localhost:5174',
        'http://localhost:5175', 'http://localhost:5176',
        'http://127.0.0.1:5000',
    ]
    heroku_url = os.environ.get('HEROKU_APP_URL')
    if heroku_url:
        allowed.append(heroku_url)
    CORS(app, resources={r'/api/*': {'origins': allowed}}, supports_credentials=True)

    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'warning'

    # Register blueprints
    from app.auth.routes import auth
    from app.main.routes import main
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(main)

    from app.schedules.routes import schedules_bp
    app.register_blueprint(schedules_bp, url_prefix='/schedules')

    from app.employees.routes import employees_bp
    app.register_blueprint(employees_bp, url_prefix='/employees')

    from app.api import api_bp
    # Exempt the JSON API from CSRF (it uses CORS + JSON Content-Type instead)
    csrf.exempt(api_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    # Import all models so db.create_all() picks up new tables
    from app.schedules.models import ExposureReading, EmployeeExposure, MedicalRecord, FieldSheet  # noqa
    from app.employees.models import Employee  # noqa

    with app.app_context():
        db.create_all()

    return app
