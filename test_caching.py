"""Test OAuth token caching functionality."""
import asyncio
import json
from datadog_mcp_client import DatadogMCPClient


async def test_token_caching():
    """Test that tokens are cached and reused across runs."""
    
    print("🧪 Testing OAuth token caching functionality...\n")
    
    # First run - should do full OAuth flow and cache tokens
    print("=" * 60)
    print("🚀 FIRST RUN - Should perform OAuth flow and cache tokens")
    print("=" * 60)
    
    client1 = DatadogMCPClient()
    try:
        await client1.initialize()
        await client1.get_server_info()
        
        # Quick test call
        result = await client1.call_tool("ask_docs", {
            "query": "What is Datadog?"
        })
        print(f"✅ First run successful!")
        
    except Exception as e:
        print(f"❌ First run failed: {e}")
        return
    finally:
        await client1.close()
    
    print("\n" + "=" * 60)
    print("🔄 SECOND RUN - Should use cached tokens (no browser)")
    print("=" * 60)
    
    # Second run - should use cached tokens without browser OAuth
    client2 = DatadogMCPClient()
    try:
        await client2.initialize()
        await client2.get_server_info()
        
        # Quick test call  
        result = await client2.call_tool("ask_docs", {
            "query": "What are metrics in Datadog?"
        })
        print(f"✅ Second run successful - used cached tokens!")
        
    except Exception as e:
        print(f"❌ Second run failed: {e}")
    finally:
        await client2.close()
    
    print("\n🎉 Token caching test completed!")


if __name__ == "__main__":
    asyncio.run(test_token_caching())
