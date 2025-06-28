from fastmcp import FastMCP, Client
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.admin_v1beta import AnalyticsAdminServiceClient
from google.analytics.data_v1beta.types import (
    RunReportRequest,
    RunRealtimeReportRequest,
    Dimension,
    Metric,
    DateRange,
    OrderBy,
    Filter,
    FilterExpression
)
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Instantiate the server, giving it a name
mcp = FastMCP(name="Google Analytics 4 MCP Server")

# Global variables for OAuth and GA4 clients
_ga4_client: Optional[BetaAnalyticsDataClient] = None
_admin_client: Optional[AnalyticsAdminServiceClient] = None
_oauth_credentials: Optional[Credentials] = None

# OAuth2 Configuration
SCOPES = [
    'https://www.googleapis.com/auth/analytics.readonly',
    'https://www.googleapis.com/auth/analytics.manage.users.readonly'
]
REDIRECT_URI = 'http://localhost:8080'  # For installed applications

print("Google Analytics 4 MCP server object created.")

def _get_oauth_client_config() -> dict:
    """Get OAuth client configuration from environment variables."""
    client_id = os.getenv('GA4_CLIENT_ID')
    client_secret = os.getenv('GA4_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        missing = []
        if not client_id:
            missing.append('GA4_CLIENT_ID')
        if not client_secret:
            missing.append('GA4_CLIENT_SECRET')
        
        raise ValueError(f"Missing environment variables: {', '.join(missing)}. "
                        f"Please set them in your .env file or environment. "
                        f"Current GA4_CLIENT_ID: {'[SET]' if client_id else '[NOT SET]'}, "
                        f"GA4_CLIENT_SECRET: {'[SET]' if client_secret else '[NOT SET]'}")
    
    return {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [REDIRECT_URI]
        }
    }

@mcp.tool()
def start_oauth_flow() -> str:
    """Start OAuth2 flow and return authorization URL."""
    try:
        client_config = _get_oauth_client_config()
        flow = Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
        
        auth_url, state = flow.authorization_url(prompt='consent')
        
        # Store flow state for completion
        flow_state = {
            'client_config': client_config,
            'state': state
        }
        
        # In a real implementation, you'd store this securely
        with open('.oauth_flow_state.json', 'w') as f:
            json.dump(flow_state, f)
        
        return f"Please visit this URL to authorize the application: {auth_url}"
        
    except Exception as e:
        return f"Error starting OAuth flow: {str(e)}"

@mcp.tool()
def complete_oauth_flow(authorization_code: str) -> str:
    """Complete OAuth2 flow with authorization code."""
    global _oauth_credentials, _ga4_client, _admin_client
    
    try:
        # Load flow state
        with open('.oauth_flow_state.json', 'r') as f:
            flow_state = json.load(f)
        
        flow = Flow.from_client_config(
            flow_state['client_config'],
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI,
            state=flow_state['state']
        )
        
        # Exchange authorization code for tokens
        flow.fetch_token(code=authorization_code)
        
        _oauth_credentials = flow.credentials
        _ga4_client = BetaAnalyticsDataClient(credentials=_oauth_credentials)
        _admin_client = AnalyticsAdminServiceClient(credentials=_oauth_credentials)
        
        # Save credentials for future use
        creds_data = {
            'token': _oauth_credentials.token,
            'refresh_token': _oauth_credentials.refresh_token,
            'token_uri': _oauth_credentials.token_uri,
            'client_id': _oauth_credentials.client_id,
            'client_secret': _oauth_credentials.client_secret,
            'scopes': _oauth_credentials.scopes
        }
        
        with open('.ga4_credentials.json', 'w') as f:
            json.dump(creds_data, f)
        
        # Clean up flow state
        if os.path.exists('.oauth_flow_state.json'):
            os.remove('.oauth_flow_state.json')
        
        return "OAuth2 authentication completed successfully. GA4 client is now ready."
        
    except Exception as e:
        return f"Error completing OAuth flow: {str(e)}"

@mcp.tool()
def load_saved_credentials() -> str:
    """Load previously saved OAuth2 credentials."""
    global _oauth_credentials, _ga4_client, _admin_client
    
    try:
        if not os.path.exists('.ga4_credentials.json'):
            return "No saved credentials found. Please run start_oauth_flow first."
        
        with open('.ga4_credentials.json', 'r') as f:
            creds_data = json.load(f)
        
        _oauth_credentials = Credentials(
            token=creds_data.get('token'),
            refresh_token=creds_data.get('refresh_token'),
            token_uri=creds_data.get('token_uri'),
            client_id=creds_data.get('client_id'),
            client_secret=creds_data.get('client_secret'),
            scopes=creds_data.get('scopes')
        )
        
        _ga4_client = BetaAnalyticsDataClient(credentials=_oauth_credentials)
        _admin_client = AnalyticsAdminServiceClient(credentials=_oauth_credentials)
        
        return "Saved credentials loaded successfully. GA4 and Admin clients are ready."
        
    except Exception as e:
        return f"Error loading saved credentials: {str(e)}"

