"""Entry point for running the MCP server with stdio transport."""

import asyncio

from .server import app, initialize_server

if __name__ == "__main__":
    # Initialize server components
    asyncio.run(initialize_server())

    # Run the FastMCP server (stdio mode for MCP Inspector)
    app.run()
