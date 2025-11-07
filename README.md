# MCP Knowledge Base Server

[![Tests](https://github.com/yourusername/mcp-knowledge-base/workflows/Tests/badge.svg)](https://github.com/yourusername/mcp-knowledge-base/actions)
[![PyPI version](https://badge.fury.io/py/mcp-knowledge-base.svg)](https://badge.fury.io/py/mcp-knowledge-base)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Model Context Protocol (MCP) server that provides document ingestion, indexing, and semantic search capabilities using LanceDB as the vector database.

**Use this with your local LLM** (Claude Desktop, Kiro IDE, Continue.dev, etc.) to give it the ability to search and understand your codebase and documents.

## Features

- Document ingestion for Python (.py) and text (.txt) files
- Vector-based semantic search using local embeddings
- Complete offline functionality with sentence-transformers
- MCP protocol compliance for AI assistant integration
- Configurable via environment variables or YAML files
- Works with Claude Desktop, Kiro IDE, Continue.dev, and other MCP clients

## Installation

### For Published Package (Coming Soon)

Once published to PyPI, no manual installation needed! Just configure your LLM client with `uvx`.

### For Local Development (Current)

Since the package isn't published yet, install it locally:

```bash
# Navigate to the project directory
cd /path/to/mcp-knowledge-base

# Install dependencies and the package
pip install -r requirements.txt
pip install -e .

# Verify installation
mcp-knowledge-base --version
```

Then configure your LLM client to use the installed command (see [Setup](#setup-with-your-llm) below).

## Setup with Your LLM

### Claude Desktop

1. **Edit your Claude config** (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

   **For local development (not yet published):**
   ```json
   {
     "mcpServers": {
       "knowledge-base": {
         "command": "mcp-knowledge-base"
       }
     }
   }
   ```

   **Once published to PyPI:**
   ```json
   {
     "mcpServers": {
       "knowledge-base": {
         "command": "uvx",
         "args": ["mcp-knowledge-base"]
       }
     }
   }
   ```

2. **Restart Claude Desktop**

3. **Start using it:**
   - "Add the file ./src/main.py to the knowledge base"
   - "Search for authentication implementation"
   - "What documents are in the knowledge base?"

### Kiro IDE

1. **Edit `.kiro/settings/mcp.json`** in your workspace:

   **For local development (not yet published):**
   ```json
   {
     "mcpServers": {
       "knowledge-base": {
         "command": "mcp-knowledge-base",
         "disabled": false,
         "autoApprove": ["list_documents", "search_documents"]
       }
     }
   }
   ```

   **Or use Python module directly:**
   ```json
   {
     "mcpServers": {
       "knowledge-base": {
         "command": "python",
         "args": ["-m", "mcp_knowledge_base.main"],
         "disabled": false,
         "autoApprove": ["list_documents", "search_documents"]
       }
     }
   }
   ```

   **Once published to PyPI:**
   ```json
   {
     "mcpServers": {
       "knowledge-base": {
         "command": "uvx",
         "args": ["mcp-knowledge-base"],
         "disabled": false,
         "autoApprove": ["list_documents", "search_documents"]
       }
     }
   }
   ```

2. **Reload MCP servers** (Command Palette → "MCP: Reload Servers")

3. **Start using it** - Ask Kiro to search your documents!

### Continue.dev / Cursor / Other Clients

See [USAGE_WITH_LLM.md](docs/USAGE_WITH_LLM.md) for setup instructions.

## How It Works

On first use, `uvx` automatically:
- Downloads and installs the package
- Installs all dependencies
- Downloads the embedding model (~100MB, one-time)
- Starts the server

The server then:
- Creates a `knowledge_base.db` in your current directory
- Stores logs in `./logs`
- Supports `.py` and `.txt` files by default

**Zero configuration needed!**

## Troubleshooting

**Server not starting?**
```bash
# Check installation
mcp-knowledge-base --version

# View logs
tail -f logs/mcp_knowledge_base.log
```

**First run is slow?**
The embedding model (~100MB) downloads on first use. This only happens once.

**Need help?** See the [documentation](#documentation) below.

## Documentation

- **[LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md)** - 🔧 Setup for local development (current - not yet published)
- **[INSTALL.md](INSTALL.md)** - Detailed setup guide for all LLM clients
- **[USAGE_WITH_LLM.md](docs/USAGE_WITH_LLM.md)** - Usage examples and tips

### Advanced

- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Manual installation, custom configuration, production deployment
- **[QUICKSTART.md](docs/QUICKSTART.md)** - Configuration options and advanced features

## License

MIT License