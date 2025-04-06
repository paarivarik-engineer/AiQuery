from datetime import datetime
from app import db
from enum import Enum
import enum
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet, InvalidToken
from config import Config # Import Config to access FERNET_KEY
from flask import current_app # To log errors

# Initialize Fernet - Ensure FERNET_KEY is set in Config/env
try:
    if not Config.FERNET_KEY:
        raise ValueError("FERNET_KEY is not set. Cannot initialize encryption.")
    fernet = Fernet(Config.FERNET_KEY.encode())
except Exception as e:
    # Log error and potentially raise it to prevent app startup without encryption
    current_app.logger.error(f"Failed to initialize Fernet encryption: {e}")
    # Depending on requirements, you might want to raise the error:
    # raise RuntimeError(f"Failed to initialize Fernet encryption: {e}") from e
    fernet = None # Indicate encryption is unavailable

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class DatabaseType(enum.Enum):
    POSTGRESQL = 'postgresql'
    MYSQL = 'mysql'
    ORACLE = 'oracle'

class Connector(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    db_type = db.Column(db.Enum(DatabaseType), nullable=False)
    host = db.Column(db.String(100), nullable=False)
    port = db.Column(db.Integer, nullable=False)
    database = db.Column(db.String(100), nullable=False)
    db_username = db.Column(db.String(100), nullable=False)
    db_password_encrypted = db.Column(db.Text) # Use Text for potentially longer encrypted strings
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='connectors')

    def set_db_password(self, password):
        """Encrypts and stores the database password."""
        if not fernet:
            current_app.logger.error("Fernet not initialized. Cannot encrypt password.")
            # Handle this case appropriately - maybe raise error or store placeholder?
            # Storing plain text here would defeat the purpose.
            raise RuntimeError("Encryption service is not available.")
        if password: # Only encrypt if a password is provided
            self.db_password_encrypted = fernet.encrypt(password.encode()).decode('utf-8')
        else:
             self.db_password_encrypted = None # Clear password if empty string provided

    def get_decrypted_db_password(self):
        """Decrypts and returns the database password."""
        if not fernet:
            current_app.logger.error("Fernet not initialized. Cannot decrypt password.")
            raise RuntimeError("Encryption service is not available.")
        if not self.db_password_encrypted:
            return None
        try:
            return fernet.decrypt(self.db_password_encrypted.encode()).decode('utf-8')
        except InvalidToken:
            current_app.logger.error(f"Failed to decrypt password for connector ID {self.id}. Invalid token.")
            return None # Or raise an error
        except Exception as e:
            current_app.logger.error(f"Failed to decrypt password for connector ID {self.id}: {e}")
            return None # Or raise an error

    def __repr__(self):
        return f'<Connector {self.name} ({self.db_type.value})>'

    def get_connection_string(self):
        """Generate a database connection string using the decrypted password."""
        password = self.get_decrypted_db_password()
        if password is None:
             # Handle cases where decryption failed or password is not set
             # Option 1: Raise error
             # raise ValueError(f"Password for connector {self.id} is missing or cannot be decrypted.")
             # Option 2: Return string with placeholder (might fail connection test)
             current_app.logger.warning(f"Password for connector {self.id} is missing or failed decryption. Using placeholder.")
             password = "PASSWORD_UNAVAILABLE" # Placeholder

        # Ensure username and password are URL-encoded if they contain special characters
        from urllib.parse import quote_plus
        safe_username = quote_plus(self.db_username)
        safe_password = quote_plus(password)

        if self.db_type == DatabaseType.POSTGRESQL:
             return f"postgresql://{safe_username}:{safe_password}@{self.host}:{self.port}/{self.database}"
        elif self.db_type == DatabaseType.MYSQL:
             return f"mysql+mysqlconnector://{safe_username}:{safe_password}@{self.host}:{self.port}/{self.database}"
        elif self.db_type == DatabaseType.ORACLE:
             # cx_Oracle typically handles encoding, but let's be safe
             return f"oracle+cx_oracle://{safe_username}:{safe_password}@{self.host}:{self.port}/?service_name={self.database}"
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")

class AuditActionType(enum.Enum):
    QUERY_EXECUTED = 'query_executed'
    LLM_CALL = 'llm_call'
    USER_LOGIN = 'user_login'
    CONNECTOR_ADDED = 'connector_added'
    # Add more action types as needed

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action_type = db.Column(db.Enum(AuditActionType), nullable=False)
    details = db.Column(db.JSON)
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='audit_logs')

    def __repr__(self):
        return f'<AuditLog {self.action_type} by User {self.user_id}>'
