# Technical Details

Technical documentation about Context Lens's architecture, implementation, and performance.

## Table of Contents

- [How It Works](#how-it-works)
- [Stack](#stack)
- [Performance](#performance)
- [Supported File Types](#supported-file-types)
- [Smart Parsing](#smart-parsing)
- [Storage](#storage)
- [Security & Privacy](#security--privacy)

---

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

### Document Processing Pipeline

1. **Input** - File path or GitHub URL
2. **Validation** - Check file size, type, encoding
3. **Content Extraction** - Read and decode file content
4. **Deduplication** - Hash content to skip duplicates
5. **Parsing** - Use language-specific parser or generic chunker
6. **Chunking** - Split into logical, overlapping chunks
7. **Embedding** - Convert chunks to vectors
8. **Storage** - Save to LanceDB with metadata
9. **Indexing** - Build vector index for fast search

### Search Pipeline

1. **Query** - User's natural language question
2. **Embedding** - Convert query to vector
3. **Vector Search** - Find similar chunks using ANN
4. **Ranking** - Sort by cosine similarity score
5. **Filtering** - Apply any filters (file type, date, etc.)
6. **Results** - Return top N chunks with metadata

---

## Stack

### Core Technologies

- **MCP Framework**: [FastMCP](https://github.com/jlowin/fastmcp) - Modern Python MCP implementation
- **Vector Database**: [LanceDB](https://lancedb.com/) - Fast, embedded vector database
- **Embeddings**: [sentence-transformers](https://www.sbert.net/) - all-MiniLM-L6-v2 model (384 dimensions)
- **Search**: Approximate Nearest Neighbor (ANN) with cosine similarity
- **Storage**: Columnar format with [Apache Arrow](https://arrow.apache.org/)

### Python Dependencies

- **lancedb** - Vector database
- **sentence-transformers** - Embedding models
- **torch** - PyTorch for model inference
- **fastmcp** - MCP server framework
- **pydantic** - Data validation
- **gitpython** - GitHub repository cloning
- **pyyaml** - Configuration files

### Embedding Model

**Model**: `sentence-transformers/all-MiniLM-L6-v2`

**Specifications:**
- **Dimensions**: 384
- **Max Sequence Length**: 256 tokens
- **Model Size**: ~90MB
- **Speed**: ~1000 tokens/second on CPU
- **Quality**: Good balance of speed and accuracy

**Why this model:**
- Fast inference on CPU (no GPU needed)
- Small size for quick downloads
- Good semantic understanding
- Widely used and tested
- Works well for code and text

---

## Performance

### Benchmarks

**Embedding Speed:**
- ~1000 tokens/second on CPU
- ~5000 tokens/second on GPU (if available)
- Batch processing for efficiency

**Search Latency:**
- <100ms for most queries
- <50ms for small databases (<10k chunks)
- <200ms for large databases (>100k chunks)

**Storage Efficiency:**
- ~1KB per chunk (text + vector + metadata)
- Columnar storage reduces disk usage
- Efficient compression

**Memory Usage:**
- ~500MB for embedding model
- ~100MB for LanceDB operations
- Scales with database size

### Scalability

**Tested with:**
- ✅ Single files up to 10MB
- ✅ Repositories with 1000+ files
- ✅ Databases with 100k+ chunks
- ✅ Concurrent searches

**Limits:**
- Max file size: 10MB (configurable)
- Max chunk size: 10,000 characters
- Max search results: 100 per query

---

## Supported File Types

### Complete List (23 formats)

**Programming Languages:**
- `.py` - Python
- `.js`, `.jsx` - JavaScript
- `.ts`, `.tsx` - TypeScript  
- `.mjs`, `.cjs` - JavaScript modules
- `.java` - Java
- `.cpp`, `.c`, `.h`, `.hpp` - C/C++
- `.go` - Go
- `.rs` - Rust
- `.rb` - Ruby
- `.php` - PHP

**Documentation & Config:**
- `.txt` - Plain text
- `.md`, `.markdown`, `.mdx` - Markdown
- `.json`, `.jsonc` - JSON
- `.yaml`, `.yml` - YAML
- `.toml` - TOML

**Scripts:**
- `.sh` - Shell script
- `.bash` - Bash script
- `.zsh` - Zsh script

### File Processing

**Encoding Detection:**
- Automatic encoding detection (UTF-8, Latin-1, etc.)
- Fallback to binary read if needed
- Handles BOM markers

**Size Limits:**
- Default: 10MB per file
- Configurable via `MAX_FILE_SIZE_MB`
- Large files automatically skipped

**Ignored Patterns:**
- `node_modules/`, `venv/`, `vendor/`
- `dist/`, `build/`, `target/`, `out/`
- `__pycache__/`, `.cache/`, `.pytest_cache/`
- `.git/`, `.svn/`, `.hg/`
- `.idea/`, `.vscode/`, `.vs/`

---

## Smart Parsing

Context Lens uses language-specific parsers to create intelligent chunks that respect code structure.

### Parser Types

**AST-Based (Python):**
- Most accurate
- Understands syntax deeply
- Handles complex nesting
- Uses Python's `ast` module

**Regex-Based (JavaScript, Rust, etc.):**
- Fast and efficient
- Pattern matching for structures
- Good for most use cases
- Handles common patterns

**Structure-Based (JSON, YAML):**
- Uses native parsers
- Respects data structure
- Chunks by keys/sections
- Preserves validity

**Header-Based (Markdown):**
- Splits by headers
- Preserves hierarchy
- Keeps code blocks with sections
- Maintains document structure

### Supported Parsers

- **🐍 Python** - Functions, classes, imports (AST-based)
- **⚡ JavaScript/TypeScript** - Functions, classes, imports (Regex)
- **📦 JSON** - Top-level keys, nested objects (Native)
- **📋 YAML** - Top-level keys, lists, mappings (Native)
- **📝 Markdown** - Header hierarchy, code blocks (Regex)
- **🦀 Rust** - Structs, traits, impl blocks, functions (Regex)
- **📄 Generic** - Paragraph/sentence splitting (Text-based)

For detailed examples, see [PARSING_EXAMPLES.md](PARSING_EXAMPLES.md).

---

## Storage

### LanceDB

**Why LanceDB:**
- Embedded database (no server needed)
- Fast vector similarity search
- Columnar storage (Apache Arrow)
- Efficient updates and deletes
- ACID transactions
- Works like SQLite for vectors

**Database Structure:**

```
knowledge_base.db/
├── documents/          # Document metadata table
│   ├── file_path      # Unique identifier
│   ├── content_hash   # For deduplication
│   ├── size           # File size in bytes
│   ├── added_at       # Timestamp
│   └── metadata       # Additional info
│
└── chunks/            # Chunk data table
    ├── id             # Unique chunk ID
    ├── document_id    # Reference to document
    ├── content        # Text content
    ├── chunk_index    # Order in document
    ├── embedding      # 384-dim vector
    └── metadata       # Line numbers, etc.
```

**Operations:**
- **Add**: Insert document and chunks
- **Search**: Vector similarity search
- **List**: Query documents table
- **Remove**: Delete document and chunks
- **Clear**: Truncate all tables

---

## Security & Privacy

### Local-First Architecture

**Everything stays local:**
- ✅ All data stored on your machine
- ✅ All processing happens locally
- ✅ No external API calls
- ✅ No telemetry or tracking
- ✅ No internet required (after setup)

**What gets downloaded:**
- Embedding model (~100MB, one-time)
- Python packages (via pip/uvx)
- GitHub repositories (if you add them)

**What never leaves your machine:**
- Your code and documents
- Embeddings and vectors
- Search queries
- Database contents

### Data Protection

**File System:**
- Database stored in current directory
- Standard file permissions apply
- Easy to backup and encrypt
- Can be moved/deleted anytime

**No Cloud Dependencies:**
- No AWS, GCP, or Azure required
- No API keys needed
- No subscriptions
- No vendor lock-in

### Recommended Practices

**For sensitive data:**
- Store database in encrypted directory
- Use full disk encryption
- Regular backups
- Restrict file permissions

**For team sharing (future):**
- Use encrypted S3 buckets
- VPN for remote access
- Access control lists
- Audit logging

---

## Development

### Running from Source

```bash
# Clone repository
git clone https://github.com/cornelcroi/context-lens.git
cd context-lens

# Install in development mode
pip install -e .

# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=context_lens --cov-report=html

# Start server
python -m context_lens.server
```

### Project Structure

```
context-lens/
├── src/context_lens/
│   ├── server.py              # MCP server
│   ├── models/                # Data models
│   ├── services/              # Business logic
│   ├── processors/            # Content processing
│   ├── parsers/               # Language parsers
│   └── utils/                 # Utilities
├── tests/                     # Test suite
├── docs/                      # Documentation
└── pyproject.toml            # Project config
```

### Testing

**Test Coverage:**
- 398 tests (all passing)
- Unit tests for all parsers
- Integration tests
- End-to-end tests

**Run tests:**
```bash
pytest tests/                  # All tests
pytest tests/test_parsers/     # Parser tests only
pytest -v                      # Verbose output
pytest --cov                   # With coverage
```

---

## Additional Resources

- 📖 [Setup Guide](SETUP.md) - Configuration details
- 📚 [Usage Guide](USAGE_GUIDE.md) - How to use effectively
- 🎨 [Parsing Examples](PARSING_EXAMPLES.md) - Parser examples
- 🔧 [Troubleshooting](TROUBLESHOOTING.md) - Common issues
- 🤝 [Contributing](CONTRIBUTING.md) - How to contribute
