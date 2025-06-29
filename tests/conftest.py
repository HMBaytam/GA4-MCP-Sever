"""Pytest configuration and shared fixtures."""

import pytest
import os
import json
from unittest.mock import patch, MagicMock
from fastmcp import Client

from src.server import GA4MCPServer


def extract_text_from_response(response):
    """Extract text from FastMCP response."""
    if isinstance(response, list) and len(response) > 0:
        if hasattr(response[0], 'text'):
            return response[0].text
    return str(response)


@pytest.fixture
def server():
    """Create a GA4MCPServer instance for testing."""
    return GA4MCPServer()


@pytest.fixture
def client(server):
    """Create a FastMCP client for testing."""
    return Client(server.get_mcp_instance())


@pytest.fixture
def cleanup():
    """Cleanup test files after each test."""
    yield
    # Cleanup test files
    for file in ['.oauth_flow_state.json', '.ga4_credentials.json']:
        if os.path.exists(file):
            os.remove(file)


@pytest.fixture
def mock_credentials():
    """Mock credentials data for testing."""
    return {
        'token': 'mock_access_token',
        'refresh_token': 'mock_refresh_token',
        'token_uri': 'https://oauth2.googleapis.com/token',
        'client_id': 'test_client_id',
        'client_secret': 'test_client_secret',
        'scopes': ['https://www.googleapis.com/auth/analytics.readonly']
    }


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    original_client_id = os.environ.get('GA4_CLIENT_ID')
    original_client_secret = os.environ.get('GA4_CLIENT_SECRET')
    
    # Set test env vars
    os.environ['GA4_CLIENT_ID'] = 'test_client_id'
    os.environ['GA4_CLIENT_SECRET'] = 'test_client_secret'
    
    yield
    
    # Restore original values
    if original_client_id:
        os.environ['GA4_CLIENT_ID'] = original_client_id
    elif 'GA4_CLIENT_ID' in os.environ:
        del os.environ['GA4_CLIENT_ID']
        
    if original_client_secret:
        os.environ['GA4_CLIENT_SECRET'] = original_client_secret
    elif 'GA4_CLIENT_SECRET' in os.environ:
        del os.environ['GA4_CLIENT_SECRET']


@pytest.fixture
def mock_authenticated_server(server, mock_credentials):
    """Mock an authenticated server for testing."""
    # Create mock credentials file
    with open('.ga4_credentials.json', 'w') as f:
        json.dump(mock_credentials, f)
    
    with patch('src.analytics.ga4_client.BetaAnalyticsDataClient') as mock_client:
        with patch('src.analytics.ga4_client.AnalyticsAdminServiceClient') as mock_admin:
            mock_client_instance = MagicMock()
            mock_admin_instance = MagicMock()
            
            mock_client.return_value = mock_client_instance
            mock_admin.return_value = mock_admin_instance
            
            # Load credentials into server
            server.oauth_manager.load_saved_credentials()
            
            yield server, mock_client_instance, mock_admin_instance
    
    # Cleanup
    if os.path.exists('.ga4_credentials.json'):
        os.remove('.ga4_credentials.json')