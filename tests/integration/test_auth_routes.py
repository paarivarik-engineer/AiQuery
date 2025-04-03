import pytest
from flask import url_for
from tests.factories import UserFactory

class TestAuthRoutes:
    def test_login(self, client, session):
        user = UserFactory(password='password')
        response = client.post(url_for('auth.login'), data={
            'username': user.username,
            'password': 'password'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Welcome' in response.data

    def test_invalid_login(self, client, session):
        user = UserFactory(password='password')
        response = client.post(url_for('auth.login'), data={
            'username': user.username,
            'password': 'wrong'
        })
        assert b'Invalid username or password' in response.data

    def test_registration(self, client, session):
        response = client.post(url_for('auth.register'), data={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'password',
            'password2': 'password'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'registered successfully' in response.data

    def test_password_reset_flow(self, client, session):
        user = UserFactory()
        
        # Request reset
        response = client.post(url_for('auth.reset_password_request'), 
            data={'email': user.email}, follow_redirects=True)
        assert b'Check your email' in response.data
        
        # Get token (in real app this would come from email)
        token = user.get_reset_password_token()
        
        # Reset password
        response = client.post(url_for('auth.reset_password', token=token), 
            data={'password': 'newpass', 'password2': 'newpass'},
            follow_redirects=True)
        assert b'Your password has been reset' in response.data
