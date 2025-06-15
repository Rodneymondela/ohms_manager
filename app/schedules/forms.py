from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, DateField, TextAreaField
from wtforms.validators import DataRequired, Optional, Length, Regexp

class HEGForm(FlaskForm):
    heg_number = StringField('HEG Number', validators=[DataRequired(), Length(max=10), Regexp(r'^[a-zA-Z0-9_]*$', message='HEG Number must contain only letters, numbers, or underscores')])
    job_title = StringField('Job Title', validators=[DataRequired(), Length(max=100)])
    department = StringField('Department', validators=[DataRequired(), Length(max=100)])
    exposure_agents = StringField('Exposure Agents', validators=[DataRequired(), Length(max=255)])
    risk_level = SelectField('Risk Level', choices=[('Low', 'Low'), ('Moderate', 'Moderate'), ('High', 'High')], validators=[DataRequired()])
    submit = SubmitField('Save HEG')

class ScheduleForm(FlaskForm):
    sampling_type = StringField('Sampling Type', validators=[DataRequired(), Length(max=100)])
    frequency = SelectField('Frequency', choices=[('Monthly', 'Monthly'), ('Quarterly', 'Quarterly'), ('Annually', 'Annually')], validators=[DataRequired()])
    last_sampled_date = DateField('Last Sampled Date (YYYY-MM-DD)', format='%Y-%m-%d', validators=[Optional()])
    remarks = TextAreaField('Remarks', validators=[Optional(), Length(max=255)])
    submit = SubmitField('Save Schedule')
