from flask import Blueprint

auth_bp = Blueprint('auth', __name__)

from . import routes # Import routes after blueprint definition to avoid circular dependency.
