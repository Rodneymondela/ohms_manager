from flask import render_template, redirect, url_for, flash, request, render_template_string
from app import app, db
from app.models import HEG, SamplingSchedule
from app.forms import HEGForm, ScheduleForm
from datetime import datetime

@app.route('/')
@app.route('/index')
def index():
    hegs = HEG.query.all()
    # Using an inline template string for now
    html = '''
    <!DOCTYPE html>
    <html>
    <head><title>Sampling Schedule</title></head>
    <body>
        <h1>HEG Sampling Schedules</h1>
        <p><a href="{{ url_for('add_heg') }}">Add New HEG</a></p>
        <table border='1'>
            <tr><th>HEG Number</th><th>Job Title</th><th>Department</th><th>Risk Level</th><th>Schedules</th><th>Actions</th></tr>
            {% for heg in hegs %}
            <tr>
                <td>{{ heg.heg_number }}</td>
                <td>{{ heg.job_title }}</td>
                <td>{{ heg.department }}</td>
                <td>{{ heg.risk_level }}</td>
                <td>
                    {% if heg.schedules %}
                    <ul>
                        {% for schedule in heg.schedules %}
                        <li>
                            {{ schedule.sampling_type }} ({{ schedule.frequency }})<br>
                            Last: {{ schedule.last_sampled_date.strftime('%Y-%m-%d') if schedule.last_sampled_date else 'N/A' }}<br>
                            Next: {{ schedule.next_sample_due.strftime('%Y-%m-%d') if schedule.next_sample_due else 'N/A' }}<br>
                            <a href="{{ url_for('edit_schedule', schedule_id=schedule.id) }}">Edit</a> | <a href="{{ url_for('delete_schedule', schedule_id=schedule.id) }}" onclick="return confirm('Are you sure?');">Delete</a>
                        </li>
                        {% endfor %}
                    </ul>
                    {% else %}
                    No schedules yet.
                    {% endif %}
                    <a href="{{ url_for('add_schedule', heg_id=heg.id) }}">Add Schedule</a>
                </td>
                <td><a href="{{ url_for('edit_heg', heg_id=heg.id) }}">Edit HEG</a> | <a href="{{ url_for('delete_heg', heg_id=heg.id) }}" onclick="return confirm('Are you sure you want to delete this HEG and all its schedules?');">Delete HEG</a></td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    '''
    return render_template_string(html, hegs=hegs)

@app.route('/add_heg', methods=['GET', 'POST'])
def add_heg():
    form = HEGForm()
    if form.validate_on_submit():
        heg = HEG(heg_number=form.heg_number.data, job_title=form.job_title.data, department=form.department.data, exposure_agents=form.exposure_agents.data, risk_level=form.risk_level.data)
        db.session.add(heg)
        db.session.commit()
        flash('HEG added successfully!', 'success')
        return redirect(url_for('index'))
    html = '''
    <!DOCTYPE html>
    <html><head><title>Add HEG</title></head><body>
    <h1>Add New HEG</h1>
    <form method='POST' action=''>
        {{ form.hidden_tag() }}
        <p>{{ form.heg_number.label }}<br>{{ form.heg_number(size=30) }}<br>{% for error in form.heg_number.errors %}<span style="color: red;">[{{ error }}]</span>{% endfor %}</p>
        <p>{{ form.job_title.label }}<br>{{ form.job_title(size=30) }}<br>{% for error in form.job_title.errors %}<span style="color: red;">[{{ error }}]</span>{% endfor %}</p>
        <p>{{ form.department.label }}<br>{{ form.department(size=30) }}<br>{% for error in form.department.errors %}<span style="color: red;">[{{ error }}]</span>{% endfor %}</p>
        <p>{{ form.exposure_agents.label }}<br>{{ form.exposure_agents(size=30) }}<br>{% for error in form.exposure_agents.errors %}<span style="color: red;">[{{ error }}]</span>{% endfor %}</p>
        <p>{{ form.risk_level.label }}<br>{{ form.risk_level() }}<br>{% for error in form.risk_level.errors %}<span style="color: red;">[{{ error }}]</span>{% endfor %}</p>
        <p>{{ form.submit() }}</p>
    </form>
    <a href="{{ url_for('index') }}">Back to list</a>
    </body></html>
    '''
    return render_template_string(html, form=form)

