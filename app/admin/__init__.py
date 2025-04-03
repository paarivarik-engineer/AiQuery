from flask import Blueprint

bp = Blueprint('admin', __name__, template_folder='../templates/admin')

# Import routes and decorators at the bottom
from app.admin import routes, decorators
