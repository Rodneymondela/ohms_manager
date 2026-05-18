r"""
Tests for multi-operation (tenant) isolation.

Run with:
    python -m pytest tests/test_operations.py -v
"""

import pytest
from app import create_app, db
from app.models import User, Operation


@pytest.fixture(scope='function')
def app():
    application = create_app()
    application.config['TESTING'] = True
    application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    application.config['WTF_CSRF_ENABLED'] = False
    with application.app_context():
        db.create_all()
        _seed(application)
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _seed(app):
    """Create two operations, one super_admin, one user per operation."""
    from app.schedules.models import Stressor, HEG, SamplingSchedule, ExposureReading, MedicalRecord
    from app.employees.models import Employee

    op_a = Operation(operation_name='Operation Alpha', code='ALPHA', status='active')
    op_b = Operation(operation_name='Operation Beta',  code='BETA',  status='active')
    db.session.add_all([op_a, op_b])
    db.session.flush()

    super_admin = User(username='superadmin', email='super@test.com', role='super_admin', operation_id=None)
    super_admin.set_password('password')

    user_a = User(username='user_alpha', email='alpha@test.com', role='admin', operation_id=op_a.id)
    user_a.set_password('password')

    user_b = User(username='user_beta', email='beta@test.com', role='admin', operation_id=op_b.id)
    user_b.set_password('password')

    db.session.add_all([super_admin, user_a, user_b])
    db.session.flush()

    # Stressors per operation
    s_a = Stressor(name='Silica Dust', category='Chemical', operation_id=op_a.id, is_active=True, default_frequency='Annual')
    s_b = Stressor(name='Noise',       category='Physical', operation_id=op_b.id, is_active=True, default_frequency='Annual')
    db.session.add_all([s_a, s_b])
    db.session.flush()

    # Employees per operation
    e_a = Employee(name='Alice', job_title='Miner',    department='Mining', operation_id=op_a.id)
    e_b = Employee(name='Bob',   job_title='Operator', department='Ops',   operation_id=op_b.id)
    db.session.add_all([e_a, e_b])
    db.session.flush()

    # Medical records per operation
    m_a = MedicalRecord(employee_id=e_a.id, test_name='Lung Function', status='scheduled', operation_id=op_a.id)
    m_b = MedicalRecord(employee_id=e_b.id, test_name='Audiogram',     status='scheduled', operation_id=op_b.id)
    db.session.add_all([m_a, m_b])

    db.session.commit()


def _login(client, email, password='password'):
    return client.post('/api/auth/login', json={'email': email, 'password': password})


# ─── Authentication ───────────────────────────────────────────────────────────

class TestLogin:
    def test_super_admin_login(self, client):
        r = _login(client, 'super@test.com')
        assert r.status_code == 200
        data = r.get_json()
        assert data['user']['role'] == 'super_admin'
        assert data['user']['is_super_admin'] is True

    def test_operation_user_login_includes_operation(self, client):
        r = _login(client, 'alpha@test.com')
        assert r.status_code == 200
        data = r.get_json()
        assert data['user']['operation']['code'] == 'ALPHA'

    def test_login_bad_credentials(self, client):
        r = _login(client, 'alpha@test.com', 'wrong')
        assert r.status_code == 401


# ─── Data isolation ───────────────────────────────────────────────────────────

class TestDataIsolation:
    def test_employees_scoped_to_operation(self, client):
        _login(client, 'alpha@test.com')
        r = client.get('/api/employees')
        assert r.status_code == 200
        names = [e['name'] for e in r.get_json()]
        assert 'Alice' in names
        assert 'Bob' not in names

    def test_stressors_scoped_to_operation(self, client):
        _login(client, 'alpha@test.com')
        r = client.get('/api/stressors')
        assert r.status_code == 200
        names = [s['name'] for s in r.get_json()]
        assert 'Silica Dust' in names
        assert 'Noise' not in names

    def test_medical_records_scoped_to_operation(self, client):
        _login(client, 'beta@test.com')
        r = client.get('/api/medical-records')
        assert r.status_code == 200
        tests = [m['testName'] for m in r.get_json()]
        assert 'Audiogram' in tests
        assert 'Lung Function' not in tests

    def test_operation_b_cannot_see_operation_a_employees(self, client):
        _login(client, 'beta@test.com')
        r = client.get('/api/employees')
        names = [e['name'] for e in r.get_json()]
        assert 'Alice' not in names

    def test_new_employee_gets_operation_id(self, client):
        _login(client, 'alpha@test.com')
        r = client.post('/api/employees', json={'name': 'Charlie', 'jobTitle': 'Engineer', 'department': 'Eng'})
        assert r.status_code == 201
        from app.employees.models import Employee
        with client.application.app_context():
            emp = Employee.query.filter_by(name='Charlie').first()
            op  = Operation.query.filter_by(code='ALPHA').first()
            assert emp.operation_id == op.id

    def test_new_stressor_gets_operation_id(self, client):
        _login(client, 'alpha@test.com')
        r = client.post('/api/stressors', json={'name': 'Vibration', 'category': 'Physical'})
        assert r.status_code == 201
        from app.schedules.models import Stressor
        with client.application.app_context():
            s  = Stressor.query.filter_by(name='Vibration').first()
            op = Operation.query.filter_by(code='ALPHA').first()
            assert s.operation_id == op.id


