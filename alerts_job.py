"""
Daily alerts job — run via Heroku Scheduler: python alerts_job.py

Sends email summaries to operation admins covering:
  - Medical surveillance overdue / due within 30 days
  - Sampling schedules overdue / due within 30 days
"""

from datetime import date, timedelta
from app import create_app, db
from app.models import Operation, User
from app.schedules.models import MedicalRecord, SamplingSchedule
from app.email import send_alert_email

WARN_DAYS = 30


def run():
    app = create_app()
    with app.app_context():
        today     = date.today()
        warn_date = today + timedelta(days=WARN_DAYS)

        operations = Operation.query.filter_by(status='active').all()
        sent = skipped = 0

        for op in operations:
            admins = User.query.filter_by(operation_id=op.id, role='admin').all()
            if not admins:
                print(f"  {op.operation_name}: no admin users, skipping")
                skipped += 1
                continue

            medical_overdue = (
                MedicalRecord.query
                .filter_by(operation_id=op.id)
                .filter(MedicalRecord.next_due.isnot(None))
                .filter(MedicalRecord.next_due < today)
                .all()
            )
            medical_due_soon = (
                MedicalRecord.query
                .filter_by(operation_id=op.id)
                .filter(MedicalRecord.next_due.isnot(None))
                .filter(MedicalRecord.next_due >= today)
                .filter(MedicalRecord.next_due <= warn_date)
                .all()
            )
            sampling_overdue = (
                SamplingSchedule.query
                .filter_by(operation_id=op.id)
                .filter(SamplingSchedule.next_sample_due.isnot(None))
                .filter(SamplingSchedule.next_sample_due < today)
                .all()
            )
            sampling_due_soon = (
                SamplingSchedule.query
                .filter_by(operation_id=op.id)
                .filter(SamplingSchedule.next_sample_due.isnot(None))
                .filter(SamplingSchedule.next_sample_due >= today)
                .filter(SamplingSchedule.next_sample_due <= warn_date)
                .all()
            )

            if not any([medical_overdue, medical_due_soon, sampling_overdue, sampling_due_soon]):
                print(f"  {op.operation_name}: nothing to report, skipping")
                skipped += 1
                continue

            print(f"  {op.operation_name}: "
                  f"{len(medical_overdue)} med overdue, "
                  f"{len(medical_due_soon)} med due soon, "
                  f"{len(sampling_overdue)} sampling overdue, "
                  f"{len(sampling_due_soon)} sampling due soon")

            for admin in admins:
                send_alert_email(
                    to_email=admin.email,
                    username=admin.username,
                    operation_name=op.operation_name,
                    medical_overdue=medical_overdue,
                    medical_due_soon=medical_due_soon,
                    sampling_overdue=sampling_overdue,
                    sampling_due_soon=sampling_due_soon,
                    today=today,
                )
                print(f"    Sent to {admin.email}")
                sent += 1

        print(f"\nDone — {sent} email(s) sent, {skipped} operation(s) skipped.")


if __name__ == '__main__':
    run()