@mcp.tool()
def check_auth_status() -> str:
    """Check if GA4 client is authenticated and ready."""
    if _ga4_client is None:
        return "Not authenticated. Use start_oauth_flow or load_saved_credentials first."
    
    if _oauth_credentials and _oauth_credentials.expired:
        return "Credentials expired. Please re-authenticate using start_oauth_flow."
    
    return "Authenticated and ready to access Google Analytics 4 data."

@mcp.tool()
def debug_env_vars() -> str:
    """Debug environment variables for GA4 configuration."""
    client_id = os.getenv('GA4_CLIENT_ID')
    client_secret = os.getenv('GA4_CLIENT_SECRET')
    property_id = os.getenv('GA4_PROPERTY_ID')
    
    # Check if .env file exists
    env_file_exists = os.path.exists('.env')
    
    result = {
        "env_file_exists": env_file_exists,
        "variables": {
            "GA4_CLIENT_ID": "[SET]" if client_id else "[NOT SET]",
            "GA4_CLIENT_SECRET": "[SET]" if client_secret else "[NOT SET]", 
            "GA4_PROPERTY_ID": property_id if property_id else "[NOT SET]"
        }
    }
    
    if client_id:
        result["variables"]["GA4_CLIENT_ID_preview"] = f"{client_id[:10]}..."
    
    return json.dumps(result, indent=2)

@mcp.tool()
def debug_list_properties() -> str:
    """Debug version of list_properties with more detailed output."""
    auth_error = _ensure_authenticated()
    if auth_error:
        return auth_error
    
    if _admin_client is None:
        return "Error: Admin client not initialized. Please re-authenticate to access property listing."
    
    try:
        # First try to list all properties without filter
        debug_info = {
            "api_attempts": [],
            "final_result": None
        }
        
        # Attempt 1: Try with request object and parent filter
        try:
            from google.analytics.admin_v1beta.types import ListPropertiesRequest
            
            request = ListPropertiesRequest(filter="parent:accounts/*")
            all_properties = _admin_client.list_properties(request=request)
            
            properties_list = []
            for property in all_properties:
                properties_list.append({
                    "name": property.name,
                    "display_name": property.display_name,
                    "parent": getattr(property, 'parent', 'NO PARENT ATTRIBUTE'),
                    "has_parent_attr": hasattr(property, 'parent')
                })
            
            debug_info["api_attempts"].append({
                "method": "list_properties(request with parent:accounts/*)",
                "success": True,
                "property_count": len(properties_list)
            })
            
            debug_info["final_result"] = {
                "method_used": "request object with parent filter",
                "properties": properties_list
            }
            
        except Exception as e1:
            debug_info["api_attempts"].append({
                "method": "list_properties(request with parent:accounts/*)", 
                "success": False,
                "error": str(e1)
            })
            
            # Attempt 2: Try with ancestor filter
            try:
                from google.analytics.admin_v1beta.types import ListPropertiesRequest
                
                request = ListPropertiesRequest(filter="ancestor:accounts/*")
                filtered_properties = _admin_client.list_properties(request=request)
                
                properties_list = []
                for property in filtered_properties:
                    properties_list.append({
                        "name": property.name,
                        "display_name": property.display_name,
                        "parent": getattr(property, 'parent', 'NO PARENT ATTRIBUTE'),
                        "has_parent_attr": hasattr(property, 'parent')
                    })
                
                debug_info["api_attempts"].append({
                    "method": "list_properties(request with ancestor:accounts/*)",
                    "success": True,
                    "property_count": len(properties_list)
                })
                
                debug_info["final_result"] = {
                    "method_used": "request object with ancestor filter",
                    "properties": properties_list
                }
                
            except Exception as e2:
                debug_info["api_attempts"].append({
                    "method": "list_properties(request with ancestor:accounts/*)",
                    "success": False, 
                    "error": str(e2)
                })
                
                # Attempt 3: Try without any filter in request
                try:
                    from google.analytics.admin_v1beta.types import ListPropertiesRequest
                    
                    request = ListPropertiesRequest()
                    no_filter_properties = _admin_client.list_properties(request=request)
                    
                    properties_list = []
                    for property in no_filter_properties:
                        properties_list.append({
                            "name": property.name,
                            "display_name": property.display_name,
                            "parent": getattr(property, 'parent', 'NO PARENT ATTRIBUTE'),
                            "has_parent_attr": hasattr(property, 'parent')
                        })
                    
                    debug_info["api_attempts"].append({
                        "method": "list_properties(empty request object)",
                        "success": True,
                        "property_count": len(properties_list)
                    })
                    
                    debug_info["final_result"] = {
                        "method_used": "empty request object",
                        "properties": properties_list
                    }
                    
                except Exception as e3:
                    debug_info["api_attempts"].append({
                        "method": "list_properties(empty request object)",
                        "success": False,
                        "error": str(e3)
                    })
        
        return json.dumps(debug_info, indent=2)
        
    except Exception as e:
        return f"Error in debug list properties: {str(e)}"

