from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt
from sqlalchemy import Index
from sqlalchemy.orm import validates, relationship
import re

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    __table_args__ = (
        Index('idx_users_username', 'username'),
        Index('idx_users_email', 'email'),
    )

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    role = db.Column(db.String(50), nullable=False, default='user')
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    reset_token = db.Column(db.String(100), unique=True, nullable=True)
    reset_token_expires = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not re.search(r"[0-9]", password):
            raise ValueError("Password must contain at least one number.")
        if not re.search(r"[A-Z]", password):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", password):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"[!@#$%^&*()-_=+[]{};:'\",.<>/?]", password):
            raise ValueError("Password must contain at least one special character (e.g., !@#$%^&*).")

        # All checks passed, hash the password
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    @validates('email')
    def validate_email(self, key, email):
        if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise ValueError("Invalid email address")
        return email

    def __repr__(self):
        return f'<User {self.username}>'

class Employee(db.Model):
    __tablename__ = 'employees'
    __table_args__ = (
        Index('idx_employees_name', 'name'),
        Index('idx_employees_department', 'department'),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    job_title = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    hire_date = db.Column(db.Date)
    date_of_birth = db.Column(db.Date)
    contact_number = db.Column(db.String(20))
    emergency_contact = db.Column(db.String(100))
    emergency_phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    exposures = relationship('Exposure', backref='employee', lazy=True, cascade='all, delete-orphan')
    health_records = relationship('HealthRecord', backref='employee', lazy=True, cascade='all, delete-orphan')

    @validates('contact_number', 'emergency_phone')
    def validate_phone(self, key, phone):
        if phone and not re.match(r'^[\d\s\-+()]{7,20}$', phone):
            raise ValueError("Invalid phone number format")
        return phone

    def __repr__(self):
        return f'<Employee {self.name}>'

class Hazard(db.Model):
    __tablename__ = 'hazards'
    __table_args__ = (
        Index('idx_hazards_name', 'name'),
        Index('idx_hazards_category', 'category'),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    exposure_limit = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text)
    safety_measures = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    exposures = relationship('Exposure', backref='hazard', lazy=True, cascade='all, delete-orphan')

    @validates('exposure_limit')
    def validate_exposure_limit(self, key, limit):
        if limit <= 0:
            raise ValueError("Exposure limit must be positive")
        return limit

    def __repr__(self):
        return f'<Hazard {self.name}>'

class Exposure(db.Model):
    __tablename__ = 'exposures'
    __table_args__ = (
        Index('idx_exposures_employee', 'employee_id'),
        Index('idx_exposures_hazard', 'hazard_id'),
        Index('idx_exposures_date', 'date'),
    )

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    hazard_id = db.Column(db.Integer, db.ForeignKey('hazards.id', ondelete='CASCADE'), nullable=False)
    exposure_level = db.Column(db.Float, nullable=False)
    duration = db.Column(db.Float)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    location = db.Column(db.String(100))
    notes = db.Column(db.Text)
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    employee = relationship('Employee', backref=db.backref('exposures', lazy=True))
    hazard = relationship('Hazard', backref=db.backref('exposures', lazy=True))
    recorder = relationship('User', foreign_keys=[recorded_by])

    @validates('exposure_level')
    def validate_exposure_level(self, key, level):
        if level <= 0:
            raise ValueError("Exposure level must be positive")
        return level

    def __repr__(self):
        return f'<Exposure {self.id}>'

class HealthRecord(db.Model):
    __tablename__ = 'health_records'
    __table_args__ = (
        Index('idx_health_records_employee', 'employee_id'),
        Index('idx_health_records_test_type', 'test_type'),
        Index('idx_health_records_date', 'date'),
    )

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    test_type = db.Column(db.String(100), nullable=False)
    result = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    next_test_date = db.Column(db.Date)
    physician = db.Column(db.String(100))
    facility = db.Column(db.String(100))
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    employee = relationship('Employee', backref=db.backref('health_records', lazy=True))
    recorder = relationship('User', foreign_keys=[recorded_by])

    def __repr__(self):
        return f'<HealthRecord {self.id}>'
