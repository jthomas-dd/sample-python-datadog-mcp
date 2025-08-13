# MCP-Compliant Datadog Client

A Python client for connecting to Datadog's MCP server using Anthropic's official MCP library with **full MCP Authorization specification compliance**.

## ✅ MCP Compliance Features

This implementation follows the [MCP Authorization specification](https://modelcontextprotocol.io/specification/draft/basic/authorization) including:

- **🔍 OAuth 2.0 Protected Resource Metadata (RFC 9728)** - Automatic discovery of authorization servers
- **🚀 Dynamic Client Registration (RFC 7591)** - No manual client registration required
- **🎯 Resource Indicators (RFC 8707)** - Proper token audience binding for security
- **🔒 PKCE with S256** - Required security for authorization code protection
- **🔄 Authorization Server Metadata Discovery** - RFC 8414 and OpenID Connect Discovery 1.0 support
- **⚡ State Parameter Validation** - CSRF protection

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. (Optional) Set up fallback OAuth credentials in `.env`:
   ```bash
   cp .env.example .env
   # Edit .env if you want fallback credentials
   ```

3. Run the client:
   ```bash
   python main.py      # Basic demo
   python examples.py  # Advanced examples
   ```

## MCP OAuth Flow

The client automatically performs the complete MCP-compliant OAuth flow:

1. **Server Discovery**: Discovers Datadog's authorization servers via Protected Resource Metadata
2. **Metadata Discovery**: Fetches authorization server capabilities and endpoints
3. **Dynamic Registration**: Automatically registers as an OAuth client (with fallback support)
4. **Authorization Flow**: Performs PKCE-protected authorization with resource indicators
5. **Token Management**: Handles token refresh with proper audience validation

## Configuration (Optional)

For environments where dynamic client registration fails, you can provide fallback credentials:

- `DATADOG_CLIENT_ID`: Fallback Datadog OAuth application client ID
- `DATADOG_CLIENT_SECRET`: Fallback Datadog OAuth application client secret  
- `DATADOG_REDIRECT_URI`: OAuth redirect URI (default: `http://localhost:8080/callback`)
- `DATADOG_SITE`: Your Datadog site (default: `datadoghq.com`)

## Security Features

- **Token Audience Binding**: Tokens are bound to the specific MCP server resource
- **PKCE Protection**: Authorization code protection against interception attacks
- **State Parameter**: CSRF protection during OAuth flow
- **Automatic Token Refresh**: Secure token lifecycle management
- **Dynamic Client Registration**: No hardcoded credentials needed

## Usage

The client handles all MCP compliance requirements automatically. Simply instantiate and use:

```python
from datadog_mcp_client import DatadogMCPClient

async def example():
    client = DatadogMCPClient()
    await client.initialize()  # Handles full MCP OAuth flow
    
    # Use the client for MCP operations
    tools = await client.list_tools()
    print(f"Available tools: {tools}")
    
    await client.close()
```
