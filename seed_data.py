"""
seed_data.py
============
Seeds the database with sample employees, hazards, exposure readings,
and medical records so the app is functional out of the box.

Run from the project root:
    python seed_data.py
"""

import calendar as cal_module
from datetime import date, timedelta
from app import create_app, db
from app.models import User
from app.schedules.models import Stressor, HEG, SamplingSchedule, ExposureReading, EmployeeExposure, MedicalRecord
from app.employees.models import Employee

app = create_app()


HEGS = [
    dict(heg_number='HEG-01', job_title='Opencast Drill Assistant',
         department='Mining', risk_level='High',
         occupations=['Drilling Assistant']),
    dict(heg_number='HEG-02', job_title='Opencast Drill and Blast',
         department='Mining', risk_level='High',
         occupations=['Operator: Drillrig Machine', 'Drilling Supervisor', 'LDV Driver', 'Blaster', 'Blasting Assistant']),
    dict(heg_number='HEG-03', job_title='Opencast Trackless Mobile Machines - Load and Haul',
         department='Mining', risk_level='High',
         occupations=['Driver: Bulldozer', 'Driver: HAMV (Code 13) - TMM', 'Pit Worker', 'Mine Overseer', 'Driver: Grader', 'Explosive Truck Driver']),
    dict(heg_number='HEG-04', job_title='Mobile Screen and Crusher',
         department='Processing', risk_level='Moderate',
         occupations=['Boilermaker', 'Electrician', 'Fitter: Operative (grade 1)', 'Plant Worker: Workers', 'Plant Supervisor', 'Engineering Assistant']),
    dict(heg_number='HEG-05', job_title='Final Product - Stockpile, Stacker and Reclaimer',
         department='Processing', risk_level='Moderate',
         occupations=['Plant Worker: Stacker Operator', 'Plant Supervisor', 'Weighbridge Controller', 'Boilermaker', 'Driver: Bob Cat']),
    dict(heg_number='HEG-06', job_title='Roving Plant Fixed Plants',
         department='Processing', risk_level='Moderate',
         occupations=['Boilermaker', 'Driver: Bob Cat', 'Electrician', 'Fitter: Operative (grade 1)', 'Plant Worker: Workers', 'Plant Supervisor', 'Instrument Technician', 'Engineering Assistant', 'Millwright']),
    dict(heg_number='HEG-07', job_title='Surface Roving Exploration',
         department='Mining', risk_level='Low',
         occupations=['Drilling Supervisor', 'Diamond Drill Operator', 'Diamond Drill Worker', 'Water Truck Driver', 'Safety Officer']),
    dict(heg_number='HEG-08', job_title='Surface Roving General Mining Area',
         department='Mining', risk_level='Moderate',
         occupations=['Security Guard/Mine Police', 'Environmental Officer', 'Driver: Tractor (Code 05)', 'Grader Operator', 'Safety Officer', 'Electrician: Aide', 'General Worker: Environment', 'Production Manager', 'Electrician']),
    dict(heg_number='HEG-09', job_title='Assay Lab',
         department='Laboratory', risk_level='Low',
         occupations=['Chemist Superintendent', 'Laboratory Analyst', 'Laboratory Assistant', 'Sample Worker (Prep Lab)']),
    dict(heg_number='HEG-10', job_title='Surface Workshop - Engineering Structure',
         department='Engineering', risk_level='Moderate',
         occupations=['Diesel Mechanics', 'Boilermaker', 'Engineering Assistant (n.e.c.)', 'Garage Mechanic: Fitter', 'Electrician Foreman', 'Control Room Operator', 'Mechanical Foreman', 'Cleaner Officer']),
]

