from flask import render_template, redirect, url_for, flash, request, current_app # Added current_app
from flask_login import login_required
from app import db
from app.models import Hazard
from app.forms import HazardForm
from app.decorators import admin_required # Import admin_required
from . import hazards_bp
from sqlalchemy.exc import IntegrityError

@hazards_bp.route('/')
@login_required
def list_hazards(): # Renamed from 'hazards'
    all_hazards = Hazard.query.all()
    return render_template('hazards/hazards.html', hazards=all_hazards, title='Manage Hazards')

@hazards_bp.route('/add', methods=['GET', 'POST'])
@login_required
@admin_required
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
            current_app.logger.warning(f'IntegrityError while adding new hazard {form.name.data}: {str(e)}', exc_info=True)
            flash('Error: This hazard might already exist or conflicts with existing data.', 'danger')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'An unexpected error occurred while adding new hazard {form.name.data}: {str(e)}', exc_info=True)
            flash(f'An unexpected error occurred: {str(e)}', 'danger')
    return render_template('hazards/hazard_form.html', form=form, title='Add Hazard')

@hazards_bp.route('/<int:hazard_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
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
            current_app.logger.warning(f'IntegrityError while updating hazard ID {hazard_id}: {str(e)}', exc_info=True)
            flash('Error: Could not update hazard due to a data conflict.', 'danger')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'An unexpected error occurred while updating hazard ID {hazard_id}: {str(e)}', exc_info=True)
            flash(f'An unexpected error occurred: {str(e)}', 'danger')

    return render_template('hazards/hazard_form.html', form=form, title='Edit Hazard', hazard_id=hazard_id)

@hazards_bp.route('/<int:hazard_id>/delete', methods=['POST'])
@login_required
@admin_required # Added decorator
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
        current_app.logger.error(f'An unexpected error occurred while deleting hazard ID {hazard_id}: {str(e)}', exc_info=True)
        flash(f'An unexpected error occurred: {str(e)}', 'danger')
    return redirect(url_for('hazards.list_hazards'))
