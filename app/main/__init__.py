from flask import Blueprint

bp = Blueprint('main', __name__)

# Import routes at the bottom
from app.main import routes
