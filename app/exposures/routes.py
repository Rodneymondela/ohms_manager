from flask import render_template, redirect, url_for, flash, request, current_app, make_response # Added make_response
from flask_login import login_required, current_user
from app import db
from app.models import Exposure, Employee, Hazard
from app.forms import ExposureForm
from app.utils.pdf_generator import generate_exposure_pdf # Added PDF generator
from app.decorators import admin_required # Import admin_required
from . import exposures_bp
from sqlalchemy.exc import IntegrityError

@exposures_bp.route('/')
@login_required
def list_exposures(): # Renamed from 'exposures'
    all_exposures = Exposure.query.order_by(Exposure.date.desc()).all()
    return render_template('exposures/exposures.html', exposures=all_exposures, title='Manage Exposures')

@exposures_bp.route('/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_exposure():
    form = ExposureForm()
    form.employee.choices = [(e.id, e.name) for e in Employee.query.order_by(Employee.name).all()]
    form.hazard.choices = [(h.id, h.name) for h in Hazard.query.order_by(Hazard.name).all()]

    if form.validate_on_submit():
        try:
            exposure = Exposure(
                employee_id=form.employee.data,
                hazard_id=form.hazard.data,
                exposure_level=form.exposure_level.data,
                duration=form.duration.data,
                date=form.date.data,
                location=form.location.data,
                notes=form.notes.data,
                recorded_by=current_user.id
            )
            db.session.add(exposure)
            db.session.commit()
            flash('Exposure record added successfully.', 'success')
            return redirect(url_for('exposures.list_exposures'))
        except ValueError as e:
            db.session.rollback()
            flash(f'Error adding exposure record: {e}', 'danger')
        except IntegrityError:
            db.session.rollback()
            current_app.logger.warning(f'IntegrityError while adding new exposure for employee ID {form.employee.data} and hazard ID {form.hazard.data}: {str(e)}', exc_info=True)
            flash('Error: Could not add exposure record due to a data conflict or missing related record.', 'danger')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'An unexpected error occurred while adding new exposure: {str(e)}', exc_info=True)
            flash(f'An unexpected error occurred: {str(e)}', 'danger')
    return render_template('exposures/exposure_form.html', form=form, title='Add Exposure Record')

@exposures_bp.route('/<int:exposure_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_exposure(exposure_id):
    exposure = Exposure.query.get_or_404(exposure_id)
    form = ExposureForm(obj=exposure)

    form.employee.choices = [(e.id, e.name) for e in Employee.query.order_by(Employee.name).all()]
    form.hazard.choices = [(h.id, h.name) for h in Hazard.query.order_by(Hazard.name).all()]

    if request.method == 'GET':
        form.employee.data = exposure.employee_id
        form.hazard.data = exposure.hazard_id
        # form.date.data = exposure.date # Usually handled by obj=exposure

    if form.validate_on_submit():
        try:
            exposure.employee_id = form.employee.data
            exposure.hazard_id = form.hazard.data
            exposure.exposure_level = form.exposure_level.data
            exposure.duration = form.duration.data
            exposure.date = form.date.data
            exposure.location = form.location.data
            exposure.notes = form.notes.data

            db.session.commit()
            flash('Exposure record updated successfully.', 'success')
            return redirect(url_for('exposures.list_exposures'))
        except ValueError as e:
            db.session.rollback()
            flash(f'Error updating exposure record: {e}', 'danger')
        except IntegrityError:
            db.session.rollback()
            current_app.logger.warning(f'IntegrityError while updating exposure ID {exposure_id}: {str(e)}', exc_info=True)
            flash('Error: Could not update exposure record due to a data conflict.', 'danger')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'An unexpected error occurred while updating exposure ID {exposure_id}: {str(e)}', exc_info=True)
            flash(f'An unexpected error occurred: {str(e)}', 'danger')

    return render_template('exposures/exposure_form.html', form=form, title='Edit Exposure Record', exposure_id=exposure_id)

@exposures_bp.route('/<int:exposure_id>/delete', methods=['POST'])
@login_required
@admin_required # Added decorator
def delete_exposure(exposure_id):
    exposure = Exposure.query.get_or_404(exposure_id)
    try:
        db.session.delete(exposure)
        db.session.commit()
        flash('Exposure record deleted successfully.', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('Error: Could not delete exposure record due to a data conflict.', 'danger')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'An unexpected error occurred while deleting exposure ID {exposure_id}: {str(e)}', exc_info=True)
        flash(f'An unexpected error occurred: {str(e)}', 'danger')
    return redirect(url_for('exposures.list_exposures'))

@exposures_bp.route('/<int:exposure_id>/print_pdf', methods=['GET'])
@login_required # Ensures only logged-in users can access
def print_exposure_pdf(exposure_id):
    exposure = Exposure.query.get_or_404(exposure_id)

    try:
        pdf_data = generate_exposure_pdf(exposure)

        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=exposure_record_{exposure.id}.pdf'
        # Use 'inline' to try to display in browser, 'attachment' to force download.

        current_app.logger.info(f"User {current_user.username} generated PDF for Exposure ID {exposure.id}.")
        return response
    except Exception as e:
        current_app.logger.error(f"Error generating PDF for Exposure ID {exposure.id}: {str(e)}", exc_info=True)
        flash('Error generating PDF for this exposure record. Please try again later or contact support.', 'danger')
        return redirect(url_for('exposures.list_exposures')) # Or to a more appropriate error page or back
