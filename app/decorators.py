from functools import wraps
from flask import flash, redirect, url_for, request
from flask_login import current_user
from app.models import ROLE_ADMIN # Import ROLE_ADMIN from app.models

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            # This case is primarily handled by @login_required, which should ideally
            # be used in conjunction with @admin_required (applied first).
            # This is a fallback.
            flash('Please log in to access this page.', 'info')
            # request.path might not be available if there's no active request context
            # (e.g. if decorator is somehow called outside a request).
            # However, for a route decorator, it should be fine.
            next_url = request.path if request else None
            return redirect(url_for('auth.login', next=next_url))

        if getattr(current_user, 'role', None) != ROLE_ADMIN:
            flash('You do not have permission to access this page. (Administrators only)', 'danger')
            return redirect(url_for('main.index')) # Redirect to a general page like home

        return f(*args, **kwargs)
    return decorated_function
