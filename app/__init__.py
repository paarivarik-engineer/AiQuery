from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail # Import Mail
import os
import logging
from logging.handlers import RotatingFileHandler

# Initialize extensions
db = SQLAlchemy()
login = LoginManager()
login.login_view = 'auth.login' # Redirect to login page if user is not logged in
login.login_message = 'Please log in to access this page.'

@login.user_loader
def load_user(id):
    from app.models import User  # Local import to avoid circular imports
    return User.query.get(int(id))

migrate = Migrate()
csrf = CSRFProtect()
mail = Mail() # Initialize Mail

def create_app(config_class=Config):
    """Creates and configures the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Configure Logging
    if not app.debug and not app.testing: # Only configure file logging in production
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/aiquery.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('AIQuery startup')
    else:
        # Ensure basic config for debug/testing if needed, or rely on Flask default
        logging.basicConfig(level=logging.DEBUG) # Ensure DEBUG level logs show in console
        app.logger.info('AIQuery startup in DEBUG mode')


    # Initialize Flask extensions with the app
    db.init_app(app)
    login.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    mail.init_app(app) # Initialize Mail with app

    # Register blueprints
    # We will create these blueprints later
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.connectors import bp as connectors_bp
    app.register_blueprint(connectors_bp, url_prefix='/connectors')

    from app.query import bp as query_bp
    app.register_blueprint(query_bp, url_prefix='/query')

    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Create database tables if they don't exist (useful for initial setup)
    # For production, migrations are preferred (Flask-Migrate handles this)
    # with app.app_context():
    #     db.create_all() # Comment out or remove if using migrations exclusively

    print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}") # For debugging

    return app

# Import models at the bottom to avoid circular imports
# We will create models.py next
from app import models
