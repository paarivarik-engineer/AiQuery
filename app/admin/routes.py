from flask import render_template, flash, redirect, url_for, abort, request
from flask_login import login_required, current_user
from app import db
from app.admin import bp
from app.admin.decorators import admin_required
from app.models import User, Connector, AuditLog
from sqlalchemy.orm import joinedload # To efficiently load connectors with users
from datetime import datetime, timedelta

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

@bp.route('/audit-logs')
@login_required
@admin_required
def audit_logs():
    """View audit logs with filtering options"""
    # Default to last 7 days of logs
    days = int(request.args.get('days', 7))
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get logs with user information
    logs = db.session.scalars(
        db.select(AuditLog)
        .join(User)
        .where(AuditLog.created_at >= start_date)
        .order_by(AuditLog.created_at.desc())
    ).all()

    return render_template('admin/audit_logs.html', 
                         title='Audit Logs',
                         logs=logs,
                         days=days)

# Add other admin actions here later (e.g., delete user, edit user roles)
