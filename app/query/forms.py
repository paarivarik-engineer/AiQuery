from flask_wtf import FlaskForm
from wtforms import SelectField, TextAreaField, SubmitField, StringField
from wtforms.validators import DataRequired, Optional # Add Optional
from app.models import Connector
from app import db
from flask_login import current_user

class QueryForm(FlaskForm):
    # Choices will be populated dynamically in the route
    connector = SelectField('Select Connector', coerce=int, validators=[DataRequired()])
    query_mode = SelectField(
        'Query Mode',
        choices=[('sql', 'SQL Query'), ('nl', 'Talk to your DB')],
        default='sql',
        validators=[DataRequired()]
    )
    # Renamed from sql_query, make DataRequired conditional later if needed
    query_input = TextAreaField('Query Input', validators=[DataRequired()], render_kw={"rows": 10, "placeholder": "Enter your SQL query here..."})
    submit = SubmitField('Run') # Changed button label

    def __init__(self, *args, **kwargs):
        super(QueryForm, self).__init__(*args, **kwargs)
        # Populate connector choices for the current user
        self.connector.choices = [
            (c.id, f"{c.name} ({c.db_type.name.title()})")
            for c in db.session.scalars(
                db.select(Connector).where(Connector.user_id == current_user.id).order_by(Connector.name)
            ).all()
        ]
        if not self.connector.choices:
             self.connector.choices = [(0, "No connectors available")] # Placeholder if no connectors
             self.submit.render_kw = {"disabled": True} # Disable submit if no connectors
