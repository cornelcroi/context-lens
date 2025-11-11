# Context Lens

**Give your AI the ability to understand meaning, not just match keywords.**

[![Tests](https://github.com/cornelcroi/codelens/workflows/Tests/badge.svg)](https://github.com/cornelcroi/codelens/actions)
[![PyPI version](https://badge.fury.io/py/context-lens.svg)](https://badge.fury.io/py/context-lens)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## What is Context Lens?

Context Lens is a self-contained Model Context Protocol (MCP) server with built-in serverless vector storage (LanceDB) that brings semantic search to your AI assistant. Point it at any content - codebases, documentation, contracts, or text files - and your AI can instantly understand and answer questions about the content.

**Traditional keyword search** finds files containing specific words. Miss the exact term? Miss the content.

**Context Lens** understands meaning. Ask about "authentication" and find code about login, credentials, tokens, OAuth, and access control - even if those files never use the word "authentication."

## Why LanceDB?

Context Lens uses **LanceDB** - a modern, serverless vector database:

- **🆓 Completely Free & Local** - No cloud services, API keys, or subscriptions
- **⚡ Zero Infrastructure** - Embedded database, just a file on disk
- **🚀 Fast & Efficient** - Built on Apache Arrow, optimized for vector search
- **💾 Simple Storage** - Single file database, easy to backup or move

Think of it as "SQLite for AI embeddings" - all the power of vector search without the complexity.

## Features

- 🔍 **Semantic Search** - Understand meaning, not just keywords
- 🚀 **Zero Setup** - No installation, no configuration, no API keys
- 💾 **Serverless Storage** - Built-in LanceDB, no external database
- 🔒 **100% Local & Private** - All data stays on your machine
- 📁 **Local & GitHub** - Index local files or public GitHub repositories
- 🎯 **Smart Parsing** - Language-aware chunking for better results

## Quick Setup

### Kiro IDE

Add to `.kiro/settings/mcp.json`:

```json
{
  "mcpServers": {
    "context-lens": {
      "command": "uvx",
      "args": ["context-lens"],
      "autoApprove": ["list_documents", "search_documents"]
    }
  }
}
```

Reload: Command Palette → "MCP: Reload Servers"

### Cursor

Add to `.cursor/mcp.json`:

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

### Other MCP Clients

For Claude Desktop, Continue.dev, or any MCP-compatible client:

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

> 📖 **Need detailed setup instructions?** See [SETUP.md](SETUP.md) for all clients, programmatic usage, and configuration options.

## Architecture

![Context Lens Architecture](img/architecture.jpg)

### How It Works

```
1. 📄 Document Ingestion
   └─ Read content → Generate hash → Extract metadata → Smart chunking

2. 🧮 Vector Embedding
   └─ Load model → Convert to 384-dim vectors → Batch processing

3. 🔍 Semantic Search
   └─ Query to vector → Find similar → Rank by similarity → Return results

4. 💾 Storage
   └─ LanceDB: Fast columnar vector database, all data stays local
```

## Smart Parsing & Chunking

Context Lens doesn't just split text blindly - it understands code structure and creates intelligent chunks that respect language boundaries.

**The difference:** Generic chunking splits code arbitrarily by character count, often breaking functions mid-way. Smart parsing understands your code's structure and creates complete, meaningful chunks.

### Supported File Types

- **🐍 Python** (`.py`, `.pyw`) - Functions, classes, imports
- **⚡ JavaScript/TypeScript** (`.js`, `.jsx`, `.ts`, `.tsx`, `.mjs`, `.cjs`) - Functions, classes, imports
- **📦 JSON** (`.json`, `.jsonc`) - Top-level keys, nested objects
- **📋 YAML** (`.yaml`, `.yml`) - Top-level keys, lists, mappings
- **📝 Markdown** (`.md`, `.markdown`, `.mdx`) - Header hierarchy, code blocks
- **🦀 Rust** (`.rs`) - Structs, traits, impl blocks, functions
- **📄 Other Files** (`.txt`, `.log`, `.cpp`, `.java`, etc.) - Intelligent paragraph/sentence splitting

### Benefits

✅ **Complete Code Units** - Never splits functions or classes mid-way  
✅ **Preserved Context** - Docstrings, comments, and structure stay intact  
✅ **Better Search** - Find complete, understandable code snippets  
✅ **Automatic** - No configuration needed, works based on file extension  

> 📖 **Want to see how it works?** Check out [PARSING_EXAMPLES.md](PARSING_EXAMPLES.md) for detailed examples.

## What You Can Add

- **📁 Local files & folders** - Your projects, documentation, any text files
- **🌐 GitHub repositories** - Public repos, specific branches, directories, or files
- **📄 Documents** - Contracts, policies, research papers, technical docs

Examples:
- `./src/` - Local directory
- `https://github.com/fastapi/fastapi` - Entire repository
- `https://github.com/django/django/tree/main/django/contrib/auth` - Specific directory
- `/path/to/contracts/` - Legal documents

> 📖 **See more examples:** [USAGE_GUIDE.md](USAGE_GUIDE.md)

## Available Tools

- **📥 add_document** - Add files, folders, or GitHub URLs
- **🔍 search_documents** - Semantic search across all content
- **📋 list_documents** - Browse indexed documents
- **ℹ️ get_document_info** - Get metadata about a document
- **🗑️ remove_document** - Remove specific documents
- **🧹 clear_knowledge_base** - Remove all documents

> 📖 **See detailed examples:** [USAGE_GUIDE.md](USAGE_GUIDE.md#available-tools)

## Quick Start

### Add Your Project
```
You: Add all Python files from ./src to the knowledge base
LLM: ✓ Added 23 Python files with 156 chunks
```

### Learn from Open Source
```
You: Add https://github.com/fastapi/fastapi to the knowledge base
LLM: ✓ Added 247 files from repository with 1,543 chunks

You: How does FastAPI handle dependency injection?
LLM: [Searches and explains based on actual source code]
```

### Analyze Documents
```
You: Add all contracts from ./legal/contracts
LLM: ✓ Added 12 contract documents with 487 chunks

You: Find all termination clauses
LLM: [Searches and summarizes termination terms]
```

> 📖 **More examples:** [USAGE_GUIDE.md](USAGE_GUIDE.md#quick-start-examples)

## Example Queries

**Code Understanding:**
- "How does this project handle database connections?"
- "Explain the authentication flow"
- "Find similar error handling patterns"

**Document Analysis:**
- "Find all liability clauses in these contracts"
- "What are the coverage exclusions?"
- "Summarize the payment terms"

**Learning:**
- "How does FastAPI implement dependency injection?"
- "Show me examples of async/await usage"
- "Compare how Django and Flask handle routing"

> 📖 **100+ query examples:** [USAGE_GUIDE.md](USAGE_GUIDE.md#example-queries)

## FAQ

**How does this compare to GitHub's MCP server?**  
They serve different purposes and complement each other:

**Context Lens is better for:**
- 🧠 Semantic understanding - "Find authentication code" returns login, credentials, tokens, OAuth - even without exact keywords
- 📚 Learning codebases - Ask "How does X work?" and get conceptually relevant results across the entire project
- 🔍 Pattern discovery - Find similar code patterns, error handling approaches, or architectural decisions
- 💾 Offline development - Once indexed, works without internet connection
- 🔒 Privacy - All processing happens locally, no data sent to external services

**GitHub's MCP server is better for:**
- 🔧 Repository management - Create issues, manage PRs, handle CI/CD operations
- 📊 Real-time state - Always fetches the latest version from GitHub
- 🌐 GitHub-specific features - Integrates with GitHub's ecosystem (Actions, Projects, etc.)

**Key difference:** Context Lens clones once and indexes everything for fast semantic search (offline). GitHub MCP makes API calls per query for real-time access (online). Use Context Lens to understand code, GitHub MCP to manage repositories.

**Why is the first run slow?**  
The embedding model (~100MB) downloads on first use. This only happens once.

**Do I need an API key?**  
No! Context Lens runs completely locally. No API keys, no cloud services.

**Where is my data stored?**  
Everything is stored locally in `knowledge_base.db`. You can change this location.

**Can I use this with private code?**  
Yes! All processing happens locally. Nothing is sent to external services.

**How much disk space does it use?**  
~100MB for the model + ~1KB per text chunk. A 10MB codebase uses ~5-10MB of database space.

> 📖 **More questions:** [TROUBLESHOOTING.md](TROUBLESHOOTING.md#faq)

## Documentation

- 📖 **[Setup Guide](SETUP.md)** - Detailed setup for all clients, configuration options
- 📚 **[Usage Guide](USAGE_GUIDE.md)** - Examples, queries, and best practices
- 🎨 **[Parsing Examples](PARSING_EXAMPLES.md)** - How smart parsing works
- 🔧 **[Troubleshooting](TROUBLESHOOTING.md)** - Common issues and solutions
- ⚙️ **[Technical Details](TECHNICAL.md)** - Architecture, stack, and performance
- 🤝 **[Contributing](CONTRIBUTING.md)** - How to contribute, roadmap

## Contributing

Contributions are welcome! Please:

1. Open an issue first to discuss your idea
2. Get approval before starting work
3. Submit a PR referencing the issue

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MIT License - see [LICENSE](LICENSE) for details.

---

**Star the repo if you find it useful!** ⭐
