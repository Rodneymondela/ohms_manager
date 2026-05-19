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


def send_alert_email(to_email, username, operation_name,
                     medical_overdue, medical_due_soon,
                     sampling_overdue, sampling_due_soon, today):
    has_overdue = bool(medical_overdue or sampling_overdue)
    subject = (
        f"[ACTION REQUIRED] OHMS Alert — {operation_name}"
        if has_overdue else
        f"OHMS Daily Summary — {operation_name}"
    )

    lines = [
        f"Hi {username},",
        "",
        f"Daily OHS alert summary for {operation_name} — {today.strftime('%d %b %Y')}.",
        "",
    ]

    if medical_overdue:
        lines += [f"*** MEDICAL SURVEILLANCE OVERDUE ({len(medical_overdue)} record(s)) ***", ""]
        for r in sorted(medical_overdue, key=lambda x: x.next_due):
            days = (today - r.next_due).days
            lines.append(f"  • {r.employee.name} — {r.test_name} — {days} day(s) overdue (was due {r.next_due})")
        lines.append("")

    if medical_due_soon:
        lines += [f"MEDICAL SURVEILLANCE DUE WITHIN 30 DAYS ({len(medical_due_soon)} record(s))", ""]
        for r in sorted(medical_due_soon, key=lambda x: x.next_due):
            days = (r.next_due - today).days
            lines.append(f"  • {r.employee.name} — {r.test_name} — due in {days} day(s) ({r.next_due})")
        lines.append("")

    if sampling_overdue:
        lines += [f"*** SAMPLING SCHEDULES OVERDUE ({len(sampling_overdue)} schedule(s)) ***", ""]
        for s in sorted(sampling_overdue, key=lambda x: x.next_sample_due):
            days = (today - s.next_sample_due).days
            lines.append(f"  • HEG {s.heg.heg_number} / {s.stressor.name} ({s.frequency}) — {days} day(s) overdue (was due {s.next_sample_due})")
        lines.append("")

    if sampling_due_soon:
        lines += [f"SAMPLING DUE WITHIN 30 DAYS ({len(sampling_due_soon)} schedule(s))", ""]
        for s in sorted(sampling_due_soon, key=lambda x: x.next_sample_due):
            days = (s.next_sample_due - today).days
            lines.append(f"  • HEG {s.heg.heg_number} / {s.stressor.name} ({s.frequency}) — due in {days} day(s) ({s.next_sample_due})")
        lines.append("")

    lines += ["Log in to OHMS Manager to take action.", "", "— OHMS Manager"]

    from_email = os.environ.get('SENDGRID_FROM_EMAIL', 'noreply@rodmon.co.za')
    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        plain_text_content="\n".join(lines),
    )
    SendGridAPIClient(os.environ.get('SENDGRID_API_KEY')).send(message)


def send_reset_email(to_email, username, reset_url):
    body = f"""Hi {username},

We received a request to reset your OHMS Manager password.

Click the link below to choose a new password:

{reset_url}

This link expires in 1 hour. If you did not request a password reset, you can safely ignore this email.

— OHMS Manager
"""
    from_email = os.environ.get('SENDGRID_FROM_EMAIL', 'noreply@rodmon.co.za')
    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject='Reset your OHMS Manager password',
        plain_text_content=body.strip(),
    )
    client = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
    client.send(message)
