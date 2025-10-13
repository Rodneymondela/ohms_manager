from app.admin import admin_bp
from flask import render_template

@admin_bp.route('/admin')
def admin_dashboard():
    return "Admin Dashboard"  # Placeholder for now, replace with template if needed
