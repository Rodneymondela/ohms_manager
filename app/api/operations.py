"""
Operations endpoints  —  /api/operations/*
Super Admin only — manages tenant operations and user assignments.
"""

from datetime import datetime
from flask import request, jsonify
from flask_login import login_required, current_user
from app.api import api_bp
from app import db
from app.models import Operation, User, ROLES


def _super_admin_required():
    if current_user.role != 'super_admin':
        return jsonify({'error': 'Super Admin access required'}), 403
    return None


# ── Operations CRUD ───────────────────────────────────────────────────────────

@api_bp.route('/operations', methods=['GET'])
@login_required
def list_operations():
    err = _super_admin_required()
    if err:
        return err
    ops = Operation.query.order_by(Operation.operation_name).all()
    result = []
    for op in ops:
        d = op.to_dict()
        d['user_count'] = User.query.filter_by(operation_id=op.id).count()
        result.append(d)
    return jsonify(result)


@api_bp.route('/operations', methods=['POST'])
@login_required
def create_operation():
    err = _super_admin_required()
    if err:
        return err
    data = request.get_json(silent=True) or {}
    if not data.get('operation_name') or not data.get('code'):
        return jsonify({'error': 'operation_name and code are required'}), 400
    code = data['code'].upper().strip()
    if Operation.query.filter_by(code=code).first():
        return jsonify({'error': 'Code already in use'}), 400

    op = Operation(
        operation_name=data['operation_name'].strip(),
        code=code,
        location=data.get('location') or None,
        status=data.get('status', 'active'),
    )
    db.session.add(op)
    db.session.commit()
    d = op.to_dict()
    d['user_count'] = 0
    return jsonify(d), 201


@api_bp.route('/operations/<int:oid>', methods=['PUT'])
@login_required
def update_operation(oid):
    err = _super_admin_required()
    if err:
        return err
    op = Operation.query.get_or_404(oid)
    data = request.get_json(silent=True) or {}

    if 'operation_name' in data:
        op.operation_name = data['operation_name'].strip()
    if 'code' in data:
        new_code = data['code'].upper().strip()
        existing = Operation.query.filter_by(code=new_code).first()
        if existing and existing.id != oid:
            return jsonify({'error': 'Code already in use'}), 400
        op.code = new_code
    if 'location' in data:
        op.location = data['location'] or None
    if 'status' in data:
        op.status = data['status']
    op.updated_at = datetime.utcnow()
    db.session.commit()
    d = op.to_dict()
    d['user_count'] = User.query.filter_by(operation_id=op.id).count()
    return jsonify(d)


@api_bp.route('/operations/<int:oid>/deactivate', methods=['POST'])
@login_required
def deactivate_operation(oid):
    err = _super_admin_required()
    if err:
        return err
    op = Operation.query.get_or_404(oid)
    op.status = 'inactive'
    op.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify(op.to_dict())


@api_bp.route('/operations/<int:oid>/activate', methods=['POST'])
@login_required
def activate_operation(oid):
    err = _super_admin_required()
    if err:
        return err
    op = Operation.query.get_or_404(oid)
    op.status = 'active'
    op.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify(op.to_dict())


# ── Users across all operations (super admin view) ────────────────────────────

@api_bp.route('/operations/users', methods=['GET'])
@login_required
def list_all_users():
    err = _super_admin_required()
    if err:
        return err
    users = User.query.order_by(User.username).all()
    ops   = {o.id: o for o in Operation.query.all()}
    return jsonify([_full_user_dict(u, ops) for u in users])


@api_bp.route('/operations/users/<int:uid>/assign', methods=['POST'])
@login_required
def assign_user_operation(uid):
    err = _super_admin_required()
    if err:
        return err
    u    = User.query.get_or_404(uid)
    data = request.get_json(silent=True) or {}
    op_id = data.get('operation_id')
    if op_id is not None and not Operation.query.get(op_id):
        return jsonify({'error': 'Operation not found'}), 404
    u.operation_id = op_id
    db.session.commit()
    ops = {o.id: o for o in Operation.query.all()}
    return jsonify(_full_user_dict(u, ops))


def _full_user_dict(u, ops_by_id=None):
    op = None
    if u.operation_id and ops_by_id:
        op_obj = ops_by_id.get(u.operation_id)
        if op_obj:
            op = {'id': op_obj.id, 'operation_name': op_obj.operation_name, 'code': op_obj.code}
    return {
        'id':             u.id,
        'username':       u.username,
        'email':          u.email,
        'role':           u.role,
        'is_admin':       u.role in ('admin', 'super_admin'),
        'operation_id':   u.operation_id,
        'operation':      op,
        'invite_pending': u.invite_pending,
    }


@api_bp.route('/operations/users/<int:uid>/resend-invite', methods=['POST'])
@login_required
def resend_invite(uid):
    err = _super_admin_required()
    if err:
        return err
    u = User.query.get_or_404(uid)
    if not u.invite_pending:
        return jsonify({'error': 'User has already set their password.'}), 400
    try:
        from app.api.auth import _send_invite
        _send_invite(u)
    except Exception as e:
        return jsonify({'error': f'Failed to send email: {e}'}), 500
    return jsonify({'ok': True})
