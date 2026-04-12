"""Remove seed/fake employees that were added by seed_data.py"""
from app import create_app, db
from app.employees.models import Employee

FAKE_NAMES = {
    'james mokoena', 'thabo dlamini', 'priya naidoo',
    'willem botha', 'nomsa khumalo', 'sipho mthembu', 'amanda peters',
}

app = create_app()
with app.app_context():
    removed = 0
    for emp in Employee.query.all():
        if emp.name.lower() in FAKE_NAMES:
            db.session.delete(emp)
            removed += 1
    db.session.commit()
    print(f'Removed {removed} fake employees.')
    print(f'Remaining: {Employee.query.filter_by(is_active=True).count()} active employees.')
