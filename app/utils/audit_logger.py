from flask import request
from app.models import AuditLog, AuditActionType
from app import db
from datetime import datetime
from flask import current_app

def log_audit_event(user_id, action_type, details=None):
    """Log an audit event to the database"""
    try:
        log_entry = AuditLog(
            user_id=user_id,
            action_type=action_type,
            details=details or {},
            ip_address=request.remote_addr,
            created_at=datetime.utcnow()
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(f"Failed to write audit log: {str(e)}")
