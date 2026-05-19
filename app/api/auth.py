"""
Authentication endpoints  —  /api/auth/*
Uses Flask-Login session cookies (forwarded transparently by the Vite proxy).
"""

import os
from flask import request, jsonify, current_app
from flask_login import login_user, logout_user, current_user, login_required
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from app.api import api_bp
from app.models import User, Operation, ROLES
from app import db


def _make_invite_token(user_id):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return s.dumps(user_id, salt='invite')


def _verify_invite_token(token, max_age=72 * 3600):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        return s.loads(token, salt='invite', max_age=max_age), None
    except SignatureExpired:
        return None, 'Invite link has expired. Ask your administrator to resend it.'
    except BadSignature:
        return None, 'Invalid invite link.'


def _make_reset_token(user_id):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return s.dumps(user_id, salt='reset')


def _verify_reset_token(token, max_age=3600):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        return s.loads(token, salt='reset', max_age=max_age), None
    except SignatureExpired:
        return None, 'Reset link has expired. Please request a new one.'
    except BadSignature:
        return None, 'Invalid reset link.'


def _send_invite(user):
    from app.email import send_invite_email
    token = _make_invite_token(user.id)
    app_url = os.environ.get('APP_URL', 'http://localhost:5173').rstrip('/')
    invite_url = f"{app_url}/set-password?token={token}"
    op_name = None
    if user.operation_id:
        op = Operation.query.get(user.operation_id)
        op_name = op.operation_name if op else None
    send_invite_email(user.email, user.username, invite_url, op_name)


def _user_dict(u):
    op = None
    if u.operation_id:
        op_obj = Operation.query.get(u.operation_id)
        if op_obj:
            op = {'id': op_obj.id, 'operation_name': op_obj.operation_name, 'code': op_obj.code}
    return {
        'id':           u.id,
        'username':     u.username,
        'email':        u.email,
        'role':         u.role,
        'is_admin':       u.role in ('admin', 'super_admin'),
        'is_super_admin': u.role == 'super_admin',
        'operation_id':   u.operation_id,
        'operation':      op,
        'invite_pending': u.invite_pending,
    }


def _can_manage_users():
    """Admin and super_admin can manage users."""
    return current_user.role in ('admin', 'super_admin')


def _admin_or_super():
    if not _can_manage_users():
        return jsonify({'error': 'Admin access required'}), 403
    return None


@api_bp.route('/auth/login', methods=['POST'])
def login():
    data     = request.get_json(silent=True) or {}
    email    = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if not email or not password:
        return jsonify({'error': 'email and password are required'}), 400

    user = User.query.filter_by(email=email).first()
    if user and user.invite_pending:
        return jsonify({'error': 'Please check your email and click the invite link to set your password before logging in.'}), 401
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid email or password'}), 401

    # Block login for users with no operation unless super_admin
    if user.role != 'super_admin' and not user.operation_id:
        return jsonify({'error': 'Your account is not assigned to an operation. Contact your administrator.'}), 403

    login_user(user, remember=True)
    return jsonify({'user': _user_dict(user)})


@api_bp.route('/auth/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'ok': True})


@api_bp.route('/auth/me', methods=['GET'])
@login_required
def me():
    return jsonify(_user_dict(current_user))


# ── User management ───────────────────────────────────────────────────────────

@api_bp.route('/users', methods=['GET'])
@login_required
def list_users():
    err = _admin_or_super()
    if err:
        return err
    if current_user.role == 'super_admin':
        users = User.query.order_by(User.username).all()
    else:
        # Operation admin sees only users in their operation
        users = User.query.filter_by(operation_id=current_user.operation_id).order_by(User.username).all()
    return jsonify([_user_dict(u) for u in users])


@api_bp.route('/users', methods=['POST'])
@login_required
def create_user():
    err = _admin_or_super()
    if err:
        return err
    data     = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    email    = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    role     = data.get('role', 'viewer')

    if not username or not email:
        return jsonify({'error': 'username and email are required'}), 400
    if role not in ROLES:
        return jsonify({'error': f'role must be one of: {", ".join(ROLES)}'}), 400

    # Operation admins cannot create super_admin accounts
    if current_user.role == 'admin' and role == 'super_admin':
        return jsonify({'error': 'Operation admins cannot create Super Admin accounts'}), 403

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already in use'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already in use'}), 400

    # Determine operation: super_admin can specify; admin forces their own op
    if current_user.role == 'super_admin':
        op_id = data.get('operation_id') or None
    else:
        op_id = current_user.operation_id

    u = User(
        username=username,
        email=email,
        role=role,
        is_admin=(role in ('admin', 'super_admin')),
        operation_id=op_id,
    )
    if password:
        u.set_password(password)
    else:
        u.password_hash = 'INVITE_PENDING'
    db.session.add(u)
    db.session.commit()

    if u.invite_pending:
        try:
            _send_invite(u)
        except Exception as e:
            current_app.logger.error(f"Invite email failed for user {u.id}: {e}")

    return jsonify(_user_dict(u)), 201


