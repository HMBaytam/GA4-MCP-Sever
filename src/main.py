"""Main entry point for GA4 MCP Server."""

import asyncio
from fastmcp import Client

from .server import GA4MCPServer
from .utils.logging import get_logger

logger = get_logger(__name__)


async def test_server_locally():
    """Test the GA4 MCP Server locally."""
    print("\n--- Testing GA4 MCP Server Locally ---")
    
    # Create server instance
    server = GA4MCPServer()
    mcp = server.get_mcp_instance()
    
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


def main():
    """Main function to run the server."""
    try:
        # Create and run server
        server = GA4MCPServer()
        
        if __name__ == "__main__":
            # Run the local test function first
            asyncio.run(test_server_locally())
            
            print("\n--- Starting FastMCP Server via main ---")
            # This starts the server, typically using the stdio transport by default
            server.run()
        else:
            # If imported, just return the server instance
            return server
            
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise


if __name__ == "__main__":
    main()