"""FastMCP server setup and tool definitions."""

import json
from typing import Dict, Any
from fastmcp import FastMCP

from .config.settings import Settings
from .auth.oauth_manager import OAuthManager
from .auth.credentials_manager import CredentialsManager
from .analytics.ga4_client import GA4Client
from .utils.errors import GA4ServerError
from .utils.logging import get_logger, setup_logging

# Setup logging
logger = setup_logging()
module_logger = get_logger(__name__)


class GA4MCPServer:
    """GA4 MCP Server with modular architecture."""
    
    def __init__(self):
        """Initialize the server with all components."""
        self.mcp = FastMCP(name="Google Analytics 4 MCP Server")
        self.settings = Settings()
        self.credentials_manager = CredentialsManager()
        self.oauth_manager = OAuthManager(self.settings, self.credentials_manager)
        self.ga4_client = GA4Client()
        
        self._register_tools()
        self._register_resources()
        
        module_logger.info("GA4 MCP Server initialized successfully")
    
    def _register_tools(self) -> None:
        """Register all MCP tools."""
        
        @self.mcp.tool()
        def start_oauth_flow() -> str:
            """Start OAuth2 flow and return authorization URL."""
            try:
                auth_url = self.oauth_manager.start_oauth_flow()
                return f"Please visit this URL to authorize the application: {auth_url}"
            except Exception as e:
                module_logger.error(f"OAuth flow start failed: {e}")
                return f"Error starting OAuth flow: {str(e)}"
        
        @self.mcp.tool()
        def complete_oauth_flow(authorization_code: str) -> str:
            """Complete OAuth2 flow with authorization code."""
            try:
                credentials = self.oauth_manager.complete_oauth_flow(authorization_code)
                self.ga4_client.update_credentials(credentials)
                return "OAuth2 authentication completed successfully. GA4 client is now ready."
            except Exception as e:
                module_logger.error(f"OAuth flow completion failed: {e}")
                return f"Error completing OAuth flow: {str(e)}"
        
        @self.mcp.tool()
        def load_saved_credentials() -> str:
            """Load previously saved OAuth2 credentials."""
            try:
                credentials = self.oauth_manager.load_saved_credentials()
                self.ga4_client.update_credentials(credentials)
                return "Saved credentials loaded successfully. GA4 and Admin clients are ready."
            except Exception as e:
                module_logger.error(f"Loading saved credentials failed: {e}")
                return f"Error loading saved credentials: {str(e)}"
        
        @self.mcp.tool()
        def check_auth_status() -> str:
            """Check if GA4 client is authenticated and ready."""
            try:
                is_auth, status = self.oauth_manager.check_auth_status()
                return status
            except Exception as e:
                module_logger.error(f"Auth status check failed: {e}")
                return f"Error checking auth status: {str(e)}"
        
        @self.mcp.tool()
        def debug_env_vars() -> str:
            """Debug environment variables for GA4 configuration."""
            try:
                debug_info = self.settings.get_debug_info()
                return json.dumps(debug_info, indent=2)
            except Exception as e:
                module_logger.error(f"Environment debug failed: {e}")
                return f"Error debugging environment variables: {str(e)}"
        
        @self.mcp.tool()
        def list_properties() -> str:
            """List all Google Analytics 4 properties accessible with current credentials."""
            try:
                if not self.ga4_client.is_authenticated:
                    return "Error: Not authenticated. Use start_oauth_flow or load_saved_credentials first."
                
                properties_data = self.ga4_client.list_properties()
                return json.dumps(properties_data, indent=2)
            except Exception as e:
                module_logger.error(f"List properties failed: {e}")
                return f"Error listing properties: {str(e)}"
        
        @self.mcp.tool()
        def get_ga4_report(
            property_id: str,
            start_date: str = "7daysAgo",
            end_date: str = "today",
            metrics: str = "sessions,users,pageviews",
            dimensions: str = "date",
            limit: int = 10
        ) -> str:
            """Get a standard Google Analytics 4 report."""
            try:
                if not self.ga4_client.is_authenticated:
                    return "Error: Not authenticated. Use start_oauth_flow or load_saved_credentials first."
                
                report_data = self.ga4_client.get_standard_report(
                    property_id, start_date, end_date, metrics, dimensions, limit
                )
                return json.dumps(report_data, indent=2)
            except Exception as e:
                module_logger.error(f"Get GA4 report failed: {e}")
                return f"Error getting GA4 report: {str(e)}"
        
        @self.mcp.tool()
        def get_realtime_data(
            property_id: str,
            metrics: str = "activeUsers",
            dimensions: str = "country",
            limit: int = 10
        ) -> str:
            """Get real-time Google Analytics 4 data."""
            try:
                if not self.ga4_client.is_authenticated:
                    return "Error: Not authenticated. Use start_oauth_flow or load_saved_credentials first."
                
                realtime_data = self.ga4_client.get_realtime_data(
                    property_id, metrics, dimensions, limit
                )
                return json.dumps(realtime_data, indent=2)
            except Exception as e:
                module_logger.error(f"Get realtime data failed: {e}")
                return f"Error getting real-time data: {str(e)}"
        
        @self.mcp.tool()
        def get_ga4_audience_data(
            property_id: str,
            start_date: str = "30daysAgo",
            end_date: str = "today",
            limit: int = 20
        ) -> str:
            """Get audience insights from Google Analytics 4."""
            try:
                if not self.ga4_client.is_authenticated:
                    return "Error: Not authenticated. Use start_oauth_flow or load_saved_credentials first."
                
                audience_data = self.ga4_client.get_audience_data(
                    property_id, start_date, end_date, limit
                )
                return json.dumps(audience_data, indent=2)
            except Exception as e:
                module_logger.error(f"Get audience data failed: {e}")
                return f"Error getting audience data: {str(e)}"
        
        @self.mcp.tool()
        def get_popular_pages(
            property_id: str,
            start_date: str = "7daysAgo",
            end_date: str = "today",
            limit: int = 15
        ) -> str:
            """Get most popular pages from Google Analytics 4."""
            try:
                if not self.ga4_client.is_authenticated:
                    return "Error: Not authenticated. Use start_oauth_flow or load_saved_credentials first."
                
                pages_data = self.ga4_client.get_popular_pages(
                    property_id, start_date, end_date, limit
                )
                return json.dumps(pages_data, indent=2)
            except Exception as e:
                module_logger.error(f"Get popular pages failed: {e}")
                return f"Error getting popular pages: {str(e)}"
        
        module_logger.info("All MCP tools registered successfully")
    
    def _register_resources(self) -> None:
        """Register MCP resources."""
        
        @self.mcp.resource("data://ga4_config")
        def get_ga4_config() -> Dict[str, Any]:
            """Provides GA4 MCP server configuration and status."""
            try:
                auth_info = self.oauth_manager.get_auth_info()
                
                return {
                    "server_name": "Google Analytics 4 MCP Server",
                    "version": "1.0.0",
                    "authenticated": auth_info["authenticated"],
                    "scopes": auth_info["required_scopes"],
                    "available_tools": [
                        "start_oauth_flow",
                        "complete_oauth_flow", 
                        "load_saved_credentials",
                        "check_auth_status",
                        "debug_env_vars",
                        "list_properties",
                        "get_ga4_report",
                        "get_realtime_data",
                        "get_ga4_audience_data",
                        "get_popular_pages"
                    ],
                    "auth_info": auth_info
                }
            except Exception as e:
                module_logger.error(f"Config resource generation failed: {e}")
                return {
                    "error": f"Failed to generate config: {str(e)}"
                }
        
        module_logger.info("MCP resources registered successfully")
    
    def run(self) -> None:
        """Run the MCP server."""
        module_logger.info("Starting GA4 MCP Server")
        self.mcp.run()
    
    def get_mcp_instance(self) -> FastMCP:
        """Get the FastMCP instance for testing."""
        return self.mcp