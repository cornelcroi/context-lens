# Local Development Setup

Quick guide for using the MCP Knowledge Base Server from local source code (before publishing to PyPI).

## Installation

```bash
# Navigate to the project directory
cd ~/Documents/mcp_knowledge_base

# Install dependencies
pip install -r requirements.txt

# Install in editable mode
pip install -e .

# Verify it works
mcp-knowledge-base --version
```

## Configuration for Kiro IDE

Edit `.kiro/settings/mcp.json` in your workspace:

### Option 1: Using the installed command (recommended)

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

### Option 2: Using Python module directly

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

### Option 3: Using full path (if command not found)

```bash
# Find the full path
which mcp-knowledge-base
# Example output: /Users/you/.pyenv/shims/mcp-knowledge-base
```

Then use the full path:

```json
{
  "mcpServers": {
    "knowledge-base": {
      "command": "/Users/you/.pyenv/shims/mcp-knowledge-base",
      "disabled": false,
      "autoApprove": ["list_documents", "search_documents"]
    }
  }
}
```

## Reload MCP Servers

After editing the config:

1. Open Command Palette (Cmd/Ctrl + Shift + P)
2. Type "MCP: Reload Servers"
3. Press Enter

## Testing

Ask Kiro:
- "What MCP tools do you have available?"
- "Add the file ./README.md to the knowledge base"
- "Search for installation instructions"

## Troubleshooting

### Command not found

If `mcp-knowledge-base` is not found:

1. **Check if it's installed:**
   ```bash
   which mcp-knowledge-base
   pip show mcp-knowledge-base
   ```

2. **Reinstall:**
   ```bash
   pip install -e .
   ```

3. **Use Python module syntax instead:**
   ```json
   {
     "command": "python",
     "args": ["-m", "mcp_knowledge_base.main"]
   }
   ```

### Virtual Environment

If you're using a virtual environment:

```bash
# Activate it first
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Then install
pip install -e .

# Find the path
which mcp-knowledge-base
```

Use the full path in your Kiro config.

### Check Logs

If something isn't working:

```bash
# View logs
tail -f logs/mcp_knowledge_base.log

# View errors only
tail -f logs/errors.log
```

### First Run

The first time you use it, the server will download the embedding model (~100MB). This is normal and only happens once.

## Development Workflow

1. **Make changes** to the code
2. **No need to reinstall** (using `pip install -e .` means changes are live)
3. **Reload MCP servers** in Kiro to pick up changes
4. **Test** your changes

## Publishing to PyPI (Future)

Once published, users can use `uvx` for automatic installation:

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

But for now, local installation is required.

## Getting Help

- Check [INSTALL.md](INSTALL.md) for detailed setup
- See [USAGE_WITH_LLM.md](docs/USAGE_WITH_LLM.md) for usage examples
- Review [DEPLOYMENT.md](docs/DEPLOYMENT.md) for advanced configuration
