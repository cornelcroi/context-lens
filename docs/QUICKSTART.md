# Quick Start Guide

Get up and running with the MCP Knowledge Base Server in minutes.

## Prerequisites

- Python 3.8 or higher
- pip package manager
- 2GB+ RAM recommended

## Installation

### Step 1: Install the Package

```bash
# Clone the repository (if from source)
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

## First Run

### Start with Defaults

The simplest way to start the server:

```bash
mcp-knowledge-base
```

This will:
- Create a `knowledge_base.db` database in the current directory
- Download the embedding model to `./models` (first run only, ~100MB)
- Create log files in `./logs`
- Start the MCP server

### View Configuration

Check what configuration is being used:

```bash
mcp-knowledge-base --show-config
```

## Basic Configuration

### Option 1: Configuration File

Create a `config.yaml` file:

```bash
cp config.example.yaml config.yaml
```

Edit `config.yaml` to customize settings, then start:

```bash
mcp-knowledge-base --config config.yaml
```

### Option 2: Environment Variables

Set environment variables before starting:

```bash
export LANCE_DB_PATH="./my_knowledge_base.db"
export LOG_LEVEL="DEBUG"
mcp-knowledge-base
```

### Option 3: Command-Line Arguments

Override settings via command-line:

```bash
mcp-knowledge-base --log-level DEBUG --db-path ./my_kb.db
```

## Using the Server

Once started, the server exposes four MCP tools:

### 1. Add Document

Add a document to the knowledge base:

```python
# Via MCP client
result = await client.call_tool("add_document", {
    "file_path": "/path/to/document.py"
})
```

### 2. List Documents

List all indexed documents:

```python
result = await client.call_tool("list_documents", {
    "limit": 10,
    "offset": 0
})
```

### 3. Search Documents

Search for relevant documents:

```python
result = await client.call_tool("search_documents", {
    "query": "how to implement authentication",
    "limit": 5
})
```

### 4. Clear Knowledge Base

Remove all documents:

```python
result = await client.call_tool("clear_knowledge_base", {})
```

## Common Scenarios

### Development Setup

For local development with verbose logging:

```bash
mcp-knowledge-base --log-level DEBUG
```

### Production Setup

For production with custom paths:

```bash
mcp-knowledge-base \
  --config /etc/mcp-kb/config.yaml \
  --log-dir /var/log/mcp-kb \
  --log-level INFO
```

## Monitoring

### Check Logs

View real-time logs:

```bash
tail -f logs/mcp_knowledge_base.log
```

View errors only:

```bash
tail -f logs/errors.log
```

### Check Status

If running as a systemd service:

```bash
sudo systemctl status mcp-knowledge-base
```

## Stopping the Server

### Graceful Shutdown

Press `Ctrl+C` in the terminal where the server is running.

Or send a SIGTERM signal:

```bash
kill -TERM $(pgrep -f mcp-knowledge-base)
```

### Force Stop

If the server is unresponsive:

```bash
kill -9 $(pgrep -f mcp-knowledge-base)
```

## Troubleshooting

### Server Won't Start

**Check configuration:**
```bash
mcp-knowledge-base --show-config
```

**Check logs:**
```bash
cat logs/errors.log
```

### Model Download Fails

Pre-download the embedding model:

```bash
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
```

### Permission Errors

Ensure directories are writable:

```bash
chmod -R 755 ./logs ./models
```

### Database Locked

If database is locked, ensure no other instance is running:

```bash
ps aux | grep mcp-knowledge-base
```

## Next Steps

- Read the [Deployment Guide](DEPLOYMENT.md) for production setup
- Check [Error Handling](ERROR_HANDLING.md) for error management
- Review the [README](../README.md) for detailed configuration options

## Getting Help

- GitHub Issues: https://github.com/example/mcp-knowledge-base/issues
- Documentation: https://github.com/example/mcp-knowledge-base/docs
- Email: info@example.com

## Tips

1. **First Run**: The first startup will be slower as it downloads the embedding model (~100MB)
2. **Resource Usage**: The server uses ~500MB RAM for the embedding model plus database overhead
3. **File Limits**: Default max file size is 10MB, adjust in config if needed
4. **Supported Files**: Currently supports .py and .txt files, more formats coming soon
5. **Offline Mode**: Once the model is downloaded, the server works completely offline
