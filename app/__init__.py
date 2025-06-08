import os
from flask import Flask, render_template # render_template for error handlers
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, current_user # current_user for nav_links
from flask_wtf.csrf import CSRFProtect

# Globally accessible extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
csrf = CSRFProtect()

# Login manager configuration
login_manager.login_view = 'auth.login' # Blueprint.route_function_name
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
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(app.instance_path, 'ohms.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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

    # Set template and static folder relative to the 'app' package directory
    # Flask default is 'templates' and 'static' at the same level as where Flask() is called.
    # Since Flask(__name__) is used and __name__ is 'app', it looks for app/templates and app/static by default.
    # Explicitly setting can be done if needed:
    # app.template_folder = 'templates'
    # app.static_folder = 'static'

    # User loader function for Flask-Login
    # Must import User model here to avoid circular imports if models.py imports 'db' from 'app'
    from app.models import User
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
                ('Logout', 'auth.logout')
            ])
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
    app.register_blueprint(main_bp) # No prefix for main, usually

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
    with app.app_context():
        db.create_all()
        # You might want to remove this for production or guard it
        # e.g. if app.config.get('ENV') == 'development': db.create_all()

    return app
