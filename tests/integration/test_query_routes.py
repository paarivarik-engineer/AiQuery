import pytest
from flask import url_for
from tests.factories import UserFactory, ConnectorFactory
from unittest.mock import patch, MagicMock

class TestQueryRoutes:
    def test_query_interface_requires_login(self, client):
        response = client.get(url_for('query.query_interface'))
        assert response.status_code == 302
        assert '/auth/login' in response.location

    @pytest.mark.usefixtures('logged_in_user')
    def test_query_interface_loads(self, client):
        response = client.get(url_for('query.query_interface'))
        assert response.status_code == 200
        assert b'Execute Query' in response.data

    @pytest.mark.usefixtures('logged_in_user')
    def test_sql_query_execution(self, client, session):
        connector = ConnectorFactory()
        with patch('sqlalchemy.create_engine') as mock_engine:
            mock_conn = MagicMock()
            mock_engine.return_value.connect.return_value.__enter__.return_value = mock_conn
            mock_result = MagicMock()
            mock_result.returns_rows = True
            mock_result.keys.return_value = ['id', 'name']
            mock_result.fetchall.return_value = [(1, 'test')]
            mock_conn.execute.return_value = mock_result

            response = client.post(url_for('query.query_interface'), data={
                'connector': connector.id,
                'query_mode': 'sql',
                'query_input': 'SELECT * FROM test'
            })
            assert response.status_code == 200
            assert b'id' in response.data
            assert b'test' in response.data

    @pytest.mark.usefixtures('logged_in_user')
    @patch('app.query.routes.client')
    def test_nl_query_execution(self, mock_client, client, session):
        connector = ConnectorFactory()
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = 'SELECT * FROM test'
        mock_client.chat.completions.create.return_value = mock_completion

        with patch('sqlalchemy.create_engine') as mock_engine:
            mock_conn = MagicMock()
            mock_engine.return_value.connect.return_value.__enter__.return_value = mock_conn
            mock_result = MagicMock()
            mock_result.returns_rows = True
            mock_result.keys.return_value = ['id', 'name']
            mock_result.fetchall.return_value = [(1, 'test')]
            mock_conn.execute.return_value = mock_result

            response = client.post(url_for('query.query_interface'), data={
                'connector': connector.id,
                'query_mode': 'nl',
                'query_input': 'Show all tests'
            })
            assert response.status_code == 200
            assert b'Generated SQL' in response.data
            assert b'id' in response.data
