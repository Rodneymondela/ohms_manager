import os
from flask import Flask, jsonify, send_from_directory, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_wtf import CSRFProtect
from flask_cors import CORS
from sqlalchemy import text


def _migrate_field_sheet(db):
    """Add new columns to existing tables if they don't already exist."""
    migrations = [
        ('field_sheet', 'activity_area',    'VARCHAR(120)'),
        ('field_sheet', 'occupation_group', 'VARCHAR(120)'),
        ('field_sheet', 'result_mn_twa',    'FLOAT'),
        ('field_sheet', 'result_si_twa',    'FLOAT'),
        ('field_sheet', 'result_pnoc_twa',  'FLOAT'),
        ('lab_result',  'shift_duration',    'FLOAT'),
        ('lab_result',  'sampling_duration', 'INTEGER'),
    ]
    for table, col, col_type in migrations:
        try:
            db.session.execute(
                text(f'ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {col_type}')
            )
            db.session.commit()
        except Exception:
            db.session.rollback()

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
csrf = CSRFProtect()


def create_app():
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
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
    from app.models import Operation, User  # noqa
    from app.schedules.models import ExposureReading, EmployeeExposure, MedicalRecord, FieldSheet, LabResult  # noqa
    from app.employees.models import Employee  # noqa

    with app.app_context():
        db.create_all()
        _migrate_field_sheet(db)

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_react(path):
        file_path = os.path.join(static_dir, path)
        if path and os.path.isfile(file_path):
            return send_from_directory(static_dir, path)
        resp = make_response(send_from_directory(static_dir, 'index.html'))
        resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        resp.headers['Pragma'] = 'no-cache'
        resp.headers['Expires'] = '0'
        return resp

    return app
