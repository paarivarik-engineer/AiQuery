from flask import render_template, redirect, url_for, flash, request, current_app # Added current_app
from urllib.parse import urlparse # Use Python's built-in urlparse
from flask_login import login_user, logout_user, current_user
from app import db
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm # Added reset forms
from app.models import User
from app.auth.email import send_password_reset_email # Import email function
import os # For checking admin email
import logging # Import standard logging

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index')) # Redirect logged-in users
    form = LoginForm()
    if form.validate_on_submit():
        login_identifier = form.username.data # Input can be username or email
        # Try finding user by username OR email
        user = db.session.scalar(
            db.select(User).where(
                (User.username == login_identifier) | (User.email == login_identifier)
            )
        )
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username/email or password') # Updated flash message
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        # Security: Ensure next_page is a relative path using urlparse
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('main.index') # Default redirect after login
        flash(f'Welcome back, {user.username}!')
        return redirect(next_page)
    return render_template('auth/login.html', title='Sign In', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index')) # Redirect to home page after logout

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        # Check if this is the admin user based on email in config
        # Get the CLEANED email from Flask config, not directly from os.environ
        admin_email = current_app.config.get('ADMIN_EMAIL') 
        
        # --- MORE DEBUGGING ---
        logger = logging.getLogger(__name__) # Get logger instance
        logger.info(f"DEBUG: Comparing user email '{user.email}' (Form Input) with admin email '{admin_email}' (From .env)")
        logger.info(f"DEBUG: Lowercase stripped user email: '{user.email.strip().lower()}'")
        logger.info(f"DEBUG: Lowercase stripped admin email: '{admin_email.strip().lower() if admin_email else 'None'}'")
        # --- END MORE DEBUGGING ---

        # Make comparison case-insensitive and strip whitespace
        if admin_email and user.email.strip().lower() == admin_email.strip().lower():
            logger.info(f"ADMIN CHECK PASSED: Setting is_admin=True for {user.email}") # Log inside condition
            user.is_admin = True
            flash(f'Admin user {user.username} registered successfully!')
        else:
             flash(f'User {user.username} registered successfully!')
        
        # --- DEBUGGING ---
        logger = logging.getLogger(__name__) # Use standard logging here too
        logger.info(f"Registering user: {user.username}, Email: {user.email}, Is Admin: {user.is_admin}")
        # --- END DEBUGGING ---

        db.session.add(user)
        db.session.commit()
        logger.info(f"User {user.username} committed to DB with is_admin={user.is_admin}") # Log after commit
        # Log in the user automatically after registration
        login_user(user)
        return redirect(url_for('main.index')) # Redirect to home after registration
    return render_template('auth/register.html', title='Register', form=form)

@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    """Handles request to reset password."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = db.session.scalar(db.select(User).where(User.email == form.email.data))
        if user:
            send_password_reset_email(user)
            flash('Check your email for instructions to reset your password.', 'info')
        else:
            # Don't reveal if email exists or not for security
            flash('If an account with that email exists, instructions have been sent.', 'info')
        # Always redirect to login to prevent info leakage
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_request.html',
                           title='Reset Password', form=form)

@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Handles the actual password reset using the token."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = User.verify_reset_password_token(token)
    if not user:
        flash('The password reset link is invalid or has expired.', 'warning')
        return redirect(url_for('auth.reset_password_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset successfully.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', title='Reset Password', form=form)
