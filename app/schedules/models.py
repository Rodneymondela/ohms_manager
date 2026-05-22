"""
Occupational Hygiene Sampling Schedule Models
=============================================
Models: Stressor, HEG, HEGStressor, SamplingSchedule,
        ExposureReading, EmployeeExposure, MedicalRecord
"""

import calendar
from datetime import date, datetime
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
    name            = db.Column(db.String(120), nullable=False)
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
    operation_id       = db.Column(db.Integer, db.ForeignKey('operation.id'), nullable=True)

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
    heg_number   = db.Column(db.String(40),  nullable=False)
    job_title    = db.Column(db.String(120), nullable=False)
    department   = db.Column(db.String(120), nullable=False)
    risk_level   = db.Column(db.String(20),  nullable=False, default='Moderate')
    description  = db.Column(db.Text, nullable=True)
    occupations  = db.Column(db.JSON, nullable=True, default=list)
    created_at   = db.Column(db.Date, default=date.today)
    operation_id = db.Column(db.Integer, db.ForeignKey('operation.id'), nullable=True)

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
    operation_id      = db.Column(db.Integer,     db.ForeignKey('operation.id'), nullable=True)

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
    operation_id   = db.Column(db.Integer, db.ForeignKey('operation.id'), nullable=True)

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

    id           = db.Column(db.Integer, primary_key=True)
    employee_id  = db.Column(db.Integer, db.ForeignKey('employee.id'),  nullable=False)
    stressor_id  = db.Column(db.Integer, db.ForeignKey('stressor.id'),  nullable=True)
    test_name    = db.Column(db.String(120), nullable=False)
    last_done    = db.Column(db.Date, nullable=True)
    next_due     = db.Column(db.Date, nullable=True)
    result       = db.Column(db.String(120), nullable=True)
    status       = db.Column(db.String(20),  nullable=False, default='scheduled')
    operation_id = db.Column(db.Integer,     db.ForeignKey('operation.id'), nullable=True)

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


# ---------------------------------------------------------------------------
# FieldSheet  (electronic field data capture sheet)
# ---------------------------------------------------------------------------

