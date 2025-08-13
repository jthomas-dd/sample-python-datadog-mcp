"""Main entry point for the Datadog MCP Client."""
import asyncio
from datadog_mcp_client import main

if __name__ == "__main__":
    asyncio.run(main())
