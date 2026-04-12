"""
Authentication endpoints  —  /api/auth/*
Uses Flask-Login session cookies (forwarded transparently by the Vite proxy).
"""

from flask import request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from app.api import api_bp
from app.models import User


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
    return jsonify({
        'user': {
            'id':       user.id,
            'username': user.username,
            'email':    user.email,
            'is_admin': user.is_admin,
        }
    })


@api_bp.route('/auth/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'ok': True})


@api_bp.route('/auth/me', methods=['GET'])
@login_required
def me():
    return jsonify({
        'id':       current_user.id,
        'username': current_user.username,
        'email':    current_user.email,
        'is_admin': current_user.is_admin,
    })
