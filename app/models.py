# app/models.py (ensure this is the full file content with additions)
from datetime import datetime, timedelta
import secrets
from flask_login import UserMixin
from sqlalchemy import Index
from sqlalchemy.orm import validates, relationship # Ensure relationship is imported
import re
from app import db, bcrypt

# Role constants
ROLE_USER = 'user'
ROLE_ADMIN = 'admin'

# HEG Risk Levels
RISK_LEVEL_LOW = 'Low'
RISK_LEVEL_MODERATE = 'Moderate'
RISK_LEVEL_HIGH = 'High'
HEG_RISK_LEVELS = [RISK_LEVEL_LOW, RISK_LEVEL_MODERATE, RISK_LEVEL_HIGH]

# Sampling Frequencies
FREQUENCY_MONTHLY = 'Monthly'
FREQUENCY_QUARTERLY = 'Quarterly'
FREQUENCY_ANNUALLY = 'Annually'
SAMPLING_FREQUENCIES = [FREQUENCY_MONTHLY, FREQUENCY_QUARTERLY, FREQUENCY_ANNUALLY]

class User(db.Model, UserMixin):
    # ... (existing User model code) ...
    __tablename__ = 'users'
    __table_args__ = (
        Index('idx_users_username', 'username'),
        Index('idx_users_email', 'email'),
    )

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    role = db.Column(db.String(50), nullable=False, default=ROLE_USER)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    reset_token = db.Column(db.String(100), unique=True, nullable=True)
    reset_token_expires = db.Column(db.DateTime, nullable=True)

    # Ensure all User methods (set_password, check_password, validate_email, get_reset_token, verify_reset_token, __repr__) are here

    def set_password(self, password):
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not re.search(r"[0-9]", password):
            raise ValueError("Password must contain at least one number.")
        if not re.search(r"[A-Z]", password):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", password):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r'[!@#$%^&*()_\-+=\[\]{};:\'",./?<>~`|]', password): # Corrected regex escaping
            raise ValueError("Password must contain at least one special character (e.g., !@#$%^&*).")
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    @validates('email')
    def validate_email(self, key, email):
        if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email): # Corrected regex escaping for dot
            raise ValueError("Invalid email address")
        return email

    def get_reset_token(self, expires_sec=1800):
        token = secrets.token_urlsafe(32)
        self.reset_token = token
        self.reset_token_expires = datetime.utcnow() + timedelta(seconds=expires_sec)
        return token

    @staticmethod
    def verify_reset_token(token_value):
        user = User.query.filter_by(reset_token=token_value).first()
        if user and user.reset_token_expires and user.reset_token_expires > datetime.utcnow():
            return user
        return None

    def __repr__(self):
        return f'<User {self.username}>'


class Employee(db.Model):
    # ... (existing Employee model code) ...
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
    exposures = relationship("Exposure", back_populates="employee", cascade="all, delete-orphan", lazy=True)
    health_records = relationship("HealthRecord", back_populates="employee", cascade="all, delete-orphan", lazy=True)

    @validates('contact_number', 'emergency_phone')
    def validate_phone(self, key, phone):
        if phone and not re.match(r'^[\d\s\-+()]{7,20}$', phone): # Corrected regex escaping
            raise ValueError("Invalid phone number format")
        return phone

    def __repr__(self):
        return f'<Employee {self.name}>'


class Hazard(db.Model):
    # ... (existing Hazard model code) ...
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
    exposures = relationship("Exposure", back_populates="hazard", cascade="all, delete-orphan", lazy=True)

    @validates('exposure_limit')
    def validate_exposure_limit(self, key, limit):
        if limit <= 0:
            raise ValueError("Exposure limit must be positive")
        return limit

    def __repr__(self):
        return f'<Hazard {self.name}>'


class Exposure(db.Model):
    # ... (existing Exposure model code) ...
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
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    employee = relationship("Employee", back_populates="exposures")
    hazard = relationship("Hazard", back_populates="exposures")
    recorder = relationship('User', foreign_keys=[recorded_by]) # This should not conflict with User.exposures_recorded or User.health_records_recorded if those are defined with different back_populates

    @validates('exposure_level')
    def validate_exposure_level(self, key, level):
        if level <= 0:
            raise ValueError("Exposure level must be positive")
        return level

    def __repr__(self):
        return f'<Exposure {self.id}>'


class HealthRecord(db.Model):
    # ... (existing HealthRecord model code) ...
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
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    employee = relationship("Employee", back_populates="health_records")
    recorder = relationship('User', foreign_keys=[recorded_by]) # Similar to Exposure.recorder

    def __repr__(self):
        return f'<HealthRecord {self.id}>'


# New Models
class HEG(db.Model):
    __tablename__ = 'hegs'
    __table_args__ = (
        Index('idx_hegs_heg_number', 'heg_number'),
        Index('idx_hegs_department_job_title', 'department', 'job_title'),
    )
    id = db.Column(db.Integer, primary_key=True)
    heg_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    job_title = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    exposure_agents = db.Column(db.Text, nullable=True)
    risk_level = db.Column(db.String(50), nullable=False, default=RISK_LEVEL_LOW)
    schedules = db.relationship('SamplingSchedule',
                                back_populates='heg',
                                lazy='dynamic',
                                cascade='all, delete-orphan')
    def __repr__(self):
        return f'<HEG {self.heg_number} - {self.job_title} in {self.department}>'

class SamplingSchedule(db.Model):
    __tablename__ = 'sampling_schedules'
    __table_args__ = (
        Index('idx_sampling_schedules_heg_id_type', 'heg_id', 'sampling_type'),
        Index('idx_sampling_schedules_next_sample_due', 'next_sample_due'),
    )
    id = db.Column(db.Integer, primary_key=True)
    heg_id = db.Column(db.Integer, db.ForeignKey('hegs.id', ondelete='CASCADE'), nullable=False)
    sampling_type = db.Column(db.String(100), nullable=False)
    frequency = db.Column(db.String(50), nullable=False, default=FREQUENCY_QUARTERLY)
    last_sampled_date = db.Column(db.Date, nullable=True)
    next_sample_due = db.Column(db.Date, nullable=True)
    remarks = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    heg = db.relationship('HEG', back_populates='schedules')

    def calculate_next_sample_due(self):
        if self.last_sampled_date and self.frequency:
            if self.frequency == FREQUENCY_MONTHLY:
                self.next_sample_due = self.last_sampled_date + timedelta(days=30) # Approximation
            elif self.frequency == FREQUENCY_QUARTERLY:
                self.next_sample_due = self.last_sampled_date + timedelta(days=91) # Approximation
            elif self.frequency == FREQUENCY_ANNUALLY:
                try:
                    self.next_sample_due = self.last_sampled_date.replace(year=self.last_sampled_date.year + 1)
                except ValueError: # Handle Feb 29th on non-leap year target
                    self.next_sample_due = self.last_sampled_date.replace(year=self.last_sampled_date.year + 1, day=28)
            else: # Unknown frequency
                self.next_sample_due = None
        else:
            self.next_sample_due = None

    def __repr__(self):
        return f'<SamplingSchedule ID {self.id} for HEG ID {self.heg_id} due {self.next_sample_due}>'

# Ensure User model has relationships back to Exposure and HealthRecord if needed for 'recorder'
# If User.exposures_recorded = relationship("Exposure", back_populates="recorder" ...) is needed,
# ensure 'recorder' in Exposure/HealthRecord uses back_populates.
# Current User model does not have these collections, which is fine if not needed.
# The `Exposure.recorder` and `HealthRecord.recorder` are simple `relationship('User', foreign_keys=[recorded_by])`
# which means they are many-to-one. If a `User.recorded_exposures` collection is desired,
# then User model would need:
# recorded_exposures = db.relationship("Exposure", foreign_keys="Exposure.recorded_by", back_populates="recorder")
# recorded_health_records = db.relationship("HealthRecord", foreign_keys="HealthRecord.recorded_by", back_populates="recorder")
# And Exposure.recorder and HealthRecord.recorder would need `back_populates="recorded_exposures"` etc.
# For now, keeping it simple as the user request didn't specify these reverse collections on User.
# The existing `recorder = relationship('User', foreign_keys=[recorded_by])` is fine for one-way from Exposure/HealthRecord to User.
