from fastmcp import Client
import asyncio
import json

async def test():
    print("🔗 Connecting to MCP Server...")
    
    client = Client({
        "mcpServers": {
            "snowflake": {
                "transport": "streamable-http",
                "url": "https://snowflake-mcp-va6ytiztka-ew.a.run.app/mcp"
            }
        }
    })
    
    try:
        async with client:
            print("✅ Connected!")
            
            # List available tools
            print("\n📋 Available Tools:")
            tools = await client.list_tools()
            for tool in tools:
                print(f"  - {tool.name}: {getattr(tool, 'description', 'No description')}")
            
            # Test connection_status tool
            print("\n🔍 Testing connection_status tool...")
            result = await client.call_tool("connection_status", {})
            print(f"📊 Result:")
            for content in result.content:
                if hasattr(content, 'text'):
                    print(content.text)
            
            # Test snowflake_query tool
            print("\n🔍 Testing snowflake_query tool...")
            result = await client.call_tool("snowflake_query", {
                "sql": "SELECT COUNT(*) as product_count FROM PRODUCT LIMIT 1"
            })
            print(f"📊 Query Result:")
            for content in result.content:
                if hasattr(content, 'text'):
                    print(content.text)
            
            print("\n✅ All tests passed!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
