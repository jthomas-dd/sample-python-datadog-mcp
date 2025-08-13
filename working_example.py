"""Working example demonstrating successful MCP tool calls."""
import asyncio
import json
from datadog_mcp_client import DatadogMCPClient


async def demonstrate_working_tools():
    """Demonstrate working MCP tool calls."""
    client = DatadogMCPClient()
    
    try:
        print("🚀 Initializing MCP client...")
        await client.initialize()
        
        print("\n📋 Getting server info to establish session...")
        server_info = await client.get_server_info()
        print(f"Server: {server_info.get('serverInfo', {}).get('name', 'Unknown')}")
        
        print("\n📚 Testing ask_docs tool...")
        docs_result = await client.call_tool("ask_docs", {
            "query": "What are Datadog monitors and how do they work?"
        })
        print("Documentation result:")
        for content in docs_result.get("content", []):
            if content.get("type") == "text":
                print(content.get("text", "")[:500] + "...")
        
        print("\n📊 Testing list_dashboards tool...")
        dashboards_result = await client.call_tool("list_dashboards", {
            "query": "system"
        })
        print("Dashboards result:")
        print(json.dumps(dashboards_result, indent=2)[:1000] + "...")
        
        print("\n🔍 Testing list_metrics tool...")
        metrics_result = await client.call_tool("list_metrics", {
            "name_filter": "system.cpu"
        })
        print("Metrics result:")
        print(json.dumps(metrics_result, indent=2)[:1000] + "...")
        
        print("\n✅ All tool calls successful!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(demonstrate_working_tools())
