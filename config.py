import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-change-me'

    # Heroku sets DATABASE_URL with postgres:// scheme; SQLAlchemy needs postgresql://
    _db_url = os.environ.get('DATABASE_URL') or \
              'sqlite:///' + os.path.join(os.path.dirname(__file__), 'instance', 'ohms.db')
    if _db_url.startswith('postgres://'):
        _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = _db_url

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REMEMBER_COOKIE_DURATION = timedelta(days=30)

    SENDGRID_API_KEY    = os.environ.get('SENDGRID_API_KEY', '')
    SENDGRID_FROM_EMAIL = os.environ.get('SENDGRID_FROM_EMAIL', 'noreply@rodmon.co.za')
    APP_URL             = os.environ.get('APP_URL', 'http://localhost:5173')

