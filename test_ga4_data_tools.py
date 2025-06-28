import pytest
import json
from unittest.mock import patch, MagicMock
from fastmcp import Client
from app import mcp

def extract_text_from_response(response):
    """Extract text from FastMCP response."""
    if isinstance(response, list) and len(response) > 0:
        if hasattr(response[0], 'text'):
            return response[0].text
    return str(response)

# Mock GA4 API objects
class MockDimensionHeader:
    def __init__(self, name):
        self.name = name

class MockMetricHeader:
    def __init__(self, name, type_name="TYPE_INTEGER"):
        self.name = name
        self.type_ = MagicMock()
        self.type_.name = type_name

class MockDimensionValue:
    def __init__(self, value):
        self.value = value

class MockMetricValue:
    def __init__(self, value):
        self.value = value

class MockRow:
    def __init__(self, dimension_values, metric_values):
        self.dimension_values = [MockDimensionValue(v) for v in dimension_values]
        self.metric_values = [MockMetricValue(v) for v in metric_values]

def create_mock_ga4_response(row_count, dimension_headers, metric_headers, rows_data):
    """Create a mock GA4 API response."""
    mock_response = MagicMock()
    mock_response.row_count = row_count
    mock_response.metadata = None
    mock_response.dimension_headers = [MockDimensionHeader(name) for name in dimension_headers]
    mock_response.metric_headers = [MockMetricHeader(name) for name in metric_headers]
    mock_response.rows = [MockRow(row[0], row[1]) for row in rows_data]
    return mock_response

def create_mock_realtime_response(row_count, dimension_headers, metric_headers, rows_data):
    """Create a mock GA4 realtime API response (similar structure)."""
    mock_response = MagicMock()
    mock_response.row_count = row_count
    mock_response.dimension_headers = [MockDimensionHeader(name) for name in dimension_headers]
    mock_response.metric_headers = [MockMetricHeader(name) for name in metric_headers]
    mock_response.rows = [MockRow(row[0], row[1]) for row in rows_data]
    return mock_response

@pytest.fixture
def client():
    """Create a FastMCP client for testing."""
    return Client(mcp)

@pytest.fixture
def mock_authenticated_client():
    """Mock an authenticated GA4 client."""
    import app
    
    # Create mock client instance
    mock_client_instance = MagicMock()
    
    # Create mock credentials
    mock_creds = MagicMock()
    mock_creds.expired = False
    
    # Store original values
    original_client = app._ga4_client
    original_creds = app._oauth_credentials
    
    # Set mock values
    app._ga4_client = mock_client_instance
    app._oauth_credentials = mock_creds
    
    yield mock_client_instance
    
    # Restore original values
    app._ga4_client = original_client
    app._oauth_credentials = original_creds

@pytest.mark.asyncio
async def test_list_properties_not_authenticated(client):
    """Test list_properties when not authenticated."""
    import app
    
    # Ensure not authenticated
    original_client = app._ga4_client
    original_creds = app._oauth_credentials
    app._ga4_client = None
    app._oauth_credentials = None
    
    try:
        async with client:
            result = await client.call_tool("list_properties", {})
            result_text = extract_text_from_response(result)
            assert "Error: Not authenticated" in result_text
    finally:
        # Restore original state
        app._ga4_client = original_client
        app._oauth_credentials = original_creds

@pytest.mark.asyncio
async def test_list_properties_authenticated(client, mock_authenticated_client):
    """Test list_properties when authenticated."""
    async with client:
        result = await client.call_tool("list_properties", {})
        result_text = extract_text_from_response(result)
        assert "To use GA4 data retrieval tools" in result_text
        assert "Property ID" in result_text

@pytest.mark.asyncio
async def test_get_ga4_report_not_authenticated(client):
    """Test get_ga4_report when not authenticated."""
    import app
    
    # Ensure not authenticated
    original_client = app._ga4_client
    original_creds = app._oauth_credentials
    app._ga4_client = None
    app._oauth_credentials = None
    
    try:
        async with client:
            result = await client.call_tool("get_ga4_report", {
                "property_id": "123456789"
            })
            result_text = extract_text_from_response(result)
            assert "Error: Not authenticated" in result_text
    finally:
        # Restore original state
        app._ga4_client = original_client
        app._oauth_credentials = original_creds

@pytest.mark.asyncio
async def test_get_ga4_report_authenticated(client, mock_authenticated_client):
    """Test get_ga4_report when authenticated."""
    # Create mock GA4 response
    mock_response = create_mock_ga4_response(
        row_count=2,
        dimension_headers=["date"],
        metric_headers=["sessions"],
        rows_data=[
            (["2024-01-01"], ["100"]),
            (["2024-01-02"], ["150"])
        ]
    )
    
    mock_authenticated_client.run_report.return_value = mock_response
    
    async with client:
        result = await client.call_tool("get_ga4_report", {
            "property_id": "123456789",
            "start_date": "7daysAgo",
            "end_date": "today",
            "metrics": "sessions",
            "dimensions": "date"
        })
        result_text = extract_text_from_response(result)
        
        # Parse the JSON response
        response_data = json.loads(result_text)
        
        assert response_data["row_count"] == 2
        assert len(response_data["rows"]) == 2
        assert response_data["dimension_headers"] == ["date"]
        assert response_data["metric_headers"][0]["name"] == "sessions"
        assert response_data["rows"][0]["dimensions"] == ["2024-01-01"]
        assert response_data["rows"][0]["metrics"] == ["100"]