print("OAuth2 authentication tools added.")

# Helper functions for GA4 data processing
def _ensure_authenticated() -> str:
    """Check if client is authenticated and return error message if not."""
    if _ga4_client is None:
        return "Error: Not authenticated. Use start_oauth_flow or load_saved_credentials first."
    
    if _oauth_credentials and _oauth_credentials.expired:
        return "Error: Credentials expired. Please re-authenticate using start_oauth_flow."
    
    return ""

def _format_ga4_response(response) -> Dict[str, Any]:
    """Format GA4 API response into a readable dictionary."""
    result = {
        "row_count": response.row_count,
        "metadata": {
            "data_loss_from_other_row": response.metadata.data_loss_from_other_row if response.metadata else False,
            "schema_restriction_response": response.metadata.schema_restriction_response.name if response.metadata and response.metadata.schema_restriction_response else None,
            "currency_code": response.metadata.currency_code if response.metadata else None,
            "time_zone": response.metadata.time_zone if response.metadata else None
        },
        "dimension_headers": [header.name for header in response.dimension_headers],
        "metric_headers": [{"name": header.name, "type": header.type_.name} for header in response.metric_headers],
        "rows": []
    }
    
    for row in response.rows:
        row_data = {
            "dimensions": [dim.value for dim in row.dimension_values],
            "metrics": [metric.value for metric in row.metric_values]
        }
        result["rows"].append(row_data)
    
    return result

@mcp.tool()
def list_properties() -> str:
    """List all Google Analytics 4 properties accessible with current credentials."""
    auth_error = _ensure_authenticated()
    if auth_error:
        return auth_error
    
    if _admin_client is None:
        return "Error: Admin client not initialized. Please re-authenticate to access property listing."
    
    try:
        # First get all accounts
        accounts_request = _admin_client.list_accounts()
        
        result = {
            "accounts": [],
            "total_accounts": 0,
            "total_properties": 0
        }
        
        from google.analytics.admin_v1beta.types import ListPropertiesRequest
        
        for account in accounts_request:
            account_data = {
                "account_id": account.name.split('/')[-1],
                "account_name": account.display_name,
                "account_resource_name": account.name,
                "properties": []
            }
            
            # List properties for this specific account
            try:
                # Use the account's resource name in the filter
                filter_string = f"parent:{account.name}"
                request = ListPropertiesRequest(filter=filter_string)
                properties_response = _admin_client.list_properties(request=request)
                
                for property in properties_response:
                    property_data = {
                        "property_id": property.name.split('/')[-1],
                        "property_name": property.display_name,
                        "property_resource_name": property.name,
                        "currency_code": getattr(property, 'currency_code', None),
                        "time_zone": getattr(property, 'time_zone', None),
                        "create_time": property.create_time.isoformat() if hasattr(property, 'create_time') and property.create_time else None,
                        "parent": account.name
                    }
                    account_data["properties"].append(property_data)
                    result["total_properties"] += 1
                        
            except Exception as e:
                account_data["properties_error"] = f"Could not list properties: {str(e)}"
            
            result["accounts"].append(account_data)
            result["total_accounts"] += 1
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return f"Error listing properties: {str(e)}"

