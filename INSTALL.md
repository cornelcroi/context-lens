# Installation Guide

Setup guide for the MCP Knowledge Base Server with your LLM client.

## What You'll Get

After setup, your local LLM will be able to:
- 📄 Add documents to a searchable knowledge base
- 🔍 Search your codebase semantically (not just keyword matching)
- 📋 List all indexed documents
- 🗑️ Clear the knowledge base when needed

All processing happens **locally** - no data sent to external services!

## Installation

### For Local Development (Current - Not Yet Published)

Since the package isn't on PyPI yet, install it locally:

```bash
# Navigate to the project directory
cd ~/Documents/mcp_knowledge_base  # or wherever you cloned it

# Install dependencies
pip install -r requirements.txt

# Install the package in editable mode
pip install -e .

# Verify it works
mcp-knowledge-base --version
```

You should see: `mcp-knowledge-base 0.1.0`

### For Published Package (Future)

Once published to PyPI, you can use `uvx` for automatic installation:

```bash
pip install uv
```

Then just configure your LLM client - no manual installation needed!

## Configure Your LLM Client

Choose your LLM client below and follow the instructions.

## Configure Your LLM Client

### For Claude Desktop

1. Find your Claude config file:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`

2. Edit the file and add:

**For local development (current):**
```json
{
  "mcpServers": {
    "knowledge-base": {
      "command": "mcp-knowledge-base"
    }
  }
}
```

**Alternative - using Python module:**
```json
{
  "mcpServers": {
    "knowledge-base": {
      "command": "python",
      "args": ["-m", "mcp_knowledge_base.main"]
    }
  }
}
```

**Once published (future):**
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

3. Restart Claude Desktop

4. Test it by asking Claude:
   - "What MCP tools do you have available?"
   - You should see: add_document, list_documents, search_documents, clear_knowledge_base

### For Kiro IDE

Create or edit `.kiro/settings/mcp.json` in your workspace:

**For local development (current):**
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

**Alternative - using Python module directly:**
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

**Once published (future):**
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

Reload MCP servers from Command Palette (Cmd/Ctrl + Shift + P → "MCP: Reload Servers")

### For Continue.dev (VS Code)

Edit `~/.continue/config.json`:

**For local development (current):**
```json
{
  "mcpServers": [
    {
      "name": "knowledge-base",
      "command": "mcp-knowledge-base"
    }
  ]
}
```

**Once published (future):**
```json
{
  "mcpServers": [
    {
      "name": "knowledge-base",
      "command": "uvx",
      "args": ["mcp-knowledge-base"]
    }
  ]
}
```

Restart VS Code

## First Use

Once configured, try these commands with your LLM:

1. **Add a document:**
   ```
   Add the file ./README.md to the knowledge base
   ```

2. **Search for content:**
   ```
   Search for installation instructions
   ```

3. **List documents:**
   ```
   Show me all documents in the knowledge base
   ```

The first time you use it, `uvx` will download and install everything automatically (~100MB). This only happens once.

## Troubleshooting

### uvx Not Found

If `uvx` command is not found:

```bash
# Install uv (includes uvx)
pip install uv

# Or on macOS with Homebrew
brew install uv
```

See [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/) for other methods.

### First Run is Slow

The first connection will download the embedding model (~100MB). This is normal and only happens once.

### Check Logs

If something isn't working, check the logs in your current directory:

```bash
tail -f logs/mcp_knowledge_base.log
```

## Advanced Setup

Need manual installation or custom configuration? See:
- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Manual installation, custom paths, environment variables
- **[QUICKSTART.md](docs/QUICKSTART.md)** - Configuration options and advanced features

## Getting Help

- Check logs: `logs/mcp_knowledge_base.log`
- Usage examples: [USAGE_WITH_LLM.md](docs/USAGE_WITH_LLM.md)
- GitHub Issues: https://github.com/example/mcp-knowledge-base/issues
