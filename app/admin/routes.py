from flask import render_template, flash, redirect, url_for, request, current_app # Added current_app
from flask_login import current_user
from app.models import User, ROLE_ADMIN
from app.forms import EditUserForm
from app import db
from . import admin_bp
# login_required and role checks are handled by the blueprint's before_request hook.

@admin_bp.route('/')
@admin_bp.route('/users')
def list_users():
    page_title = "User Management"
    users = User.query.order_by(User.id).all()
    return render_template('list_users.html', users=users, title=page_title)

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
def edit_user_role_status(user_id):
    user_to_edit = User.query.get_or_404(user_id)
    # Pass current user's data to the form if it's a GET request
    form = EditUserForm(obj=user_to_edit if request.method == 'GET' else None)

    # Set choices dynamically (already done in form definition, but ensure it's correct)
    # form.role.choices = [(ROLE_ADMIN, 'Admin'), (ROLE_USER, 'User')] -> This is now set in forms.py

    if request.method == 'GET':
        # Pre-populate form fields correctly for obj with different attribute names or types
        form.role.data = user_to_edit.role
        form.is_active.data = user_to_edit.is_active

    if form.validate_on_submit():
        # Safeguard: Prevent admin from deactivating self or changing own role from admin
        if user_to_edit.id == current_user.id:
            if not form.is_active.data and user_to_edit.is_active: # Check if trying to deactivate
                flash('You cannot deactivate your own account.', 'danger')
                return redirect(url_for('admin.list_users'))
            if form.role.data != ROLE_ADMIN and user_to_edit.role == ROLE_ADMIN:
                flash('You cannot remove your own admin role.', 'danger')
                return redirect(url_for('admin.list_users'))

        user_to_edit.role = form.role.data
        user_to_edit.is_active = form.is_active.data
        try:
            db.session.commit()
            flash(f"User '{user_to_edit.username}' (ID: {user_to_edit.id}) has been updated.", 'success')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'An unexpected error occurred while updating user ID {user_id}: {str(e)}', exc_info=True)
            flash(f'Error updating user: {str(e)}', 'danger')
        return redirect(url_for('admin.list_users'))

    return render_template('edit_user.html', form=form, user_to_edit=user_to_edit, title=f"Edit User: {user_to_edit.username}")

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
# Admin access is handled by admin_bp.before_request via require_admin_access
def delete_user(user_id):
    user_to_delete = User.query.get_or_404(user_id)

    # Safeguard: Prevent admin from deleting their own account
    if user_to_delete.id == current_user.id:
        flash('You cannot delete your own administrator account.', 'danger')
        return redirect(url_for('admin.list_users'))

    try:
        # Deleting the user will trigger 'ondelete=SET NULL'
        # for recorded_by fields in Exposure and HealthRecord models.
        db.session.delete(user_to_delete)
        db.session.commit()
        flash(f'User {user_to_delete.username} (ID: {user_to_delete.id}) has been deleted. Associated records (Exposures, Health Records) recorded by this user will have their recorder field set to NULL.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting user {user_to_delete.username}: {str(e)}', exc_info=True)
        flash(f'Error deleting user: {str(e)}', 'danger')

    return redirect(url_for('admin.list_users'))
