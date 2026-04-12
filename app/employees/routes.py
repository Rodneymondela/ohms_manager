"""
Employee Management Routes
==========================
Blueprint prefix: /employees
"""

import csv
import io
from datetime import datetime

from flask import (
    render_template, redirect, url_for, flash,
    request, jsonify, Response, session
)
from app import db
from app.employees import employees_bp
from app.employees.models import Employee
from app.employees.forms import EmployeeForm, BulkUploadForm
from app.schedules.models import HEG


# ── Helpers ──────────────────────────────────────────────────────────────────

CSV_HEADERS = ['name', 'job_title', 'department', 'heg_number',
               'email', 'contact_number', 'date_of_birth',
               'emergency_contact', 'date_employed']

def _parse_date(val):
    """Return a date object or None from a string."""
    val = (val or '').strip()
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%m/%d/%Y'):
        try:
            return datetime.strptime(val, fmt).date()
        except ValueError:
            continue
    return None

def _parse_csv(stream):
    """
    Parse CSV stream.  Returns (rows, errors).
    rows  = list of dicts ready to validate / insert.
    errors = list of (line_no, message) for bad rows.
    """
    text    = stream.read().decode('utf-8-sig')   # strip BOM if present
    reader  = csv.DictReader(io.StringIO(text))

    # Normalise header names (lower, strip)
    reader.fieldnames = [h.strip().lower().replace(' ', '_')
                         for h in (reader.fieldnames or [])]

    rows, errors = [], []
    required = {'name', 'job_title', 'department'}

    for i, row in enumerate(reader, start=2):           # line 1 = headers
        row = {k.strip(): (v or '').strip() for k, v in row.items()}
        missing = required - {k for k, v in row.items() if v}
        if missing:
            errors.append((i, f"Missing required field(s): {', '.join(missing)}"))
            continue
        rows.append({
            'name':              row.get('name', ''),
            'job_title':         row.get('job_title', ''),
            'department':        row.get('department', ''),
            'heg_number':        row.get('heg_number', '') or None,
            'email':             row.get('email', '')         or None,
            'contact_number':    row.get('contact_number', '') or None,
            'date_of_birth':     _parse_date(row.get('date_of_birth', '')),
            'emergency_contact': row.get('emergency_contact', '') or None,
            'date_employed':     _parse_date(row.get('date_employed', '')),
        })
    return rows, errors


# ══════════════════════════════════════════════════════════════════════════════
# LIST
# ══════════════════════════════════════════════════════════════════════════════

@employees_bp.route('/')
def employee_list():
    search     = request.args.get('q', '').strip()
    dept       = request.args.get('department', '')
    heg        = request.args.get('heg', '')
    active_only = request.args.get('active', '1')

    query = Employee.query

    if active_only == '1':
        query = query.filter_by(is_active=True)
    if search:
        query = query.filter(Employee.name.ilike(f'%{search}%'))
    if dept:
        query = query.filter_by(department=dept)
    if heg:
        query = query.filter_by(heg_number=heg)

    employees = query.order_by(Employee.name).all()

    departments = [r[0] for r in
                   db.session.query(Employee.department).distinct().order_by(Employee.department).all()]
    hegs = HEG.query.order_by(HEG.heg_number).all()
    heg_map = {h.heg_number: h.job_title for h in hegs}

    return render_template('employees/employee_list.html',
                           employees=employees,
                           departments=departments,
                           heg_map=heg_map,
                           hegs=hegs,
                           filters={'q': search, 'department': dept,
                                    'heg': heg, 'active': active_only})


# ══════════════════════════════════════════════════════════════════════════════
# ADD / EDIT / DELETE
# ══════════════════════════════════════════════════════════════════════════════

@employees_bp.route('/add', methods=['GET', 'POST'])
def employee_add():
    form = EmployeeForm()
    hegs = HEG.query.order_by(HEG.heg_number).all()

    if form.validate_on_submit():
        emp = Employee(
            name              = form.name.data.strip(),
            job_title         = form.job_title.data.strip(),
            department        = form.department.data.strip(),
            heg_number        = form.heg_number.data.strip() or None,
            email             = form.email.data.strip()       or None,
            contact_number    = form.contact_number.data.strip() or None,
            date_of_birth     = form.date_of_birth.data,
            emergency_contact = form.emergency_contact.data.strip() or None,
            date_employed     = form.date_employed.data,
            is_active         = form.is_active.data,
        )
        db.session.add(emp)
        db.session.commit()
        flash(f'Employee "{emp.name}" added successfully.', 'success')
        return redirect(url_for('employees.employee_list'))

    return render_template('employees/employee_form.html',
                           form=form, title='Add Employee', editing=False, hegs=hegs)


