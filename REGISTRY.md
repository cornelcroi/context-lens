# MCP Registry

Context Lens is published to the official Model Context Protocol Registry, making it easy to discover and install through MCP-compatible clients.

## Registry Information

**Registry Name:** `io.github.cornelcroi/context-lens`

**Validation String:** `mcp-name: io.github.cornelcroi/context-lens`

## Installation from Registry

The easiest way to install Context Lens is through the MCP Registry using `uvx`:

```bash
# Install and run directly
uvx context-lens

# Check version
uvx context-lens --version
```

### Add to MCP Client

Add to your MCP client configuration (see [SETUP.md](SETUP.md) for client-specific instructions):

```json
{
  "mcpServers": {
    "context-lens": {
      "command": "uvx",
      "args": ["context-lens"]
    }
  }
}
```

### Benefits of Registry Installation

- ✅ Always gets the latest version from PyPI
- ✅ No manual installation required
- ✅ Automatic dependency management
- ✅ Works across all MCP-compatible clients
- ✅ Consistent installation experience

## Verification

To verify that Context Lens is published and available in the MCP Registry:

### 1. Search the Registry

Visit the [MCP Registry](https://registry.modelcontextprotocol.io/) and search for:
- "context-lens"
- "io.github.cornelcroi/context-lens"

The server should appear in the search results with its description and metadata.

### 2. Check via API

Query the registry API directly:

```bash
curl "https://registry.modelcontextprotocol.io/api/search?q=context-lens"
```

This returns JSON with server information, including:
- Name and namespace
- Description
- Version
- Package information
- Installation instructions

### 3. Verify Installation

Test that the package installs and runs correctly:

```bash
# Install via uvx (recommended)
uvx context-lens --version

# Or via pip
pip install context-lens
python -m context_lens.run --version
```

### 4. Test in MCP Client

Add Context Lens to your MCP client configuration and verify:
- Server connects successfully
- Tools are available (add_document, search_documents, etc.)
- Basic operations work (add a test document, search)

## Registry Metadata

The registry entry includes:

- **Name:** `io.github.cornelcroi/context-lens`
- **Title:** Context Lens
- **Description:** Semantic search for AI assistants with built-in vector storage
- **Package Type:** PyPI
- **Package Name:** `context-lens`
- **Transport:** stdio (standard input/output)
- **Schema Version:** 2025-10-17

## Publishing Process

For maintainers: See [PUBLISHING.md](PUBLISHING.md) for detailed instructions on publishing new versions to the registry.

## Support

If you encounter issues with registry installation:

1. Check the [Troubleshooting Guide](TROUBLESHOOTING.md)
2. Verify the package exists on [PyPI](https://pypi.org/project/context-lens/)
3. Check the [GitHub Issues](https://github.com/cornelcroi/context-lens/issues)
4. Open a new issue with details about your environment and error messages

## Related Documentation

- 📖 [Setup Guide](SETUP.md) - Detailed installation for all MCP clients
- 📦 [Publishing Guide](PUBLISHING.md) - How to publish to the registry (maintainers)
- 🔧 [Troubleshooting](TROUBLESHOOTING.md) - Common installation issues
