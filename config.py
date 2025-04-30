import os
# Use dotenv_values as well
from dotenv import load_dotenv, dotenv_values

basedir = os.path.abspath(os.path.dirname(__file__))
env_path = os.path.join(basedir, '.env')
load_dotenv(dotenv_path=env_path) # Load into os.environ

# Also get values directly to bypass potential os.environ caching issues
config_values = dotenv_values(dotenv_path=env_path)

class Config:
    """Base configuration settings."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess' # Change this in production!
    # Prioritize direct read from dotenv_values, fallback to os.environ, then default
    # Ensure the value read doesn't contain unexpected characters
    raw_db_url = config_values.get('DATABASE_URL') or os.environ.get('DATABASE_URL')
    SQLALCHEMY_DATABASE_URI = raw_db_url.strip() if raw_db_url else \
                              'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Read ADMIN_EMAIL robustly, stripping potential comments/whitespace
    raw_admin_email = config_values.get('ADMIN_EMAIL') or os.environ.get('ADMIN_EMAIL')
    ADMIN_EMAIL = raw_admin_email.strip() if raw_admin_email else None

    # Fernet Encryption Key (MUST be generated and kept secret)
    # Generate using: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    FERNET_KEY = config_values.get('FERNET_KEY') or os.environ.get('FERNET_KEY')
    if not FERNET_KEY:
        print("WARNING: FERNET_KEY not set in .env. Connector password encryption will fail.")
        # In a real app, you might raise an error here or disable the feature.
        # raise ValueError("FERNET_KEY is required for encryption but not set in .env")

    # Mail Server Configuration (for password reset)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or MAIL_USERNAME