@app.route('/edit_heg/<int:heg_id>', methods=['GET', 'POST'])
def edit_heg(heg_id):
    heg = HEG.query.get_or_404(heg_id)
    form = HEGForm(obj=heg)
    if form.validate_on_submit():
        # Check for uniqueness of heg_number if it's changed
        if heg.heg_number != form.heg_number.data:
            existing_heg = HEG.query.filter_by(heg_number=form.heg_number.data).first()
            if existing_heg:
                flash('HEG Number already exists. Please choose a different one.', 'error')
                # Re-render form with error, do not redirect yet
                html = '''
                <!DOCTYPE html>
                <html><head><title>Edit HEG</title></head><body>
                <h1>Edit HEG</h1>
                {% with messages = get_flashed_messages(with_categories=true) %}
                  {% if messages %}
                    <ul class=flashes>
                    {% for category, message in messages %}
                      <li class="{{ category }}">{{ message }}</li>
                    {% endfor %}
                    </ul>
                  {% endif %}
                {% endwith %}
                <form method='POST' action=''>
                    {{ form.hidden_tag() }}
                    <p>{{ form.heg_number.label }}<br>{{ form.heg_number(size=30) }}<br>{% for error in form.heg_number.errors %}<span style="color: red;">[{{ error }}]</span>{% endfor %}</p>
                    <p>{{ form.job_title.label }}<br>{{ form.job_title(size=30) }}<br>{% for error in form.job_title.errors %}<span style="color: red;">[{{ error }}]</span>{% endfor %}</p>
                    <p>{{ form.department.label }}<br>{{ form.department(size=30) }}<br>{% for error in form.department.errors %}<span style="color: red;">[{{ error }}]</span>{% endfor %}</p>
                    <p>{{ form.exposure_agents.label }}<br>{{ form.exposure_agents(size=30) }}<br>{% for error in form.exposure_agents.errors %}<span style="color: red;">[{{ error }}]</span>{% endfor %}</p>
                    <p>{{ form.risk_level.label }}<br>{{ form.risk_level() }}<br>{% for error in form.risk_level.errors %}<span style="color: red;">[{{ error }}]</span>{% endfor %}</p>
                    <p>{{ form.submit() }}</p>
                </form>
                <a href="{{ url_for('index') }}">Back to list</a>
                </body></html>
                '''
                return render_template_string(html, form=form, heg=heg)

        heg.heg_number = form.heg_number.data
        heg.job_title = form.job_title.data
        heg.department = form.department.data
        heg.exposure_agents = form.exposure_agents.data
        heg.risk_level = form.risk_level.data
        db.session.commit()
        flash('HEG updated successfully!', 'success')
        return redirect(url_for('index'))
    # Pre-populate form for GET request
    html = '''
    <!DOCTYPE html>
    <html><head><title>Edit HEG</title></head><body>
    <h1>Edit HEG</h1>
    <form method='POST' action=''>
        {{ form.hidden_tag() }}
        <p>{{ form.heg_number.label }}<br>{{ form.heg_number(size=30, value=heg.heg_number) }}<br>{% for error in form.heg_number.errors %}<span style="color: red;">[{{ error }}]</span>{% endfor %}</p>
        <p>{{ form.job_title.label }}<br>{{ form.job_title(size=30, value=heg.job_title) }}<br>{% for error in form.job_title.errors %}<span style="color: red;">[{{ error }}]</span>{% endfor %}</p>
        <p>{{ form.department.label }}<br>{{ form.department(size=30, value=heg.department) }}<br>{% for error in form.department.errors %}<span style="color: red;">[{{ error }}]</span>{% endfor %}</p>
        <p>{{ form.exposure_agents.label }}<br>{{ form.exposure_agents(size=30, value=heg.exposure_agents) }}<br>{% for error in form.exposure_agents.errors %}<span style="color: red;">[{{ error }}]</span>{% endfor %}</p>
        <p>{{ form.risk_level.label }}<br>{{ form.risk_level(value=heg.risk_level) }}<br>{% for error in form.risk_level.errors %}<span style="color: red;">[{{ error }}]</span>{% endfor %}</p>
        <p>{{ form.submit() }}</p>
    </form>
    <a href="{{ url_for('index') }}">Back to list</a>
    </body></html>
    '''
    return render_template_string(html, form=form, heg=heg)

@app.route('/delete_heg/<int:heg_id>', methods=['GET', 'POST']) # Allow GET for link click with JS confirm
def delete_heg(heg_id):
    heg = HEG.query.get_or_404(heg_id)
    db.session.delete(heg)
    db.session.commit()
    flash('HEG and its schedules deleted successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/add_schedule/<int:heg_id>', methods=['GET', 'POST'])
