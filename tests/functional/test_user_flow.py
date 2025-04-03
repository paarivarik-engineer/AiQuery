import pytest
from flask import url_for
from tests.factories import UserFactory

class TestUserFlow:
    def test_full_user_flow(self, client, session):
        # Registration
        response = client.post(url_for('auth.register'), data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password',
            'password2': 'password'
        }, follow_redirects=True)
        assert b'registered successfully' in response.data

        # Login
        response = client.post(url_for('auth.login'), data={
            'username': 'testuser',
            'password': 'password'
        }, follow_redirects=True)
        assert b'Welcome' in response.data

        # Add connector
        response = client.post(url_for('connectors.add_connector'), data={
            'name': 'Test DB',
            'db_type': 'postgresql',
            'host': 'localhost',
            'port': 5432,
            'database': 'testdb',
            'db_username': 'user',
            'db_password': 'pass'
        }, follow_redirects=True)
        assert b'Connector added successfully' in response.data

        # Execute query
        with patch('sqlalchemy.create_engine') as mock_engine:
            mock_conn = MagicMock()
            mock_engine.return_value.connect.return_value.__enter__.return_value = mock_conn
            mock_result = MagicMock()
            mock_result.returns_rows = True
            mock_result.keys.return_value = ['id', 'name']
            mock_result.fetchall.return_value = [(1, 'test')]
            mock_conn.execute.return_value = mock_result

            response = client.post(url_for('query.query_interface'), data={
                'connector': 1,
                'query_mode': 'sql',
                'query_input': 'SELECT * FROM test'
            })
            assert b'id' in response.data
            assert b'test' in response.data

        # Logout
        response = client.get(url_for('auth.logout'), follow_redirects=True)
        assert b'You have been logged out' in response.data
