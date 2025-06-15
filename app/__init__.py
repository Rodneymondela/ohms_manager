from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key' # Change this!
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sampling.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Import models here - ensure they are defined before blueprints if blueprints use them directly at import time
# Or ensure models are imported within blueprint files where needed.
from app import models # This ensures models are registered with db before create_all or migrations

# Import and register Blueprints
from app.schedules import schedules_bp
app.register_blueprint(schedules_bp, url_prefix='/schedules')

# Define a simple root route if not already handled by a blueprint at '/'
@app.route('/')
def root_redirect():
    from flask import redirect, url_for
    return redirect(url_for('schedules_bp.index')) # Redirect to the main page of the schedules blueprint
