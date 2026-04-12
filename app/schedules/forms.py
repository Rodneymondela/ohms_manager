"""
Occupational Hygiene Sampling Schedule Forms
============================================
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField, SelectField, TextAreaField,
    DateField, FloatField, BooleanField, SubmitField
)
from wtforms.validators import DataRequired, Optional, Length, NumberRange


RISK_LEVELS = [
    ('Low',      'Low'),
    ('Moderate', 'Moderate'),
    ('High',     'High'),
]

FREQUENCIES = [
    ('Monthly',     'Monthly'),
    ('Quarterly',   'Quarterly (every 3 months)'),
    ('Bi-Annually', 'Bi-Annually (every 6 months)'),
    ('Annually',    'Annually'),
]

PRIORITIES = [
    ('Low',    'Low'),
    ('Medium', 'Medium'),
    ('High',   'High'),
]

SAMPLING_TYPES = [
    ('Personal',    'Personal (worker-worn)'),
    ('Area',        'Area / Static'),
    ('Biological',  'Biological Monitoring'),
    ('Observational','Observational / Walkthrough'),
]

STATUSES = [
    ('Upcoming',  'Upcoming'),
    ('Due',       'Due'),
    ('Overdue',   'Overdue'),
    ('Completed', 'Completed'),
]

CATEGORIES = [
    ('Chemical',     'Chemical'),
    ('Physical',     'Physical'),
    ('Biological',   'Biological'),
    ('Ergonomic',    'Ergonomic'),
    ('Psychosocial', 'Psychosocial'),
]


class HEGForm(FlaskForm):
    heg_number  = StringField('HEG Number',   validators=[DataRequired(), Length(max=40)],
                              render_kw={'placeholder': 'e.g. HEG-A1'})
    job_title   = StringField('Job Title',    validators=[DataRequired(), Length(max=120)])
    department  = StringField('Department',   validators=[DataRequired(), Length(max=120)])
    risk_level  = SelectField('Risk Level',   choices=RISK_LEVELS, validators=[DataRequired()])
    description = TextAreaField('Description / Notes', validators=[Optional(), Length(max=500)],
                                render_kw={'rows': 3})
    submit      = SubmitField('Save HEG')


class HEGStressorForm(FlaskForm):
    stressor_id         = SelectField('Stressor', coerce=int, validators=[DataRequired()])
    monitoring_priority = SelectField('Monitoring Priority', choices=PRIORITIES, validators=[DataRequired()])
    exposure_notes      = TextAreaField('Exposure Notes', validators=[Optional(), Length(max=500)],
                                        render_kw={'rows': 3,
                                                   'placeholder': 'Describe how the exposure occurs, controls in place, etc.'})
    submit              = SubmitField('Assign Stressor')

    def set_stressor_choices(self, stressors):
        """Populate stressor dropdown from DB query result."""
        self.stressor_id.choices = [
            (s.id, f"{s.name}  [{s.oel_display()}]")
            for s in stressors
        ]


class SamplingScheduleForm(FlaskForm):
    heg_id            = SelectField('HEG',           coerce=int, validators=[DataRequired()])
    stressor_id       = SelectField('Stressor',      coerce=int, validators=[DataRequired()])
    sampling_type     = SelectField('Sampling Type', choices=SAMPLING_TYPES, validators=[Optional()])
    frequency         = SelectField('Frequency',     choices=FREQUENCIES,    validators=[DataRequired()])
    last_sampled_date = DateField('Last Sampled Date', validators=[Optional()], format='%Y-%m-%d')
    status            = SelectField('Status',        choices=STATUSES,       validators=[DataRequired()])
    remarks           = TextAreaField('Remarks',     validators=[Optional(), Length(max=500)],
                                      render_kw={'rows': 3})
    submit            = SubmitField('Save Schedule')

    def set_heg_choices(self, hegs):
        self.heg_id.choices = [
            (h.id, f"{h.heg_number} — {h.job_title} ({h.department})")
            for h in hegs
        ]

    def set_stressor_choices(self, stressors):
        self.stressor_id.choices = [
            (s.id, f"{s.name}  [{s.oel_display()}]")
            for s in stressors
        ]


class StressorForm(FlaskForm):
    """Admin form for managing the master stressor list."""
    name            = StringField('Stressor Name',    validators=[DataRequired(), Length(max=120)])
    category        = SelectField('Category',         choices=CATEGORIES, validators=[DataRequired()])
    oel_value       = FloatField('OEL Value (numeric)', validators=[Optional(),
                                                                    NumberRange(min=0, message='Must be positive')])
    oel_unit        = StringField('OEL Unit',         validators=[Optional(), Length(max=40)],
                                  render_kw={'placeholder': 'e.g. mg/m³  ppm  dB(A)  m/s²'})
    oel_text        = TextAreaField('OEL Text / Qualitative Limit', validators=[Optional(), Length(max=255)],
                                    render_kw={'rows': 2,
                                               'placeholder': 'Use when no single numeric value applies'})
    oel_reference   = StringField('OEL Reference',   validators=[Optional(), Length(max=120)],
                                  render_kw={'placeholder': 'e.g. SANS 10083, ACGIH TLV, OHS Act'})
    sampling_method = StringField('Sampling Method', validators=[Optional(), Length(max=120)],
                                  render_kw={'placeholder': 'e.g. NIOSH 0600, ISO 9612'})
    is_active       = BooleanField('Active', default=True)
    submit          = SubmitField('Save Stressor')
