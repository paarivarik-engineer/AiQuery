from flask import Blueprint

bp = Blueprint('query', __name__, template_folder='../templates/query')

# Import routes and forms at the bottom
from app.query import routes, forms
