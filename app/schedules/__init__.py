from flask import Blueprint

schedules_bp = Blueprint('schedules_bp', __name__,
                        template_folder='templates',
                        static_folder='static', static_url_path='/schedules/static')

# Import routes after blueprint definition to avoid circular imports
from . import routes
