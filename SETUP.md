# Setup & Configuration Guide

Complete guide for setting up Context Lens with different clients and customizing configuration.

## Table of Contents

- [Client Setup](#client-setup)
  - [Kiro IDE](#kiro-ide)
  - [Cursor](#cursor)
  - [Claude Desktop](#claude-desktop)
  - [Continue.dev](#continuedev)
  - [Other MCP Clients](#other-mcp-clients)
- [Programmatic Usage](#programmatic-usage)
- [Configuration Options](#configuration-options)
  - [Custom Database Location](#custom-database-location)
  - [CLI Parameters](#cli-parameters)
  - [Environment Variables](#environment-variables)
  - [Configuration File (YAML)](#configuration-file-yaml)

---

## Client Setup

### Kiro IDE

**Config file:** `.kiro/settings/mcp.json` in your workspace

```json
{
  "mcpServers": {
    "context-lens": {
      "command": "uvx",
      "args": ["context-lens"],
      "disabled": false,
      "autoApprove": ["list_documents", "search_documents"]
    }
  }
}
```

**Reload:** Command Palette → "MCP: Reload Servers"

The `autoApprove` setting allows read-only operations without confirmation prompts.

---

### Cursor

**Config file:** `.cursor/mcp.json` in your workspace

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

Open **Settings → MCP Servers** to confirm the connection and view available tools.

---

### Claude Desktop

**Config file location:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%/Claude/claude_desktop_config.json`

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

**Alternative using CLI:**
```bash
claude mcp add context-lens -- npx context-lens@latest
```

Restart Claude Desktop and you're ready!

---

### Continue.dev

**Config file:** `~/.continue/config.json`

```json
{
  "mcpServers": [
    {
      "name": "context-lens",
      "command": "uvx",
      "args": ["context-lens"]
    }
  ]
}
```

Restart Continue.dev to apply changes.

---

### Other MCP Clients

For any MCP-compatible client, use the standard configuration:

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

Check your client's documentation for the specific config file location.

---

## Programmatic Usage

Use Context Lens directly in your Python code with any MCP-compatible framework:

```python
#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from mcp import StdioServerParameters, stdio_client
from strands import Agent
from strands.models.openai import OpenAIModel
from strands.tools.mcp import MCPClient

def main():
    # Load environment variables from .env file
    load_dotenv()
    
    # Create MCP client for context-lens server
    mcp_client = MCPClient(
        lambda: stdio_client(
            StdioServerParameters(
                command="uvx",
                args=["context-lens"]
            )
        )
    )
    
    # Create an agent with OpenAI model and MCP tools
    model = OpenAIModel(model_id="gpt-4o-mini")
    agent = Agent(model=model, tools=[mcp_client])
    
    print("Chatbot started! Type 'quit' to exit.")
    
    while True:
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("Goodbye!")
            break
            
        if not user_input:
            continue
            
        try:
            response = agent(user_input)
            print(f"Bot: {response}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
```

This example uses the [Strands](https://github.com/plastic-labs/strands) framework, but Context Lens works with any MCP client library.

---

## Configuration Options

### Custom Database Location

Specify a custom location for your knowledge base:

```json
{
  "mcpServers": {
    "context-lens": {
      "command": "uvx",
      "args": ["context-lens", "--db-path", "./my_knowledge_base.db"]
    }
  }
}
```

Or using environment variables:
```json
{
  "mcpServers": {
    "context-lens": {
      "command": "uvx",
      "args": ["context-lens"],
      "env": {
        "LANCE_DB_PATH": "./my_knowledge_base.db"
      }
    }
  }
}
```

---

### CLI Parameters

Context Lens supports various CLI parameters for customization:

**Available Options:**
- `--config PATH` - Path to YAML configuration file
- `--db-path PATH` - Path to LanceDB database (default: `./knowledge_base.db`)
- `--log-level LEVEL` - Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- `--show-config` - Display current configuration and exit
- `--version` - Show version information
- `--help` - Show help message

**Example:**
```json
{
  "mcpServers": {
    "context-lens": {
      "command": "uvx",
      "args": [
        "context-lens",
        "--config", "/path/to/config.yaml",
        "--db-path", "/path/to/knowledge_base.db",
        "--log-level", "DEBUG"
      ]
    }
  }
}
```

---

### Environment Variables

All configuration can be set via environment variables:

```json
{
  "mcpServers": {
    "context-lens": {
      "command": "uvx",
      "args": ["context-lens"],
      "env": {
        "LANCE_DB_PATH": "/path/to/knowledge_base.db",
        "LANCE_DB_TABLE_PREFIX": "kb_",
        "LOG_LEVEL": "DEBUG",
        "MCP_SERVER_NAME": "my-knowledge-base",
        "EMBEDDING_MODEL": "sentence-transformers/all-MiniLM-L6-v2",
        "EMBEDDING_BATCH_SIZE": "32",
        "EMBEDDING_CACHE_DIR": "./models",
        "MAX_FILE_SIZE_MB": "10",
        "CHUNK_SIZE": "1000",
        "CHUNK_OVERLAP": "200",
        "SUPPORTED_EXTENSIONS": ".py,.txt,.md,.js,.ts,.java,.cpp,.c,.h,.go,.rs,.sh,.bash,.rb,.php,.json,.yaml,.yml,.jsx,.tsx"
      }
    }
  }
}
```

**Environment Variables Reference:**

| Variable | Default | Description |
|----------|---------|-------------|
| `LANCE_DB_PATH` | `./knowledge_base.db` | Path to LanceDB database |
| `LANCE_DB_TABLE_PREFIX` | `kb_` | Prefix for database tables |
| `LOG_LEVEL` | `INFO` | Logging level |
| `MCP_SERVER_NAME` | `knowledge-base` | Server name for identification |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model to use |
| `EMBEDDING_BATCH_SIZE` | `32` | Batch size for embedding processing |
| `EMBEDDING_CACHE_DIR` | `./models` | Directory to cache embedding models |
| `MAX_FILE_SIZE_MB` | `10` | Maximum file size to process (MB) |
| `CHUNK_SIZE` | `1000` | Text chunk size for processing |
| `CHUNK_OVERLAP` | `200` | Overlap between text chunks |
| `SUPPORTED_EXTENSIONS` | See [Technical Details](TECHNICAL.md) | Comma-separated list of file extensions |

---

### Configuration File (YAML)

Create a `config.yaml` file for complex setups:

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
  supported_extensions:
    - ".py"
    - ".txt"
    - ".md"
    - ".js"
    - ".ts"
    - ".json"
    - ".yaml"
    - ".yml"
    # Add more as needed

server:
  name: "knowledge-base"
  log_level: "INFO"
```

Then use it:
```json
{
  "mcpServers": {
    "context-lens": {
      "command": "uvx",
      "args": ["context-lens", "--config", "config.yaml"]
    }
  }
}
```

---

## Installation (Optional)

Most users don't need to install anything - `uvx` handles everything automatically.

If you prefer to install locally:

```bash
pip install context-lens
```

Or install from source:

```bash
git clone https://github.com/cornelcroi/context-lens.git
cd context-lens
pip install -e .
```

---

## First Run

On first use, `uvx` automatically:
- Downloads and installs the package
- Installs all dependencies  
- Downloads the embedding model (~100MB, one-time)
- Starts the server

The server then:
- Creates `knowledge_base.db` in your current directory
- Stores logs in `./logs`
- Ready to use!

**Zero configuration needed!**
