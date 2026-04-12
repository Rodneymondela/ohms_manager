from app import db
from datetime import date

# Association table: direct employee ↔ stressor assignments
employee_stressor = db.Table(
    'employee_stressor',
    db.Column('employee_id', db.Integer, db.ForeignKey('employee.id'), primary_key=True),
    db.Column('stressor_id', db.Integer, db.ForeignKey('stressor.id'), primary_key=True),
)


class Employee(db.Model):
    __tablename__ = 'employee'

    id               = db.Column(db.Integer, primary_key=True)
    name             = db.Column(db.String(120), nullable=False)
    job_title        = db.Column(db.String(120), nullable=False)
    department       = db.Column(db.String(100), nullable=False)
    heg_number       = db.Column(db.String(30),  nullable=True)   # matches HEG.heg_number
    email            = db.Column(db.String(120), nullable=True)
    contact_number   = db.Column(db.String(30),  nullable=True)
    date_of_birth    = db.Column(db.Date,        nullable=True)
    emergency_contact = db.Column(db.String(120), nullable=True)
    date_employed    = db.Column(db.Date,        nullable=True)
    is_active        = db.Column(db.Boolean,     default=True)

    # Direct hazard assignments (used by the React frontend)
    stressors = db.relationship('Stressor', secondary=employee_stressor, lazy='subquery',
                                backref=db.backref('employees', lazy=True))

    def to_api_dict(self):
        return {
            'id':         self.id,
            'name':       self.name,
            'jobTitle':   self.job_title,
            'department': self.department,
            'heg':        self.heg_number or '',
            'hazardIds':  [s.id for s in self.stressors],
        }

    def __repr__(self):
        return f'<Employee {self.name}>'

    @property
    def age(self):
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None