STRESSORS = [
    dict(name='Noise',              category='Physical',     oel_value=85.0,  oel_unit='dB(A)',    description='High noise levels from heavy machinery and drilling equipment.',   health_effects='Noise-Induced Hearing Loss (NIHL), tinnitus',              linked_test='Audiometry',                       default_frequency='Annual'),
    dict(name='Lead',               category='Chemical',     oel_value=0.05,  oel_unit='mg/m³',    description='Lead dust and fume exposure during smelting and battery operations.', health_effects='Neurological damage, anaemia, kidney disease',             linked_test='Blood Lead Levels',                default_frequency='6 Monthly'),
    dict(name='Silica (RCS)',       category='Chemical',     oel_value=0.1,   oel_unit='mg/m³',    description='Respirable crystalline silica from rock drilling and crushing.',    health_effects='Silicosis, lung cancer, COPD',                             linked_test='Lung Function Test + Chest X-ray', default_frequency='Annual'),
    dict(name='Whole-body Vibration', category='Ergonomic',  oel_value=1.15,  oel_unit='m/s²',     description='Vibration transmitted through seats of heavy machinery operators.',  health_effects='Lower back pain, spinal disorders',                        linked_test='Musculoskeletal Assessment',        default_frequency='Annual'),
    dict(name='Heat Stress',        category='Physical',     oel_value=28.0,  oel_unit='°C WBGT',  description='Extreme ambient temperatures in smelter and furnace areas.',          health_effects='Heat exhaustion, heat stroke, cardiovascular strain',      linked_test='Cardiovascular Fitness Assessment', default_frequency='Annual'),
    dict(name='Asbestos',           category='Chemical',     oel_value=0.1,   oel_unit='f/ml',     description='Legacy asbestos-containing materials in older plant structures.',     health_effects='Mesothelioma, asbestosis, lung cancer',                    linked_test='Chest X-ray + Lung Function',      default_frequency='Annual'),
    dict(name='Work-related Stress', category='Psychosocial', oel_value=None, oel_unit=None,       description='High workload, shift work and job insecurity.',                       health_effects='Anxiety, depression, burnout, cardiovascular disease',     linked_test='Mental Health Screening (GHQ-12)', default_frequency='Annual'),
    dict(name='Manganese',           category='Chemical',     oel_value=0.2,  oel_unit='mg/m³',    description='Manganese dust and fume from ore processing and welding operations.', health_effects='Manganism (neurological disorder), respiratory irritation', linked_test='Blood Manganese Levels + Neurological Assessment',          default_frequency='Annual'),
    dict(name='PNOC',                category='Chemical',     oel_value=10.0, oel_unit='mg/m³',    description='Particulates Not Otherwise Classified — general nuisance dust.',       health_effects='Respiratory irritation, reduced lung function',            linked_test='Lung Function Test',                                        default_frequency='Annual'),
    dict(name='Welding Fumes',       category='Chemical',     oel_value=1.0,  oel_unit='mg/m³',    description='Mixed metal fume and particulates generated during welding operations.', health_effects='Respiratory disease, lung cancer, neurological effects',   linked_test='Lung Function Test + Chest X-ray',                          default_frequency='Annual'),
    dict(name='DPM',                 category='Chemical',     oel_value=0.16, oel_unit='mg/m³',    description='Diesel Particulate Matter from diesel-powered trackless mobile machines.', health_effects='Lung cancer, respiratory and cardiovascular disease',      linked_test='Lung Function Test',                                        default_frequency='Annual'),
]

EMPLOYEES = [
    dict(name='James Mokoena',      job_title='Drill Operator',       department='Mining',      heg_number='HEG-01: Opencast Drill Assistant',                             hazard_names=['Noise', 'Silica (RCS)', 'Whole-body Vibration']),
    dict(name='Sarah van der Berg', job_title='Blasting Technician',  department='Mining',      heg_number='HEG-02: Opencast Drill and Blast',                             hazard_names=['Noise', 'Lead', 'Heat Stress']),
    dict(name='Thabo Dlamini',      job_title='Load and Haul Operator',department='Mining',      heg_number='HEG-03: Opencast Trackless Mobile Machines - Load and Haul',   hazard_names=['Noise', 'Whole-body Vibration']),
    dict(name='Priya Naidoo',       job_title='Process Operator',     department='Processing',  heg_number='HEG-04: Mobile Screen and Crusher',                            hazard_names=['Noise', 'Silica (RCS)']),
    dict(name='Willem Botha',       job_title='Stacker Operator',     department='Processing',  heg_number='HEG-05: Final Product - Stockpile, Stacker and Reclaimer',     hazard_names=['Noise', 'Work-related Stress']),
    dict(name='Nomsa Khumalo',      job_title='Lab Technician',       department='Laboratory',  heg_number='HEG-09: Assay Lab',                                            hazard_names=['Lead', 'Asbestos']),
    dict(name='Sipho Mthembu',      job_title='Plant Operator',       department='Processing',  heg_number='HEG-06: Roving Plant Fixed Plants',                            hazard_names=['Noise', 'Silica (RCS)', 'Whole-body Vibration']),
    dict(name='Amanda Peters',      job_title='Structural Engineer',  department='Engineering', heg_number='HEG-10: Surface Workshop - Engineering Structure',              hazard_names=['Noise', 'Asbestos']),
]

