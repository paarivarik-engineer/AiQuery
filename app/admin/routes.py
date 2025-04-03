from flask import render_template, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from app import db
from app.admin import bp
from app.admin.decorators import admin_required
from app.models import User, Connector
from sqlalchemy.orm import joinedload # To efficiently load connectors with users

@bp.route('/')
@login_required
@admin_required
def index():
    """Admin dashboard showing all users and their connectors."""
    # Query all users. Connectors will be loaded lazily when accessed in the template.
    users = db.session.scalars(
        db.select(User).order_by(User.username)
    ).all()

    return render_template('admin/index.html', title='Admin Panel', users=users)

# Add other admin actions here later (e.g., delete user, edit user roles)
