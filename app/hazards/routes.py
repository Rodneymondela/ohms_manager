from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required
from app import db # Assuming db from app package
from app.models import Hazard
from app.forms import HazardForm
from . import hazards_bp
from sqlalchemy.exc import IntegrityError

@hazards_bp.route('/')
@login_required
def list_hazards(): # Renamed from 'hazards'
    all_hazards = Hazard.query.all()
    return render_template('hazards/hazards.html', hazards=all_hazards, title='Manage Hazards')

@hazards_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_hazard():
    form = HazardForm()
    if form.validate_on_submit():
        try:
            hazard = Hazard(
                name=form.name.data,
                category=form.category.data,
                exposure_limit=form.exposure_limit.data,
                unit=form.unit.data,
                description=form.description.data,
                safety_measures=form.safety_measures.data
            )
            db.session.add(hazard)
            db.session.commit()
            flash('Hazard added successfully.', 'success')
            return redirect(url_for('hazards.list_hazards'))
        except ValueError as e:
            db.session.rollback()
            flash(f'Error adding hazard: {e}', 'danger')
        except IntegrityError:
            db.session.rollback()
            flash('Error: This hazard might already exist or conflicts with existing data.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'An unexpected error occurred: {e}', 'danger')
    return render_template('hazards/hazard_form.html', form=form, title='Add Hazard')

@hazards_bp.route('/<int:hazard_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_hazard(hazard_id):
    hazard = Hazard.query.get_or_404(hazard_id)
    form = HazardForm(obj=hazard)

    if form.validate_on_submit():
        try:
            form.populate_obj(hazard)
            db.session.commit()
            flash('Hazard updated successfully.', 'success')
            return redirect(url_for('hazards.list_hazards'))
        except ValueError as e:
            db.session.rollback()
            flash(f'Error updating hazard: {e}', 'danger')
        except IntegrityError:
            db.session.rollback()
            flash('Error: Could not update hazard due to a data conflict.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'An unexpected error occurred: {e}', 'danger')

    return render_template('hazards/hazard_form.html', form=form, title='Edit Hazard', hazard_id=hazard_id)

@hazards_bp.route('/<int:hazard_id>/delete', methods=['POST'])
@login_required
def delete_hazard(hazard_id):
    hazard = Hazard.query.get_or_404(hazard_id)
    try:
        db.session.delete(hazard)
        db.session.commit()
        flash('Hazard deleted successfully.', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('Error: Cannot delete this hazard as it has related records (e.g., exposures). Please remove those first.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'An unexpected error occurred: {e}', 'danger')
    return redirect(url_for('hazards.list_hazards'))
