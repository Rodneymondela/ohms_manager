from flask import current_app
from . import bp
from ...extensions import cache, limiter

@bp.get("/")
@cache.cached(timeout=30)
def index():
    return {"app": current_app.name, "message": "OHMS Manager API"}, 200

@bp.get("/ping")
@limiter.limit("20/minute")
def ping():
    return {"pong": True}, 200