@mcp.tool()
def get_ga4_report(
    property_id: str,
    start_date: str = "7daysAgo",
    end_date: str = "today",
    metrics: str = "sessions,users,pageviews",
    dimensions: str = "date",
    limit: int = 10
) -> str:
    """Get a standard Google Analytics 4 report.
    
    Args:
        property_id: GA4 property ID (format: properties/123456789)
        start_date: Start date (YYYY-MM-DD or relative like '7daysAgo', '30daysAgo')
        end_date: End date (YYYY-MM-DD or relative like 'today', 'yesterday')
        metrics: Comma-separated metrics (e.g., 'sessions,users,pageviews')
        dimensions: Comma-separated dimensions (e.g., 'date,country,city')
        limit: Maximum number of rows to return (default: 10, max: 100000)
    """
    auth_error = _ensure_authenticated()
    if auth_error:
        return auth_error
    
    try:
        # Ensure property_id has correct format
        if not property_id.startswith('properties/'):
            property_id = f"properties/{property_id}"
        
        # Parse metrics and dimensions
        metric_list = [Metric(name=metric.strip()) for metric in metrics.split(',')]
        dimension_list = [Dimension(name=dim.strip()) for dim in dimensions.split(',')]
        
        # Create date range
        date_range = DateRange(start_date=start_date, end_date=end_date)
        
        # Create and execute request
        request = RunReportRequest(
            property=property_id,
            dimensions=dimension_list,
            metrics=metric_list,
            date_ranges=[date_range],
            limit=limit
        )
        
        response = _ga4_client.run_report(request=request)
        formatted_response = _format_ga4_response(response)
        
        return json.dumps(formatted_response, indent=2)
        
    except Exception as e:
        return f"Error getting GA4 report: {str(e)}"

@mcp.tool()
def get_realtime_data(
    property_id: str,
    metrics: str = "activeUsers",
    dimensions: str = "country",
    limit: int = 10
) -> str:
    """Get real-time Google Analytics 4 data.
    
    Args:
        property_id: GA4 property ID (format: properties/123456789)
        metrics: Comma-separated real-time metrics (e.g., 'activeUsers')
        dimensions: Comma-separated dimensions (e.g., 'country,city,deviceCategory')
        limit: Maximum number of rows to return (default: 10)
    """
    auth_error = _ensure_authenticated()
    if auth_error:
        return auth_error
    
    try:
        # Ensure property_id has correct format
        if not property_id.startswith('properties/'):
            property_id = f"properties/{property_id}"
        
        # Parse metrics and dimensions
        metric_list = [Metric(name=metric.strip()) for metric in metrics.split(',')]
        dimension_list = [Dimension(name=dim.strip()) for dim in dimensions.split(',')]
        
        # Create and execute real-time request
        request = RunRealtimeReportRequest(
            property=property_id,
            dimensions=dimension_list,
            metrics=metric_list,
            limit=limit
        )
        
        response = _ga4_client.run_realtime_report(request=request)
        
        # Format real-time response (similar structure)
        result = {
            "row_count": response.row_count,
            "dimension_headers": [header.name for header in response.dimension_headers],
            "metric_headers": [{"name": header.name, "type": header.type_.name} for header in response.metric_headers],
            "rows": []
        }
        
        for row in response.rows:
            row_data = {
                "dimensions": [dim.value for dim in row.dimension_values],
                "metrics": [metric.value for metric in row.metric_values]
            }
            result["rows"].append(row_data)
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return f"Error getting real-time data: {str(e)}"

@mcp.tool()
def get_ga4_audience_data(
    property_id: str,
    start_date: str = "30daysAgo",
    end_date: str = "today",
    limit: int = 20
) -> str:
    """Get audience insights from Google Analytics 4.
    
    Args:
        property_id: GA4 property ID (format: properties/123456789)
        start_date: Start date (YYYY-MM-DD or relative like '30daysAgo')
        end_date: End date (YYYY-MM-DD or relative like 'today')
        limit: Maximum number of rows to return (default: 20)
    """
    auth_error = _ensure_authenticated()
    if auth_error:
        return auth_error
    
    try:
        # Ensure property_id has correct format
        if not property_id.startswith('properties/'):
            property_id = f"properties/{property_id}"
        
        # Define audience-focused metrics and dimensions
        metrics = [
            Metric(name="users"),
            Metric(name="newUsers"),
            Metric(name="sessions"),
            Metric(name="engagedSessions"),
            Metric(name="averageSessionDuration")
        ]
        
        dimensions = [
            Dimension(name="country"),
            Dimension(name="city"),
            Dimension(name="deviceCategory"),
            Dimension(name="operatingSystem")
        ]
        
        # Create date range
        date_range = DateRange(start_date=start_date, end_date=end_date)
        
        # Create and execute request
        request = RunReportRequest(
            property=property_id,
            dimensions=dimensions,
            metrics=metrics,
            date_ranges=[date_range],
            limit=limit,
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="users"), desc=True)]
        )
        
        response = _ga4_client.run_report(request=request)
        formatted_response = _format_ga4_response(response)
        
        return json.dumps(formatted_response, indent=2)
        
    except Exception as e:
        return f"Error getting audience data: {str(e)}"