@employees_bp.route('/<int:emp_id>/edit', methods=['GET', 'POST'])
def employee_edit(emp_id):
    emp  = Employee.query.get_or_404(emp_id)
    form = EmployeeForm(obj=emp)
    hegs = HEG.query.order_by(HEG.heg_number).all()

    if form.validate_on_submit():
        emp.name              = form.name.data.strip()
        emp.job_title         = form.job_title.data.strip()
        emp.department        = form.department.data.strip()
        emp.heg_number        = form.heg_number.data.strip() or None
        emp.email             = form.email.data.strip()       or None
        emp.contact_number    = form.contact_number.data.strip() or None
        emp.date_of_birth     = form.date_of_birth.data
        emp.emergency_contact = form.emergency_contact.data.strip() or None
        emp.date_employed     = form.date_employed.data
        emp.is_active         = form.is_active.data
        db.session.commit()
        flash(f'Employee "{emp.name}" updated.', 'success')
        return redirect(url_for('employees.employee_list'))

    return render_template('employees/employee_form.html',
                           form=form, title='Edit Employee', editing=True,
                           employee=emp, hegs=hegs)


@employees_bp.route('/<int:emp_id>/delete', methods=['POST'])
def employee_delete(emp_id):
    emp = Employee.query.get_or_404(emp_id)
    name = emp.name
    db.session.delete(emp)
    db.session.commit()
    flash(f'Employee "{name}" deleted.', 'warning')
    return redirect(url_for('employees.employee_list'))


# ══════════════════════════════════════════════════════════════════════════════
# BULK UPLOAD
# ══════════════════════════════════════════════════════════════════════════════

@employees_bp.route('/bulk-upload', methods=['GET', 'POST'])
def bulk_upload():
    form = BulkUploadForm()

    if form.validate_on_submit():
        rows, errors = _parse_csv(form.csv_file.data.stream)
        # Store rows in session for confirmation step
        session['bulk_rows']   = rows
        session['bulk_errors'] = errors
        return redirect(url_for('employees.bulk_confirm'))

    return render_template('employees/bulk_upload.html', form=form)


@employees_bp.route('/bulk-upload/confirm', methods=['GET', 'POST'])
def bulk_confirm():
    rows   = session.get('bulk_rows', [])
    errors = session.get('bulk_errors', [])
    heg_map = {h.heg_number: h.job_title for h in HEG.query.all()}

    if request.method == 'POST':
        skip_dupes = request.form.get('skip_dupes') == '1'
        added = 0
        skipped = 0
        for row in rows:
            if skip_dupes:
                exists = Employee.query.filter(
                    Employee.name.ilike(row['name']),
                    Employee.department.ilike(row['department'])
                ).first()
                if exists:
                    skipped += 1
                    continue
            emp = Employee(**row, is_active=True)
            db.session.add(emp)
            added += 1
        db.session.commit()
        session.pop('bulk_rows', None)
        session.pop('bulk_errors', None)
        flash(f'{added} employee(s) imported successfully.{f" {skipped} duplicate(s) skipped." if skipped else ""}',
              'success')
        return redirect(url_for('employees.employee_list'))

    return render_template('employees/bulk_confirm.html', rows=rows, errors=errors, heg_map=heg_map)


# ── CSV template download ────────────────────────────────────────────────────

@employees_bp.route('/bulk-upload/template')
def csv_template():
    header = 'name,job_title,department,heg_number,email,contact_number,date_of_birth,emergency_contact,date_employed\n'
    sample = 'John Doe,Driller,Underground,HEG-A1,john@example.com,+27821234567,1985-06-15,Jane Doe,2020-01-10\n'
    return Response(
        header + sample,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=employee_import_template.csv'}
    )


# ── JSON API ─────────────────────────────────────────────────────────────────

@employees_bp.route('/api')
def api_employees():
    employees = Employee.query.filter_by(is_active=True).order_by(Employee.name).all()
    data = [{
        'id':            e.id,
        'name':          e.name,
        'job_title':     e.job_title,
        'department':    e.department,
        'heg_number':    e.heg_number,
        'email':         e.email,
        'contact_number': e.contact_number,
    } for e in employees]
    resp = jsonify(data)
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp
