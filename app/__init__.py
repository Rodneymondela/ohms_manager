import os
from flask import Flask, render_template # render_template for error handlers
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, current_user # current_user for nav_links
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from flask_mail import Mail
import logging # Added logging
from logging.handlers import RotatingFileHandler # Added RotatingFileHandler

# Globally accessible extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate()
mail = Mail() # Added Mail instance

# Login manager configuration
# Problem statement indicates Flask-Login redirects to /login instead of /auth/login.
# Setting login_view to the literal path /auth/login to bypass url_for resolution issues by Flask-Login.
login_manager.login_view = '/auth/login'
login_manager.login_message_category = 'info'
login_manager.login_message = "Please log in to access this page."


def create_app(config_class=None):
    """
    Application factory function.
    """
    app = Flask(__name__, instance_relative_config=True) # instance_relative_config=True allows instance folder configs

    # Configuration
    # In a real app, this would likely come from a config object/file
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'your_default_secret_key_here_app_factory')
    # Construct path relative to the instance folder, which is one level up from 'app' directory where __init__.py is
    # app.instance_path is typically <project_root>/instance
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = database_url or \
        'sqlite:///' + os.path.join(app.instance_path, 'ohms.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Mail configuration
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.googlemail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', '587'))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'false').lower() in ['true', 'on', '1']
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', app.config['MAIL_USERNAME'])

    # For robust URL generation, especially in redirects by extensions
    app.config['SERVER_NAME'] = os.environ.get('FLASK_SERVER_NAME', None)
    if app.config['SERVER_NAME']: # Only set these if SERVER_NAME is actually set
        app.config['APPLICATION_ROOT'] = os.environ.get('FLASK_APPLICATION_ROOT', '/')
        app.config['PREFERRED_URL_SCHEME'] = os.environ.get('FLASK_PREFERRED_URL_SCHEME', 'http')


    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass # Already exists or can't be created, Flask will handle it

    # Initialize extensions with the app
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app) # Initialize Flask-Mail

    # Set template and static folder relative to the 'app' package directory
    # Flask default is 'templates' and 'static' at the same level as where Flask() is called.
    # Since Flask(__name__) is used and __name__ is 'app', it looks for app/templates and app/static by default.
    # Explicitly setting can be done if needed:
    # app.template_folder = 'templates'
    # app.static_folder = 'static'

    # User loader function for Flask-Login
    # Must import User model here to avoid circular imports if models.py imports 'db' from 'app'
    from app.models import User, ROLE_ADMIN # Import ROLE_ADMIN for nav_links
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Context processor for navigation links
    @app.context_processor
    def inject_nav_links():
        nav_links = []
        if current_user.is_authenticated:
            nav_links.extend([
                ('Home', 'main.index'),
                ('Employees', 'employees.list_employees'),
                ('Hazards', 'hazards.list_hazards'),
                ('Exposures', 'exposures.list_exposures'),
                ('Health Records', 'health_records.list_health_records'),
            ])
            if current_user.role == ROLE_ADMIN:
                nav_links.append(('User Management', 'admin.list_users')) # Admin specific link
            nav_links.append(('Logout', 'auth.logout')) # Logout always last for authenticated
        else:
            nav_links.extend([
                ('Login', 'auth.login'),
                ('Register', 'auth.register')
            ])
        return dict(nav_links=nav_links)

    # Register blueprints
    from app.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.employees import employees_bp
    app.register_blueprint(employees_bp, url_prefix='/employees')

    from app.hazards import hazards_bp
    app.register_blueprint(hazards_bp, url_prefix='/hazards')

    from app.exposures import exposures_bp
    app.register_blueprint(exposures_bp, url_prefix='/exposures')

    from app.health_records import health_records_bp
    app.register_blueprint(health_records_bp, url_prefix='/health_records')

    # Main blueprint (for index, etc.) - to be created next
    from app.main import main_bp
    app.register_blueprint(main_bp)

    from app.admin import admin_bp
    app.register_blueprint(admin_bp)

    from app.api import api_bp as api_v1_bp # Import and register API blueprint
    app.register_blueprint(api_v1_bp) # url_prefix is defined in api_bp creation

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback() # Good practice for 500 errors with DB
        return render_template('500.html'), 500

    # Create database tables if they don't exist (for development)
    # In production, use Flask-Migrate
    # For initial migration generation, it's often best to have this commented out
    # to ensure Alembic sees the "empty" state as the starting point.
    # with app.app_context():
    #     db.create_all()
        # You might want to remove this for production or guard it
        # e.g. if app.config.get('ENV') == 'development': db.create_all()

    # Logging Configuration
    if not app.debug and not app.testing:
        # Ensure instance path exists for log file (though it should from above)
        if not os.path.exists(app.instance_path):
            try:
                os.makedirs(app.instance_path)
            except OSError:
                pass # Should not happen if above check passed or instance_relative_config worked

        log_file_path = os.path.join(app.instance_path, 'ohms_app.log')
        file_handler = RotatingFileHandler(log_file_path, maxBytes=102400, backupCount=10)

        log_formatter = logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )
        file_handler.setFormatter(log_formatter)

        file_handler.setLevel(logging.INFO) # Set level for the file handler

        # Remove any default handlers Flask might have added
        # Be cautious if other extensions add handlers to app.logger
        for handler in list(app.logger.handlers): # Iterate over a copy
            app.logger.removeHandler(handler)

        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO) # Set overall level for the app's logger

        app.logger.info('OHMS Application file logging configured.') # More specific message

    # This message will log regardless of debug/testing mode, if logger level permits
    app.logger.info('OHMS Application initialized and configured.')

    return app
