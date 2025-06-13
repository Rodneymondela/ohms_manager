from flask_mail import Message
from app import mail # Assuming mail is the Flask-Mail instance from app/__init__.py
from flask import render_template, url_for, current_app

def send_password_reset_email(user, token):
    """
    Sends a password reset email to the user.
    """
    reset_url = url_for('auth.reset_with_token', token=token, _external=True)

    # The email template will be created in a subsequent step.
    # For now, this assumes 'auth/email/reset_password_email.html' will exist.
    html_body = render_template('auth/email/reset_password_email.html',
                                user=user, reset_url=reset_url)

    # Using current_app.config for sender to ensure it's from the initialized app context
    sender_email = current_app.config.get('MAIL_DEFAULT_SENDER', current_app.config.get('MAIL_USERNAME'))
    if not sender_email:
        # Fallback or error if no sender is configured
        # This case should ideally be handled by app configuration validation
        current_app.logger.error("MAIL_DEFAULT_SENDER or MAIL_USERNAME not configured.")
        # Depending on policy, either raise error or don't send email
        return

    msg = Message(
        subject="Password Reset Request - OHMS",
        sender=sender_email,
        recipients=[user.email],
        html=html_body
    )

    try:
        mail.send(msg)
        current_app.logger.info(f'Password reset email successfully sent to {user.email} for user {user.username} (ID: {user.id}).')
    except Exception as e:
        # Log the error for debugging, include exc_info for full traceback in logs
        current_app.logger.error(f"Failed to send password reset email to {user.email}: {e}", exc_info=True)
        # Optionally, re-raise or handle as appropriate for the application
        # For now, we'll let it fail silently in the background after logging,
        # as the user-facing message is generic.
        pass
