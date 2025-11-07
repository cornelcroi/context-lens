# MCP Knowledge Base Server - Deployment Guide

This guide covers deployment, configuration, and operational aspects of the MCP Knowledge Base Server.

## Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Server](#running-the-server)
- [Command-Line Options](#command-line-options)
- [Environment Variables](#environment-variables)
- [Deployment Scenarios](#deployment-scenarios)
- [Monitoring and Logging](#monitoring-and-logging)
- [Troubleshooting](#troubleshooting)
- [Shutdown and Cleanup](#shutdown-and-cleanup)

## Installation

### Standard Installation (Using uvx)

For most users, no manual installation is needed. Just configure your LLM client with:

```json
{
  "command": "uvx",
  "args": ["mcp-knowledge-base"]
}
```

See [INSTALL.md](../INSTALL.md) for LLM client setup instructions.

### Manual Installation (Development/Custom Deployment)

Only needed if you want to:
- Modify the source code
- Deploy without uvx
- Use custom Python environments
- Run in restricted environments

#### From Source

```bash
# Clone the repository
git clone https://github.com/example/mcp-knowledge-base.git
cd mcp-knowledge-base

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .

# Verify installation
mcp-knowledge-base --version
```

#### Using the Install Script

```bash
# Run the interactive installer
./scripts/install.sh
```

The installer will guide you through:
- Python version check
- Virtual environment setup (optional)
- Dependency installation
- Directory creation
- Configuration setup

#### Requirements

- Python 3.8 or higher
- 2GB+ RAM recommended for embedding models
- ~100MB disk space for the embedding model
- Disk space for:
  - Embedding model cache (~100MB)
  - LanceDB database (varies by document count)
  - Log files

## Configuration

The server supports three configuration methods with the following priority:

1. **Explicit configuration file** (via `--config` flag)
2. **Default config.yaml** in the current directory
3. **Environment variables**
4. **Built-in defaults**

### Creating a Configuration File

Copy the example configuration:

```bash
cp config.example.yaml config.yaml
```

Edit `config.yaml` to customize settings:

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

### Configuration Options

#### Database Settings

- `path`: Path to LanceDB database file
- `table_prefix`: Prefix for database tables

#### Embedding Settings

- `model`: HuggingFace model identifier for embeddings
- `batch_size`: Number of texts to process in parallel (1-1000)
- `cache_dir`: Directory to cache downloaded models

#### Processing Settings

- `max_file_size_mb`: Maximum file size to process (1-100 MB)
- `chunk_size`: Size of text chunks for embedding (100+ characters)
- `chunk_overlap`: Overlap between chunks (0 to chunk_size-1)
- `supported_extensions`: List of file extensions to process

#### Server Settings

- `name`: Server name for identification
- `log_level`: Logging verbosity (DEBUG, INFO, WARNING, ERROR, CRITICAL)

## Running the Server

### Basic Usage

Start the server with default configuration:

```bash
mcp-knowledge-base
```

### With Custom Configuration

```bash
mcp-knowledge-base --config /path/to/config.yaml
```

### With Command-Line Overrides

```bash
mcp-knowledge-base --log-level DEBUG --db-path ./my_kb.db
```

### Display Configuration

View the active configuration without starting the server:

```bash
mcp-knowledge-base --show-config
```

## Command-Line Options

```
usage: mcp-knowledge-base [-h] [--config PATH] [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                          [--log-dir PATH] [--db-path PATH] [--version] [--show-config]

MCP Knowledge Base Server - Document ingestion and semantic search

optional arguments:
  -h, --help            show this help message and exit
  --config PATH         Path to YAML configuration file
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Logging level (default: INFO or from config)
  --log-dir PATH        Directory for log files (default: ./logs)
  --db-path PATH        Path to LanceDB database
  --version             show program's version number and exit
  --show-config         Display configuration and exit
```

### Examples

```bash
# Start with debug logging
mcp-knowledge-base --log-level DEBUG

# Use custom database location
mcp-knowledge-base --db-path /data/knowledge_base.db

# Custom log directory
mcp-knowledge-base --log-dir /var/log/mcp-kb

# Combine multiple options
mcp-knowledge-base --config prod.yaml --log-level INFO --log-dir /var/log/mcp-kb
```

## Environment Variables

All configuration options can be set via environment variables:

```bash
# Database configuration
export LANCE_DB_PATH="./knowledge_base.db"
export LANCE_DB_TABLE_PREFIX="kb_"

# Embedding configuration
export EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2"
export EMBEDDING_BATCH_SIZE="32"
export EMBEDDING_CACHE_DIR="./models"

# Processing configuration
export MAX_FILE_SIZE_MB="10"
export CHUNK_SIZE="1000"
export CHUNK_OVERLAP="200"
export SUPPORTED_EXTENSIONS=".py,.txt"

# Server configuration
export MCP_SERVER_NAME="knowledge-base"
export LOG_LEVEL="INFO"

# Start server
mcp-knowledge-base
```

## Deployment Scenarios

### Development Environment

```bash
# Use default settings with debug logging
mcp-knowledge-base --log-level DEBUG
```

### Production Environment

Create a production configuration file:

```yaml
# prod.yaml
database:
  path: "/var/lib/mcp-kb/knowledge_base.db"
  table_prefix: "kb_"

embedding:
  model: "sentence-transformers/all-MiniLM-L6-v2"
  batch_size: 64
  cache_dir: "/var/lib/mcp-kb/models"

processing:
  max_file_size_mb: 20
  chunk_size: 1000
  chunk_overlap: 200
  supported_extensions: [".py", ".txt", ".md"]

server:
  name: "knowledge-base-prod"
  log_level: "INFO"
```

Run with production config:

```bash
mcp-knowledge-base --config prod.yaml --log-dir /var/log/mcp-kb
```

### Systemd Service

Create `/etc/systemd/system/mcp-knowledge-base.service`:

```ini
[Unit]
Description=MCP Knowledge Base Server
After=network.target

[Service]
Type=simple
User=mcp-kb
Group=mcp-kb
WorkingDirectory=/opt/mcp-knowledge-base
Environment="LANCE_DB_PATH=/var/lib/mcp-kb/knowledge_base.db"
Environment="EMBEDDING_CACHE_DIR=/var/lib/mcp-kb/models"
Environment="LOG_LEVEL=INFO"
ExecStart=/usr/local/bin/mcp-knowledge-base --log-dir /var/log/mcp-kb
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable mcp-knowledge-base
sudo systemctl start mcp-knowledge-base
sudo systemctl status mcp-knowledge-base
```

## Monitoring and Logging

### Log Files

The server creates three log files in the log directory (default: `./logs`):

1. **mcp_knowledge_base.log**: All log messages (DEBUG and above)
2. **errors.log**: Error messages only (ERROR and above)
3. Console output: INFO and above (configurable)

### Log Rotation

For production, configure log rotation with `logrotate`:

```
# /etc/logrotate.d/mcp-knowledge-base
/var/log/mcp-kb/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 mcp-kb mcp-kb
    sharedscripts
    postrotate
        systemctl reload mcp-knowledge-base > /dev/null 2>&1 || true
    endscript
}
```

### Monitoring Metrics

Monitor these key metrics:

- **Startup time**: Server initialization duration
- **Document count**: Number of indexed documents
- **Search latency**: Time to execute searches
- **Error rate**: Frequency of errors in logs
- **Disk usage**: Database and model cache size
- **Memory usage**: Process memory consumption

### Health Checks

Check server health:

```bash
# Check if process is running
ps aux | grep mcp-knowledge-base

# Check logs for errors
tail -f logs/errors.log

# View recent activity
tail -f logs/mcp_knowledge_base.log
```

## Troubleshooting

### Server Won't Start

**Configuration errors:**
```bash
# Validate configuration
mcp-knowledge-base --show-config
```

**Permission issues:**
```bash
# Check directory permissions
ls -la ./knowledge_base.db
ls -la ./models
ls -la ./logs
```

**Port conflicts:**
```bash
# Check if port is in use (if applicable)
netstat -tuln | grep 8080
```

### Model Download Issues

If the embedding model fails to download:

```bash
# Pre-download the model
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Or set a custom cache directory with write permissions
export EMBEDDING_CACHE_DIR="/path/to/writable/dir"
```

### Database Corruption

If the database becomes corrupted:

```bash
# Backup existing database
cp knowledge_base.db knowledge_base.db.backup

# Remove corrupted database
rm knowledge_base.db

# Restart server (will create new database)
mcp-knowledge-base
```

### Memory Issues

If the server runs out of memory:

1. Reduce `batch_size` in configuration
2. Reduce `max_file_size_mb`
3. Increase system swap space
4. Use a smaller embedding model

### High CPU Usage

If CPU usage is high:

1. Reduce `batch_size` for embedding
2. Limit concurrent document processing
3. Check for infinite loops in logs

## Shutdown and Cleanup

### Graceful Shutdown

The server supports graceful shutdown via signals:

```bash
# Send SIGINT (Ctrl+C)
kill -INT <pid>

# Send SIGTERM
kill -TERM <pid>
```

The server will:
1. Stop accepting new requests
2. Complete in-progress operations
3. Close database connections
4. Clean up resources
5. Exit with code 0

### Force Shutdown

If graceful shutdown hangs:

```bash
# Send SIGKILL (force)
kill -9 <pid>
```

### Cleanup Operations

The server automatically performs cleanup on shutdown:

- Closes LanceDB connections
- Releases embedding model memory
- Flushes log buffers
- Removes temporary files

### Manual Cleanup

To manually clean up resources:

```bash
# Remove database
rm -rf knowledge_base.db

# Remove model cache
rm -rf models/

# Remove logs
rm -rf logs/

# Remove temporary files
rm -rf /tmp/mcp-kb-*
```

## Best Practices

1. **Configuration Management**
   - Use version control for configuration files
   - Keep sensitive data in environment variables
   - Document configuration changes

2. **Resource Management**
   - Monitor disk space for database growth
   - Set appropriate file size limits
   - Configure log rotation

3. **Security**
   - Run server with minimal privileges
   - Restrict file system access
   - Validate input file paths

4. **Backup**
   - Regularly backup the LanceDB database
   - Keep configuration files in version control
   - Document deployment procedures

5. **Monitoring**
   - Set up log aggregation
   - Monitor error rates
   - Track performance metrics

## Support

For issues and questions:

- GitHub Issues: https://github.com/example/mcp-knowledge-base/issues
- Documentation: https://github.com/example/mcp-knowledge-base/docs
- Email: info@example.com
