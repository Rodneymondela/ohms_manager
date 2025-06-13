from flask import Blueprint, flash, redirect, url_for
from flask_login import current_user, login_required
from app.models import ROLE_ADMIN

admin_bp = Blueprint('admin',
                     __name__,
                     url_prefix='/admin',
                     template_folder='templates') # Looks for templates in app/admin/templates/

@admin_bp.before_request
@login_required # Ensures user is logged in before checking admin role
def require_admin_access():
    # Check if current_user has the admin role
    # getattr is used to safely access 'role', defaulting to None if not present
    if getattr(current_user, 'role', None) != ROLE_ADMIN:
        flash('You must be an administrator to access this page.', 'danger')
        return redirect(url_for('main.index')) # Redirect non-admins to the main index page

from . import routes  # Import routes after blueprint and before_request are defined
