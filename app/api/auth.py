"""
Authentication endpoints  —  /api/auth/*
Uses Flask-Login session cookies (forwarded transparently by the Vite proxy).
"""

from flask import request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from app.api import api_bp
from app.models import User, ROLES
from app import db


@api_bp.route('/auth/login', methods=['POST'])
def login():
    data     = request.get_json(silent=True) or {}
    email    = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if not email or not password:
        return jsonify({'error': 'email and password are required'}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid email or password'}), 401

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


def _user_dict(u):
    return {
        'id':       u.id,
        'username': u.username,
        'email':    u.email,
        'role':     u.role,
        'is_admin': u.role == 'admin',
    }


def _admin_required():
    if current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    return None


# ── User management (admin only) ─────────────────────────────────────────────

@api_bp.route('/users', methods=['GET'])
@login_required
def list_users():
    err = _admin_required()
    if err: return err
    return jsonify([_user_dict(u) for u in User.query.order_by(User.username).all()])


@api_bp.route('/users', methods=['POST'])
@login_required
def create_user():
    err = _admin_required()
    if err: return err
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    email    = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    role     = data.get('role', 'viewer')

    if not username or not email or not password:
        return jsonify({'error': 'username, email and password are required'}), 400
    if role not in ROLES:
        return jsonify({'error': f'role must be one of: {", ".join(ROLES)}'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already in use'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already in use'}), 400

    u = User(username=username, email=email, role=role, is_admin=(role == 'admin'))
    u.set_password(password)
    db.session.add(u)
    db.session.commit()
    return jsonify(_user_dict(u)), 201


@api_bp.route('/users/<int:uid>', methods=['PUT'])
@login_required
def update_user(uid):
    err = _admin_required()
    if err: return err
    u = User.query.get_or_404(uid)
    data = request.get_json(silent=True) or {}

    if 'username' in data:
        u.username = data['username'].strip()
    if 'email' in data:
        u.email = data['email'].strip().lower()
    if 'role' in data:
        if data['role'] not in ROLES:
            return jsonify({'error': f'role must be one of: {", ".join(ROLES)}'}), 400
        u.role     = data['role']
        u.is_admin = (data['role'] == 'admin')
    if data.get('password'):
        u.set_password(data['password'])

    db.session.commit()
    return jsonify(_user_dict(u))


@api_bp.route('/users/<int:uid>', methods=['DELETE'])
@login_required
def delete_user(uid):
    err = _admin_required()
    if err: return err
    if uid == current_user.id:
        return jsonify({'error': 'Cannot delete your own account'}), 400
    u = User.query.get_or_404(uid)
    db.session.delete(u)
    db.session.commit()
    return jsonify({'deleted': uid})
