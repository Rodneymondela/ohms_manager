from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, DateField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Optional, Email, Length


class EmployeeForm(FlaskForm):
    name              = StringField('Full Name',         validators=[DataRequired(), Length(max=120)])
    job_title         = StringField('Job Title',         validators=[DataRequired(), Length(max=120)])
    department        = StringField('Department',        validators=[DataRequired(), Length(max=100)])
    heg_number        = StringField('HEG Number',        validators=[Optional(), Length(max=30)])
    email             = StringField('Email',             validators=[Optional(), Email(), Length(max=120)])
    contact_number    = StringField('Contact Number',    validators=[Optional(), Length(max=30)])
    date_of_birth     = DateField('Date of Birth',       validators=[Optional()])
    emergency_contact = StringField('Emergency Contact', validators=[Optional(), Length(max=120)])
    date_employed     = DateField('Date Employed',       validators=[Optional()])
    is_active         = BooleanField('Active Employee',  default=True)
    submit            = SubmitField('Save Employee')


class BulkUploadForm(FlaskForm):
    csv_file = FileField('CSV File', validators=[
        FileRequired(),
        FileAllowed(['csv'], 'CSV files only.')
    ])
    submit = SubmitField('Upload & Preview')
