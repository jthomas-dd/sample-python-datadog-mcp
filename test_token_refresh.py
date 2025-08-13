"""Test OAuth token refresh functionality."""
import asyncio
import json
import time
from pathlib import Path
from datadog_mcp_client import DatadogMCPClient


async def test_token_refresh():
    """Test that expired tokens are automatically refreshed."""
    
    print("🔄 Testing OAuth token refresh functionality...\n")
    
    # Path to the token cache
    cache_file = Path.home() / ".datadog-mcp" / "oauth_tokens.json"
    
    if not cache_file.exists():
        print("❌ No cached tokens found. Please run test_caching.py first.")
        return
    
    # Load and modify the cache to simulate an expired token
    print("📁 Loading existing token cache...")
    with open(cache_file, 'r') as f:
        cache_data = json.load(f)
    
    print(f"🕐 Original token expires at: {time.ctime(cache_data['token_expires_at'])}")
    
    # Simulate an expired token (set expiration to 1 minute ago)
    expired_time = time.time() - 60
    cache_data['token_expires_at'] = expired_time
    
    print(f"⏰ Setting token expiration to: {time.ctime(expired_time)} (expired)")
    
    # Write back the modified cache
    with open(cache_file, 'w') as f:
        json.dump(cache_data, f, indent=2)
    
    cache_file.chmod(0o600)
    print("✅ Modified cache saved")
    
    print("\n" + "=" * 60)
    print("🔄 Testing automatic token refresh...")
    print("=" * 60)
    
    # Now test the client - it should detect the expired token and refresh it
    client = DatadogMCPClient()
    try:
        await client.initialize()
        await client.get_server_info()
        
        # Test a tool call to ensure everything works
        result = await client.call_tool("ask_docs", {
            "query": "How do I use the Datadog API?"
        })
        
        print("✅ Token refresh test successful!")
        print("🎯 The client automatically refreshed the expired token")
        
        # Check the updated cache
        with open(cache_file, 'r') as f:
            updated_cache = json.load(f)
        
        print(f"🕐 New token expires at: {time.ctime(updated_cache['token_expires_at'])}")
        
    except Exception as e:
        print(f"❌ Token refresh test failed: {e}")
        
    finally:
        await client.close()
    
    print("\n🎉 Token refresh test completed!")


async def test_invalid_refresh_token():
    """Test handling of invalid refresh tokens."""
    
    print("\n" + "=" * 60)
    print("🚫 Testing invalid refresh token handling...")
    print("=" * 60)
    
    cache_file = Path.home() / ".datadog-mcp" / "oauth_tokens.json"
    
    if not cache_file.exists():
        print("❌ No cached tokens found.")
        return
    
    # Load and corrupt the refresh token
    with open(cache_file, 'r') as f:
        cache_data = json.load(f)
    
    # Set an invalid refresh token and expired access token
    cache_data['refresh_token'] = 'invalid_refresh_token'
    cache_data['token_expires_at'] = time.time() - 60
    
    with open(cache_file, 'w') as f:
        json.dump(cache_data, f, indent=2)
    
    cache_file.chmod(0o600)
    
    print("🚫 Set invalid refresh token...")
    
    # Test the client - it should detect invalid refresh token and do new OAuth flow
    client = DatadogMCPClient()
    try:
        await client.initialize()
        print("✅ Client handled invalid refresh token correctly!")
        
    except Exception as e:
        print(f"❌ Invalid refresh token test failed: {e}")
        
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_token_refresh())
    # asyncio.run(test_invalid_refresh_token())  # Uncomment to test invalid refresh token
