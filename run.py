
from app import create_app, db
from app.models import User, Connector # We will create models.py soon
from flask_migrate import Migrate

app = create_app()
migrate = Migrate(app, db)

@app.shell_context_processor
def make_shell_context():
    """Provides access to database and models in Flask shell."""
    return {'db': db, 'User': User, 'Connector': Connector}

if __name__ == '__main__':
    # Consider adding host='0.0.0.0' if running in a container or VM
    # and debug=True only for development
    app.run(debug=True)
