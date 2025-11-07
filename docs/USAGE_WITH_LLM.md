# Using MCP Knowledge Base with Local LLMs

This guide explains how to install and use the MCP Knowledge Base Server with local LLM applications.

## What is MCP?

Model Context Protocol (MCP) is a standard protocol that allows AI applications to connect to external tools and data sources. This server provides document search capabilities to any MCP-compatible client.

## Installation

### Step 1: Install the MCP Server

```bash
# Clone the repository
git clone https://github.com/example/mcp-knowledge-base.git
cd mcp-knowledge-base

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

Or use the automated installer:

```bash
./scripts/install.sh
```

### Step 2: Verify Installation

```bash
mcp-knowledge-base --version
```

You should see: `mcp-knowledge-base 0.1.0`

## Configuration for MCP Clients

### Using with Claude Desktop

Claude Desktop has built-in MCP support. Configure it by editing the MCP settings file:

**Location:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

**Minimal Configuration (Recommended):**

```json
{
  "mcpServers": {
    "knowledge-base": {
      "command": "mcp-knowledge-base"
    }
  }
}
```

That's it! The server uses sensible defaults automatically.

After configuration:
1. Restart Claude Desktop
2. The knowledge base tools will be available in conversations
3. You can ask Claude to search your documents

**Advanced Configuration (Optional):**

If you need custom settings, you can add environment variables or arguments:

```json
{
  "mcpServers": {
    "knowledge-base": {
      "command": "mcp-knowledge-base",
      "args": ["--log-level", "DEBUG"],
      "env": {
        "LANCE_DB_PATH": "/custom/path/knowledge_base.db"
      }
    }
  }
}
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for all available options.

### Using with Kiro IDE

Kiro IDE supports MCP servers through its configuration:

**Edit `.kiro/settings/mcp.json` in your workspace:**

**Using uvx (recommended):**
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

**Or if manually installed:**
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

**Or edit global config at `~/.kiro/settings/mcp.json`**

After configuration:
1. Reload the MCP servers (Command Palette → "MCP: Reload Servers")
2. The tools will be available to Kiro's AI assistant

### Using with Continue.dev

Continue.dev is a VS Code extension that supports MCP:

**Edit `~/.continue/config.json`:**

**Using uvx (recommended):**
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

**Or if manually installed:**
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

### Using with Other MCP Clients

For any MCP-compatible client, use one of these configurations:

**Using uvx (recommended):**
```json
{
  "command": "uvx",
  "args": ["mcp-knowledge-base"]
}
```

**Or if manually installed:**
```json
{
  "command": "mcp-knowledge-base"
}
```

## Available Tools

Once connected, your LLM will have access to these tools:

### 1. add_document
Add a document to the knowledge base.

**Parameters:**
- `file_path` (string): Path to the document file (.py or .txt)

**Example usage in conversation:**
```
"Add the file /path/to/my_code.py to the knowledge base"
```

### 2. list_documents
List all documents in the knowledge base.

**Parameters:**
- `limit` (integer, optional): Maximum number of documents (default: 100)
- `offset` (integer, optional): Number to skip for pagination (default: 0)

**Example usage:**
```
"Show me all documents in the knowledge base"
"List the first 10 documents"
```

### 3. search_documents
Search for relevant documents using semantic search.

**Parameters:**
- `query` (string): Search query text
- `limit` (integer, optional): Maximum results to return (default: 10)

**Example usage:**
```
"Search for authentication implementation"
"Find documents about error handling"
"What do we have about database connections?"
```

### 4. clear_knowledge_base
Remove all documents from the knowledge base.

**Parameters:** None

**Example usage:**
```
"Clear the knowledge base"
"Remove all documents"
```

## Usage Workflow

### 1. Start the Server (if not auto-started by client)

Some MCP clients start the server automatically. If you need to start it manually:

```bash
mcp-knowledge-base
```

### 2. Add Documents

In your LLM conversation:

```
User: Add the file ./src/main.py to the knowledge base


LLM: I'll add that file to the knowledge base.
[Calls add_document tool]
The file has been successfully added to the knowledge base.
```

### 3. Search Documents

```
User: What authentication methods do we use in our codebase?

LLM: Let me search the knowledge base for authentication information.
[Calls search_documents with query "authentication methods"]
Based on the search results, your codebase uses JWT tokens and OAuth2...
```

### 4. List Documents

```
User: What documents are in the knowledge base?

LLM: [Calls list_documents]
The knowledge base contains 15 documents:
1. src/auth/login.py
2. src/auth/oauth.py
...
```

## Configuration Options

### Basic Configuration

Create a `config.yaml` file:

