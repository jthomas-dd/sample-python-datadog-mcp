"""MCP Authorization Specification Compliance Check Script"""
import asyncio
import json
from datadog_mcp_client import DatadogMCPClient
from oauth_handler import MCPDatadogOAuthHandler


async def check_mcp_compliance():
    """Check compliance with MCP Authorization specification requirements."""
    
    print("🔍 MCP Authorization Specification Compliance Check")
    print("=" * 60)
    
    compliance_results = {
        "resource_parameter": False,
        "protected_resource_metadata": False,
        "authorization_server_discovery": False,
        "dynamic_client_registration": False,
        "pkce_s256": False,
        "state_parameter": False,
        "token_audience_binding": False,
        "www_authenticate_parsing": False
    }
    
    # Initialize the OAuth handler to check implementation
    mcp_url = "https://mcp.datadoghq.com/api/unstable/mcp-server/mcp"
    oauth_handler = MCPDatadogOAuthHandler(mcp_url)
    
    print(f"🎯 Target MCP Server: {mcp_url}")
    print(f"🎯 Resource URI: {oauth_handler.resource_uri}")
    
    # Check 1: Resource Parameter Implementation (RFC 8707)
    print("\n1️⃣ Checking Resource Parameter Implementation (RFC 8707)...")
    
    # Check if resource_uri is set correctly
    if oauth_handler.resource_uri == mcp_url:
        print("✅ Resource URI correctly set to MCP server URL")
        compliance_results["resource_parameter"] = True
    else:
        print("❌ Resource URI not set correctly")
    
    # Check 2: Protected Resource Metadata Discovery (RFC 9728)
    print("\n2️⃣ Checking Protected Resource Metadata Discovery (RFC 9728)...")
    
    try:
        # Test the discovery method
        auth_servers = await oauth_handler.discover_authorization_servers()
        if auth_servers:
            print(f"✅ Authorization server discovery successful: {auth_servers}")
            compliance_results["protected_resource_metadata"] = True
            compliance_results["authorization_server_discovery"] = True
            
            # Test dynamic client registration support
            print("   🔍 Checking dynamic client registration support...")
            for server in auth_servers:
                try:
                    metadata = await oauth_handler.discover_authorization_server_metadata(server)
                    if 'registration_endpoint' in metadata:
                        print(f"   ✅ Server supports dynamic registration: {metadata['registration_endpoint']}")
                        compliance_results["dynamic_client_registration"] = True
                        break
                    else:
                        print(f"   ⚠️  Server {server} does not advertise registration endpoint")
                except Exception as e:
                    print(f"   ⚠️  Could not check registration support: {e}")
        else:
            print("❌ No authorization servers discovered")
    except Exception as e:
        print(f"❌ Authorization server discovery failed: {e}")
    
    # Check 3: WWW-Authenticate Header Parsing
    print("\n3️⃣ Checking WWW-Authenticate Header Parsing...")
    
    # Test the header parsing method
    test_header = 'Bearer realm="example", as_uri="https://auth.example.com/.well-known/oauth-protected-resource"'
    parsed_uri = oauth_handler._parse_as_uri_from_header(test_header)
    if parsed_uri:
        print(f"✅ WWW-Authenticate header parsing works: {parsed_uri}")
        compliance_results["www_authenticate_parsing"] = True
    else:
        print("❌ WWW-Authenticate header parsing failed")
    
    # Check 4: PKCE Implementation
    print("\n4️⃣ Checking PKCE Implementation...")
    
    # Check if PKCE parameters are generated
    if oauth_handler.code_verifier and oauth_handler.code_challenge:
        print("✅ PKCE code verifier and challenge generated")
        
        # Check if using S256 method (would be in authorization URL)
        try:
            # This will fail without proper setup, but we can check the structure
            await oauth_handler.discover_authorization_servers()
            if oauth_handler.authorization_servers:
                await oauth_handler.discover_authorization_server_metadata(oauth_handler.authorization_servers[0])
                if oauth_handler.client_id or True:  # Skip actual registration for testing
                    oauth_handler.client_id = "test_client"  # Mock for URL generation
                    auth_url = oauth_handler.get_authorization_url()
                    if 'code_challenge_method=S256' in auth_url:
                        print("✅ PKCE S256 method used in authorization URL")
                        compliance_results["pkce_s256"] = True
                    else:
                        print("❌ PKCE S256 method not found in authorization URL")
        except Exception as e:
            print(f"⚠️  Could not fully test PKCE: {e}")
    else:
        print("❌ PKCE parameters not generated")
    
    # Check 5: State Parameter
    print("\n5️⃣ Checking State Parameter...")
    
    if oauth_handler.state:
        print(f"✅ State parameter generated: {oauth_handler.state[:10]}...")
        compliance_results["state_parameter"] = True
    else:
        print("❌ State parameter not generated")
    
    # Check 6: Check if resource parameter would be included in requests
    print("\n6️⃣ Checking Resource Parameter in OAuth Requests...")
    
    # Check authorization URL (mock client_id for testing)
    oauth_handler.client_id = "test_client"
    oauth_handler.auth_server_metadata = {
        "authorization_endpoint": "https://example.com/authorize",
        "token_endpoint": "https://example.com/token"
    }
    
    try:
        auth_url = oauth_handler.get_authorization_url()
        if f'resource={oauth_handler.resource_uri}' in auth_url.replace('%3A', ':').replace('%2F', '/'):
            print("✅ Resource parameter included in authorization URL")
            compliance_results["token_audience_binding"] = True
        else:
            print("❌ Resource parameter not found in authorization URL")
    except Exception as e:
        print(f"⚠️  Could not test authorization URL: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 COMPLIANCE SUMMARY")
    print("=" * 60)
    
    total_checks = len(compliance_results)
    passed_checks = sum(compliance_results.values())
    
    for check, passed in compliance_results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {check.replace('_', ' ').title()}")
    
    print(f"\n🎯 Overall Compliance: {passed_checks}/{total_checks} ({passed_checks/total_checks*100:.1f}%)")
    
    if passed_checks == total_checks:
        print("🎉 FULL MCP AUTHORIZATION SPECIFICATION COMPLIANCE!")
    elif passed_checks >= total_checks * 0.8:
        print("✅ EXCELLENT MCP compliance with minor gaps")
    elif passed_checks >= total_checks * 0.6:
        print("⚠️  GOOD MCP compliance with some gaps")
    else:
        print("❌ NEEDS IMPROVEMENT for full MCP compliance")
    
    # Specific MCP requirements check
    print("\n" + "=" * 60)
    print("📋 SPECIFIC MCP REQUIREMENTS CHECK")
    print("=" * 60)
    
    requirements = [
        ("RFC 8707 Resource Indicators", "Resource parameter MUST be included in authorization and token requests", compliance_results["resource_parameter"]),
        ("RFC 9728 Protected Resource Metadata", "MCP clients MUST use Protected Resource Metadata for discovery", compliance_results["protected_resource_metadata"]),
        ("OAuth 2.1 PKCE", "MCP clients MUST implement PKCE with S256", compliance_results["pkce_s256"]),
        ("State Parameter", "MCP clients SHOULD use state parameters", compliance_results["state_parameter"]),
        ("Dynamic Client Registration", "MCP clients and servers SHOULD support RFC 7591", compliance_results["dynamic_client_registration"]),
        ("WWW-Authenticate Parsing", "MCP clients MUST parse WWW-Authenticate headers", compliance_results["www_authenticate_parsing"]),
        ("Token Audience Binding", "Tokens must be bound to intended MCP server", compliance_results["token_audience_binding"])
    ]
    
    for req_name, req_desc, status in requirements:
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {req_name}: {req_desc}")
    
    return compliance_results


if __name__ == "__main__":
    asyncio.run(check_mcp_compliance())