def add_schedule(heg_id):
    heg = HEG.query.get_or_404(heg_id)
    form = ScheduleForm()
    if form.validate_on_submit():
        schedule = SamplingSchedule(heg_id=heg.id, sampling_type=form.sampling_type.data, frequency=form.frequency.data, last_sampled_date=form.last_sampled_date.data, remarks=form.remarks.data)
        schedule.set_next_sample_due()
        db.session.add(schedule)
        db.session.commit()
        flash('Sampling schedule added successfully!', 'success')
        return redirect(url_for('index'))
    html = '''
    <!DOCTYPE html>
    <html><head><title>Add Schedule for {{ heg.heg_number }}</title></head><body>
    <h1>Add Schedule for {{ heg.heg_number }}</h1>
    <form method='POST' action=''>
        {{ form.hidden_tag() }}
        <p>{{ form.sampling_type.label }}<br>{{ form.sampling_type(size=30) }}<br>{% for error in form.sampling_type.errors %}<span style="color: red;">[{{ error }}]</span>{% endfor %}</p>
        <p>{{ form.frequency.label }}<br>{{ form.frequency() }}<br>{% for error in form.frequency.errors %}<span style="color: red;">[{{ error }}]</span>{% endfor %}</p>
        <p>{{ form.last_sampled_date.label }} (YYYY-MM-DD)<br>{{ form.last_sampled_date() }}<br>{% for error in form.last_sampled_date.errors %}<span style="color: red;">[{{ error }}]</span>{% endfor %}</p>
        <p>{{ form.remarks.label }}<br>{{ form.remarks(rows=3, cols=30) }}<br>{% for error in form.remarks.errors %}<span style="color: red;">[{{ error }}]</span>{% endfor %}</p>
        <p>{{ form.submit() }}</p>
    </form>
    <a href="{{ url_for('index') }}">Back to list</a>
    </body></html>
    '''
    return render_template_string(html, form=form, heg=heg)

@app.route('/edit_schedule/<int:schedule_id>', methods=['GET', 'POST'])
def edit_schedule(schedule_id):
    schedule = SamplingSchedule.query.get_or_404(schedule_id)
    heg = schedule.heg
    form = ScheduleForm(obj=schedule)
    if form.validate_on_submit():
        schedule.sampling_type = form.sampling_type.data
        schedule.frequency = form.frequency.data
        schedule.last_sampled_date = form.last_sampled_date.data
        schedule.remarks = form.remarks.data
        schedule.set_next_sample_due()
        db.session.commit()
        flash('Sampling schedule updated successfully!', 'success')
        return redirect(url_for('index'))
    html = '''
    <!DOCTYPE html>
    <html><head><title>Edit Schedule for {{ heg.heg_number }}</title></head><body>
    <h1>Edit Schedule for {{ heg.heg_number }}</h1>
    <form method='POST' action=''>
        {{ form.hidden_tag() }}
        <p>{{ form.sampling_type.label }}<br>{{ form.sampling_type(size=30, value=schedule.sampling_type) }}<br>{% for error in form.sampling_type.errors %}<span style="color: red;">[{{ error }}]</span>{% endfor %}</p>
        <p>{{ form.frequency.label }}<br>{{ form.frequency(value=schedule.frequency) }}<br>{% for error in form.frequency.errors %}<span style="color: red;">[{{ error }}]</span>{% endfor %}</p>
        <p>{{ form.last_sampled_date.label }} (YYYY-MM-DD)<br>{{ form.last_sampled_date(value=schedule.last_sampled_date.strftime('%Y-%m-%d') if schedule.last_sampled_date else '') }}<br>{% for error in form.last_sampled_date.errors %}<span style="color: red;">[{{ error }}]</span>{% endfor %}</p>
        <p>{{ form.remarks.label }}<br>{{ form.remarks(rows=3, cols=30, value=schedule.remarks if schedule.remarks else '') }}<br>{% for error in form.remarks.errors %}<span style="color: red;">[{{ error }}]</span>{% endfor %}</p>
        <p>{{ form.submit() }}</p>
    </form>
    <a href="{{ url_for('index') }}">Back to list</a>
    </body></html>
    '''
    return render_template_string(html, form=form, schedule=schedule, heg=heg)

@app.route('/delete_schedule/<int:schedule_id>', methods=['GET', 'POST']) # Allow GET for link click with JS confirm
def delete_schedule(schedule_id):
    schedule = SamplingSchedule.query.get_or_404(schedule_id)
    db.session.delete(schedule)
    db.session.commit()
    flash('Schedule deleted successfully!', 'success')
    return redirect(url_for('index'))