@pytest.mark.asyncio
async def test_get_realtime_data_authenticated(client, mock_authenticated_client):
    """Test get_realtime_data when authenticated."""
    # Create mock realtime response
    mock_response = create_mock_realtime_response(
        row_count=1,
        dimension_headers=["country"],
        metric_headers=["activeUsers"],
        rows_data=[
            (["United States"], ["50"])
        ]
    )
    
    mock_authenticated_client.run_realtime_report.return_value = mock_response
    
    async with client:
        result = await client.call_tool("get_realtime_data", {
            "property_id": "123456789"
        })
        result_text = extract_text_from_response(result)
        
        # Parse the JSON response
        response_data = json.loads(result_text)
        
        assert response_data["row_count"] == 1
        assert len(response_data["rows"]) == 1
        assert response_data["dimension_headers"] == ["country"]
        assert response_data["rows"][0]["dimensions"] == ["United States"]
        assert response_data["rows"][0]["metrics"] == ["50"]

@pytest.mark.asyncio
async def test_get_ga4_audience_data_authenticated(client, mock_authenticated_client):
    """Test get_ga4_audience_data when authenticated."""
    # Create mock audience data response
    mock_response = create_mock_ga4_response(
        row_count=1,
        dimension_headers=["country", "city", "deviceCategory", "operatingSystem"],
        metric_headers=["users", "newUsers", "sessions", "engagedSessions", "averageSessionDuration"],
        rows_data=[
            (["United States", "New York", "desktop", "Windows"], ["1000", "300", "1500", "800", "120.5"])
        ]
    )
    
    mock_authenticated_client.run_report.return_value = mock_response
    
    async with client:
        result = await client.call_tool("get_ga4_audience_data", {
            "property_id": "123456789"
        })
        result_text = extract_text_from_response(result)
        
        # Parse the JSON response
        response_data = json.loads(result_text)
        
        assert response_data["row_count"] == 1
        assert len(response_data["dimension_headers"]) == 4
        assert len(response_data["metric_headers"]) == 5
        assert response_data["rows"][0]["dimensions"] == ["United States", "New York", "desktop", "Windows"]

@pytest.mark.asyncio
async def test_get_popular_pages_authenticated(client, mock_authenticated_client):
    """Test get_popular_pages when authenticated."""
    # Create mock popular pages response
    mock_response = create_mock_ga4_response(
        row_count=2,
        dimension_headers=["pageTitle", "pagePath"],
        metric_headers=["screenPageViews", "users", "sessions", "averageSessionDuration", "bounceRate"],
        rows_data=[
            (["Home Page", "/"], ["5000", "1200", "1500", "180.5", "0.25"]),
            (["About Page", "/about"], ["2000", "800", "900", "210.3", "0.15"])
        ]
    )
    
    mock_authenticated_client.run_report.return_value = mock_response
    
    async with client:
        result = await client.call_tool("get_popular_pages", {
            "property_id": "123456789"
        })
        result_text = extract_text_from_response(result)
        
        # Parse the JSON response
        response_data = json.loads(result_text)
        
        assert response_data["row_count"] == 2
        assert len(response_data["rows"]) == 2
        assert response_data["rows"][0]["dimensions"] == ["Home Page", "/"]
        assert response_data["rows"][1]["dimensions"] == ["About Page", "/about"]

@pytest.mark.asyncio
async def test_property_id_format_handling(client, mock_authenticated_client):
    """Test that property ID format is handled correctly."""
    mock_response = create_mock_ga4_response(
        row_count=0,
        dimension_headers=[],
        metric_headers=[],
        rows_data=[]
    )
    
    mock_authenticated_client.run_report.return_value = mock_response
    
    async with client:
        # Test with numeric property ID (should be converted)
        result1 = await client.call_tool("get_ga4_report", {
            "property_id": "123456789"
        })
        
        # Test with already formatted property ID (should remain unchanged)
        result2 = await client.call_tool("get_ga4_report", {
            "property_id": "properties/123456789"
        })
        
        # Both should work and return valid JSON
        result1_text = extract_text_from_response(result1)
        result2_text = extract_text_from_response(result2)
        
        response1 = json.loads(result1_text)
        response2 = json.loads(result2_text)
        
        assert response1["row_count"] == 0
        assert response2["row_count"] == 0

if __name__ == "__main__":
    pytest.main([__file__])