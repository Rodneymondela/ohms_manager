from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key' # Change this!
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sampling.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

from app import models # Import models
from app import routes # Import routes AFTER app and db are defined
