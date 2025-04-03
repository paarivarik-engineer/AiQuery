from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, IntegerField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from app.models import DatabaseType # Import the enum

class ConnectorForm(FlaskForm):
    name = StringField('Connector Name', validators=[DataRequired(), Length(max=100)])
    # Create choices from the DatabaseType enum
    db_type_choices = [(db_type.value, db_type.name.replace('_', ' ').title()) for db_type in DatabaseType]
    db_type = SelectField('Database Type', choices=db_type_choices, validators=[DataRequired()])
    host = StringField('Host', validators=[DataRequired(), Length(max=100)])
    port = IntegerField('Port', validators=[DataRequired(), NumberRange(min=1, max=65535)])
    database = StringField('Database Name/SID/Service Name', validators=[DataRequired(), Length(max=100)])
    db_username = StringField('Username', validators=[DataRequired(), Length(max=100)])
    # Password is optional on edit, required on add (handled in route)
    db_password = PasswordField('Password', validators=[Optional(), Length(min=1)]) # Optional validator for edit
    submit = SubmitField('Save Connector')
