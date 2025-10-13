from flask import Flask
from .config import config_by_name
from .extensions import db, migrate, login_manager, cache, limiter

def register_extensions(app: Flask) -> None:
    for ext in (db, migrate, login_manager, cache, limiter):
        ext.init_app(app)

def register_blueprints(app: Flask) -> None:
    from .blueprints.core import bp as core_bp
    app.register_blueprint(core_bp)

def create_app(config_name: str | None = None) -> Flask:
    """Application factory pattern.

    Usage:

        export FLASK_ENV=development

        flask run

    """
    config_name = config_name or "development"
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    register_extensions(app)
    register_blueprints(app)

    @app.route("/health")
    def health():
        return {"status": "ok"}, 200

    return app
