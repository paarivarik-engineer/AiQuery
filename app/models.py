from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.orm import relationship
import enum
from time import time
from flask import current_app
from itsdangerous import URLSafeTimedSerializer as Serializer # For tokens

# Enum for database types
class DatabaseType(enum.Enum):
    POSTGRESQL = 'postgresql'
    MYSQL = 'mysql'
    ORACLE = 'oracle'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256)) # Increased length for stronger hashes
    is_admin = db.Column(db.Boolean, default=False)
    connectors = relationship('Connector', back_populates='user', lazy='dynamic', cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

    def get_reset_password_token(self, expires_in=600):
        """Generates a password reset token."""
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id}, salt='password-reset-salt')

    @staticmethod
    def verify_reset_password_token(token, expires_in=600):
        """Verifies the password reset token."""
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token, salt='password-reset-salt', max_age=expires_in)
            user_id = data.get('user_id')
        except Exception: # Catches SignatureExpired, BadTimeSignature, BadSignature, etc.
            return None
        return db.session.get(User, user_id)

class Connector(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    db_type = db.Column(db.Enum(DatabaseType), nullable=False)
    host = db.Column(db.String(100), nullable=False)
    port = db.Column(db.Integer, nullable=False)
    database = db.Column(db.String(100), nullable=False)
    db_username = db.Column(db.String(100), nullable=False)
    # Consider encrypting the password in a real application
    db_password_encrypted = db.Column(db.String(256)) # Store encrypted password
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = relationship('User', back_populates='connectors')

    # Method to set encrypted password (implementation needed)
    def set_db_password(self, password):
        # Placeholder: Implement actual encryption here (e.g., using Fernet)
        # For now, storing plain text for simplicity, but THIS IS INSECURE
        # self.db_password_encrypted = encrypt_function(password)
        self.db_password_encrypted = password # Replace with encryption

    # Method to get decrypted password (implementation needed)
    def get_db_password(self):
        # Placeholder: Implement actual decryption here
        # return decrypt_function(self.db_password_encrypted)
        return self.db_password_encrypted # Replace with decryption

    def get_connection_string(self):
        """Generates a SQLAlchemy connection string (example)."""
        password = self.get_db_password()
        if self.db_type == DatabaseType.POSTGRESQL:
            return f"postgresql+psycopg2://{self.db_username}:{password}@{self.host}:{self.port}/{self.database}"
        elif self.db_type == DatabaseType.MYSQL:
            return f"mysql+mysqlconnector://{self.db_username}:{password}@{self.host}:{self.port}/{self.database}"
        elif self.db_type == DatabaseType.ORACLE:
            # Basic Oracle connection string, might need adjustments (e.g., SID vs Service Name)
            # Ensure Oracle Instant Client is set up correctly
            return f"oracle+cx_oracle://{self.db_username}:{password}@{self.host}:{self.port}/?service_name={self.database}"
            # Or for SID: return f"oracle+cx_oracle://{self.db_username}:{password}@{self.host}:{self.port}/{self.database}"
        else:
            raise ValueError("Unsupported database type")


    def __repr__(self):
        return f'<Connector {self.name} ({self.db_type.value}) for User {self.user_id}>'

@login.user_loader
def load_user(id):
    """Flask-Login user loader callback."""
    return db.session.get(User, int(id)) # Use db.session.get for SQLAlchemy 2.0+