# (stressor_name, location, measured_value, date_str, employee_names)
READINGS = [
    ('Noise',              'Drill Platform A',    92.0,  '2026-03-15', ['James Mokoena', 'Sipho Mthembu', 'Amanda Peters']),
    ('Lead',               'Smelter Zone B',      0.04,  '2026-03-20', ['Sarah van der Berg', 'Priya Naidoo', 'Nomsa Khumalo']),
    ('Silica (RCS)',       'Drill Platform A',    0.18,  '2026-03-15', ['James Mokoena', 'Sipho Mthembu']),
    ('Whole-body Vibration','Workshop Bay 3',     0.9,   '2026-03-22', ['Thabo Dlamini', 'Sipho Mthembu']),
    ('Heat Stress',        'Smelter Zone A',      31.0,  '2026-03-18', ['Sarah van der Berg']),
    ('Asbestos',           'Block C Maintenance', 0.08,  '2026-02-28', ['Thabo Dlamini', 'Nomsa Khumalo']),
    ('Noise',              'Processing Plant',    83.0,  '2026-03-25', ['Priya Naidoo', 'Willem Botha']),
]

# (employee_name, stressor_name, test_name, last_done, next_due, result, status)
MEDICAL = [
    ('James Mokoena',      'Noise',               'Audiometry',                  '2025-03-10', '2026-03-10', 'Normal',           'overdue'),
    ('James Mokoena',      'Silica (RCS)',         'Lung Function + Chest X-ray', '2025-06-01', '2026-06-01', 'Normal',           'upcoming'),
    ('James Mokoena',      'Whole-body Vibration', 'Musculoskeletal Assessment',  '2025-04-15', '2026-04-15', 'Mild back strain', 'upcoming'),
    ('Sarah van der Berg', 'Noise',               'Audiometry',                  '2025-09-15', '2026-09-15', 'Mild NIHL',        'scheduled'),
    ('Sarah van der Berg', 'Lead',                'Blood Lead Levels',            '2025-12-01', '2026-06-01', '38 µg/dL',         'upcoming'),
    ('Sarah van der Berg', 'Heat Stress',         'Cardiovascular Fitness',       '2025-09-15', '2026-09-15', 'Fit',              'scheduled'),
    ('Thabo Dlamini',      'Noise',               'Audiometry',                  '2024-12-05', '2025-12-05', 'Normal',           'overdue'),
    ('Thabo Dlamini',      'Asbestos',            'Chest X-ray + Lung Function',  '2025-03-20', '2026-03-20', 'Normal',           'overdue'),
    ('Priya Naidoo',       'Lead',                'Blood Lead Levels',            '2025-10-01', '2026-04-01', '22 µg/dL',         'overdue'),
    ('Priya Naidoo',       'Silica (RCS)',         'Lung Function + Chest X-ray', '2025-06-10', '2026-06-10', 'Normal',           'upcoming'),
    ('Willem Botha',       'Noise',               'Audiometry',                  '2025-11-20', '2026-11-20', 'Normal',           'scheduled'),
    ('Nomsa Khumalo',      'Lead',                'Blood Lead Levels',            '2025-11-15', '2026-05-15', '28 µg/dL',         'upcoming'),
    ('Nomsa Khumalo',      'Asbestos',            'Chest X-ray + Lung Function',  '2025-05-10', '2026-05-10', 'Normal',           'upcoming'),
    ('Sipho Mthembu',      'Noise',               'Audiometry',                  '2025-08-20', '2026-08-20', 'Mild NIHL',        'scheduled'),
    ('Sipho Mthembu',      'Silica (RCS)',         'Lung Function + Chest X-ray', '2025-08-20', '2026-08-20', 'Normal',           'scheduled'),
    ('Amanda Peters',      'Noise',               'Audiometry',                  '2025-07-12', '2026-07-12', 'Normal',           'scheduled'),
    ('Amanda Peters',      'Silica (RCS)',         'Lung Function + Chest X-ray', '2025-07-12', '2026-07-12', 'Normal',           'scheduled'),
]


def _parse(d):
    return date.fromisoformat(d) if d else None


