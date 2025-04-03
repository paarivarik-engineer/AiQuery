import os
from dotenv import load_dotenv
from unittest.mock import patch

# Load test environment variables
load_dotenv('.env.test')

class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv('TEST_DATABASE_URL', 
        'postgresql://aiquery:aiquery@localhost:5432/aiquery_test')
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key'
    OPENROUTER_API_KEY = 'test-key' if not os.getenv('OPENROUTER_API_KEY') else os.getenv('OPENROUTER_API_KEY')