@mcp.tool()
def get_popular_pages(
    property_id: str,
    start_date: str = "7daysAgo",
    end_date: str = "today",
    limit: int = 15
) -> str:
    """Get most popular pages from Google Analytics 4.
    
    Args:
        property_id: GA4 property ID (format: properties/123456789)
        start_date: Start date (YYYY-MM-DD or relative like '7daysAgo')
        end_date: End date (YYYY-MM-DD or relative like 'today')
        limit: Maximum number of rows to return (default: 15)
    """
    auth_error = _ensure_authenticated()
    if auth_error:
        return auth_error
    
    try:
        # Ensure property_id has correct format
        if not property_id.startswith('properties/'):
            property_id = f"properties/{property_id}"
        
        # Define page-focused metrics and dimensions
        metrics = [
            Metric(name="screenPageViews"),
            Metric(name="users"),
            Metric(name="sessions"),
            Metric(name="averageSessionDuration"),
            Metric(name="bounceRate")
        ]
        
        dimensions = [
            Dimension(name="pageTitle"),
            Dimension(name="pagePath")
        ]
        
        # Create date range
        date_range = DateRange(start_date=start_date, end_date=end_date)
        
        # Create and execute request
        request = RunReportRequest(
            property=property_id,
            dimensions=dimensions,
            metrics=metrics,
            date_ranges=[date_range],
            limit=limit,
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="screenPageViews"), desc=True)]
        )
        
        response = _ga4_client.run_report(request=request)
        formatted_response = _format_ga4_response(response)
        
        return json.dumps(formatted_response, indent=2)
        
    except Exception as e:
        return f"Error getting popular pages: {str(e)}"

print("GA4 data retrieval tools added.")

# Configuration resource for GA4 settings
@mcp.resource("data://ga4_config")
def get_ga4_config() -> dict:
    """Provides GA4 MCP server configuration and status."""
    return {
        "server_name": "Google Analytics 4 MCP Server",
        "version": "1.0.0",
        "authenticated": _ga4_client is not None,
        "scopes": SCOPES,
        "available_tools": [
            "start_oauth_flow",
            "complete_oauth_flow", 
            "load_saved_credentials",
            "check_auth_status",
            "debug_env_vars",
            "list_properties",
            "debug_list_properties",
            "get_ga4_report",
            "get_realtime_data",
            "get_ga4_audience_data",
            "get_popular_pages"
        ]
    }

print("GA4 configuration resource added.")

async def test_server_locally():
    print("\n--- Testing GA4 MCP Server Locally ---")
    # Point the client directly at the server object
    client = Client(mcp)

    # Clients are asynchronous, so use an async context manager
    async with client:
        # Check authentication status
        auth_status = await client.call_tool("check_auth_status", {})
        print(f"Authentication status: {auth_status}")

        # Read the GA4 config resource
        config_data = await client.read_resource("data://ga4_config")
        print(f"GA4 config: {config_data}")

        print("\nTo authenticate with Google Analytics 4:")
        print("1. Set environment variables: GA4_CLIENT_ID and GA4_CLIENT_SECRET")
        print("2. Call start_oauth_flow tool to get authorization URL")
        print("3. Visit the URL and get the authorization code")
        print("4. Call complete_oauth_flow with the authorization code")
        
        print("\nAvailable GA4 data retrieval tools:")
        print("- list_properties: Get information about finding your property ID")
        print("- get_ga4_report: Get custom analytics reports")
        print("- get_realtime_data: Get real-time analytics data")
        print("- get_ga4_audience_data: Get audience insights")
        print("- get_popular_pages: Get most popular pages")
        
        if config_data and isinstance(config_data, list):
            config_text = config_data[0].text if hasattr(config_data[0], 'text') else str(config_data)
            import json
            config_json = json.loads(config_text)
            
            if config_json.get('authenticated', False):
                print("\n✅ Server is authenticated and ready for data retrieval!")
                print("Example usage:")
                print('  get_ga4_report("123456789", "7daysAgo", "today", "sessions,users", "date")')
            else:
                print("\n⚠️  Server is not authenticated yet.")

if __name__ == "__main__":
    # Run the local test function first
    asyncio.run(test_server_locally())
    
    print("\n--- Starting FastMCP Server via __main__ ---")
    # This starts the server, typically using the stdio transport by default
    mcp.run()