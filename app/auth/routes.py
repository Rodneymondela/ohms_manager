from flask import render_template, redirect, url_for, flash, request, current_app # Added current_app
from flask_login import login_user, logout_user, current_user, login_required
from app import db, bcrypt # Anticipating these are initialized in app factory
from app.models import User
from app.forms import LoginForm, RegistrationForm, RequestResetForm, ResetPasswordForm
from app.auth.email import send_password_reset_email # Added email sending utility
from . import auth_bp # Import the blueprint itself
from datetime import datetime
from sqlalchemy.exc import IntegrityError

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index')) # Assuming index will be in 'main' blueprint
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data

        user = User(username=username, email=email)
        try:
            user.set_password(password)
        except ValueError as e:
            current_app.logger.warning(f'User registration failed for {form.username.data} due to password validation: {str(e)}')
            flash(str(e), 'danger')
            return render_template('auth/register.html', form=form, title='Register')

        try:
            db.session.add(user)
            db.session.commit()
            current_app.logger.info(f'New user {user.username} (ID: {user.id}, Email: {user.email}) registered successfully.')
            flash('Your account has been created! You are now able to log in.', 'success')
            return redirect(url_for('auth.login'))
        except IntegrityError:
            db.session.rollback()
            current_app.logger.warning(f'User registration failed for {form.username.data} due to IntegrityError (likely duplicate username/email).')
            existing_user_username = User.query.filter_by(username=form.username.data).first()
            existing_user_email = User.query.filter_by(email=form.email.data).first()
            if existing_user_username:
                flash('Username already exists. Please choose a different one.', 'danger')
            elif existing_user_email:
                flash('Email already registered. Please use a different one or log in.', 'danger')
            else:
                flash('An unexpected error occurred. Please try again.', 'danger') # This could be more specific if other IntegrityErrors are possible
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'An unexpected error occurred during registration for {form.username.data}: {str(e)}', exc_info=True)
            flash(f'An error occurred: {str(e)}', 'danger')

    return render_template('auth/register.html', form=form, title='Register')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index')) # Assuming 'main.index'
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        remember = form.remember.data

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            try:
                db.session.commit()
                current_app.logger.info(f'User {user.username} (ID: {user.id}) logged in successfully.')
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f'Error updating last_login for user {user.username}: {e}', exc_info=True) # Added exc_info
                flash(f'Error updating last login: {e}', 'warning')
            next_page = request.args.get('next')
            # Ensure next_page is safe, prevent open redirect
            if next_page and not (next_page.startswith('/') or next_page.startswith(request.host_url)):
                next_page = None
            return redirect(next_page or url_for('main.index')) # Assuming 'main.index'
        else:
            current_app.logger.warning(f'Failed login attempt for username: {form.username.data}')
            flash('Login Unsuccessful. Please check username and password.', 'danger')
    return render_template('auth/login.html', form=form, title='Login')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/request_reset', methods=['GET', 'POST'])
def request_reset_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.get_reset_token()
            # The get_reset_token method updates user's reset_token and reset_token_expires fields.
            # These changes need to be committed to the database.
            db.session.commit()
            send_password_reset_email(user, token)
            current_app.logger.info(f'Password reset requested for user {user.username} (ID: {user.id}, Email: {user.email}). Reset email sent.')
            flash('If an account with that email exists, instructions to reset your password have been sent.', 'info')
        else:
            # Still flash a generic message to prevent email enumeration
            flash('If an account with that email exists, instructions to reset your password have been sent.', 'info')
        return redirect(url_for('auth.login')) # Redirect to login page in either case
    return render_template('auth/request_reset_form.html', title='Request Password Reset', form=form)

@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_with_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    user = User.verify_reset_token(token)
    if not user:
        flash('That is an invalid or expired token. Please try requesting a reset again.', 'warning')
        return redirect(url_for('auth.request_reset_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        try:
            user.set_password(form.password.data)
            user.reset_token = None
            user.reset_token_expires = None
            db.session.commit()
            current_app.logger.info(f'Password for user {user.username} (ID: {user.id}) has been successfully reset.')
            flash('Your password has been successfully updated! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        except ValueError as e: # Catch password validation errors from User.set_password()
            current_app.logger.warning(f'Password reset for user {user.username} failed due to new password validation: {str(e)}')
            flash(str(e), 'danger')
            # No redirect here, re-render the form so user can see the password error
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'An unexpected error occurred while resetting password for user {user.username}: {str(e)}', exc_info=True)
            flash(f'An unexpected error occurred: {str(e)}', 'danger')
            # No redirect here either, re-render form

    return render_template('auth/reset_password_form.html', title='Reset Your Password', form=form, token=token)
