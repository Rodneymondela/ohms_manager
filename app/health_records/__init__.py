from flask import Blueprint

health_records_bp = Blueprint('health_records', __name__)

from . import routes # Import routes after blueprint definition to avoid circular dependency.