class FieldSheet(db.Model):
    __tablename__ = 'field_sheet'

    id               = db.Column(db.Integer, primary_key=True)
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)

    # ── Header ───────────────────────────────────────────────────────────────
    mine_site        = db.Column(db.String(120), nullable=True)
    heg              = db.Column(db.String(40),  nullable=True)
    sampling_quarter = db.Column(db.String(10),  nullable=True)
    survey_number    = db.Column(db.String(80),  nullable=True)

    # ── Employee being sampled ────────────────────────────────────────────────
    employee_name    = db.Column(db.String(120), nullable=True)
    coy_number       = db.Column(db.String(40),  nullable=True)
    job_title        = db.Column(db.String(120), nullable=True)
    company_name     = db.Column(db.String(120), nullable=True)
    sampling_date    = db.Column(db.Date,        nullable=True)
    shift_sampled    = db.Column(db.String(40),  nullable=True)
    purpose          = db.Column(db.Text,        nullable=True)

    # ── Weather conditions ────────────────────────────────────────────────────
    weather_wet      = db.Column(db.Boolean, default=False)
    weather_dry      = db.Column(db.Boolean, default=False)
    weather_hot      = db.Column(db.Boolean, default=False)
    weather_warm     = db.Column(db.Boolean, default=False)
    weather_cold     = db.Column(db.Boolean, default=False)
    wind_speed       = db.Column(db.String(60),  nullable=True)  # Calm/Gentle/Fresh
    indoor_ac        = db.Column(db.Boolean, default=False)
    indoor_lev       = db.Column(db.Boolean, default=False)
    cabin_ac         = db.Column(db.Boolean, default=False)

    # ── Briefing checklist (6 items) ──────────────────────────────────────────
    brief_1          = db.Column(db.Boolean, default=False)
    brief_2          = db.Column(db.Boolean, default=False)
    brief_3          = db.Column(db.Boolean, default=False)
    brief_4          = db.Column(db.Boolean, default=False)
    brief_5          = db.Column(db.Boolean, default=False)
    brief_6          = db.Column(db.Boolean, default=False)

    # ── Noise sampling ────────────────────────────────────────────────────────
    noise_sources        = db.Column(db.Text,        nullable=True)
    noise_control_types  = db.Column(db.String(120), nullable=True)
    noise_demarcated     = db.Column(db.String(3),   nullable=True)  # Yes/No
    noise_hpd_provided   = db.Column(db.String(3),   nullable=True)
    noise_dbadge_serial  = db.Column(db.String(80),  nullable=True)
    noise_cal_date       = db.Column(db.Date,        nullable=True)
    noise_method         = db.Column(db.String(80),  nullable=True)
    noise_pre_cal        = db.Column(db.String(40),  nullable=True)
    noise_post_cal       = db.Column(db.String(40),  nullable=True)
    noise_time_on        = db.Column(db.String(10),  nullable=True)
    noise_time_off       = db.Column(db.String(10),  nullable=True)
    noise_run_time       = db.Column(db.Integer,     nullable=True)
    noise_laeq           = db.Column(db.Float,       nullable=True)

    # ── Airborne pollutants sampling ──────────────────────────────────────────
    air_contaminant      = db.Column(db.String(120), nullable=True)
    air_control_types    = db.Column(db.String(120), nullable=True)
    air_personal_sample  = db.Column(db.String(3),   nullable=True)
    air_area_sample      = db.Column(db.String(3),   nullable=True)
    air_pump_serial      = db.Column(db.String(80),  nullable=True)
    air_filter_number    = db.Column(db.String(80),  nullable=True)
    air_cal_date         = db.Column(db.Date,        nullable=True)
    air_method           = db.Column(db.String(80),  nullable=True)
    air_pre_cal_flow     = db.Column(db.Float,       nullable=True)
    air_post_cal_flow    = db.Column(db.Float,       nullable=True)
    air_time_on          = db.Column(db.String(10),  nullable=True)
    air_time_off         = db.Column(db.String(10),  nullable=True)
    air_run_time         = db.Column(db.Integer,     nullable=True)

    # ── Acknowledgement & sign-off ────────────────────────────────────────────
    wearer_signature     = db.Column(db.String(120), nullable=True)
    sampled_by           = db.Column(db.String(120), nullable=True)
    sampled_designation  = db.Column(db.String(80),  nullable=True)
    sampled_date         = db.Column(db.Date,        nullable=True)
    verified_by          = db.Column(db.String(120), nullable=True)

    # ── DMPR classification ───────────────────────────────────────────────────
    activity_area        = db.Column(db.String(120), nullable=True)   # DMPR area tab name
    occupation_group     = db.Column(db.String(120), nullable=True)   # occupation group in HEG

    # ── Lab results (returned by lab after analysis) ──────────────────────────
    result_mn_twa        = db.Column(db.Float,       nullable=True)   # Manganese TWA mg/m³ (code 378)
    result_si_twa        = db.Column(db.Float,       nullable=True)   # Silica TWA mg/m³    (code 522)
    result_pnoc_twa      = db.Column(db.Float,       nullable=True)   # PNOC TWA mg/m³      (code 459)

    # ── Scanned copy (stored in Cloudinary) ──────────────────────────────────
    scan_filename        = db.Column(db.String(255), nullable=True)
    scan_url_external    = db.Column(db.Text,        nullable=True)  # Cloudinary CDN URL
    operation_id         = db.Column(db.Integer,     db.ForeignKey('operation.id'), nullable=True)

    @property
    def status(self):
        has_core = bool(self.employee_name and self.sampling_date)
        has_sampling = bool(
            self.noise_dbadge_serial or self.noise_laeq or
            self.air_contaminant or self.air_pump_serial
        )
        has_scan = bool(self.scan_filename)
        if has_core and has_sampling and has_scan:
            return 'Completed'
        return 'Draft'

    def to_dict(self):
        return {
            'id':               self.id,
            'created_at':       self.created_at.isoformat() if self.created_at else None,
            'status':           self.status,
            # Header
            'mine_site':        self.mine_site,
            'heg':              self.heg,
            'sampling_quarter': self.sampling_quarter,
            'survey_number':    self.survey_number,
            # Employee
            'employee_name':    self.employee_name,
            'coy_number':       self.coy_number,
            'job_title':        self.job_title,
            'company_name':     self.company_name,
            'sampling_date':    self.sampling_date.isoformat() if self.sampling_date else None,
            'shift_sampled':    self.shift_sampled,
            'purpose':          self.purpose,
            # Weather
            'weather_wet':      self.weather_wet,
            'weather_dry':      self.weather_dry,
            'weather_hot':      self.weather_hot,
            'weather_warm':     self.weather_warm,
            'weather_cold':     self.weather_cold,
            'wind_speed':       self.wind_speed,
            'indoor_ac':        self.indoor_ac,
            'indoor_lev':       self.indoor_lev,
            'cabin_ac':         self.cabin_ac,
            # Briefing
            'brief_1':          self.brief_1,
            'brief_2':          self.brief_2,
            'brief_3':          self.brief_3,
            'brief_4':          self.brief_4,
            'brief_5':          self.brief_5,
            'brief_6':          self.brief_6,
            # Noise
            'noise_sources':        self.noise_sources,
            'noise_control_types':  self.noise_control_types,
            'noise_demarcated':     self.noise_demarcated,
            'noise_hpd_provided':   self.noise_hpd_provided,
            'noise_dbadge_serial':  self.noise_dbadge_serial,
            'noise_cal_date':       self.noise_cal_date.isoformat() if self.noise_cal_date else None,
            'noise_method':         self.noise_method,
            'noise_pre_cal':        self.noise_pre_cal,
            'noise_post_cal':       self.noise_post_cal,
            'noise_time_on':        self.noise_time_on,
            'noise_time_off':       self.noise_time_off,
            'noise_run_time':       self.noise_run_time,
            'noise_laeq':           self.noise_laeq,
            # Airborne
            'air_contaminant':      self.air_contaminant,
            'air_control_types':    self.air_control_types,
            'air_personal_sample':  self.air_personal_sample,
            'air_area_sample':      self.air_area_sample,
            'air_pump_serial':      self.air_pump_serial,
            'air_filter_number':    self.air_filter_number,
            'air_cal_date':         self.air_cal_date.isoformat() if self.air_cal_date else None,
            'air_method':           self.air_method,
            'air_pre_cal_flow':     self.air_pre_cal_flow,
            'air_post_cal_flow':    self.air_post_cal_flow,
            'air_time_on':          self.air_time_on,
            'air_time_off':         self.air_time_off,
            'air_run_time':         self.air_run_time,
            # Sign-off
            'wearer_signature':     self.wearer_signature,
            'sampled_by':           self.sampled_by,
            'sampled_designation':  self.sampled_designation,
            'sampled_date':         self.sampled_date.isoformat() if self.sampled_date else None,
            'verified_by':          self.verified_by,
            # DMPR classification
            'activity_area':        self.activity_area,
            'occupation_group':     self.occupation_group,
            # Lab results
            'result_mn_twa':        self.result_mn_twa,
            'result_si_twa':        self.result_si_twa,
            'result_pnoc_twa':      self.result_pnoc_twa,
            # Scan
            'scan_filename':        self.scan_filename,
            'scan_url':             f'/api/field-sheets/{self.id}/scan' if self.scan_filename else None,
            'scan_url_external':    self.scan_url_external,
        }

    def __repr__(self):
        return f"<FieldSheet id:{self.id} emp:{self.employee_name} status:{self.status}>"


