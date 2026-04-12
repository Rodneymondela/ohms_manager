"""
Occupational Hygiene Sampling Schedule Models
=============================================
Models: Stressor, HEG, HEGStressor, SamplingSchedule,
        ExposureReading, EmployeeExposure, MedicalRecord
"""

import calendar
from datetime import date
from app import db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _add_months(source_date, months):
    """Month-aware date addition that handles month-end edge cases."""
    month = source_date.month - 1 + months
    year  = source_date.year + month // 12
    month = month % 12 + 1
    day   = min(source_date.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def calculate_next_due(last_date, frequency):
    """
    Calculate next sample due date from last sampled date and frequency string.
    Returns None if last_date is None.
    """
    if not last_date:
        return None
    freq_map = {
        'Monthly':     1,
        'Quarterly':   3,
        'Bi-Annually': 6,
        'Annually':    12,
    }
    months = freq_map.get(frequency)
    if months:
        return _add_months(last_date, months)
    return None


# ---------------------------------------------------------------------------
# Stressor (master list)
# ---------------------------------------------------------------------------

class Stressor(db.Model):
    __tablename__ = 'stressor'

    id              = db.Column(db.Integer, primary_key=True)
    name            = db.Column(db.String(120), nullable=False, unique=True)
    category        = db.Column(db.String(80), nullable=False)          # Chemical, Physical, Biological, etc.
    oel_value       = db.Column(db.Float, nullable=True)                # Numeric limit; None if qualitative
    oel_unit        = db.Column(db.String(40), nullable=True)           # mg/m³, ppm, dB(A), m/s², etc.
    oel_text        = db.Column(db.String(255), nullable=True)          # Qualitative / narrative limit
    oel_reference   = db.Column(db.String(120), nullable=True)          # SANS, ACGIH, OHS Act, etc.
    sampling_method    = db.Column(db.String(120), nullable=True)
    is_active          = db.Column(db.Boolean, default=True, nullable=False)
    # UI-facing fields used by the React frontend
    description        = db.Column(db.Text, nullable=True)
    health_effects     = db.Column(db.Text, nullable=True)
    linked_test        = db.Column(db.String(120), nullable=True)
    default_frequency  = db.Column(db.String(20), nullable=True)   # Annual, 6 Monthly, Quarterly

    # Relationships
    heg_stressors      = db.relationship('HEGStressor',      back_populates='stressor', cascade='all, delete-orphan')
    sampling_schedules = db.relationship('SamplingSchedule', back_populates='stressor', cascade='all, delete-orphan')
    exposure_readings  = db.relationship('ExposureReading',  back_populates='stressor', cascade='all, delete-orphan')
    medical_records    = db.relationship('MedicalRecord',    back_populates='stressor', cascade='all, delete-orphan')

    def oel_display(self):
        """Human-readable OEL string."""
        if self.oel_value is not None and self.oel_unit:
            return f"{self.oel_value} {self.oel_unit}"
        if self.oel_text:
            return self.oel_text
        return "—"

    def to_api_dict(self):
        """Shape expected by the React OHMS Manager frontend."""
        return {
            'id':            self.id,
            'name':          self.name,
            'category':      self.category,
            'description':   self.description or '',
            'oel':           self.oel_display(),
            'oelValue':      self.oel_value,
            'unit':          self.oel_unit or '',
            'healthEffects': self.health_effects or '',
            'linkedTest':    self.linked_test or '',
            'frequency':     self.default_frequency or 'Annual',
        }

    def __repr__(self):
        return f"<Stressor {self.name} | {self.oel_display()}>"


# ---------------------------------------------------------------------------
# HEG (Homogeneous Exposure Group)
# ---------------------------------------------------------------------------

class HEG(db.Model):
    __tablename__ = 'heg'

    id           = db.Column(db.Integer, primary_key=True)
    heg_number   = db.Column(db.String(40),  nullable=False, unique=True)
    job_title    = db.Column(db.String(120), nullable=False)
    department   = db.Column(db.String(120), nullable=False)
    risk_level   = db.Column(db.String(20),  nullable=False, default='Moderate')
    description  = db.Column(db.Text, nullable=True)
    occupations  = db.Column(db.JSON, nullable=True, default=list)
    created_at   = db.Column(db.Date, default=date.today)

    # Relationships
    heg_stressors     = db.relationship('HEGStressor',     back_populates='heg',      cascade='all, delete-orphan')
    sampling_schedules = db.relationship('SamplingSchedule', back_populates='heg',     cascade='all, delete-orphan')

    @property
    def stressors(self):
        return [hs.stressor for hs in self.heg_stressors]

    @property
    def overdue_count(self):
        return sum(1 for s in self.sampling_schedules if s.computed_status == 'Overdue')

    def __repr__(self):
        return f"<HEG {self.heg_number} | {self.job_title} | {self.department}>"


# ---------------------------------------------------------------------------
# HEGStressor (linking table)
# ---------------------------------------------------------------------------

class HEGStressor(db.Model):
    __tablename__ = 'heg_stressor'

    id                  = db.Column(db.Integer, primary_key=True)
    heg_id              = db.Column(db.Integer, db.ForeignKey('heg.id'),      nullable=False)
    stressor_id         = db.Column(db.Integer, db.ForeignKey('stressor.id'), nullable=False)
    exposure_notes      = db.Column(db.Text,    nullable=True)
    monitoring_priority = db.Column(db.String(20), nullable=False, default='Medium')  # Low, Medium, High

    # Relationships
    heg      = db.relationship('HEG',      back_populates='heg_stressors')
    stressor = db.relationship('Stressor', back_populates='heg_stressors')

    __table_args__ = (
        db.UniqueConstraint('heg_id', 'stressor_id', name='uq_heg_stressor'),
    )

    def __repr__(self):
        return f"<HEGStressor HEG:{self.heg_id} | Stressor:{self.stressor_id}>"


# ---------------------------------------------------------------------------
# SamplingSchedule
# ---------------------------------------------------------------------------

class SamplingSchedule(db.Model):
    __tablename__ = 'sampling_schedule'

    id                = db.Column(db.Integer, primary_key=True)
    heg_id            = db.Column(db.Integer, db.ForeignKey('heg.id'),      nullable=False)
    stressor_id       = db.Column(db.Integer, db.ForeignKey('stressor.id'), nullable=False)
    occupation        = db.Column(db.String(120), nullable=True)
    sampling_type     = db.Column(db.String(80),  nullable=True)             # Personal, Area, Biological
    frequency         = db.Column(db.String(20),  nullable=False)            # Monthly, Quarterly, Bi-Annually, Annually
    last_sampled_date = db.Column(db.Date,        nullable=True)
    next_sample_due   = db.Column(db.Date,        nullable=True)
    status            = db.Column(db.String(20),  nullable=False, default='Upcoming')
    remarks           = db.Column(db.Text,        nullable=True)
    created_at        = db.Column(db.Date,        default=date.today)

    # Relationships
    heg      = db.relationship('HEG',      back_populates='sampling_schedules')
    stressor = db.relationship('Stressor', back_populates='sampling_schedules')

    @property
    def computed_status(self):
        """Derive status from next_sample_due vs today."""
        if not self.next_sample_due:
            return 'Unknown'
        today = date.today()
        delta = (self.next_sample_due - today).days
        if delta < 0:
            return 'Overdue'
        elif delta <= 30:
            return 'Due'
        else:
            return 'Upcoming'

    @property
    def days_until_due(self):
        if not self.next_sample_due:
            return None
        return (self.next_sample_due - date.today()).days

    def recalculate_next_due(self):
        """Recalculate and store next_sample_due from last_sampled_date + frequency."""
        self.next_sample_due = calculate_next_due(self.last_sampled_date, self.frequency)
        self.status = self.computed_status

    def to_dict(self):
        """JSON-serialisable dict for the API endpoint consumed by the React OHMS Manager."""
        return {
            'id':               self.id,
            'hegId':            self.heg_id,
            'stressorId':       self.stressor_id,
            'heg_number':       self.heg.heg_number,
            'job_title':        self.heg.job_title,
            'department':       self.heg.department,
            'risk_level':       self.heg.risk_level,
            'stressor':         self.stressor.name,
            'stressor_category':self.stressor.category,
            'oel_display':      self.stressor.oel_display(),
            'oel_unit':         self.stressor.oel_unit,
            'oel_reference':    self.stressor.oel_reference,
            'occupation':       self.occupation,
            'sampling_type':    self.sampling_type,
            'frequency':        self.frequency,
            'last_sampled_date':self.last_sampled_date.isoformat() if self.last_sampled_date else None,
            'next_sample_due':  self.next_sample_due.isoformat()   if self.next_sample_due   else None,
            'status':           self.computed_status,
            'remarks':          self.remarks,
        }

    def __repr__(self):
        return f"<SamplingSchedule HEG:{self.heg_id} | Stressor:{self.stressor_id} | Due:{self.next_sample_due}>"


# ---------------------------------------------------------------------------
# ExposureReading  (individual measurement results)
# ---------------------------------------------------------------------------

class ExposureReading(db.Model):
    __tablename__ = 'exposure_reading'

    id             = db.Column(db.Integer, primary_key=True)
    stressor_id    = db.Column(db.Integer, db.ForeignKey('stressor.id'), nullable=False)
    location       = db.Column(db.String(120), nullable=False)
    measured_value = db.Column(db.Float, nullable=False)
    oel_value      = db.Column(db.Float, nullable=True)   # snapshot at time of reading
    oel_unit       = db.Column(db.String(40), nullable=True)
    date           = db.Column(db.Date, nullable=False, default=date.today)

    stressor          = db.relationship('Stressor', back_populates='exposure_readings')
    employee_exposures = db.relationship('EmployeeExposure', back_populates='reading', cascade='all, delete-orphan')

    def to_api_dict(self):
        return {
            'id':            self.id,
            'hazardId':      self.stressor_id,
            'location':      self.location,
            'measuredValue': self.measured_value,
            'oel':           self.oel_value,
            'unit':          self.oel_unit or '',
            'date':          self.date.isoformat(),
            'employeeIds':   [ee.employee_id for ee in self.employee_exposures],
        }

    def __repr__(self):
        return f"<ExposureReading stressor:{self.stressor_id} loc:{self.location} date:{self.date}>"


# ---------------------------------------------------------------------------
# EmployeeExposure  (many-to-many: ExposureReading ↔ Employee)
# ---------------------------------------------------------------------------

class EmployeeExposure(db.Model):
    __tablename__ = 'employee_exposure'

    id          = db.Column(db.Integer, primary_key=True)
    reading_id  = db.Column(db.Integer, db.ForeignKey('exposure_reading.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'),         nullable=False)

    reading  = db.relationship('ExposureReading', back_populates='employee_exposures')
    employee = db.relationship('Employee')

    __table_args__ = (
        db.UniqueConstraint('reading_id', 'employee_id', name='uq_employee_exposure'),
    )


# ---------------------------------------------------------------------------
# MedicalRecord  (medical surveillance per employee / stressor)
# ---------------------------------------------------------------------------

class MedicalRecord(db.Model):
    __tablename__ = 'medical_record'

    id          = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'),  nullable=False)
    stressor_id = db.Column(db.Integer, db.ForeignKey('stressor.id'),  nullable=True)
    test_name   = db.Column(db.String(120), nullable=False)
    last_done   = db.Column(db.Date, nullable=True)
    next_due    = db.Column(db.Date, nullable=True)
    result      = db.Column(db.String(120), nullable=True)
    status      = db.Column(db.String(20),  nullable=False, default='scheduled')

    employee = db.relationship('Employee', backref=db.backref('medical_records', lazy='dynamic'))
    stressor = db.relationship('Stressor', back_populates='medical_records')

    def to_api_dict(self):
        return {
            'id':         self.id,
            'employeeId': self.employee_id,
            'hazardId':   self.stressor_id,
            'testName':   self.test_name,
            'lastDone':   self.last_done.isoformat() if self.last_done else '',
            'nextDue':    self.next_due.isoformat()  if self.next_due  else '',
            'result':     self.result or '',
            'status':     self.status,
        }

    def __repr__(self):
        return f"<MedicalRecord emp:{self.employee_id} test:{self.test_name} status:{self.status}>"
