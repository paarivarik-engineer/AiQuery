from flask import Blueprint

bp = Blueprint('auth', __name__, template_folder='../templates/auth') # Point to templates/auth

# Import routes and forms at the bottom to avoid circular dependencies
from app.auth import routes, forms
