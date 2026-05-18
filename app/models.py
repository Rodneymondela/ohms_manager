from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

ROLES = ('super_admin', 'admin', 'manager', 'viewer')


class Operation(db.Model):
    __tablename__ = 'operation'

    id             = db.Column(db.Integer, primary_key=True)
    operation_name = db.Column(db.String(120), nullable=False)
    code           = db.Column(db.String(20),  unique=True, nullable=False)
    location       = db.Column(db.String(120), nullable=True)
    status         = db.Column(db.String(20),  nullable=False, default='active')
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at     = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    users = db.relationship('User', backref='operation', lazy=True)

    def to_dict(self):
        return {
            'id':             self.id,
            'operation_name': self.operation_name,
            'code':           self.code,
            'location':       self.location or '',
            'status':         self.status,
            'created_at':     self.created_at.isoformat() if self.created_at else None,
            'updated_at':     self.updated_at.isoformat() if self.updated_at else None,
        }


class User(UserMixin, db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(64), unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin      = db.Column(db.Boolean, default=False)
    role          = db.Column(db.String(20), nullable=False, default='viewer')
    operation_id  = db.Column(db.Integer, db.ForeignKey('operation.id'), nullable=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def is_super_admin(self):
        return self.role == 'super_admin'

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
