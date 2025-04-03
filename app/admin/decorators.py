from functools import wraps
from flask import abort
from flask_login import current_user

def admin_required(func):
    """
    Decorator to ensure the current user is logged in and is an admin.
    """
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            # Redirect to login or return 401 Unauthorized
            # login.login_view handles redirection usually
            return current_app.login_manager.unauthorized()
        if not current_user.is_admin:
            abort(403) # Forbidden
        return func(*args, **kwargs)
    return decorated_view
