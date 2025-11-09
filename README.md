# CodeLens

### *Give your LLM glasses to understand meaning, not just read words*

[![Tests](https://github.com/cornelcroi/codelens/workflows/Tests/badge.svg)](https://github.com/cornelcroi/codelens/actions)
[![PyPI version](https://badge.fury.io/py/context-lens.svg)](https://badge.fury.io/py/context-lens)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**CodeLens is semantic search for AI assistants. Drop in any knowledge source - documentation, repositories, notes, or local files - and your AI can instantly understand and answer questions about it. No configuration, no build step - it just works.**

CodeLens is a Model Context Protocol (MCP) server that gives AI assistants the ability to semantically search and understand any content using vector embeddings and LanceDB.

Works with Claude Desktop, Kiro IDE, Continue.dev, and other MCP clients.

## Setup with Your LLM

No installation needed! Just configure your AI assistant to use CodeLens:

### Claude Desktop (Recommended)

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%/Claude/claude_desktop_config.json` (Windows):

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

Restart Claude Desktop and you're ready!

### Kiro IDE

Add to `.kiro/settings/mcp.json` in your workspace:

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

Reload MCP servers (Command Palette → "MCP: Reload Servers") and start using it!

### Continue.dev

Edit `~/.continue/config.json`:

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

### Alternative Installation Methods

**Claude Desktop using npx:**
```bash
claude mcp add context-lens -- npx context-lens@latest
```

**OpenAI Codex:**
```bash
codex mcp add context-lens -- npx @context-lens@latest
```

**Or using node with the built file:**
```json
{
  "mcpServers": {
    "context-lens": {
      "command": "node",
      "args": ["/absolute/path/to/context-lens/dist/index.js"]
    }
  }
}
```

### Other MCP Clients

For any MCP-compatible client, use:

```json
{
  "command": "uvx",
  "args": ["context-lens"]
}
```

### Custom Database Location (Optional)

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

## What You Can Add

CodeLens works with any text-based content:

- **📄 Single files**: `./README.md`, `/path/to/document.txt`
- **📁 Local folders**: `./docs/`, `/path/to/project/`
- **💻 Local repositories**: `./my-project/`, `/Users/you/code/app/`
- **🌐 GitHub URLs**: 
  - Repositories: `https://github.com/user/repo`
  - Specific files: `https://github.com/user/repo/blob/main/file.py`
  - Directories: `https://github.com/user/repo/tree/main/src`
- **📚 Documentation sites**: Any markdown, text, or code files
- **📝 Notes and wikis**: Personal knowledge bases, team wikis

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Your LLM Client                              │
│              (Claude Desktop, Kiro IDE, Continue.dev)                │
└────────────────────────────────┬────────────────────────────────────┘
                                 │ MCP Protocol
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          CodeLens Server                             │
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


## Manual Installation (Optional)

Most users don't need to install anything - just configure your LLM client as shown above and `uvx` will handle everything automatically.

If you prefer to install locally:

```bash
pip install context-lens
```

Or install from source:

```bash
git clone https://github.com/cornelcroi/codelens.git
cd codelens
pip install -e .
```

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
│  📄 Supported File Types (20+ formats)                               │
│  ├─ Python:           .py                                            │
│  ├─ JavaScript/TS:    .js, .jsx, .ts, .tsx                          │
│  ├─ Web:              .md, .txt, .json, .yaml, .yml                 │
│  ├─ Systems:          .java, .cpp, .c, .h, .go, .rs                 │
│  └─ Scripts:          .sh, .bash, .rb, .php                         │
│                                                                       │
│  🚫 Automatically Ignored                                            │
│  ├─ Dependencies:     node_modules, venv, vendor                    │
│  ├─ Build outputs:    dist, build, target, out                      │
│  ├─ Caches:           __pycache__, .cache, .pytest_cache            │
│  ├─ Version control:  .git, .svn, .hg                               │
│  ├─ IDE files:        .idea, .vscode, .vs                           │
│  └─ Large files:      Files over 10MB                               │
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

Once connected to your LLM, you get six powerful tools:

```
┌─────────────────────────────────────────────────────────────────┐
│ 📥 add_document(file_path_or_url)                               │
│    Add documents to the knowledge base                          │
│    → Local files: "/path/to/file.py"                            │
│    → GitHub repos: "https://github.com/user/repo"               │
│    → GitHub files: "https://github.com/user/repo/blob/main/..." │
│    → Smart: Skips if already indexed with same content          │
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
│ ℹ️  get_document_info(file_path)                                │
│    Get metadata about a specific document                       │
│    → Check if indexed, when added, content hash, chunk count    │
│                                                                  │
│ 🗑️  remove_document(file_path)                                  │
│    Remove a specific document from the knowledge base           │
│    → Clean up outdated or unwanted files                        │
│                                                                  │
│ 🧹 clear_knowledge_base()                                       │
│    Remove all documents and start fresh                         │
│    → Complete reset when needed                                 │
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

## Advanced Configuration

### For Local Development (Not Yet Published)

If you're developing CodeLens locally:

**Claude Desktop:**
```json
{
  "mcpServers": {
    "context-lens": {
      "command": "context-lens"
    }
  }
}
```

**Kiro IDE:**
```json
{
  "mcpServers": {
    "context-lens": {
      "command": "python",
      "args": ["-m", "context_lens.main"],
      "disabled": false,
      "autoApprove": ["list_documents", "search_documents"]
    }
  }
}
```

### MCP Inspector (Testing & Development)

MCP Inspector is a web-based tool for testing MCP servers during development.

**Quick Start:**
```bash
# Test with MCP Inspector
DANGEROUSLY_OMIT_AUTH=true npx @modelcontextprotocol/inspector python -m context_lens.server
```

**What happens:**
1. Server starts in < 1 second (lazy initialization)
2. Inspector opens in your browser showing all 6 tools
3. First tool invocation loads embedding models (5-10 seconds, one-time)
4. Subsequent calls are fast (< 1 second)

**Testing workflow:**
- Use Inspector's UI to call tools with different parameters
- View request/response JSON in real-time
- Check logs in `./logs/context-lens.log` for detailed info
- Test error handling with invalid inputs

**Note:** The server uses lazy initialization, so startup is fast but the first tool call will take longer as it loads the embedding model. This is expected behavior and only happens once per session.

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

### Common Issues

**Server not starting?**
```bash
# Check installation
context-lens --version

# View detailed logs
tail -f logs/context-lens.log

# Check for errors
tail -f logs/errors.log
```

**First run is slow?**
The embedding model (~100MB) downloads on first use. This only happens once. Subsequent runs are fast.

**First tool call is slow?**
The server uses lazy initialization - it starts quickly but loads the embedding model on the first tool invocation. This takes 5-10 seconds and only happens once per session. This is intentional to provide fast startup times for MCP Inspector and other tools.

**MCP Inspector not connecting?**
```bash
# Make sure you're using the correct command
npx @modelcontextprotocol/inspector python -m context_lens.server

# NOT this (incorrect):
# npx @modelcontextprotocol/inspector fastmcp run context_lens.server:app

# Check that Python can find the module
python -m context_lens.server --help
```

**Tools not appearing in LLM client?**
1. Verify the server is configured correctly in your client's MCP settings
2. Restart your LLM client after configuration changes
3. Check the client's logs for connection errors
4. For Kiro IDE: Use Command Palette → "MCP: Reload Servers"

**Database errors?**
```bash
# Check database location
ls -la knowledge_base.db

# If corrupted, you can reset it
rm -rf knowledge_base.db
# The server will create a new database on next run
```

**Import errors or missing dependencies?**
```bash
# Reinstall dependencies
pip install -r requirements.txt

# For development installation
pip install -e .
```

**Logs show "stdio transport" errors?**
This usually means something is writing to stdout when it shouldn't. The server is configured to log only to files to keep stdio clean for MCP protocol communication. If you see this:
1. Check for any `print()` statements in your code
2. Verify logging is configured correctly (should only write to files)
3. Check third-party libraries aren't writing to stdout

**Performance issues?**
- First document addition: Slow (model loading)
- Subsequent operations: Should be fast (< 1 second)
- Large files (>10MB): Automatically skipped
- Many files: Processed in batches

**Configuration issues?**
```bash
# Check environment variables
env | grep MCP_KB

# Use config file for complex setups
cp config.example.yaml config.yaml
# Edit config.yaml with your settings
context-lens --config config.yaml
```

**Still having issues?**
1. Check the [documentation](#documentation) below
2. Review logs in `./logs/` directory
3. Try with MCP Inspector to isolate the issue
4. Report bugs via [GitHub Issues](https://github.com/cornelcroi/codelens/issues)

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

Supported file types:
- `.py` - Python source code
- `.txt` - Plain text files
- `.md` - Markdown
- `.js`, `.ts` - JavaScript/TypeScript
- `.java`, `.cpp`, `.c`, `.h` - C/C++/Java
- `.go`, `.rs` - Go/Rust
- And more text-based formats

## Contributing

To contribute or run from source:

```bash
git clone https://github.com/yourusername/codelens.git
cd codelens
pip install -e .
pytest tests/
```

### Environment Variables

Configure via environment variables in your MCP client:

```json
{
  "env": {
    "LANCE_DB_PATH": "./codelens.db",
    "LOG_LEVEL": "INFO"
  }
}
```

## Contributing

Contributions are welcome! This is an open-source project.

- Report bugs and request features via [GitHub Issues](https://github.com/yourusername/codelens/issues)
- Submit pull requests for improvements
- Star the repo if you find it useful! ⭐

## License

MIT License
