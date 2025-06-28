import pytest
import os
import json
from unittest.mock import patch, MagicMock
from fastmcp import Client
from app import mcp, _ga4_client, _oauth_credentials

def extract_text_from_response(response):
    """Extract text from FastMCP response."""
    if isinstance(response, list) and len(response) > 0:
        if hasattr(response[0], 'text'):
            return response[0].text
    return str(response)

@pytest.fixture
def client():
    """Create a FastMCP client for testing."""
    return Client(mcp)

@pytest.fixture
def cleanup():
    """Cleanup test files after each test."""
    yield
    # Cleanup test files
    for file in ['.oauth_flow_state.json', '.ga4_credentials.json']:
        if os.path.exists(file):
            os.remove(file)

@pytest.mark.asyncio
async def test_check_auth_status_not_authenticated(client, cleanup):
    """Test check_auth_status when not authenticated."""
    async with client:
        result = await client.call_tool("check_auth_status", {})
        result_text = extract_text_from_response(result)
        assert "Not authenticated" in result_text

@pytest.mark.asyncio
async def test_load_saved_credentials_no_file(client, cleanup):
    """Test load_saved_credentials when no credentials file exists."""
    # Ensure no credentials file exists
    if os.path.exists('.ga4_credentials.json'):
        os.remove('.ga4_credentials.json')
    
    async with client:
        result = await client.call_tool("load_saved_credentials", {})
        result_text = extract_text_from_response(result)
        assert "No saved credentials found" in result_text

@pytest.mark.asyncio
async def test_start_oauth_flow_missing_env_vars(client, cleanup):
    """Test start_oauth_flow without required environment variables."""
    # Store original values
    original_client_id = os.environ.get('GA4_CLIENT_ID')
    original_client_secret = os.environ.get('GA4_CLIENT_SECRET')
    
    try:
        # Remove env vars
        if 'GA4_CLIENT_ID' in os.environ:
            del os.environ['GA4_CLIENT_ID']
        if 'GA4_CLIENT_SECRET' in os.environ:
            del os.environ['GA4_CLIENT_SECRET']
        
        async with client:
            result = await client.call_tool("start_oauth_flow", {})
            result_text = extract_text_from_response(result)
            assert "GA4_CLIENT_ID and GA4_CLIENT_SECRET environment variables must be set" in result_text
    
    finally:
        # Restore original values
        if original_client_id:
            os.environ['GA4_CLIENT_ID'] = original_client_id
        if original_client_secret:
            os.environ['GA4_CLIENT_SECRET'] = original_client_secret

@pytest.mark.asyncio
async def test_start_oauth_flow_with_env_vars(client, cleanup):
    """Test start_oauth_flow with mock environment variables."""
    # Store original values
    original_client_id = os.environ.get('GA4_CLIENT_ID')
    original_client_secret = os.environ.get('GA4_CLIENT_SECRET')
    
    try:
        # Set test env vars
        os.environ['GA4_CLIENT_ID'] = 'test_client_id'
        os.environ['GA4_CLIENT_SECRET'] = 'test_client_secret'
        
        async with client:
            result = await client.call_tool("start_oauth_flow", {})
            result_text = extract_text_from_response(result)
            
            assert "Please visit this URL to authorize" in result_text
            assert "https://accounts.google.com/o/oauth2/auth" in result_text
            
            # Verify flow state file was created
            assert os.path.exists('.oauth_flow_state.json')
            
            with open('.oauth_flow_state.json', 'r') as f:
                flow_state = json.load(f)
            
            assert 'client_config' in flow_state
            assert 'state' in flow_state
            assert flow_state['client_config']['web']['client_id'] == 'test_client_id'
    
    finally:
        # Restore original values
        if original_client_id:
            os.environ['GA4_CLIENT_ID'] = original_client_id
        elif 'GA4_CLIENT_ID' in os.environ:
            del os.environ['GA4_CLIENT_ID']
            
        if original_client_secret:
            os.environ['GA4_CLIENT_SECRET'] = original_client_secret
        elif 'GA4_CLIENT_SECRET' in os.environ:
            del os.environ['GA4_CLIENT_SECRET']

@pytest.mark.asyncio
async def test_load_saved_credentials_with_mock_file(client, cleanup):
    """Test load_saved_credentials with a mock credentials file."""
    mock_credentials = {
        'token': 'mock_access_token',
        'refresh_token': 'mock_refresh_token',
        'token_uri': 'https://oauth2.googleapis.com/token',
        'client_id': 'test_client_id',
        'client_secret': 'test_client_secret',
        'scopes': ['https://www.googleapis.com/auth/analytics.readonly']
    }
    
    # Create mock credentials file
    with open('.ga4_credentials.json', 'w') as f:
        json.dump(mock_credentials, f)
    
    with patch('app.BetaAnalyticsDataClient') as mock_client:
        mock_client.return_value = MagicMock()
        
        async with client:
            result = await client.call_tool("load_saved_credentials", {})
            result_text = extract_text_from_response(result)
            assert "Saved credentials loaded successfully" in result_text
            mock_client.assert_called_once()

@pytest.mark.asyncio
async def test_load_saved_credentials_corrupted_file(client, cleanup):
    """Test load_saved_credentials with corrupted credentials file."""
    # Create corrupted file
    with open('.ga4_credentials.json', 'w') as f:
        f.write("invalid json content")
    
    async with client:
        result = await client.call_tool("load_saved_credentials", {})
        result_text = extract_text_from_response(result)
        assert "Error loading saved credentials" in result_text

@pytest.mark.asyncio
async def test_ga4_config_resource(client):
    """Test the GA4 configuration resource."""
    async with client:
        raw_config = await client.read_resource("data://ga4_config")
        
        # Extract JSON from resource response
        config_text = raw_config[0].text if hasattr(raw_config[0], 'text') else str(raw_config)
        config_data = json.loads(config_text)
        
        # Verify expected fields
        assert config_data['server_name'] == "Google Analytics 4 MCP Server"
        assert config_data['version'] == "1.0.0"
        assert 'authenticated' in config_data
        assert 'scopes' in config_data
        assert 'available_tools' in config_data
        
        expected_tools = [
            "start_oauth_flow",
            "complete_oauth_flow", 
            "load_saved_credentials",
            "check_auth_status"
        ]
        
        for tool in expected_tools:
            assert tool in config_data['available_tools']

@pytest.mark.asyncio 
async def test_check_auth_status_authenticated(client, cleanup):
    """Test check_auth_status when authenticated."""
    # Create mock credentials file to simulate authentication
    mock_credentials = {
        'token': 'mock_access_token',
        'refresh_token': 'mock_refresh_token',
        'token_uri': 'https://oauth2.googleapis.com/token',
        'client_id': 'test_client_id',
        'client_secret': 'test_client_secret',
        'scopes': ['https://www.googleapis.com/auth/analytics.readonly']
    }
    
    with open('.ga4_credentials.json', 'w') as f:
        json.dump(mock_credentials, f)
    
    with patch('app.BetaAnalyticsDataClient') as mock_client:
        mock_client.return_value = MagicMock()
        
        async with client:
            # Load credentials first
            await client.call_tool("load_saved_credentials", {})
            
            # Then check auth status
            result = await client.call_tool("check_auth_status", {})
            result_text = extract_text_from_response(result)
            assert "Authenticated and ready" in result_text

if __name__ == "__main__":
    pytest.main([__file__])