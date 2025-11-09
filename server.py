#!/usr/bin/env python3
"""
Context Lens - Give your LLM glasses to understand meaning, not just read words

Run this file directly to start the MCP server in stdio mode:
    python server.py

Or make it executable and run:
    chmod +x server.py
    ./server.py
"""

if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Add src to path so we can import the package
    src_path = Path(__file__).parent / "src"
    sys.path.insert(0, str(src_path))
    
    from context_lens.server import mcp
    
    # Start the MCP server in stdio mode
    mcp.run()
