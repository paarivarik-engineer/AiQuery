import pytest
from flask import url_for
from tests.factories import UserFactory, ConnectorFactory

class TestAdminRoutes:
    def test_admin_requires_admin_role(self, client, session):
        user = UserFactory(is_admin=False)
        client.post(url_for('auth.login'), data={
            'username': user.username,
            'password': 'password'
        })
        response = client.get(url_for('admin.index'))
        assert response.status_code == 403

    def test_admin_access(self, client, session):
        admin = UserFactory(is_admin=True)
        client.post(url_for('auth.login'), data={
            'username': admin.username,
            'password': 'password'
        })
        response = client.get(url_for('admin.index'))
        assert response.status_code == 200
        assert b'Admin Dashboard' in response.data

    def test_user_management(self, client, session):
        admin = UserFactory(is_admin=True)
        user = UserFactory()
        client.post(url_for('auth.login'), data={
            'username': admin.username,
            'password': 'password'
        })
        response = client.get(url_for('admin.manage_users'))
        assert response.status_code == 200
        assert user.username.encode() in response.data

    def test_connector_management(self, client, session):
        admin = UserFactory(is_admin=True)
        connector = ConnectorFactory()
        client.post(url_for('auth.login'), data={
            'username': admin.username,
            'password': 'password'
        })
        response = client.get(url_for('admin.manage_connectors'))
        assert response.status_code == 200
        assert connector.name.encode() in response.data