def seed():
    with app.app_context():
        db.create_all()

        # ── Admin user ───────────────────────────────────────────────────────
        admin = User.query.filter_by(email='rodney@rodmon.co.za').first()
        if not admin:
            admin = User(
                username = 'Rodney',
                email    = 'rodney@rodmon.co.za',
                is_admin = True,
                role     = 'super_admin',
            )
            admin.set_password('Admin@1234')
            db.session.add(admin)
            db.session.flush()
            print(f"  + Admin user: {admin.username} ({admin.email})")
        else:
            print(f"  ~ Admin user already exists: {admin.email}")

        # ── HEG groups ───────────────────────────────────────────────────────
        for data in HEGS:
            if not HEG.query.filter_by(heg_number=data['heg_number']).first():
                h = HEG(**data)
                db.session.add(h)
                print(f"  + HEG: {data['heg_number']} — {data['job_title']}")
        db.session.flush()

        # ── Stressors ────────────────────────────────────────────────────────
        stressor_map = {}
        for data in STRESSORS:
            s = Stressor.query.filter_by(name=data['name']).first()
            if not s:
                s = Stressor(**{k: v for k, v in data.items()}, is_active=True)
                db.session.add(s)
                db.session.flush()
                print(f"  + Stressor: {s.name}")
            stressor_map[s.name] = s

        # ── Employees ────────────────────────────────────────────────────────
        emp_map = {}
        for data in EMPLOYEES:
            e = Employee.query.filter_by(name=data['name']).first()
            if not e:
                e = Employee(
                    name       = data['name'],
                    job_title  = data['job_title'],
                    department = data['department'],
                    heg_number = data['heg_number'],
                )
                db.session.add(e)
                db.session.flush()
                print(f"  + Employee: {e.name}")
            e.stressors = [stressor_map[n] for n in data['hazard_names'] if n in stressor_map]
            emp_map[e.name] = e

        db.session.flush()

        # ── Exposure readings ────────────────────────────────────────────────
        for (stressor_name, location, value, date_str, emp_names) in READINGS:
            s = stressor_map.get(stressor_name)
            if not s:
                continue
            exists = ExposureReading.query.filter_by(stressor_id=s.id, location=location, date=_parse(date_str)).first()
            if exists:
                continue
            r = ExposureReading(
                stressor_id    = s.id,
                location       = location,
                measured_value = value,
                oel_value      = s.oel_value,
                oel_unit       = s.oel_unit,
                date           = _parse(date_str),
            )
            db.session.add(r)
            db.session.flush()
            for name in emp_names:
                emp = emp_map.get(name)
                if emp:
                    db.session.add(EmployeeExposure(reading_id=r.id, employee_id=emp.id))
            print(f"  + Reading: {stressor_name} @ {location} ({date_str})")

        # ── Medical records ──────────────────────────────────────────────────
        for (emp_name, stressor_name, test_name, last_done, next_due, result, status) in MEDICAL:
            emp = emp_map.get(emp_name)
            s   = stressor_map.get(stressor_name)
            if not emp:
                continue
            exists = MedicalRecord.query.filter_by(employee_id=emp.id, test_name=test_name, next_due=_parse(next_due)).first()
            if exists:
                continue
            rec = MedicalRecord(
                employee_id = emp.id,
                stressor_id = s.id if s else None,
                test_name   = test_name,
                last_done   = _parse(last_done),
                next_due    = _parse(next_due),
                result      = result,
                status      = status,
            )
            db.session.add(rec)
            print(f"  + Medical: {emp_name} — {test_name}")

        # ── Sampling schedules ────────────────────────────────────────────────
        # Distribution strategy:
        #   - 3 samples per stressor per HEG per quarter, one per month-slot.
        #   - Each HEG is assigned a fixed day-of-month so samples are spread
        #     throughout the month rather than all landing on the same date.
        #   - Manganese & Silica use independent slot offsets so the same
        #     occupation is never sampled for both stressors in the same month.

        def weekdays_in_month(year, month, start_day=1):
            """Return list of weekday (Mon–Fri) dates in the month from start_day."""
            _, days_in_month = cal_module.monthrange(year, month)
            return [
                date(year, month, d)
                for d in range(start_day, days_in_month + 1)
                if date(year, month, d).weekday() < 5
            ]

        mn       = stressor_map.get('Manganese')
        sil      = stressor_map.get('Silica (RCS)')
        noise    = stressor_map.get('Noise')
        all_hegs = HEG.query.order_by(HEG.heg_number).all()

        today = date.today()
        m = today.month
        if   m in (4, 5, 6):    qm = [4, 5, 6]
        elif m in (7, 8, 9):    qm = [7, 8, 9]
        elif m in (10, 11, 12): qm = [10, 11, 12]
        else:                   qm = [1, 2, 3]
        yr = today.year

        # Pre-compute one weekday per (HEG, quarter_month), evenly distributed.
        # April 2026 starts from the 16th; all other months use full month.
        heg_numbers = [h.heg_number for h in all_hegs]
        heg_month_date = {}
        for qmonth in qm:
            start = 16 if (qmonth == 4 and yr == 2026) else 1
            wdays = weekdays_in_month(yr, qmonth, start)
            n = len(wdays)
            total = len(heg_numbers)
            for i, heg_num in enumerate(heg_numbers):
                idx = round(i * (n - 1) / (total - 1)) if total > 1 else 0
                heg_month_date[(heg_num, qmonth)] = wdays[min(idx, n - 1)]

        def due_date(heg_number, quarter_month):
            return heg_month_date[(heg_number, quarter_month)]

        # Manganese & Silica — offset: Mn=0, Silica=1 (independent months)
        stressor_offsets = {mn: 0, sil: 1}
        for stressor, offset in stressor_offsets.items():
            if not stressor:
                continue
            for heg in all_hegs:
                occupations = (heg.occupations or [None])[:3]
                for i, occ in enumerate(occupations):
                    exists = SamplingSchedule.query.filter_by(
                        heg_id=heg.id, stressor_id=stressor.id,
                        occupation=occ or None
                    ).first()
                    if not exists:
                        slot = (i + offset) % 3
                        d = due_date(heg.heg_number, qm[slot])
                        s = SamplingSchedule(
                            heg_id          = heg.id,
                            stressor_id     = stressor.id,
                            occupation      = occ or None,
                            sampling_type   = 'Personal',
                            frequency       = 'Quarterly',
                            next_sample_due = d,
                        )
                        db.session.add(s)
                        print(f"  + Schedule: {heg.heg_number} / {stressor.name} / {occ or 'General'} [{d}]")

        # Noise — 3 per HEG per quarter, one per month-slot
        for heg in all_hegs:
            if not noise:
                continue
            occupations = (heg.occupations or [None])[:3]
            for slot, occ in enumerate(occupations):
                exists = SamplingSchedule.query.filter_by(
                    heg_id=heg.id, stressor_id=noise.id,
                    occupation=occ or None
                ).first()
                if not exists:
                    d = due_date(heg.heg_number, qm[slot])
                    s = SamplingSchedule(
                        heg_id          = heg.id,
                        stressor_id     = noise.id,
                        occupation      = occ or None,
                        sampling_type   = 'Personal',
                        frequency       = 'Quarterly',
                        next_sample_due = d,
                    )
                    db.session.add(s)
                    print(f"  + Schedule: {heg.heg_number} / Noise / {occ or 'General'} [{d}]")

        # DPM — 3 samples per quarter for HEG-03 only
        dpm   = stressor_map.get('DPM')
        heg03 = next((h for h in all_hegs if h.heg_number == 'HEG-03'), None)
        if dpm and heg03:
            occupations = (heg03.occupations or [None])[:3]
            for slot, occ in enumerate(occupations):
                exists = SamplingSchedule.query.filter_by(
                    heg_id=heg03.id, stressor_id=dpm.id,
                    occupation=occ or None
                ).first()
                if not exists:
                    d = due_date(heg03.heg_number, qm[slot])
                    s = SamplingSchedule(
                        heg_id          = heg03.id,
                        stressor_id     = dpm.id,
                        occupation      = occ or None,
                        sampling_type   = 'Personal',
                        frequency       = 'Quarterly',
                        next_sample_due = d,
                    )
                    db.session.add(s)
                    print(f"  + Schedule: {heg03.heg_number} / DPM / {occ or 'General'} [{d}]")

        # Welding Fumes — 3 samples per quarter for HEG-10 only
        welding = stressor_map.get('Welding Fumes')
        heg10   = next((h for h in all_hegs if h.heg_number == 'HEG-10'), None)
        if welding and heg10:
            occupations = (heg10.occupations or [None])[:3]
            for slot, occ in enumerate(occupations):
                exists = SamplingSchedule.query.filter_by(
                    heg_id=heg10.id, stressor_id=welding.id,
                    occupation=occ or None
                ).first()
                if not exists:
                    d = due_date(heg10.heg_number, qm[slot])
                    s = SamplingSchedule(
                        heg_id          = heg10.id,
                        stressor_id     = welding.id,
                        occupation      = occ or None,
                        sampling_type   = 'Personal',
                        frequency       = 'Quarterly',
                        next_sample_due = d,
                    )
                    db.session.add(s)
                    print(f"  + Schedule: {heg10.heg_number} / Welding Fumes / {occ or 'General'} [{d}]")

        db.session.commit()
        print("\nSeed complete.")


if __name__ == '__main__':
    seed()
