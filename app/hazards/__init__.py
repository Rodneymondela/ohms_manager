from flask import Blueprint

hazards_bp = Blueprint('hazards', __name__)

from . import routes # Import routes after blueprint definition to avoid circular dependency.
