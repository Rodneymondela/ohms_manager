import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


def send_invite_email(to_email, username, invite_url, operation_name=None):
    op_line = f"\nOperation: {operation_name}\n" if operation_name else ""
    body = f"""Hi {username},

You have been invited to access OHMS Manager — Occupational Hygiene & Medical Surveillance.
{op_line}
Click the link below to set your password and activate your account:

{invite_url}

This link expires in 72 hours. If you did not expect this invitation, you can safely ignore this email.

— OHMS Manager
"""
    from_email = os.environ.get('SENDGRID_FROM_EMAIL', 'noreply@rodmon.co.za')
    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject='Your OHMS Manager invitation',
        plain_text_content=body.strip(),
    )
    client = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
    client.send(message)
