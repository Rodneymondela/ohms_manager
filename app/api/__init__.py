from flask import Blueprint

api_bp = Blueprint('api', __name__)

from app.api import routes        # noqa: E402, F401
from app.api import auth          # noqa: E402, F401
from app.api import field_sheets  # noqa: E402, F401
from app.api import operations    # noqa: E402, F401
from app.api import lab_results   # noqa: E402, F401
