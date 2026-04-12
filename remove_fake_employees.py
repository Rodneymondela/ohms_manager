"""Remove all seed/fake employees and their associated data."""
from app import create_app, db
from app.employees.models import Employee, employee_stressor
from app.schedules.models import MedicalRecord, EmployeeExposure, ExposureReading

FAKE_NAMES = {
    'james mokoena', 'thabo dlamini', 'priya naidoo',
    'willem botha', 'nomsa khumalo', 'sipho mthembu', 'amanda peters',
    'sarah van der berg',
}

app = create_app()
with app.app_context():
    fake_emps = [e for e in Employee.query.all() if e.name.lower() in FAKE_NAMES]
    fake_ids  = [e.id for e in fake_emps]

    if not fake_ids:
        print('No fake employees found.')
    else:
        # Delete medical records
        med = MedicalRecord.query.filter(MedicalRecord.employee_id.in_(fake_ids)).delete(synchronize_session=False)
        # Delete employee_exposure links
        ee  = EmployeeExposure.query.filter(EmployeeExposure.employee_id.in_(fake_ids)).delete(synchronize_session=False)
        # Delete employee_stressor links
        db.session.execute(employee_stressor.delete().where(employee_stressor.c.employee_id.in_(fake_ids)))
        # Delete the employees
        Employee.query.filter(Employee.id.in_(fake_ids)).delete(synchronize_session=False)
        db.session.commit()
        print(f'Removed {len(fake_ids)} fake employees, {med} medical records, {ee} exposure links.')

    # Also wipe all exposure readings (they're all sample data)
    count = ExposureReading.query.count()
    EmployeeExposure.query.delete()
    ExposureReading.query.delete()
    db.session.commit()
    print(f'Removed {count} sample exposure readings.')

    print(f'Active employees remaining: {Employee.query.filter_by(is_active=True).count()}')
