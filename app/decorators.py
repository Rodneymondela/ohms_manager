from functools import wraps
from flask import flash, redirect, url_for, request
from flask_login import current_user
from app.models import ROLE_ADMIN

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.path.startswith('/api/'):
                from app.api import api_restx
                api_restx.abort(401, 'Authentication required')
            flash('Please log in to access this page.', 'info')
            next_url = request.path if request else None
            return redirect(url_for('auth.login', next=next_url))

        if getattr(current_user, 'role', None) != ROLE_ADMIN:
            if request.path.startswith('/api/'):
                from app.api import api_restx
                api_restx.abort(403, 'Administrator access required')
            flash('You do not have permission to access this page. (Administrators only)', 'danger')
            return redirect(url_for('main.index'))

        return f(*args, **kwargs)
    return decorated_function
