from flask import Blueprint
from flask_restx import Api

# API Blueprint
# The url_prefix for the blueprint itself. All Api resources will be under this.
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# Flask-RESTX API object
# We pass the blueprint to the Api constructor.
# All resources/namespaces added to this 'api_restx' object will be further prefixed by api_bp's url_prefix.
api_restx = Api(api_bp,
                version='1.0',
                title='OHMS API',
                description='Occupational Health Monitoring System API',
                doc='/doc/',  # Mount Swagger UI at /api/v1/doc/
                authorizations=None, # Can add auth definitions here later
                security=None)      # Can add global security requirements here later

# Example of how namespaces would be added (for future steps):
# from .some_resource import ns as some_resource_ns
# api_restx.add_namespace(some_resource_ns)

# Import modules that define namespaces and resources.
# This will register the namespaces and resources with the api_restx object.
from . import employees_resources
# from . import hazards_resources # Example for future
# from . import exposures_resources # Example for future
# from . import health_records_resources # Example for future
