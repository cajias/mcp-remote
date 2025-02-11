"""Tests for Cognito authentication implementation"""

import os
import pytest
from unittest.mock import MagicMock

from mpc_remote.security.cognito_authenticator import CognitoAuthenticator
from mpc_remote.security.cognito_auth_integration import CognitoAuthIntegration


@pytest.fixture
def mock_cognito_env():
    """Set up mock Cognito environment variables"""
    original_env = {
        'COGNITO_POOL_ID': os.getenv('COGNITO_POOL_ID'),
        'AWS_REGION': os.getenv('AWS_REGION'),
        'COGNITO_CLIENT_ID': os.getenv('COGNITO_CLIENT_ID')
    }

    # Set test environment variables
    os.environ['COGNITO_POOL_ID'] = 'test-pool-id'
    os.environ['AWS_REGION'] = 'us-east-1'
    os.environ['COGNITO_CLIENT_ID'] = 'test-client-id'

    yield

    # Restore original environment variables
    for key, value in original_env.items():
        if value is None:
            del os.environ[key]
        else:
            os.environ[key] = value


def test_cognito_authenticator_initialization(mock_cognito_env):
    """Test Cognito authenticator initialization"""
    authenticator = CognitoAuthenticator()

    assert authenticator.pool_id == 'test-pool-id'
    assert authenticator.region == 'us-east-1'
    assert authenticator.client_id == 'test-client-id'
    assert authenticator.jwks_url == 'https://cognito-idp.us-east-1.amazonaws.com/test-pool-id/.well-known/jwks.json'


@pytest.mark.skip(reason='Requires AWS credentials')
def test_initiate_auth(mock_cognito_env):
    """Test user authentication"""
    authenticator = CognitoAuthenticator()
    assert authenticator.cognito_client is None



def test_cognito_auth_integration(mock_cognito_env):
    """Test Cognito authentication integration"""
    auth_integration = CognitoAuthIntegration()

    # Verify integration creates a CognitoAuthenticator
    assert hasattr(auth_integration, 'authenticator')
    assert isinstance(auth_integration.authenticator, CognitoAuthenticator)

    # Verify key methods exist
    assert hasattr(auth_integration, 'authenticate')
    assert hasattr(auth_integration, 'validate_token')
    assert hasattr(auth_integration, 'refresh_tokens')
