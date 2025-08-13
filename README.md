# MCP-Compliant Datadog Client

A Python client for connecting to Datadog's MCP server using Anthropic's official MCP library with **full MCP Authorization specification compliance** and **persistent token caching**.

## 🎉 **Current Status: FULLY FUNCTIONAL**

This implementation is **production-ready** and provides:
- ✅ Complete MCP-compliant OAuth 2.1 flow
- ✅ Automatic token caching and refresh 
- ✅ Access to all 15 Datadog MCP tools
- ✅ Dynamic client registration
- ✅ Secure token management

## ✅ MCP Compliance Features

This implementation follows the [MCP Authorization specification](https://modelcontextprotocol.io/specification/draft/basic/authorization) including:

- **🔍 OAuth 2.0 Protected Resource Metadata (RFC 9728)** - Automatic discovery of authorization servers
- **🚀 Dynamic Client Registration (RFC 7591)** - No manual client registration required
- **🎯 Resource Indicators (RFC 8707)** - Proper token audience binding for security
- **🔒 PKCE with S256** - Required security for authorization code protection
- **🔄 Authorization Server Metadata Discovery** - RFC 8414 and OpenID Connect Discovery 1.0 support
- **⚡ State Parameter Validation** - CSRF protection
- **💾 Persistent Token Caching** - Secure token storage with automatic refresh

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the client (first time will open browser for OAuth):**
   ```bash
   python main.py          # Basic demo with server info and tool listing
   python working_example.py  # Multiple tool call examples
   python test_caching.py     # Test token caching functionality
   ```

3. **Subsequent runs use cached tokens (no browser needed!)**

## 🏆 Available Datadog Tools

The client provides access to all 15 Datadog MCP tools:

| Tool | Description |
|------|-------------|
| `ask_docs` | Search Datadog documentation |
| `get_events` | Query Datadog events |
| `get_incident` | Get incident details |
| `get_metrics` | Retrieve metrics data |
| `get_monitors` | List and query monitors |
| `get_synthetics_tests` | Get Synthetics test data |
| `get_trace` | Retrieve APM traces |
| `list_dashboards` | List available dashboards |
| `list_hosts` | Get host inventory |
| `list_incidents` | List incidents |
| `list_metrics` | Discover available metrics |
| `list_services` | List services |
| `list_spans` | Query APM spans |
| `search_logs` | Search log data |
| `search_rum_events` | Query RUM events |

## 💾 Token Caching & Management

The client automatically handles OAuth tokens with secure caching:

- **🗄️ Persistent Storage**: Tokens cached to `~/.datadog-mcp/oauth_tokens.json`
- **🔒 Secure Permissions**: Cache files protected with `600` permissions
- **🔄 Auto Refresh**: Expired tokens automatically refreshed using refresh tokens
- **⚡ Fast Startup**: Subsequent runs skip OAuth flow (no browser needed)
- **🗑️ Smart Cleanup**: Invalid tokens automatically cleared and re-authenticated

### Token Lifecycle:
1. **First Run**: Full OAuth flow → browser opens → tokens cached
2. **Subsequent Runs**: Cached tokens used → no browser needed
3. **Token Expiry**: Automatic refresh using refresh token
4. **Refresh Failure**: Automatic re-authentication with new OAuth flow

## 🔧 MCP OAuth Flow

The client automatically performs the complete MCP-compliant OAuth flow:

1. **Server Discovery**: Discovers Datadog's authorization servers via Protected Resource Metadata
2. **Metadata Discovery**: Fetches authorization server capabilities and endpoints  
3. **Dynamic Registration**: Automatically registers as an OAuth client (with fallback support)
4. **Authorization Flow**: Performs PKCE-protected authorization with resource indicators
5. **Token Management**: Handles token refresh with proper audience validation
6. **Session Management**: Maintains MCP session IDs for proper tool calls

## ⚙️ Configuration (Optional)

For environments where dynamic client registration fails, you can provide fallback credentials:

```bash
cp .env.example .env
# Edit .env with your credentials (optional)
```

- `DATADOG_CLIENT_ID`: Fallback Datadog OAuth application client ID
- `DATADOG_CLIENT_SECRET`: Fallback Datadog OAuth application client secret  
- `DATADOG_REDIRECT_URI`: OAuth redirect URI (default: `http://localhost:8080/callback`)
- `DATADOG_SITE`: Your Datadog site (default: `datadoghq.com`)

## 🛡️ Security Features

- **🎯 Token Audience Binding**: Tokens are bound to the specific MCP server resource
- **🔒 PKCE Protection**: Authorization code protection against interception attacks
- **⚡ State Parameter**: CSRF protection during OAuth flow
- **🔄 Automatic Token Refresh**: Secure token lifecycle management
- **🚀 Dynamic Client Registration**: No hardcoded credentials needed
- **💾 Secure Caching**: Tokens stored outside repository with restrictive permissions
- **🗑️ Automatic Cleanup**: Invalid tokens and cache automatically managed

## 📖 Usage Examples

### Basic Usage:
```python
from datadog_mcp_client import DatadogMCPClient

async def example():
    client = DatadogMCPClient()
    await client.initialize()        # OAuth flow (browser on first run)
    await client.get_server_info()   # Establish MCP session
    
    # Query documentation
    docs = await client.call_tool("ask_docs", {
        "query": "How do I create a dashboard?"
    })
    
    # List dashboards
    dashboards = await client.call_tool("list_dashboards", {
        "query": "system"
    })
    
    await client.close()
```

### Advanced Usage:
```python
# Search logs
logs = await client.call_tool("search_logs", {
    "query": "status:error service:web",
    "from": "now-1h"
})

# Get metrics
metrics = await client.call_tool("get_metrics", {
    "query": "system.cpu.user{*}",
    "from": "now-1h"
})

# List monitors
monitors = await client.call_tool("get_monitors", {
    "query": "status:alert"
})
```

## 🧪 Testing

Test various aspects of the client:

```bash
# Test basic functionality
python main.py

# Test multiple tool calls
python working_example.py

# Test token caching (run twice to see caching in action)
python test_caching.py

# Test token refresh functionality
python test_token_refresh.py
```

## 🗂️ File Structure

```
sample-python-datadog-mcp/
├── datadog_mcp_client.py    # Main MCP client implementation
├── oauth_handler.py         # MCP-compliant OAuth handler with caching
├── main.py                  # Basic demo
├── working_example.py       # Multiple tool call examples  
├── test_caching.py         # Token caching tests
├── test_token_refresh.py   # Token refresh tests
├── examples.py             # Advanced usage examples
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
├── .gitignore            # Secure git ignore rules
└── README.md             # This file
```

## 🔗 OAuth App Setup (Optional)

To create a Datadog OAuth app for fallback credentials:
1. Visit: https://app.datadoghq.com/account/settings#api
2. Click "OAuth Apps" and create a new application
3. Set redirect URI to: `http://localhost:8080/callback`
4. Copy Client ID and Secret to `.env` file

**Note**: Dynamic client registration usually works, so manual setup is often unnecessary.

## 🎯 Next Steps

The client is production-ready! You can:
- Integrate it into your applications
- Build custom tools using the Datadog MCP tools
- Extend functionality for your specific use cases
- Deploy in production environments with confidence

All MCP Authorization specification requirements are implemented and tested! 🚀
