"""
Backward compatibility wrapper for the refactored GA4 MCP Server.

This module maintains the same interface as the original app.py
while using the new modular architecture underneath.
"""

import asyncio
from src.main import main
from src.server import GA4MCPServer

# Create server instance
_server = GA4MCPServer()
mcp = _server.get_mcp_instance()

# Global variables for backward compatibility (deprecated)
_ga4_client = None
_admin_client = None
_oauth_credentials = None

print("Google Analytics 4 MCP server object created (using refactored architecture).")
print("OAuth2 authentication tools added.")
print("GA4 data retrieval tools added.")
print("GA4 configuration resource added.")

async def test_server_locally():
    """Test server locally - delegates to new implementation."""
    from src.main import test_server_locally
    await test_server_locally()

if __name__ == "__main__":
    # Run the local test function first
    asyncio.run(test_server_locally())
    
    print("\n--- Starting FastMCP Server via __main__ ---")
    # This starts the server, typically using the stdio transport by default
    mcp.run()