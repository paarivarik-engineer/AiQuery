from flask import Blueprint

bp = Blueprint('connectors', __name__, template_folder='../templates/connectors')

# Import routes and forms at the bottom
from app.connectors import routes, forms
