#!/usr/bin/env python3

import asyncio
from fastmcp import Client
from app import mcp

async def test_list_properties():
    """Test the list_properties tool."""
    print("Testing list_properties tool...")
    
    client = Client(mcp)
    
    async with client:
        # Test list_properties when not authenticated
        result = await client.call_tool("list_properties", {})
        
        # Extract text from the response
        if isinstance(result, list) and len(result) > 0:
            if hasattr(result[0], 'text'):
                result_text = result[0].text
            else:
                result_text = str(result)
        else:
            result_text = str(result)
        
        print("List Properties Result:")
        print(result_text)

if __name__ == "__main__":
    asyncio.run(test_list_properties())