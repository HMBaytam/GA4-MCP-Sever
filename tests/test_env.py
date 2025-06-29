#!/usr/bin/env python3

import asyncio
from fastmcp import Client
from app import mcp

async def test_env_debug():
    """Test the environment variable debugging tool."""
    print("Testing environment variable debugging...")
    
    client = Client(mcp)
    
    async with client:
        # Test the debug_env_vars tool
        result = await client.call_tool("debug_env_vars", {})
        
        # Extract text from the response
        if isinstance(result, list) and len(result) > 0:
            if hasattr(result[0], 'text'):
                result_text = result[0].text
            else:
                result_text = str(result)
        else:
            result_text = str(result)
        
        print("Environment Debug Result:")
        print(result_text)
        
        # Test start_oauth_flow to see the improved error message
        print("\nTesting start_oauth_flow...")
        oauth_result = await client.call_tool("start_oauth_flow", {})
        
        if isinstance(oauth_result, list) and len(oauth_result) > 0:
            if hasattr(oauth_result[0], 'text'):
                oauth_text = oauth_result[0].text
            else:
                oauth_text = str(oauth_result)
        else:
            oauth_text = str(oauth_result)
        
        print("OAuth Flow Result:")
        print(oauth_text)

if __name__ == "__main__":
    asyncio.run(test_env_debug())