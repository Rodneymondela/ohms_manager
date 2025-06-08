from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app import db, bcrypt # Anticipating these are initialized in app factory
from app.models import User
from app.forms import LoginForm, RegistrationForm
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
            flash(str(e), 'danger')
            return render_template('auth/register.html', form=form, title='Register')

        try:
            db.session.add(user)
            db.session.commit()
            flash('Your account has been created! You are now able to log in.', 'success')
            return redirect(url_for('auth.login'))
        except IntegrityError:
            db.session.rollback()
            existing_user_username = User.query.filter_by(username=form.username.data).first()
            existing_user_email = User.query.filter_by(email=form.email.data).first()
            if existing_user_username:
                flash('Username already exists. Please choose a different one.', 'danger')
            elif existing_user_email:
                flash('Email already registered. Please use a different one or log in.', 'danger')
            else:
                flash('An unexpected error occurred. Please try again.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {e}', 'danger')

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
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating last login: {e}', 'warning')
            next_page = request.args.get('next')
            # Ensure next_page is safe, prevent open redirect
            if next_page and not (next_page.startswith('/') or next_page.startswith(request.host_url)):
                next_page = None
            return redirect(next_page or url_for('main.index')) # Assuming 'main.index'
        else:
            flash('Login Unsuccessful. Please check username and password.', 'danger')
    return render_template('auth/login.html', form=form, title='Login')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
