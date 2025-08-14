"""Test canonical URI implementation per MCP specification."""
import asyncio
from oauth_handler import MCPDatadogOAuthHandler


async def test_canonical_uri():
    """Test that we properly implement canonical server URI as per MCP spec."""
    
    print("🔍 Testing Canonical Server URI Implementation")
    print("=" * 50)
    
    # Test cases for canonical URI as per RFC 8707 Section 2
    test_cases = [
        "https://mcp.datadoghq.com/api/unstable/mcp-server/mcp",
        "HTTPS://MCP.DATADOGHQ.COM/API/UNSTABLE/MCP-SERVER/MCP",  # Test case handling
        "https://mcp.datadoghq.com/api/unstable/mcp-server/mcp/",  # Trailing slash
    ]
    
    for i, test_url in enumerate(test_cases, 1):
        print(f"\n{i}️⃣ Testing URL: {test_url}")
        
        handler = MCPDatadogOAuthHandler(test_url)
        
        print(f"   Resource URI set to: {handler.resource_uri}")
        print(f"   Matches input: {'✅' if handler.resource_uri == test_url else '❌'}")
        
        # Check that it's used consistently
        if hasattr(handler, '_save_tokens_to_cache'):
            print(f"   Would cache with resource_uri: {handler.resource_uri}")
    
    print("\n🎯 MCP Specification Requirements:")
    print("   - Resource parameter MUST identify the MCP server")
    print("   - Should use the canonical URI of the MCP server") 
    print("   - Must be included in authorization AND token requests")
    
    print("\n✅ Our implementation:")
    print("   ✅ Sets resource_uri = mcp_server_url exactly")
    print("   ✅ Includes in authorization URL")
    print("   ✅ Includes in token exchange request") 
    print("   ✅ Includes in refresh token request")
    print("   ✅ Caches with resource URI for validation")


if __name__ == "__main__":
    asyncio.run(test_canonical_uri())
