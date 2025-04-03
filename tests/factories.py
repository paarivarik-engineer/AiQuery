import factory
from factory.alchemy import SQLAlchemyModelFactory
from app.models import User, Connector, DatabaseType
from app import db

class BaseFactory(SQLAlchemyModelFactory):
    class Meta:
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = 'commit'

class UserFactory(BaseFactory):
    class Meta:
        model = User

    username = factory.Faker('user_name')
    email = factory.Faker('email')
    password = factory.PostGenerationMethodCall('set_password', 'password')

class ConnectorFactory(BaseFactory):
    class Meta:
        model = Connector

    name = factory.Faker('word')
    db_type = DatabaseType.POSTGRESQL
    host = factory.Faker('hostname')
    port = 5432
    database = factory.Faker('word')
    db_username = factory.Faker('user_name')
    db_password = factory.Faker('password')
