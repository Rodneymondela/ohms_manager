from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt
from sqlalchemy import event
from sqlalchemy.orm import validates

# Initialize extensions
db = SQLAlchemy()
bcrypt = Bcrypt()

# User model with enhanced security
class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    role = db.Column(db.String(50), nullable=False, default='user')
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Password reset fields
    reset_token = db.Column(db.String(100), unique=True, nullable=True)
    reset_token_expires = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        """Hash and set the user's password"""
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """Verify the password against the stored hash"""
        return bcrypt.check_password_hash(self.password_hash, password)

    @validates('email')
    def validate_email(self, key, email):
        """Basic email validation"""
        if email and '@' not in email:
            raise ValueError("Invalid email address")
        return email

    def __repr__(self):
        return f'<User {self.username}>'

# Employee model with enhanced fields
class Employee(db.Model):
    __tablename__ = 'employees'

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

    # Relationships
    exposures = db.relationship('Exposure', backref='employee', lazy=True, cascade='all, delete-orphan')
    health_records = db.relationship('HealthRecord', backref='employee', lazy=True, cascade='all, delete-orphan')

    @validates('contact_number', 'emergency_phone')
    def validate_phone(self, key, phone):
        """Basic phone number validation"""
        if phone and not phone.replace('-', '').replace(' ', '').isdigit():
            raise ValueError("Invalid phone number format")
        return phone

    def __repr__(self):
        return f'<Employee {self.name}>'

# Hazard model with safety standards
class Hazard(db.Model):
    __tablename__ = 'hazards'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    category = db.Column(db.String(50), nullable=False)  # Chemical, Physical, Biological, Ergonomic
    exposure_limit = db.Column(db.Float, nullable=False)  # e.g., 85 dB(A)
    unit = db.Column(db.String(20), default='dB(A)')  # Unit of measurement
    description = db.Column(db.Text)
    safety_measures = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    exposures = db.relationship('Exposure', backref='hazard', lazy=True, cascade='all, delete-orphan')

    @validates('exposure_limit')
    def validate_exposure_limit(self, key, limit):
        """Validate exposure limit is positive"""
        if limit <= 0:
            raise ValueError("Exposure limit must be positive")
        return limit

    def __repr__(self):
        return f'<Hazard {self.name}>'

# Exposure model with enhanced tracking
class Exposure(db.Model):
    __tablename__ = 'exposures'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    hazard_id = db.Column(db.Integer, db.ForeignKey('hazards.id', ondelete='CASCADE'), nullable=False)
    exposure_level = db.Column(db.Float, nullable=False)
    duration = db.Column(db.Float)  # Duration in hours
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    location = db.Column(db.String(100))
    notes = db.Column(db.Text)
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to User who recorded the exposure
    recorder = db.relationship('User', foreign_keys=[recorded_by])

    @validates('exposure_level')
    def validate_exposure_level(self, key, level):
        """Validate exposure level is positive"""
        if level <= 0:
            raise ValueError("Exposure level must be positive")
        return level

    def __repr__(self):
        return f'<Exposure {self.id} - Employee {self.employee_id}>'

# Health record model with comprehensive tracking
class HealthRecord(db.Model):
    __tablename__ = 'health_records'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    test_type = db.Column(db.String(100), nullable=False)  # e.g., Audiometry, Spirometry
    result = db.Column(db.String(100), nullable=False)  # e.g., "Normal", "Hearing Loss"
    details = db.Column(db.Text)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    next_test_date = db.Column(db.Date)
    physician = db.Column(db.String(100))
    facility = db.Column(db.String(100))
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to User who recorded the health record
    recorder = db.relationship('User', foreign_keys=[recorded_by])

    def __repr__(self):
        return f'<HealthRecord {self.id} - {self.test_type}>'

# Add indexes for better performance
event.listen(User.__table__, 'after_create', 
            db.DDL('CREATE INDEX idx_users_username ON users (username)'))
event.listen(Employee.__table__, 'after_create', 
            db.DDL('CREATE INDEX idx_employees_name ON employees (name)'))
event.listen(Hazard.__table__, 'after_create', 
            db.DDL('CREATE INDEX idx_hazards_name ON hazards (name)'))
