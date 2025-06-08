from flask import render_template
from flask_login import login_required
from . import main_bp

@main_bp.route('/')
@login_required
def index():
    return render_template('main/index.html', title='Home')
