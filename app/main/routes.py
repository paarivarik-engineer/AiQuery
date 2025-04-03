from flask import render_template, redirect, url_for, flash
from flask_login import current_user, login_required
from app.main import bp
from app import db
# Import models and forms as needed later

@bp.route('/')
@bp.route('/index')
def index():
    """Homepage route."""
    # Later, this might show dashboard elements or redirect to query page if logged in
    return render_template('index.html', title='Home')

# Add other main routes here later (e.g., dashboard, profile)
