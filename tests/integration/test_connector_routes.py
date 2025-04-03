import pytest
from flask import url_for
from tests.factories import UserFactory, ConnectorFactory
from app.models import DatabaseType

class TestConnectorRoutes:
    def test_connector_creation(self, client, session):
        user = UserFactory()
        client.post(url_for('auth.login'), data={
            'username': user.username,
            'password': 'password'
        })
        response = client.post(url_for('connectors.add_connector'), data={
            'name': 'Test Connector',
            'db_type': DatabaseType.POSTGRESQL.value,
            'host': 'localhost',
            'port': 5432,
            'database': 'testdb',
            'db_username': 'admin',
            'db_password': 'secret'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Connector added successfully' in response.data

    def test_connector_list(self, client, session):
        user = UserFactory()
        connector = ConnectorFactory(user=user)
        client.post(url_for('auth.login'), data={
            'username': user.username,
            'password': 'password'
        })
        response = client.get(url_for('connectors.list_connectors'))
        assert response.status_code == 200
        assert connector.name.encode() in response.data

    def test_connector_edit(self, client, session):
        user = UserFactory()
        connector = ConnectorFactory(user=user)
        client.post(url_for('auth.login'), data={
            'username': user.username,
            'password': 'password'
        })
        response = client.post(url_for('connectors.edit_connector', connector_id=connector.id), data={
            'name': 'Updated Connector',
            'db_type': DatabaseType.MYSQL.value,
            'host': 'newhost',
            'port': 3306,
            'database': 'newdb',
            'db_username': 'newuser',
            'db_password': 'newpass'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Connector updated successfully' in response.data
        assert b'Updated Connector' in response.data
