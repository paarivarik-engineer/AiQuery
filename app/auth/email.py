from flask import render_template, current_app
from flask_mail import Message
from app import mail # Import the mail instance from app/__init__.py
from threading import Thread

def send_async_email(app, msg):
    """Sends email asynchronously in a separate thread."""
    with app.app_context():
        try:
            mail.send(msg)
            current_app.logger.info(f"Email sent successfully to {msg.recipients}")
        except Exception as e:
            current_app.logger.error(f"Failed to send email to {msg.recipients}: {e}")

def send_password_reset_email(user):
    """Generates token and sends password reset email."""
    token = user.get_reset_password_token()
    app = current_app._get_current_object() # Get the actual app instance for the thread
    msg = Message('Password Reset Request - AIQuery',
                  sender=app.config['MAIL_DEFAULT_SENDER'],
                  recipients=[user.email])
    msg.body = render_template('auth/email/reset_password.txt',
                               user=user, token=token)
    msg.html = render_template('auth/email/reset_password.html',
                               user=user, token=token)
    # Send email asynchronously
    Thread(target=send_async_email, args=(app, msg)).start()
    current_app.logger.info(f"Password reset email queued for {user.email}")
