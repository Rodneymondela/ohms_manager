from app import db
from datetime import datetime, timedelta

class HEG(db.Model):
    __tablename__ = 'HEG' # Explicitly set table name
    id = db.Column(db.Integer, primary_key=True)
    heg_number = db.Column(db.String(10), nullable=False, unique=True)
    job_title = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    exposure_agents = db.Column(db.String(255), nullable=False)
    risk_level = db.Column(db.String(20), nullable=False)  # Low, Moderate, High

    schedules = db.relationship('SamplingSchedule', backref='heg', lazy=True, cascade='all, delete-orphan')

class SamplingSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    heg_id = db.Column(db.Integer, db.ForeignKey('HEG.id'), nullable=False)
    sampling_type = db.Column(db.String(100), nullable=False)
    frequency = db.Column(db.String(20), nullable=False)  # Monthly, Quarterly, Annually
    last_sampled_date = db.Column(db.Date, nullable=True)
    next_sample_due = db.Column(db.Date, nullable=True)
    remarks = db.Column(db.String(255), nullable=True)

    def set_next_sample_due(self):
        if not self.last_sampled_date:
            self.next_sample_due = None # Ensure it's None if no last_sampled_date
            return
        freq_map = {
            "Monthly": 30,
            "Quarterly": 90,
            "Annually": 365
        }
        days = freq_map.get(self.frequency, 30)  # Default to 30 days if frequency is somehow not in map
        self.next_sample_due = self.last_sampled_date + timedelta(days=days)