@api_bp.route('/users/<int:uid>', methods=['PUT'])
@login_required
def update_user(uid):
    err = _admin_or_super()
    if err:
        return err
    u = User.query.get_or_404(uid)

    # Operation admin can only manage users in their operation
    if current_user.role == 'admin' and u.operation_id != current_user.operation_id:
        return jsonify({'error': 'Access denied'}), 403

    data = request.get_json(silent=True) or {}

    if 'username' in data:
        u.username = data['username'].strip()
    if 'email' in data:
        u.email = data['email'].strip().lower()
    if 'role' in data:
        new_role = data['role']
        if new_role not in ROLES:
            return jsonify({'error': f'role must be one of: {", ".join(ROLES)}'}), 400
        if current_user.role == 'admin' and new_role == 'super_admin':
            return jsonify({'error': 'Operation admins cannot assign Super Admin role'}), 403
        u.role     = new_role
        u.is_admin = (new_role in ('admin', 'super_admin'))
    if data.get('password'):
        u.set_password(data['password'])
    # Super admin can reassign operation
    if current_user.role == 'super_admin' and 'operation_id' in data:
        u.operation_id = data['operation_id'] or None

    db.session.commit()
    return jsonify(_user_dict(u))


# ── Invite / set-password (public endpoints, no login required) ───────────────

@api_bp.route('/auth/invite-info/<token>', methods=['GET'])
def invite_info(token):
    user_id, err = _verify_invite_token(token)
    if err:
        return jsonify({'error': err}), 400
    u = User.query.get(user_id)
    if not u:
        return jsonify({'error': 'User not found.'}), 404
    if not u.invite_pending:
        return jsonify({'error': 'This invite has already been used.'}), 400
    return jsonify({'username': u.username, 'email': u.email})


@api_bp.route('/auth/set-password', methods=['POST'])
def set_password_via_invite():
    data     = request.get_json(silent=True) or {}
    token    = data.get('token', '')
    password = data.get('password', '')
    if not token or not password:
        return jsonify({'error': 'token and password are required'}), 400
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400
    user_id, err = _verify_invite_token(token)
    if err:
        return jsonify({'error': err}), 400
    u = User.query.get(user_id)
    if not u:
        return jsonify({'error': 'User not found.'}), 404
    if not u.invite_pending:
        return jsonify({'error': 'This invite has already been used.'}), 400
    u.set_password(password)
    db.session.commit()
    return jsonify({'ok': True})


# ── Password reset (public endpoints) ────────────────────────────────────────

@api_bp.route('/auth/forgot-password', methods=['POST'])
def forgot_password():
    data  = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    # Always return ok — never reveal whether email exists
    if email:
        u = User.query.filter_by(email=email).first()
        if u:
            try:
                from app.email import send_reset_email
                token     = _make_reset_token(u.id)
                app_url   = os.environ.get('APP_URL', 'http://localhost:5173').rstrip('/')
                reset_url = f"{app_url}/set-password?token={token}&type=reset"
                send_reset_email(u.email, u.username, reset_url)
            except Exception as e:
                current_app.logger.error(f"Reset email failed for {email}: {e}")
    return jsonify({'ok': True})


@api_bp.route('/auth/reset-info/<token>', methods=['GET'])
def reset_info(token):
    user_id, err = _verify_reset_token(token)
    if err:
        return jsonify({'error': err}), 400
    u = User.query.get(user_id)
    if not u:
        return jsonify({'error': 'User not found.'}), 404
    return jsonify({'username': u.username, 'email': u.email})


@api_bp.route('/auth/reset-password', methods=['POST'])
def reset_password_via_token():
    data     = request.get_json(silent=True) or {}
    token    = data.get('token', '')
    password = data.get('password', '')
    if not token or not password:
        return jsonify({'error': 'token and password are required'}), 400
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400
    user_id, err = _verify_reset_token(token)
    if err:
        return jsonify({'error': err}), 400
    u = User.query.get(user_id)
    if not u:
        return jsonify({'error': 'User not found.'}), 404
    u.set_password(password)
    db.session.commit()
    return jsonify({'ok': True})


@api_bp.route('/users/<int:uid>', methods=['DELETE'])
@login_required
def delete_user(uid):
    err = _admin_or_super()
    if err:
        return err
    if uid == current_user.id:
        return jsonify({'error': 'Cannot delete your own account'}), 400
    u = User.query.get_or_404(uid)
    # Operation admin can only delete users in their operation
    if current_user.role == 'admin' and u.operation_id != current_user.operation_id:
        return jsonify({'error': 'Access denied'}), 403
    db.session.delete(u)
    db.session.commit()
    return jsonify({'deleted': uid})
