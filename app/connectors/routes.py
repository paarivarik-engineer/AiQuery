from flask import render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import current_user, login_required
from sqlalchemy import create_engine, text
from wtforms.validators import DataRequired, Length, Optional # Import validators here
from app import db
from app.connectors import bp
from app.connectors.forms import ConnectorForm
from app.models import Connector, DatabaseType

# Database drivers for connection strings
DB_DRIVERS = {
    DatabaseType.POSTGRESQL: 'psycopg2',
    DatabaseType.MYSQL: 'mysqlconnector', 
    DatabaseType.ORACLE: 'cx_oracle'
}

@bp.route('/')
@login_required
def list_connectors():
    """Lists all connectors for the current user."""
    user_connectors = db.session.scalars(
        db.select(Connector).where(Connector.user_id == current_user.id).order_by(Connector.name)
    ).all()
    return render_template('connectors/list_connectors.html', title='My Connectors', connectors=user_connectors)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_connector():
    """Adds a new connector for the current user."""
    form = ConnectorForm()
    # Require password on add - Now DataRequired and Length are defined
    form.db_password.validators = [DataRequired(), Length(min=1)]

    if form.validate_on_submit():
        connector = Connector(
            name=form.name.data,
            db_type=DatabaseType(form.db_type.data), # Convert string back to enum
            host=form.host.data,
            port=form.port.data,
            database=form.database.data,
            db_username=form.db_username.data,
            user_id=current_user.id
        )
        connector.set_db_password(form.db_password.data)
        
        try:
            # Test the connection
            connection_str = connector.get_connection_string()
            engine = create_engine(connection_str)
            with engine.connect() as connection:
                pass  # Just test the connection
                
            db.session.add(connector)
            db.session.commit()
            flash(f'Connector "{connector.name}" added and connection tested successfully!', 'success')
            return redirect(url_for('connectors.list_connectors'))
        except Exception as e:
            db.session.rollback()
            flash(f'Failed to connect to database: {str(e)}', 'danger')
            return render_template('connectors/add_edit_connector.html', 
                                title='Add Connector', 
                                form=form,
                                form_action=url_for('connectors.add_connector'))
    return render_template('connectors/add_edit_connector.html', title='Add Connector', form=form, form_action=url_for('connectors.add_connector'))

@bp.route('/edit/<int:connector_id>', methods=['GET', 'POST'])
@login_required
def edit_connector(connector_id):
    """Edits an existing connector."""
    connector = db.session.get(Connector, connector_id)
    if not connector or connector.user_id != current_user.id:
        abort(404) # Or 403 if preferred

    form = ConnectorForm(obj=connector) # Pre-populate form
    # Password is optional on edit, only update if provided - Now Optional and Length are defined
    form.db_password.validators = [Optional(), Length(min=1)]

    if form.validate_on_submit():
        connector.name = form.name.data
        connector.db_type = DatabaseType(form.db_type.data)
        connector.host = form.host.data
        connector.port = form.port.data
        connector.database = form.database.data
        connector.db_username = form.db_username.data
        # Only update password if a new one was entered
        if form.db_password.data:
            connector.set_db_password(form.db_password.data)
        db.session.commit()
        flash(f'Connector "{connector.name}" updated successfully!')
        return redirect(url_for('connectors.list_connectors'))
    elif request.method == 'GET':
        # Populate form fields from the object on initial GET request
        form.name.data = connector.name
        form.db_type.data = connector.db_type.value # Set select field value
        form.host.data = connector.host
        form.port.data = connector.port
        form.database.data = connector.database
        form.db_username.data = connector.db_username
        # Don't pre-populate password field

    return render_template('connectors/add_edit_connector.html', title='Edit Connector', form=form, form_action=url_for('connectors.edit_connector', connector_id=connector_id))


@bp.route('/api/test-db-connection', methods=['POST'])
@login_required
def test_db_connection():
    """API endpoint to test database connection."""
    form = ConnectorForm()
    if not form.validate_on_submit():
        return jsonify({'success': False, 'error': 'Invalid form data'}), 400
        
    try:
        # Create connection string from form data
        db_type = DatabaseType(form.db_type.data)
        conn_str = f"{db_type.value}+{DB_DRIVERS[db_type]}://{form.db_username.data}:{form.db_password.data}@{form.host.data}:{form.port.data}/{form.database.data}"
        
        # Test connection
        engine = create_engine(conn_str)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            
        return jsonify({'success': True})
    except Exception as e:
        error = str(getattr(e, 'orig', e))
        return jsonify({'success': False, 'error': error}), 400

@bp.route('/delete/<int:connector_id>', methods=['POST']) # Use POST for deletion
@login_required
def delete_connector(connector_id):
    """Deletes a connector."""
    connector = db.session.get(Connector, connector_id)
    if not connector or connector.user_id != current_user.id:
        abort(404) # Or 403

    connector_name = connector.name # Get name before deleting
    db.session.delete(connector)
    db.session.commit()
    flash(f'Connector "{connector_name}" deleted successfully!')
    return redirect(url_for('connectors.list_connectors'))
