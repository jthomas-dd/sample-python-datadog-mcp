"""MCP-compliant OAuth2 handler for Datadog authentication following RFC 7591, RFC 8707, and RFC 9728."""
import asyncio
import hashlib
import secrets
import base64
import urllib.parse
import json
import uuid
from typing import Optional, Dict, Any, List
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time

import httpx
from dotenv import load_dotenv
import os

load_dotenv()


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback with state parameter support."""
    
    def do_GET(self):
        """Handle GET request for OAuth callback."""
        # Parse the callback URL
        parsed_url = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        
        # Store the authorization code and state
        if 'code' in query_params:
            self.server.auth_code = query_params['code'][0]
            self.server.received_state = query_params.get('state', [None])[0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<html><body><h1>Authorization successful!</h1><p>You can close this window.</p></body></html>')
        elif 'error' in query_params:
            self.server.auth_error = query_params['error'][0]
            error_description = query_params.get('error_description', ['Unknown error'])[0]
            
            # Special handling for invalid_scope error - provide helpful guidance
            if self.server.auth_error == 'invalid_scope':
                error_description = f"Invalid scope. The MCP server may require different scopes than requested. Original error: {error_description}"
            
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f'<html><body><h1>Authorization failed!</h1><p>Error: {self.server.auth_error}</p><p>Description: {error_description}</p><p>Check the console for more details.</p></body></html>'.encode())
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<html><body><h1>Invalid callback</h1><p>No authorization code or error found in callback.</p></body></html>')
    
    def log_message(self, format, *args):
        """Suppress server logs."""
        pass


class MCPDatadogOAuthHandler:
    """Handles MCP-compliant OAuth2 flow for Datadog authentication with dynamic client registration."""
    
    def __init__(self, mcp_server_url: str):
        self.mcp_server_url = mcp_server_url
        self.redirect_uri = os.getenv('DATADOG_REDIRECT_URI', 'http://localhost:8080/callback')
        self.datadog_site = os.getenv('DATADOG_SITE', 'datadoghq.com')
        
        # MCP-specific parameters
        self.resource_uri = mcp_server_url  # RFC 8707 Resource Indicators
        self.state = secrets.token_urlsafe(32)  # OAuth state parameter
        
        # PKCE parameters (required by MCP spec)
        self.code_verifier = self._generate_code_verifier()
        self.code_challenge = self._generate_code_challenge(self.code_verifier)
        
        # Dynamic client registration data
        self.client_id: Optional[str] = None
        self.client_secret: Optional[str] = None
        self.registration_access_token: Optional[str] = None
        self.client_id_issued_at: Optional[int] = None
        self.client_secret_expires_at: Optional[int] = None
        
        # Authorization server metadata
        self.authorization_servers: List[str] = []
        self.auth_server_metadata: Optional[Dict[str, Any]] = None
        self.selected_auth_server: Optional[str] = None
        
        # Token storage
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expires_at: Optional[float] = None
    
    def _generate_code_verifier(self) -> str:
        """Generate PKCE code verifier."""
        return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    
    def _generate_code_challenge(self, verifier: str) -> str:
        """Generate PKCE code challenge from verifier."""
        digest = hashlib.sha256(verifier.encode('utf-8')).digest()
        return base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')
    
    async def discover_authorization_servers(self) -> List[str]:
        """Discover authorization servers using RFC 9728 Protected Resource Metadata."""
        async with httpx.AsyncClient() as client:
            # First, try to get the protected resource metadata from MCP server
            try:
                # Make an unauthenticated request to trigger 401 with WWW-Authenticate header
                response = await client.get(self.mcp_server_url)
                
                if response.status_code == 401:
                    www_auth_header = response.headers.get('WWW-Authenticate', '')
                    if 'as_uri=' in www_auth_header:
                        # Parse the authorization server URI from WWW-Authenticate header
                        as_uri = self._parse_as_uri_from_header(www_auth_header)
                        if as_uri:
                            metadata_response = await client.get(as_uri)
                            metadata_response.raise_for_status()
                            metadata = metadata_response.json()
                            
                            self.authorization_servers = metadata.get('authorization_servers', [])
                            return self.authorization_servers
                
                # Fallback: try common metadata endpoints on MCP server domain
                from urllib.parse import urlparse
                mcp_parsed = urlparse(self.mcp_server_url)
                mcp_base = f"{mcp_parsed.scheme}://{mcp_parsed.netloc}"
                
                metadata_urls = [
                    f"{self.mcp_server_url}/.well-known/oauth-protected-resource",
                    f"{mcp_base}/.well-known/oauth-protected-resource",
                    f"https://api.{self.datadog_site}/.well-known/oauth-protected-resource"
                ]
                
                for url in metadata_urls:
                    try:
                        response = await client.get(url)
                        if response.status_code == 200:
                            metadata = response.json()
                            self.authorization_servers = metadata.get('authorization_servers', [])
                            return self.authorization_servers
                    except Exception:
                        continue
                        
            except Exception as e:
                print(f"Warning: Could not discover authorization servers: {e}")
            
            # Ultimate fallback: try both MCP domain and main Datadog domain
            from urllib.parse import urlparse
            mcp_parsed = urlparse(self.mcp_server_url)
            
            fallback_servers = []
            
            # First try the MCP server's domain for authorization servers
            if 'mcp.' in mcp_parsed.netloc:
                # Try the authorization server on the same subdomain
                fallback_servers.append(f"https://{mcp_parsed.netloc}/oauth2/v1")
            
            # Also try the main Datadog authorization server
            fallback_servers.append(f"https://app.{self.datadog_site}/oauth2/v1")
            
            self.authorization_servers = fallback_servers
            print(f"Using fallback authorization servers: {fallback_servers}")
            return self.authorization_servers
    
    def _parse_as_uri_from_header(self, header: str) -> Optional[str]:
        """Parse as_uri from WWW-Authenticate header."""
        # Simple parser for as_uri parameter
        parts = header.split(',')
        for part in parts:
            if 'as_uri=' in part:
                return part.split('as_uri=')[1].strip().strip('"')
        return None
    
    async def discover_authorization_server_metadata(self, issuer_url: str) -> Dict[str, Any]:
        """Discover authorization server metadata using RFC 8414 and OpenID Connect Discovery."""
        async with httpx.AsyncClient() as client:
            # Parse issuer URL
            parsed_url = urllib.parse.urlparse(issuer_url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            path = parsed_url.path.rstrip('/')
            
            # Try different discovery endpoints as per MCP spec
            discovery_urls = []
            
            if path:
                # For issuer URLs with path components
                discovery_urls.extend([
                    f"{base_url}/.well-known/oauth-authorization-server{path}",
                    f"{base_url}/.well-known/openid-configuration{path}",
                    f"{base_url}{path}/.well-known/openid-configuration"
                ])
            else:
                # For issuer URLs without path components
                discovery_urls.extend([
                    f"{base_url}/.well-known/oauth-authorization-server",
                    f"{base_url}/.well-known/openid-configuration"
                ])
            
            for url in discovery_urls:
                try:
                    response = await client.get(url)
                    if response.status_code == 200:
                        metadata = response.json()
                        
                        # Verify PKCE support as required by MCP spec (with graceful fallback)
                        if 'code_challenge_methods_supported' not in metadata:
                            print(f"⚠️  Warning: Authorization server {issuer_url} does not advertise PKCE support")
                            print("   MCP requires PKCE, but proceeding with PKCE anyway (server may still support it)")
                        elif 'S256' not in metadata['code_challenge_methods_supported']:
                            print(f"⚠️  Warning: Authorization server {issuer_url} does not advertise S256 PKCE method")
                            print("   Proceeding anyway as server may still support it")
                        
                        self.auth_server_metadata = metadata
                        self.selected_auth_server = issuer_url
                        return metadata
                        
                except Exception as e:
                    print(f"Discovery attempt failed for {url}: {e}")
                    continue
            
            # Final fallback: create minimal metadata for known Datadog endpoints
            if 'datadoghq.com' in issuer_url or 'datadog' in issuer_url.lower():
                print(f"⚠️  Using fallback metadata for Datadog authorization server: {issuer_url}")
                
                # Handle different URL structures
                if issuer_url.endswith('/authorize'):
                    auth_endpoint = issuer_url
                    token_endpoint = issuer_url.replace('/authorize', '/token')
                else:
                    auth_endpoint = f"{issuer_url}/authorize"
                    token_endpoint = f"{issuer_url}/token"
                
                fallback_metadata = {
                    'authorization_endpoint': auth_endpoint,
                    'token_endpoint': token_endpoint,
                    'issuer': issuer_url,
                    'response_types_supported': ['code'],
                    'grant_types_supported': ['authorization_code', 'refresh_token'],
                    'code_challenge_methods_supported': ['S256']  # Assume PKCE support
                }
                
                self.auth_server_metadata = fallback_metadata
                self.selected_auth_server = issuer_url
                return fallback_metadata
            
            raise Exception(f"Could not discover metadata for authorization server: {issuer_url}")
    
    async def register_dynamic_client(self) -> Dict[str, Any]:
        """Perform dynamic client registration using RFC 7591."""
        if not self.auth_server_metadata:
            raise Exception("Authorization server metadata required for dynamic client registration")
        
        registration_endpoint = self.auth_server_metadata.get('registration_endpoint')
        if not registration_endpoint:
            print("⚠️  Authorization server does not support dynamic client registration")
            raise Exception("Dynamic client registration not available - will use fallback credentials")
        
        # Prepare client registration request
        registration_request = {
            "client_name": "MCP Datadog Client",
            "client_uri": "https://github.com/your-org/datadog-mcp-client",
            "redirect_uris": [self.redirect_uri],
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
            # "scope": "mcp",  # Try without explicit scope first
            "token_endpoint_auth_method": "client_secret_basic",
            "application_type": "native"  # Since we're using localhost redirect
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                registration_endpoint,
                json=registration_request,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            
            registration_response = response.json()
            
            # Store client credentials
            self.client_id = registration_response['client_id']
            self.client_secret = registration_response.get('client_secret')
            self.registration_access_token = registration_response.get('registration_access_token')
            self.client_id_issued_at = registration_response.get('client_id_issued_at')
            self.client_secret_expires_at = registration_response.get('client_secret_expires_at')
            
            print(f"✓ Successfully registered dynamic client: {self.client_id}")
            return registration_response
    
    def get_authorization_url(self) -> str:
        """Get the MCP-compliant authorization URL with resource parameter."""
        if not self.auth_server_metadata or not self.client_id:
            raise Exception("Authorization server metadata and client registration required")
        
        authorization_endpoint = self.auth_server_metadata.get('authorization_endpoint')
        if not authorization_endpoint:
            raise Exception("Authorization server metadata missing authorization_endpoint")
        
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            # 'scope': 'mcp',  # Try without explicit scope first
            'code_challenge': self.code_challenge,
            'code_challenge_method': 'S256',
            'resource': self.resource_uri,  # RFC 8707 Resource Indicators (required by MCP)
            'state': self.state,  # OAuth state parameter for security
        }
        
        return f"{authorization_endpoint}?{urllib.parse.urlencode(params)}"
    
    async def start_mcp_oauth_flow(self) -> str:
        """Start the complete MCP-compliant OAuth flow and return access token."""
        print("🔍 Starting MCP OAuth flow with server discovery...")
        
        # Step 1: Discover authorization servers
        print("Step 1: Discovering authorization servers...")
        authorization_servers = await self.discover_authorization_servers()
        if not authorization_servers:
            raise Exception("No authorization servers discovered")
        
        print(f"Found authorization servers: {authorization_servers}")
        
        # Step 2: Discover authorization server metadata (try first server)
        print("Step 2: Discovering authorization server metadata...")
        for auth_server in authorization_servers:
            try:
                await self.discover_authorization_server_metadata(auth_server)
                print(f"✓ Using authorization server: {auth_server}")
                break
            except Exception as e:
                print(f"Failed to discover metadata for {auth_server}: {e}")
                continue
        else:
            raise Exception("Could not discover metadata for any authorization server")
        
        # Step 3: Dynamic client registration
        print("Step 3: Performing dynamic client registration...")
        try:
            await self.register_dynamic_client()
        except Exception as e:
            print(f"Dynamic client registration failed: {e}")
            # Fallback: try to use pre-configured client credentials
            self.client_id = os.getenv('DATADOG_CLIENT_ID')
            self.client_secret = os.getenv('DATADOG_CLIENT_SECRET')
            if not self.client_id:
                raise Exception("Dynamic registration failed and no fallback client_id configured")
            print("Using fallback client credentials from environment")
        
        # Step 4: Start authorization flow
        print("Step 4: Starting authorization flow...")
        return await self._perform_authorization_flow()
    
    async def _perform_authorization_flow(self) -> str:
        """Perform the authorization code flow with PKCE."""
        # Start local server for callback
        server = HTTPServer(('localhost', 8080), OAuthCallbackHandler)
        server.auth_code = None
        server.auth_error = None
        server.received_state = None
        
        # Start server in background thread
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        try:
            # Open browser for authorization
            auth_url = self.get_authorization_url()
            print(f"Opening browser for authorization: {auth_url}")
            webbrowser.open(auth_url)
            
            # Wait for callback
            print("Waiting for authorization callback...")
            timeout = 300  # 5 minutes
            start_time = time.time()
            
            while server.auth_code is None and server.auth_error is None:
                if time.time() - start_time > timeout:
                    raise TimeoutError("OAuth authorization timed out")
                await asyncio.sleep(0.5)
            
            if server.auth_error:
                error_msg = f"OAuth authorization failed: {server.auth_error}"
                if server.auth_error == 'invalid_scope':
                    error_msg += "\n💡 Hint: The MCP server rejected the requested scopes. This implementation will try again without explicit scopes."
                elif server.auth_error == 'invalid_client':
                    error_msg += "\n💡 Hint: The dynamically registered client was rejected. Check if the MCP server supports dynamic client registration."
                raise Exception(error_msg)
            
            # Verify state parameter for security
            if hasattr(server, 'received_state') and server.received_state != self.state:
                raise Exception("State parameter mismatch - possible CSRF attack")
            
            # Exchange code for token
            return await self._exchange_code_for_token(server.auth_code)
            
        finally:
            server.shutdown()
    
    async def _exchange_code_for_token(self, auth_code: str) -> str:
        """Exchange authorization code for access token with MCP-compliant resource parameter."""
        if not self.auth_server_metadata:
            raise Exception("Authorization server metadata required for token exchange")
        
        token_endpoint = self.auth_server_metadata.get('token_endpoint')
        if not token_endpoint:
            raise Exception("Authorization server metadata missing token_endpoint")
        
        data = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'code': auth_code,
            'redirect_uri': self.redirect_uri,
            'code_verifier': self.code_verifier,
            'resource': self.resource_uri,  # RFC 8707 Resource Indicators (required by MCP)
        }
        
        # Add client secret if available (for confidential clients)
        if self.client_secret:
            data['client_secret'] = self.client_secret
        
        async with httpx.AsyncClient() as client:
            response = await client.post(token_endpoint, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            self.refresh_token = token_data.get('refresh_token')
            
            # Calculate token expiration
            expires_in = token_data.get('expires_in', 3600)
            self.token_expires_at = time.time() + expires_in
            
            print("✅ Successfully obtained access token!")
            return self.access_token
    
    async def refresh_access_token(self) -> str:
        """Refresh the access token using refresh token with MCP-compliant resource parameter."""
        if not self.refresh_token:
            raise Exception("No refresh token available")
        
        if not self.auth_server_metadata:
            raise Exception("Authorization server metadata required for token refresh")
        
        token_endpoint = self.auth_server_metadata.get('token_endpoint')
        if not token_endpoint:
            raise Exception("Authorization server metadata missing token_endpoint")
        
        data = {
            'grant_type': 'refresh_token',
            'client_id': self.client_id,
            'refresh_token': self.refresh_token,
            'resource': self.resource_uri,  # RFC 8707 Resource Indicators (required by MCP)
        }
        
        # Add client secret if available (for confidential clients)
        if self.client_secret:
            data['client_secret'] = self.client_secret
        
        async with httpx.AsyncClient() as client:
            response = await client.post(token_endpoint, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            
            # Update refresh token if provided
            if 'refresh_token' in token_data:
                self.refresh_token = token_data['refresh_token']
            
            # Calculate token expiration
            expires_in = token_data.get('expires_in', 3600)
            self.token_expires_at = time.time() + expires_in
            
            return self.access_token
    
    async def get_valid_token(self) -> str:
        """Get a valid access token, refreshing if necessary or starting full MCP OAuth flow."""
        if not self.access_token:
            return await self.start_mcp_oauth_flow()
        
        # Check if token is expired (with 5 minute buffer)
        if self.token_expires_at and time.time() > (self.token_expires_at - 300):
            if self.refresh_token:
                try:
                    return await self.refresh_access_token()
                except Exception as e:
                    print(f"Token refresh failed: {e}, starting new OAuth flow")
                    return await self.start_mcp_oauth_flow()
            else:
                return await self.start_mcp_oauth_flow()
        
        return self.access_token
