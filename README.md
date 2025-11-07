# MCP Knowledge Base Server

[![Tests](https://github.com/yourusername/mcp-knowledge-base/workflows/Tests/badge.svg)](https://github.com/yourusername/mcp-knowledge-base/actions)
[![PyPI version](https://badge.fury.io/py/mcp-knowledge-base.svg)](https://badge.fury.io/py/mcp-knowledge-base)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Model Context Protocol (MCP) server that provides document ingestion, indexing, and semantic search capabilities using LanceDB as the vector database.

**Give your local LLM the ability to search and understand your codebase** - Works with Claude Desktop, Kiro IDE, Continue.dev, and other MCP clients.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Your LLM Client                              │
│              (Claude Desktop, Kiro IDE, Continue.dev)                │
└────────────────────────────────┬────────────────────────────────────┘
                                 │ MCP Protocol
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    MCP Knowledge Base Server                         │
│                                                                       │
│  ┌─────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  add_document   │  │ search_documents │  │ list_documents   │  │
│  │                 │  │                  │  │                  │  │
│  │  Ingests files  │  │  Semantic search │  │  Browse indexed  │  │
│  │  (.py, .txt)    │  │  with vectors    │  │  documents       │  │
│  └────────┬────────┘  └────────┬─────────┘  └────────┬─────────┘  │
│           │                    │                      │             │
│           ▼                    ▼                      ▼             │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              Document Processing Pipeline                     │  │
│  │                                                                │  │
│  │  1. Content Extraction  →  2. Chunking  →  3. Embedding      │  │
│  │     • File reading          • Smart split    • Sentence       │  │
│  │     • Encoding detect       • Overlap        Transformers     │  │
│  │     • Hash generation       • Metadata       • Local model    │  │
│  └────────────────────────────┬─────────────────────────────────┘  │
│                                ▼                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    LanceDB Vector Store                       │  │
│  │                                                                │  │
│  │  📄 Documents Table          📦 Chunks Table                  │  │
│  │  • Metadata                  • Text content                   │  │
│  │  • File paths                • 384-dim vectors                │  │
│  │  • Timestamps                • Document refs                  │  │
│  │  • Chunk counts              • Fast ANN search                │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
                    💾 Local Storage (100% Offline)
                    • knowledge_base.db
                    • Embedding model cache
                    • No external API calls
```

## Features

- **🔍 Semantic Search** - Find code by meaning, not just keywords
- **�  GitHub Integration** - Add entire repositories with one command
- **� FSmart Chunking** - Intelligent text splitting with overlap for better context
- **� F0ast Vector Search** - LanceDB's approximate nearest neighbor search
- **🔒 100% Local** - All processing happens on your machine, no data leaves
- **🎯 MCP Native** - Built specifically for the Model Context Protocol
- **⚡ Easy Setup** - One command with `uvx`, no configuration needed
- **� Pyth-on & Text** - Supports .py and .txt files (more formats coming)
- **🔄 Real-time Updates** - Add/remove documents on the fly

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

## What You Can Add

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Supported Input Types                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  📁 Local Files & Directories                                        │
│  ├─ Single file:      /path/to/script.py                            │
│  ├─ Directory:        /path/to/project/src/                         │
│  └─ Recursive:        Automatically processes subdirectories         │
│                                                                       │
│  🐙 GitHub Repositories (Public)                                     │
│  ├─ Entire repo:      https://github.com/user/repo                  │
│  ├─ Specific branch:  https://github.com/user/repo/tree/develop     │
│  ├─ Subdirectory:     https://github.com/user/repo/tree/main/src    │
│  └─ Single file:      https://github.com/user/repo/blob/main/file.py│
│                                                                       │
│  📄 Supported File Types                                             │
│  ├─ Python:           .py                                            │
│  ├─ Text:             .txt                                           │
│  └─ Markdown:         .md (coming soon)                              │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### 💡 Try These Popular Repositories

**Web Frameworks:**
```
https://github.com/django/django          # Django web framework
https://github.com/pallets/flask          # Flask microframework  
https://github.com/fastapi/fastapi        # FastAPI modern framework
```

**Data Science:**
```
https://github.com/pandas-dev/pandas      # Pandas data analysis
https://github.com/scikit-learn/scikit-learn  # Machine learning
https://github.com/pytorch/pytorch        # PyTorch deep learning
```

**Utilities:**
```
https://github.com/psf/requests           # HTTP library
https://github.com/python/cpython         # Python itself!
https://github.com/pallets/click          # CLI framework
```

**Learn Specific Features:**
```
https://github.com/django/django/tree/main/django/contrib/auth  # Django auth
https://github.com/fastapi/fastapi/tree/master/fastapi          # FastAPI core
https://github.com/requests/requests/tree/main/requests         # Requests lib
```

## Available Tools

Once connected to your LLM, you get four powerful tools:

```
┌─────────────────────────────────────────────────────────────────┐
│ 📥 add_document(file_path_or_url)                               │
│    Add documents to the knowledge base                          │
│    → Local files: "/path/to/file.py"                            │
│    → GitHub repos: "https://github.com/user/repo"               │
│    → GitHub files: "https://github.com/user/repo/blob/main/..." │
│    → Extracts content, creates embeddings, stores in LanceDB    │
│                                                                  │
│ 🔍 search_documents(query, limit=10)                            │
│    Semantic search across all documents                         │
│    → Finds relevant code/text by meaning, not just keywords     │
│                                                                  │
│ 📋 list_documents(limit=100, offset=0)                          │
│    List all indexed documents with pagination                   │
│    → Browse what's in your knowledge base                       │
│                                                                  │
│ 🗑️  clear_knowledge_base()                                      │
│    Remove all documents and start fresh                         │
│    → Clean slate when needed                                    │
└─────────────────────────────────────────────────────────────────┘
```

### Example Conversations

**Adding a GitHub Repository:**
```
You: Add the FastAPI repository to my knowledge base

LLM: I'll add the FastAPI repository for you.
     [Calls add_document("https://github.com/tiangolo/fastapi")]
     
     Cloning repository...
     Processing 247 Python files...
     ✓ Added 247 files from repository with 1,543 chunks
     
     You can now ask questions about FastAPI's implementation!

You: How does FastAPI handle dependency injection?

LLM: [Searches the FastAPI codebase...]
     Based on the FastAPI source code, dependency injection works through...
```

**Adding Local Files:**
```
You: Add all Python files in my src/ directory to the knowledge base

LLM: I'll add those files for you.
     [Calls add_document for each .py file]
     ✓ Added 15 Python files to the knowledge base

You: How do we handle authentication in this codebase?

LLM: Let me search for authentication-related code.
     [Calls search_documents with query "authentication handling"]
     
     Based on the code, you use JWT tokens with OAuth2. Here's what I found:
     - src/auth/jwt.py: Token generation and validation
     - src/auth/oauth.py: OAuth2 flow implementation
     - src/middleware/auth.py: Authentication middleware
     
     The main authentication flow is...
```

## Quick Start Examples

### Example 1: Add Your Project
```
You: Add all Python files from /Users/me/my-project/src to the knowledge base

LLM: [Processes all .py files in the directory]
     ✓ Added 23 Python files with 156 chunks
```

### Example 2: Learn from Open Source
```
You: Add the FastAPI repository so I can learn how it works

LLM: [Calls add_document("https://github.com/tiangolo/fastapi")]
     Cloning repository...
     ✓ Added 247 files from repository with 1,543 chunks
     
You: How does FastAPI handle dependency injection?

LLM: [Searches and explains based on actual FastAPI source code]
```

### Example 3: Research a Specific Feature
```
You: Add just the authentication module from Django

LLM: [Calls add_document("https://github.com/django/django/tree/main/django/contrib/auth")]
     ✓ Added 45 files from django/contrib/auth with 312 chunks

You: Show me how Django implements password hashing

LLM: [Provides detailed explanation with code references]
```

## Example Queries

Once you've added documents, here are powerful queries you can ask:

### 🔍 Understanding Code
```
"How does this codebase handle database connections?"
"Explain the authentication flow in this project"
"What design patterns are used in this repository?"
"How is error handling implemented?"
"Show me how the API endpoints are structured"
```

### 🐛 Debugging & Problem Solving
```
"Find examples of how to handle file uploads"
"Where is the rate limiting logic implemented?"
"Show me similar error handling patterns"
"How do other files handle this exception?"
"Find all places where we validate user input"
```

### 📚 Learning & Research
```
"How does FastAPI implement dependency injection?"
"Compare how Django and Flask handle routing"
"What's the difference between these two implementations?"
"Show me examples of async/await usage in this codebase"
"How does this library handle backwards compatibility?"
```

### ♻️ Refactoring & Code Review
```
"Find all files that use the old authentication method"
"Where else do we use this deprecated function?"
"Show me similar code that might have the same bug"
"Find duplicate logic that could be refactored"
"What files would be affected if I change this interface?"
```

### 🎯 Specific Implementation Questions
```
"How do I use the caching system in this project?"
"Show me examples of writing tests for API endpoints"
"How is configuration managed in this codebase?"
"Find examples of custom middleware implementation"
"How do I add a new database model?"
```

### 🌟 Open Source Exploration
```
"How does React implement hooks internally?"
"Show me how Django's ORM builds SQL queries"
"How does FastAPI achieve such high performance?"
"Explain how pytest's fixture system works"
"How does requests handle HTTP retries?"
```

### 💡 Tips for Better Queries

**✅ Good Queries:**
- Be specific: "How does FastAPI validate request bodies?"
- Ask about concepts: "Explain the middleware pattern in this code"
- Request examples: "Show me examples of async database queries"
- Compare: "How is this different from the old implementation?"

**❌ Avoid:**
- Too vague: "Tell me about the code"
- Too broad: "Explain everything"
- Outside scope: Questions about code not in the knowledge base

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

### The Magic Behind the Scenes

```
1. 📄 Document Ingestion
   ├─ Read file content with encoding detection
   ├─ Generate content hash for deduplication
   ├─ Extract metadata (size, timestamps, type)
   └─ Split into overlapping chunks (~1000 chars)

2. 🧮 Vector Embedding
   ├─ Load sentence-transformers model (all-MiniLM-L6-v2)
   ├─ Convert each chunk to 384-dimensional vector
   ├─ Batch processing for efficiency
   └─ Store vectors in LanceDB

3. 🔍 Semantic Search
   ├─ Convert search query to vector
   ├─ Find similar vectors using ANN (Approximate Nearest Neighbor)
   ├─ Rank results by cosine similarity
   └─ Return relevant chunks with metadata

4. 💾 Storage
   ├─ LanceDB: Fast columnar vector database
   ├─ Two tables: documents + chunks
   ├─ Efficient updates and deletes
   └─ All data stays local
```

### First Run

On first use, `uvx` automatically:
- Downloads and installs the package
- Installs all dependencies  
- Downloads the embedding model (~100MB, one-time)
- Starts the server

The server then:
- Creates `knowledge_base.db` in your current directory
- Stores logs in `./logs`
- Supports `.py` and `.txt` files by default

**Zero configuration needed!**

## Why Use This?

### Traditional Keyword Search
```
You: "Find authentication code"
Result: Files containing the word "authentication"
Problem: Misses related concepts like "login", "auth", "credentials"
```

### Semantic Search with This MCP
```
You: "Find authentication code"  
Result: All auth-related code including:
  ✓ Files about "login" and "sign in"
  ✓ Code handling "credentials" and "tokens"
  ✓ "Authorization" and "access control"
  ✓ Related security implementations

Why: Understands meaning, not just words
```

### Real-World Use Cases

- **🔍 Code Discovery** - "How do we handle database connections?"
- **📚 Onboarding** - New team members understand the codebase faster
- **🐛 Debugging** - "Find similar error handling patterns"
- **♻️ Refactoring** - "Where do we use this deprecated pattern?"
- **📖 Documentation** - "Explain how the auth system works"
- **🎯 Code Review** - "Find related code that might be affected"
- **🌟 Learn from OSS** - "Add the React repository and explain how hooks work"
- **📦 Library Research** - "Add this library and show me how to use feature X"

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

## Technical Details

### Stack

- **MCP Framework**: FastMCP - Modern Python MCP implementation
- **Vector Database**: LanceDB - Fast, embedded vector database
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2 (384 dimensions)
- **Search**: Approximate Nearest Neighbor (ANN) with cosine similarity
- **Storage**: Columnar format with Apache Arrow

### Performance

- **Embedding Speed**: ~1000 tokens/second on CPU
- **Search Latency**: <100ms for most queries
- **Storage**: ~1KB per chunk (text + vector + metadata)
- **Memory**: ~500MB (model) + database size

### Supported File Types

Currently:
- `.py` - Python source code
- `.txt` - Plain text files

Coming soon:
- `.md` - Markdown
- `.js`, `.ts` - JavaScript/TypeScript
- `.java`, `.cpp` - Other languages

## Documentation

- **[LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md)** - 🔧 Setup for local development (current - not yet published)
- **[INSTALL.md](INSTALL.md)** - Detailed setup guide for all LLM clients
- **[USAGE_WITH_LLM.md](docs/USAGE_WITH_LLM.md)** - Usage examples and tips

### Advanced

- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Manual installation, custom configuration, production deployment
- **[QUICKSTART.md](docs/QUICKSTART.md)** - Configuration options and advanced features

## Contributing

Contributions are welcome! This is an open-source project.

- Report bugs and request features via [GitHub Issues](https://github.com/yourusername/mcp-knowledge-base/issues)
- Submit pull requests for improvements
- Star the repo if you find it useful! ⭐

## License

MIT License