"""Integration tests for the refactored GA4 MCP Server."""

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
    """Create GA4MCPServer instance for testing."""
    return GA4MCPServer()


@pytest.fixture  
def client(server):
    """Create FastMCP client for testing."""
    return Client(server.get_mcp_instance())


@pytest.fixture
def cleanup():
    """Cleanup test files after each test."""
    yield
    # Cleanup test files
    for file in ['.oauth_flow_state.json', '.ga4_credentials.json']:
        if os.path.exists(file):
            os.remove(file)


@pytest.mark.asyncio
async def test_server_initialization(server):
    """Test that server initializes correctly."""
    assert server is not None
    assert server.mcp is not None
    assert server.settings is not None
    assert server.oauth_manager is not None
    assert server.ga4_client is not None


@pytest.mark.asyncio
async def test_check_auth_status_not_authenticated(client, cleanup):
    """Test check_auth_status when not authenticated."""
    async with client:
        result = await client.call_tool("check_auth_status", {})
        result_text = extract_text_from_response(result)
        assert "Not authenticated" in result_text


@pytest.mark.asyncio
async def test_debug_env_vars(client):
    """Test debug_env_vars tool."""
    async with client:
        result = await client.call_tool("debug_env_vars", {})
        result_text = extract_text_from_response(result)
        
        # Should return valid JSON
        debug_data = json.loads(result_text)
        assert "env_file_exists" in debug_data
        assert "variables" in debug_data


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
        assert 'available_tools' in config_data
        
        expected_tools = [
            "start_oauth_flow",
            "complete_oauth_flow", 
            "load_saved_credentials",
            "check_auth_status",
            "debug_env_vars"
        ]
        
        for tool in expected_tools:
            assert tool in config_data['available_tools']


@pytest.mark.asyncio
async def test_oauth_flow_missing_env_vars(client, cleanup):
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
        
        # Reinitialize server with missing env vars
        server = GA4MCPServer()
        test_client = Client(server.get_mcp_instance())
        
        async with test_client:
            result = await test_client.call_tool("start_oauth_flow", {})
            result_text = extract_text_from_response(result)
            assert "Error starting OAuth flow" in result_text
    
    finally:
        # Restore original values
        if original_client_id:
            os.environ['GA4_CLIENT_ID'] = original_client_id
        if original_client_secret:
            os.environ['GA4_CLIENT_SECRET'] = original_client_secret


@pytest.mark.asyncio
async def test_list_properties_not_authenticated(client):
    """Test list_properties when not authenticated."""
    async with client:
        result = await client.call_tool("list_properties", {})
        result_text = extract_text_from_response(result)
        assert "Error: Not authenticated" in result_text


@pytest.mark.asyncio
async def test_get_ga4_report_not_authenticated(client):
    """Test get_ga4_report when not authenticated."""
    async with client:
        result = await client.call_tool("get_ga4_report", {
            "property_id": "123456789"
        })
        result_text = extract_text_from_response(result)
        assert "Error: Not authenticated" in result_text


if __name__ == "__main__":
    pytest.main([__file__])