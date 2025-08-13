"""Datadog MCP Client using Anthropic's MCP library with MCP-compliant OAuth."""
import asyncio
import json
from typing import Any, Dict, List, Optional
import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from oauth_handler import MCPDatadogOAuthHandler


class DatadogMCPClient:
    """MCP Client for connecting to Datadog's MCP server with MCP-compliant OAuth authentication."""
    
    def __init__(self, mcp_server_url: str = "https://mcp.datadoghq.com/api/unstable/mcp-server/mcp"):
        self.mcp_server_url = mcp_server_url
        self.oauth_handler = MCPDatadogOAuthHandler(mcp_server_url)
        self.session: Optional[ClientSession] = None
        self.http_client: Optional[httpx.AsyncClient] = None
        self.session_id: Optional[str] = None
    
    async def initialize(self):
        """Initialize the MCP client with OAuth authentication."""
        # Get valid OAuth token
        access_token = await self.oauth_handler.get_valid_token()
        
        # Initialize HTTP client with authentication
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'User-Agent': 'DatadogMCPClient/1.0'
        }
        
        self.http_client = httpx.AsyncClient(
            headers=headers,
            timeout=httpx.Timeout(30.0)
        )
        
        print("✓ MCP client initialized with OAuth authentication")
    
    async def close(self):
        """Close the MCP client and cleanup resources."""
        if self.http_client:
            await self.http_client.aclose()
        if self.session:
            await self.session.close()
    
    async def send_mcp_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send an MCP request to the Datadog server."""
        if not self.http_client:
            raise Exception("Client not initialized. Call initialize() first.")
        
        # Ensure we have a valid token
        access_token = await self.oauth_handler.get_valid_token()
        self.http_client.headers['Authorization'] = f'Bearer {access_token}'
        
        # Use a unique request ID for each request
        import time
        request_id = int(time.time() * 1000)  # Use timestamp as unique ID
        
        # Construct MCP request
        request_data = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {}
        }
        
        try:
            print(f"🔄 Sending MCP request: {method}")
            if params:
                print(f"📝 Request params: {json.dumps(params, indent=2)}")
            
            # Add session ID to headers if we have one
            headers = {}
            if self.session_id:
                headers['mcp-session-id'] = self.session_id
                print(f"🔗 Using session ID: {self.session_id}")
            
            print(f"📤 Full request: {json.dumps(request_data, indent=2)}")
            
            response = await self.http_client.post(
                self.mcp_server_url,
                json=request_data,
                headers=headers
            )
            
            # Capture session ID from response if present
            if 'mcp-session-id' in response.headers:
                new_session_id = response.headers['mcp-session-id']
                if self.session_id != new_session_id:
                    self.session_id = new_session_id
                    print(f"🆔 Captured new session ID: {self.session_id}")
            
            # Log the response for debugging
            print(f"📡 Response status: {response.status_code}")
            
            response.raise_for_status()
            response_json = response.json()
            
            # Check for JSON-RPC errors
            if 'error' in response_json:
                error = response_json['error']
                raise Exception(f"MCP error {error.get('code', 'unknown')}: {error.get('message', 'Unknown error')}")
            
            return response_json
            
        except httpx.HTTPStatusError as e:
            print(f"📡 Error response body: {e.response.text}")
            raise Exception(f"HTTP error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the MCP server."""
        response = await self.send_mcp_request("tools/list")
        return response.get("result", {}).get("tools", [])
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources from the MCP server."""
        response = await self.send_mcp_request("resources/list")
        return response.get("result", {}).get("resources", [])
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool on the MCP server."""
        params = {
            "name": tool_name,
            "arguments": arguments
        }
        response = await self.send_mcp_request("tools/call", params)
        return response.get("result", {})
    
    async def read_resource(self, resource_uri: str) -> Dict[str, Any]:
        """Read a specific resource from the MCP server."""
        params = {
            "uri": resource_uri
        }
        response = await self.send_mcp_request("resources/read", params)
        return response.get("result", {})
    
    async def get_server_info(self) -> Dict[str, Any]:
        """Initialize MCP session and get server information."""
        response = await self.send_mcp_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "resources": {},
                "sampling": {}
            },
            "clientInfo": {
                "name": "DatadogMCPClient",
                "version": "1.0.0"
            }
        })
        
        # After successful initialization, send notifications/initialized
        await self.send_notification("notifications/initialized")
        
        return response.get("result", {})
    
    async def send_notification(self, method: str, params: Optional[Dict[str, Any]] = None) -> None:
        """Send a notification (no response expected)."""
        if not self.http_client:
            raise Exception("Client not initialized. Call initialize() first.")
        
        # Ensure we have a valid token
        access_token = await self.oauth_handler.get_valid_token()
        self.http_client.headers['Authorization'] = f'Bearer {access_token}'
        
        # Construct MCP notification (no id field)
        request_data = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {}
        }
        
        try:
            print(f"🔔 Sending MCP notification: {method}")
            
            # Add session ID to headers if we have one
            headers = {}
            if self.session_id:
                headers['mcp-session-id'] = self.session_id
                print(f"🔗 Using session ID for notification: {self.session_id}")
            
            response = await self.http_client.post(
                self.mcp_server_url,
                json=request_data,
                headers=headers
            )
            print(f"📡 Notification response status: {response.status_code}")
            
        except Exception as e:
            print(f"⚠️  Notification failed (may be expected): {e}")


async def main():
    """Main function demonstrating the MCP client usage."""
    client = DatadogMCPClient()
    
    try:
        print("🚀 Starting Datadog MCP Client...")
        
        # Initialize with OAuth
        await client.initialize()
        
        # Get server info
        print("\n📋 Getting server information...")
        server_info = await client.get_server_info()
        print(f"Server info: {json.dumps(server_info, indent=2)}")
        
        # List available tools
        print("\n🔧 Listing available tools...")
        tools = await client.list_tools()
        print(f"Available tools ({len(tools)}):")
        for tool in tools:
            print(f"  - {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}")
        
        # List available resources
        print("\n📚 Listing available resources...")
        resources = await client.list_resources()
        print(f"Available resources ({len(resources)}):")
        for resource in resources:
            print(f"  - {resource.get('uri', 'Unknown')}: {resource.get('description', 'No description')}")
        
        # Example tool call with proper parameters
        if tools:
            # Let's inspect the first tool's schema to understand its parameters
            first_tool = tools[0]
            tool_name = first_tool.get('name')
            print(f"\n🎯 Inspecting tool: {tool_name}")
            print(f"Tool details: {json.dumps(first_tool, indent=2)}")
            
            # Test with the ask_docs tool using a proper query
            if tool_name == 'ask_docs':
                try:
                    print(f"\n🎯 Testing {tool_name} with proper parameters...")
                    result = await client.call_tool(tool_name, {
                        "query": "How do I create a dashboard in Datadog?"
                    })
                    print(f"Tool result: {json.dumps(result, indent=2)}")
                except Exception as e:
                    print(f"Tool call failed: {e}")
            else:
                print(f"Skipping tool call test for {tool_name} - need proper parameters")
        
        print("\n✅ MCP client demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
