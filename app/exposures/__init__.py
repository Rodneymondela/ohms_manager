from flask import Blueprint

exposures_bp = Blueprint('exposures', __name__)

from . import routes # Import routes after blueprint definition to avoid circular dependency.
