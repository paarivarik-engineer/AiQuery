import pytest
from app.models import User, Connector, DatabaseType
from tests.factories import UserFactory, ConnectorFactory

class TestUserModel:
    def test_password_setter(self):
        user = User(password='test')
        assert user.password_hash is not None

    def test_no_password_getter(self):
        user = User(password='test')
        with pytest.raises(AttributeError):
            user.password

    def test_password_verification(self):
        user = User(password='test')
        assert user.check_password('test')
        assert not user.check_password('wrong')

    def test_password_salts_random(self):
        u1 = User(password='test')
        u2 = User(password='test')
        assert u1.password_hash != u2.password_hash

    def test_get_reset_token(self, session):
        user = UserFactory()
        token = user.get_reset_password_token()
        assert token is not None
        assert User.verify_reset_password_token(token) == user

    def test_invalid_reset_token(self):
        assert User.verify_reset_password_token('invalid') is None

class TestConnectorModel:
    def test_connection_string(self):
        connector = ConnectorFactory(
            db_type=DatabaseType.POSTGRESQL,
            host='localhost',
            port=5432,
            database='testdb',
            db_username='admin',
            db_password='secret'
        )
        assert 'postgresql://admin:secret@localhost:5432/testdb' in connector.get_connection_string()

    def test_connector_ownership(self, session):
        user = UserFactory()
        connector = ConnectorFactory(user=user)
        assert connector.user_id == user.id
        assert connector in user.connectors
