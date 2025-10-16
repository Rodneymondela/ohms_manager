# app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_bcrypt import Bcrypt         # NEW
from flask_mail import Mail             # NEW

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
cache = Cache()
limiter = Limiter(key_func=get_remote_address, default_limits=[])

bcrypt = Bcrypt()   # NEW
mail = Mail()       # NEW
