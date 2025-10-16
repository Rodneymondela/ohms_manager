from flask import current_app
from . import bp
from ...extensions import cache, limiter

@bp.get("/")
@cache.cached(timeout=30)
def index():
    cfg = current_app.config
    return {
        "app": cfg["APP_NAME"],
        "message": "OHMS Manager API",
        "version": cfg.get("APP_VERSION", "unknown"),
        "env": cfg.get("ENV_NAME", "development"),
    }, 200
