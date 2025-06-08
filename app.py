from flask import Flask, render_template
from models import db, User, Employee, Hazard, Exposure, HealthRecord
import os

app = Flask(__name__)

# Secret Key Configuration
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Replace with a strong, random key in production

# Database Configuration
instance_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance')
db_path = os.path.join(instance_path, 'ohms.db')

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

if not os.path.exists(instance_path):
    os.makedirs(instance_path)

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

# Error Handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)
