# Usage Guide

Complete guide for using Context Lens effectively with examples, queries, and best practices.

## Table of Contents

- [What You Can Add](#what-you-can-add)
- [Available Tools](#available-tools)
- [Example Conversations](#example-conversations)
- [Example Queries](#example-queries)
- [Quick Start Examples](#quick-start-examples)
- [Error Handling](#error-handling)
- [Tips for Better Queries](#tips-for-better-queries)

---

## What You Can Add

Context Lens works with any text-based content:

### Code & Development

- **📄 Single files**: `./README.md`, `/path/to/script.py`
- **📁 Local folders**: `./src/`, `/path/to/project/`
- **💻 Local repositories**: `./my-project/`, `/Users/you/code/app/`
- **🌐 GitHub URLs**: 
  - Repositories: `https://github.com/user/repo`
  - Specific files: `https://github.com/user/repo/blob/main/file.py`
  - Directories: `https://github.com/user/repo/tree/main/src`
  - Specific branches: `https://github.com/user/repo/tree/develop`
- **🔗 Direct file URLs**:
  - Any HTTP/HTTPS file: `https://example.com/config.yaml`
  - CDN files: `https://cdn.example.com/data.json`
  - Raw files: `https://example.com/api/schema.json`

### Documents & Content

- **📄 Legal Documents**: Contracts, agreements, terms of service
- **🏥 Insurance Policies**: Coverage documents, policy terms, claims procedures
- **📊 Research Papers**: Academic papers, technical reports, whitepapers
- **📚 Documentation**: Technical docs, user manuals, API documentation
- **📝 Business Documents**: Proposals, reports, meeting notes, wikis
- **📋 Text Files**: Any `.txt`, `.md`, or plain text content

### Supported File Types

Context Lens supports the following file extensions:

**Programming Languages:**
- **Python**: `.py`
- **JavaScript/TypeScript**: `.js`, `.jsx`, `.ts`, `.tsx`, `.mjs`, `.cjs`
- **Java**: `.java`
- **C/C++**: `.c`, `.cpp`, `.h`, `.hpp`
- **Go**: `.go`
- **Rust**: `.rs`
- **Ruby**: `.rb`
- **PHP**: `.php`

**Documentation:**
- **Markdown**: `.md`
- **Plain Text**: `.txt`

**Configuration Files:**
- **JSON**: `.json`
- **YAML**: `.yaml`, `.yml`
- **TOML**: `.toml`

**Shell Scripts:**
- **Bash/Shell**: `.sh`, `.bash`, `.zsh`

**Complete list**: `.py`, `.txt`, `.md`, `.js`, `.jsx`, `.ts`, `.tsx`, `.mjs`, `.cjs`, `.java`, `.cpp`, `.c`, `.h`, `.hpp`, `.go`, `.rs`, `.rb`, `.php`, `.json`, `.yaml`, `.yml`, `.toml`, `.sh`, `.bash`, `.zsh`

**Unsupported files** (e.g., `.exe`, `.pdf`, `.docx`, `.zip`) will be rejected with a clear error message listing all supported types.

### Automatically Ignored

- **Dependencies**: `node_modules`, `venv`, `vendor`
- **Build outputs**: `dist`, `build`, `target`, `out`
- **Caches**: `__pycache__`, `.cache`, `.pytest_cache`
- **Version control**: `.git`, `.svn`, `.hg`
- **IDE files**: `.idea`, `.vscode`, `.vs`
- **Large files**: Files over 10MB


## Available Tools

Once connected to your LLM, you get six powerful tools:

### 📥 add_document(file_path_or_url)
Add documents to the knowledge base
- Local files: `"/path/to/file.py"`
- Local folders: `"./src/"`
- GitHub repos: `"https://github.com/user/repo"`
- GitHub files: `"https://github.com/user/repo/blob/main/..."`
- Direct URLs: `"https://example.com/data.json"`
- Smart: Skips if already indexed with same content
- Extracts content, creates embeddings, stores in LanceDB

### 🔍 search_documents(query, limit=10)
Semantic search across all documents
- Finds relevant code/text by meaning, not just keywords
- Returns ranked results with relevance scores

### 📋 list_documents(limit=100, offset=0)
List all indexed documents with pagination
- Browse what's in your knowledge base
- See file paths, sizes, and when added

### ℹ️ get_document_info(file_path)
Get metadata about a specific document
- Check if indexed, when added, content hash, chunk count
- Verify document status

### 🗑️ remove_document(file_path)
Remove a specific document from the knowledge base
- Clean up outdated or unwanted files
- Free up space

### 🧹 clear_knowledge_base()
Remove all documents and start fresh
- Complete reset when needed
- Start over with new content

---

## Example Conversations

### Adding a GitHub Repository

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

### Adding Local Files

```
You: Add all Python files in my src/ directory to the knowledge base

LLM: I'll add those files for you.
     [Calls add_document for each .py file]
     ✓ Added 15 Python files to the knowledge base

You: How does this codebase handle authentication?

LLM: Let me search for authentication-related code.
     [Calls search_documents with query "authentication handling"]
     
     Based on the code, you use JWT tokens with OAuth2. Here's what I found:
     - src/auth/jwt.py: Token generation and validation
     - src/auth/oauth.py: OAuth2 flow implementation
     - src/middleware/auth.py: Authentication middleware
     
     The main authentication flow is...
```

### Analyzing Documents

```
You: Add all the contracts from the /contracts folder

LLM: [Processes all documents]
     ✓ Added 8 contract documents with 234 chunks

You: Find all liability clauses in these contracts

LLM: [Searches for liability-related content]
     I found liability clauses in 6 contracts:
     
     1. Service Agreement (Section 8): Limits liability to fees paid...
     2. Vendor Contract (Section 12): Mutual indemnification for...
     3. Partnership Agreement (Section 15): No liability for indirect damages...
     ...
```


---

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

### Example 4: Analyze Legal Documents
```
You: Add all PDF contracts from the /legal/contracts folder

LLM: [Processes all contract documents]
     ✓ Added 12 contract documents with 487 chunks

You: Find all termination clauses and summarize the notice periods

LLM: [Searches and summarizes termination terms across all contracts]
```

### Example 5: Add Files from URLs
```
You: Add https://example.com/api/openapi.yaml to the knowledge base

LLM: [Fetches and processes the file]
     ✓ Document 'openapi.yaml' added successfully with 45 chunks

You: What endpoints are defined in this API?

LLM: [Searches the OpenAPI spec and lists all endpoints]
```

### Example 6: Add Configuration Files
```
You: Add https://cdn.example.com/config/production.json

LLM: [Downloads and processes the config file]
     ✓ Document 'production.json' added successfully with 8 chunks

You: What database settings are configured?

LLM: [Extracts and explains database configuration]
```

---

## Error Handling

Context Lens provides clear error messages for common issues:

### Unsupported File Types

```
You: Add https://example.com/document.pdf

LLM: ✗ Error: Unsupported file type '.pdf'. 
     Supported types: .py, .txt, .md, .js, .jsx, .ts, .tsx, .mjs, .cjs, 
     .java, .cpp, .c, .h, .hpp, .go, .rs, .rb, .php, .json, .yaml, .yml, 
     .toml, .sh, .bash, .zsh
```

### File Not Found

```
You: Add /path/to/nonexistent/file.py

LLM: ✗ Error: File not found: /path/to/nonexistent/file.py
```

### URL Fetch Errors

```
You: Add https://example.com/missing.json

LLM: ✗ Error: HTTP error 404: Not Found
```

### File Too Large

```
You: Add /path/to/huge-file.txt

LLM: ✗ Error: File too large (15.2 MB). Maximum size: 10 MB
```

### Invalid GitHub URL

```
You: Add https://github.com/invalid

LLM: ✗ Error: Invalid GitHub URL format
```

