from flask import Blueprint

api_bp = Blueprint('api', __name__, url_prefix='/api')

# OPTIONAL: Add a basic test route
@api_bp.route('/test')
def test():
    return {'message': 'API is working'}
