from datetime import datetime
from app import db
from enum import Enum
import enum
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
# Note: Using password hashing for DB passwords is simple but not ideal.
# A real application should use proper encryption (e.g., Fernet from cryptography)
# to allow retrieving the password for connection strings. Hashing is one-way.
# For this example, we'll proceed with hashing for simplicity, assuming
# the connection string builder might need adjustment later or password isn't needed directly.

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
    db_password_encrypted = db.Column(db.String(256))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='connectors')

    def set_db_password(self, password):
        """Stores the database password.
        TODO: Replace plain text storage with proper encryption (e.g., Fernet).
        """
        self.db_password_encrypted = password # INSECURE - Storing plain text

    # Optional: Method to retrieve decrypted password (needed with real encryption)
    # def get_decrypted_db_password(self):
    #     # TODO: Implement decryption logic here
    #     # from cryptography.fernet import Fernet
    #     # key = Config.SECRET_KEY # Or a dedicated encryption key
    #     # f = Fernet(key)
    #     # return f.decrypt(self.db_password_encrypted.encode()).decode()
    #     return self.db_password_encrypted # Return plain text for now

    def __repr__(self):
        return f'<Connector {self.name} ({self.db_type.value})>'

    def get_connection_string(self):
        """Generate a database connection string based on connector settings"""
        # Uses the (currently plain text) password stored in db_password_encrypted
        # TODO: Update to use get_decrypted_db_password() once encryption is implemented
        password = self.db_password_encrypted # Using plain text for now

        if self.db_type == DatabaseType.POSTGRESQL:
             return f"postgresql://{self.db_username}:{password}@{self.host}:{self.port}/{self.database}"
        elif self.db_type == DatabaseType.MYSQL:
             # Note: MySQL connector might differ, e.g., mysql+mysqlconnector://
             return f"mysql+mysqlconnector://{self.db_username}:{password}@{self.host}:{self.port}/{self.database}"
        elif self.db_type == DatabaseType.ORACLE:
             # Note: Oracle connection strings can be complex, this is a basic example
             # May need cx_Oracle format: user/pass@host:port/service_name or SID
             # For simplicity, using a common pattern. Adjust if needed.
             return f"oracle+cx_oracle://{self.db_username}:{password}@{self.host}:{self.port}/?service_name={self.database}" # Example using service_name
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