# ---------------------------------------------------------------------------
# LabResult  (master sheet — lab results entered when report received)
# ---------------------------------------------------------------------------

class LabResult(db.Model):
    __tablename__ = 'lab_result'

    id               = db.Column(db.Integer, primary_key=True)
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)
    sampling_date    = db.Column(db.Date,        nullable=True)
    sampling_quarter = db.Column(db.String(10),  nullable=True)   # Q1 / Q2 / Q3 / Q4
    activity_area    = db.Column(db.String(120), nullable=False)
    occupation       = db.Column(db.String(120), nullable=False)
    result_mn_twa     = db.Column(db.Float,   nullable=True)   # Manganese TWA mg/m³ (code 378)
    result_si_twa     = db.Column(db.Float,   nullable=True)   # Silica TWA mg/m³    (code 522)
    result_pnoc_twa   = db.Column(db.Float,   nullable=True)   # PNOC TWA mg/m³      (code 459)
    shift_duration    = db.Column(db.Float,   nullable=True)   # standard shift length in hours (8, 9, 10, 12)
    sampling_duration = db.Column(db.Integer, nullable=True)   # actual pump run time in minutes
    survey_ref        = db.Column(db.String(80), nullable=True)
    lab_report_ref    = db.Column(db.String(80), nullable=True)
    field_sheet_id    = db.Column(db.Integer, db.ForeignKey('field_sheet.id'), nullable=True)
    operation_id      = db.Column(db.Integer, db.ForeignKey('operation.id'), nullable=True)

    @property
    def validity_pct(self):
        if self.shift_duration and self.sampling_duration is not None:
            return (self.sampling_duration / (self.shift_duration * 60)) * 100
        return None

    @property
    def is_valid_sample(self):
        pct = self.validity_pct
        if pct is None:
            return True   # no duration data — don't auto-reject
        return pct >= 80

    def to_dict(self):
        return {
            'id':               self.id,
            'created_at':       self.created_at.isoformat() if self.created_at else None,
            'sampling_date':    self.sampling_date.isoformat() if self.sampling_date else None,
            'sampling_quarter': self.sampling_quarter,
            'activity_area':    self.activity_area,
            'occupation':       self.occupation,
            'result_mn_twa':     self.result_mn_twa,
            'result_si_twa':     self.result_si_twa,
            'result_pnoc_twa':   self.result_pnoc_twa,
            'shift_duration':    self.shift_duration,
            'sampling_duration': self.sampling_duration,
            'validity_pct':      round(self.validity_pct, 1) if self.validity_pct is not None else None,
            'is_valid':          self.is_valid_sample,
            'survey_ref':        self.survey_ref,
            'lab_report_ref':    self.lab_report_ref,
            'field_sheet_id':    self.field_sheet_id,
        }

    def __repr__(self):
        return f"<LabResult {self.activity_area} / {self.occupation} {self.sampling_quarter}>"