# ─── Cross-operation access prevention ───────────────────────────────────────

class TestCrossOperationAccess:
    def _get_alpha_employee_id(self, client):
        with client.application.app_context():
            from app.employees.models import Employee
            op = Operation.query.filter_by(code='ALPHA').first()
            return Employee.query.filter_by(name='Alice', operation_id=op.id).first().id

    def _get_beta_medical_id(self, client):
        with client.application.app_context():
            from app.schedules.models import MedicalRecord
            op = Operation.query.filter_by(code='BETA').first()
            return MedicalRecord.query.filter_by(operation_id=op.id).first().id

    def test_op_b_cannot_update_op_a_employee(self, client):
        eid = self._get_alpha_employee_id(client)
        _login(client, 'beta@test.com')
        r = client.put(f'/api/employees/{eid}', json={'name': 'Hacked'})
        assert r.status_code == 403

    def test_op_b_cannot_delete_op_a_employee(self, client):
        eid = self._get_alpha_employee_id(client)
        _login(client, 'beta@test.com')
        r = client.delete(f'/api/employees/{eid}')
        assert r.status_code == 403

    def test_op_a_cannot_update_op_b_medical_record(self, client):
        mid = self._get_beta_medical_id(client)
        _login(client, 'alpha@test.com')
        r = client.put(f'/api/medical-records/{mid}', json={'status': 'completed'})
        assert r.status_code == 403

    def test_op_a_cannot_delete_op_b_medical_record(self, client):
        mid = self._get_beta_medical_id(client)
        _login(client, 'alpha@test.com')
        r = client.delete(f'/api/medical-records/{mid}')
        assert r.status_code == 403


# ─── Super Admin access ───────────────────────────────────────────────────────

class TestSuperAdminAccess:
    def test_super_admin_sees_all_employees(self, client):
        _login(client, 'super@test.com')
        r = client.get('/api/employees')
        assert r.status_code == 200
        names = [e['name'] for e in r.get_json()]
        assert 'Alice' in names
        assert 'Bob' in names

    def test_super_admin_sees_all_stressors(self, client):
        _login(client, 'super@test.com')
        r = client.get('/api/stressors')
        assert r.status_code == 200
        names = [s['name'] for s in r.get_json()]
        assert 'Silica Dust' in names
        assert 'Noise' in names

    def test_super_admin_can_list_operations(self, client):
        _login(client, 'super@test.com')
        r = client.get('/api/operations')
        assert r.status_code == 200
        codes = [o['code'] for o in r.get_json()]
        assert 'ALPHA' in codes
        assert 'BETA' in codes

    def test_super_admin_can_create_operation(self, client):
        _login(client, 'super@test.com')
        r = client.post('/api/operations', json={
            'operation_name': 'Operation Gamma',
            'code': 'GAMMA',
            'location': 'Test Site',
        })
        assert r.status_code == 201
        assert r.get_json()['code'] == 'GAMMA'

    def test_operation_admin_cannot_access_operations_endpoint(self, client):
        _login(client, 'alpha@test.com')
        r = client.get('/api/operations')
        assert r.status_code == 403

    def test_operation_admin_cannot_create_operation(self, client):
        _login(client, 'alpha@test.com')
        r = client.post('/api/operations', json={'operation_name': 'Hack', 'code': 'HACK'})
        assert r.status_code == 403


# ─── Reports isolation (via medical records as proxy) ────────────────────────

class TestReportIsolation:
    def test_alpha_medical_records_not_in_beta_view(self, client):
        _login(client, 'beta@test.com')
        r = client.get('/api/medical-records')
        tests = [m['testName'] for m in r.get_json()]
        assert 'Lung Function' not in tests

    def test_beta_medical_records_not_in_alpha_view(self, client):
        _login(client, 'alpha@test.com')
        r = client.get('/api/medical-records')
        tests = [m['testName'] for m in r.get_json()]
        assert 'Audiogram' not in tests