```yaml
database:
  path: "./knowledge_base.db"
  table_prefix: "kb_"

embedding:
  model: "sentence-transformers/all-MiniLM-L6-v2"
  batch_size: 32
  cache_dir: "./models"

processing:
  max_file_size_mb: 10
  chunk_size: 1000
  chunk_overlap: 200
  supported_extensions: [".py", ".txt"]

server:
  name: "knowledge-base"
  log_level: "INFO"
```

### Environment Variables

Set these in your MCP client configuration:

```json
{
  "env": {
    "LANCE_DB_PATH": "./knowledge_base.db",
    "EMBEDDING_MODEL": "sentence-transformers/all-MiniLM-L6-v2",
    "LOG_LEVEL": "INFO",
    "MAX_FILE_SIZE_MB": "10",
    "CHUNK_SIZE": "1000"
  }
}
```

## Troubleshooting

### Server Not Starting

**Check if the command is in PATH:**
```bash
which mcp-knowledge-base
```

If not found, use the full path in your MCP client config:
```json
{
  "command": "/full/path/to/mcp-knowledge-base"
}
```

Or use Python module syntax:
```json
{
  "command": "python",
  "args": ["-m", "mcp_knowledge_base.main"]
}
```

### Model Download Issues

The first run downloads the embedding model (~100MB). If this fails:

```bash
# Pre-download the model
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
```

### Permission Errors

Ensure the server has write access to:
- Database directory
- Model cache directory
- Log directory

```bash
chmod -R 755 ./knowledge_base.db ./models ./logs
```

### Check Logs

View server logs to diagnose issues:

```bash
# View all logs
tail -f logs/mcp_knowledge_base.log

# View errors only
tail -f logs/errors.log
```

### MCP Client Not Detecting Server

1. Verify the configuration file syntax (valid JSON)
2. Restart the MCP client application
3. Check client logs for connection errors
4. Verify the command path is correct

## Advanced Usage

### Multiple Knowledge Bases

Run separate instances with different databases:

**Client 1 - Project A:**
```json
{
  "mcpServers": {
    "kb-project-a": {
      "command": "mcp-knowledge-base",
      "args": ["--db-path", "./project_a.db"]
    }
  }
}
```

**Client 2 - Project B:**
```json
{
  "mcpServers": {
    "kb-project-b": {
      "command": "mcp-knowledge-base",
      "args": ["--db-path", "./project_b.db"]
    }
  }
}
```

### Custom Embedding Models

Use a different embedding model for better results:

```yaml
embedding:
  model: "sentence-transformers/all-mpnet-base-v2"  # Better quality, larger size
  # or
  model: "sentence-transformers/paraphrase-MiniLM-L3-v2"  # Faster, smaller
```

### Batch Document Addition

Add multiple documents at once by asking the LLM:

```
User: Add all Python files in the ./src directory to the knowledge base

LLM: [Calls add_document multiple times for each file]
```

## Example Conversations

### Code Search

```
User: I need to understand how we handle database connections

LLM: Let me search the knowledge base for database connection code.
[Searches for "database connections"]
Based on the code in src/db/connection.py, you use a connection pool with...
```

### Documentation Lookup

```
User: What's our error handling strategy?

LLM: [Searches for "error handling"]
According to the documentation in docs/ERROR_HANDLING.md, your error handling strategy includes...
```

### Code Review

```
User: Add this new file and check if it follows our existing patterns

LLM: [Adds the file, then searches for similar patterns]
I've added the file. Comparing it to existing code, I notice...
```

## Best Practices

1. **Organize Documents**: Keep related documents together for better search results
2. **Regular Updates**: Re-add modified files to keep the knowledge base current
3. **Clear Queries**: Use specific search terms for better results
4. **Chunk Size**: Adjust `chunk_size` based on your document types (larger for documentation, smaller for code)
5. **Model Selection**: Choose embedding models based on your needs (speed vs. quality)

## Performance Tips

1. **Batch Size**: Increase `batch_size` if you have more RAM available
2. **Cache Directory**: Use an SSD for the model cache directory
3. **Database Location**: Store the database on fast storage
4. **Limit Results**: Use smaller `limit` values for faster searches

## Security Considerations

1. **File Access**: The server can only access files the user has permissions for
2. **Local Only**: All processing happens locally, no data sent to external services
3. **Offline Mode**: Works completely offline after initial model download
4. **Sandboxing**: Run in a virtual environment for isolation

## Getting Help

- **Documentation**: See docs/QUICKSTART.md and docs/DEPLOYMENT.md
- **Issues**: https://github.com/example/mcp-knowledge-base/issues
- **Logs**: Check `logs/mcp_knowledge_base.log` for detailed information

## Next Steps

1. Install the server following the steps above
2. Configure your MCP client
3. Add some documents to test
4. Try searching for content
5. Integrate into your workflow

For more detailed information, see:
- [Quick Start Guide](QUICKSTART.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Error Handling](ERROR_HANDLING.md)
