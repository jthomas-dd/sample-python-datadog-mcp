"""Examples of using the Datadog MCP Client for common tasks."""
import asyncio
import json
from datadog_mcp_client import DatadogMCPClient


async def example_metrics_query():
    """Example: Query Datadog metrics through MCP."""
    client = DatadogMCPClient()
    
    try:
        await client.initialize()
        
        # Example: Get metrics data
        print("📊 Querying metrics...")
        
        # This would use the actual MCP tool for metrics
        result = await client.call_tool("get_metrics", {
            "query": "system.cpu.user{*}",
            "from": "now-1h",
            "to": "now"
        })
        
        print(f"Metrics result: {json.dumps(result, indent=2)}")
        
    except Exception as e:
        print(f"Error querying metrics: {e}")
    finally:
        await client.close()


async def example_logs_search():
    """Example: Search Datadog logs through MCP."""
    client = DatadogMCPClient()
    
    try:
        await client.initialize()
        
        print("📝 Searching logs...")
        
        # Example logs search
        result = await client.call_tool("search_logs", {
            "query": "status:error service:web",
            "from": "now-1h",
            "to": "now"
        })
        
        print(f"Logs result: {json.dumps(result, indent=2)}")
        
    except Exception as e:
        print(f"Error searching logs: {e}")
    finally:
        await client.close()


async def example_list_monitors():
    """Example: List Datadog monitors through MCP."""
    client = DatadogMCPClient()
    
    try:
        await client.initialize()
        
        print("🔔 Listing monitors...")
        
        result = await client.call_tool("get_monitors", {
            "query": "status:alert"
        })
        
        print(f"Monitors result: {json.dumps(result, indent=2)}")
        
    except Exception as e:
        print(f"Error listing monitors: {e}")
    finally:
        await client.close()


async def example_dashboard_info():
    """Example: Get dashboard information through MCP."""
    client = DatadogMCPClient()
    
    try:
        await client.initialize()
        
        print("📊 Getting dashboard info...")
        
        result = await client.call_tool("list_dashboards", {
            "query": "Redis"
        })
        
        print(f"Dashboard result: {json.dumps(result, indent=2)}")
        
    except Exception as e:
        print(f"Error getting dashboard info: {e}")
    finally:
        await client.close()


async def run_all_examples():
    """Run all examples."""
    print("🚀 Running Datadog MCP Client Examples\n")
    
    examples = [
        ("Metrics Query", example_metrics_query),
        ("Logs Search", example_logs_search),
        ("List Monitors", example_list_monitors),
        ("Dashboard Info", example_dashboard_info),
    ]
    
    for name, example_func in examples:
        print(f"\n{'='*50}")
        print(f"Running: {name}")
        print('='*50)
        
        try:
            await example_func()
        except Exception as e:
            print(f"Example '{name}' failed: {e}")
        
        print(f"Completed: {name}")


if __name__ == "__main__":
    asyncio.run(run_all_examples())
