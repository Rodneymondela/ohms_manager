"""Quick verification of the multi-operation migration state."""
from app import create_app, db
from app.models import User, Operation
from app.schedules.models import Stressor, HEG, SamplingSchedule, ExposureReading, MedicalRecord
from app.employees.models import Employee

app = create_app()
with app.app_context():
    print("=== Operations ===")
    for op in Operation.query.all():
        print(f"  id={op.id}  code={op.code}  name={op.operation_name}  status={op.status}")

    print("\n=== Users ===")
    for u in User.query.all():
        print(f"  id={u.id}  username={u.username}  role={u.role}  operation_id={u.operation_id}")

    print("\n=== Record counts (all should have operation_id) ===")
    checks = [
        ("Employee",         Employee,         Employee.query.count(),         Employee.query.filter_by(operation_id=None).count()),
        ("Stressor",         Stressor,         Stressor.query.count(),         Stressor.query.filter_by(operation_id=None).count()),
        ("HEG",              HEG,              HEG.query.count(),              HEG.query.filter_by(operation_id=None).count()),
        ("SamplingSchedule", SamplingSchedule, SamplingSchedule.query.count(), SamplingSchedule.query.filter_by(operation_id=None).count()),
        ("ExposureReading",  ExposureReading,  ExposureReading.query.count(),  ExposureReading.query.filter_by(operation_id=None).count()),
        ("MedicalRecord",    MedicalRecord,    MedicalRecord.query.count(),    MedicalRecord.query.filter_by(operation_id=None).count()),
    ]
    all_ok = True
    for name, _, total, unassigned in checks:
        status = "OK" if unassigned == 0 else "FAIL"
        if unassigned:
            all_ok = False
        print(f"  {status}  {name}: {total} total, {unassigned} unassigned")

    print("\n" + ("All records correctly assigned." if all_ok else "WARNING: some records lack operation_id!"))
