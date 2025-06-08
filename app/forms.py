from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, DateField, TextAreaField, FloatField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional, NumberRange
from app.models import Employee, Hazard, Exposure, HealthRecord # Updated import path

class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=4, max=100)])
    email = StringField('Email',
                        validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password',
                             validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=4, max=100)])
    # If login via email is also desired, you might change the label or add another field.
    # For now, sticking to username as per the class name.
    password = PasswordField('Password',
                             validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class EmployeeForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    job_title = StringField('Job Title', validators=[DataRequired(), Length(max=100)])
    department = StringField('Department', validators=[DataRequired(), Length(max=100)])
    hire_date = DateField('Hire Date', validators=[Optional()], format='%Y-%m-%d')
    date_of_birth = DateField('Date of Birth', validators=[Optional()], format='%Y-%m-%d')
    contact_number = StringField('Contact Number', validators=[Optional(), Length(max=20)])
    emergency_contact = StringField('Emergency Contact Name', validators=[Optional(), Length(max=100)])
    emergency_phone = StringField('Emergency Contact Phone', validators=[Optional(), Length(max=20)])
    submit = SubmitField('Save Employee')

class HazardForm(FlaskForm):
    name = StringField('Hazard Name', validators=[DataRequired(), Length(max=100)])
    category = StringField('Category', validators=[DataRequired(), Length(max=50)])
    # Model validates exposure_limit > 0, NumberRange min=0.000001 ensures it's positive and non-zero.
    exposure_limit = FloatField('Exposure Limit (e.g., 85.0)', validators=[DataRequired(), NumberRange(min=0.000001)])
    unit = StringField('Unit (e.g., dB(A), ppm)', validators=[DataRequired(), Length(max=20)])
    description = TextAreaField('Description', validators=[Optional()])
    safety_measures = TextAreaField('Safety Measures', validators=[Optional()])
    submit = SubmitField('Save Hazard')

class ExposureForm(FlaskForm):
    employee = SelectField('Employee', coerce=int, validators=[DataRequired()])
    hazard = SelectField('Hazard', coerce=int, validators=[DataRequired()])
    exposure_level = FloatField('Exposure Level', validators=[DataRequired(), NumberRange(min=0.000001)]) # Model validates > 0
    duration = FloatField('Duration (e.g., hours)', validators=[Optional(), NumberRange(min=0)])
    date = DateField('Date of Exposure', format='%Y-%m-%d', validators=[DataRequired()])
    location = StringField('Location', validators=[Optional(), Length(max=100)])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Save Exposure')

class HealthRecordForm(FlaskForm):
    employee = SelectField('Employee', coerce=int, validators=[DataRequired()])
    test_type = StringField('Test Type', validators=[DataRequired(), Length(max=100)])
    result = StringField('Result', validators=[DataRequired(), Length(max=100)])
    details = TextAreaField('Details', validators=[Optional()])
    date = DateField('Date of Test', format='%Y-%m-%d', validators=[DataRequired()])
    next_test_date = DateField('Next Test Date (YYYY-MM-DD)', format='%Y-%m-%d', validators=[Optional()])
    physician = StringField('Physician', validators=[Optional(), Length(max=100)])
    facility = StringField('Facility', validators=[Optional(), Length(max=100)])
    submit = SubmitField('Save Health Record')
