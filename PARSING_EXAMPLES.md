# Smart Parsing Examples

Context Lens uses language-specific parsers to understand code structure and create meaningful chunks.

## Available Parsers

| Parser | Extensions | Method | Best For |
|--------|-----------|--------|----------|
| **Python** | `.py`, `.pyw` | AST-based | Python code - most accurate |
| **JavaScript/TS** | `.js`, `.jsx`, `.ts`, `.tsx`, `.mjs`, `.cjs` | Regex | Web development |
| **JSON** | `.json`, `.jsonc` | Native parsing | Config files |
| **YAML** | `.yaml`, `.yml` | Native parsing | CI/CD configs |
| **Markdown** | `.md`, `.markdown`, `.mdx` | Header-based | Documentation |
| **Rust** | `.rs` | Regex | Systems programming |
| **Generic** | All others | Text-based | Everything else |

## Why Smart Parsing Matters

**Without smart parsing** (generic chunking):
- Code gets split mid-function
- Classes are incomplete
- Context is lost
- Search results are confusing

**With smart parsing**:
- Complete functions and classes
- Preserved docstrings and comments
- Better search results
- Meaningful code units

## Example: Python Parser

**Input Code:**
```python
"""User management module."""

import hashlib
from typing import Optional

class User:
    """Represents a user in the system."""
    
    def __init__(self, username: str, email: str):
        self.username = username
        self.email = email
    
    def hash_password(self, password: str) -> str:
        """Hash a password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

def create_user(username: str, email: str) -> User:
    """Create a new user instance."""
    return User(username, email)
```

**Parsed Chunks:**

**Chunk 1: Imports**
```python
import hashlib
from typing import Optional
```

**Chunk 2: User Class** (complete with all methods)
```python
class User:
    """Represents a user in the system."""
    
    def __init__(self, username: str, email: str):
        self.username = username
        self.email = email
    
    def hash_password(self, password: str) -> str:
        """Hash a password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
```

**Chunk 3: create_user Function**
```python
def create_user(username: str, email: str) -> User:
    """Create a new user instance."""
    return User(username, email)
```

## What Each Parser Extracts

**Python (AST-based)**
- Functions, classes, methods
- Decorators and docstrings
- Import statements
- Type hints

**JavaScript/TypeScript**
- Regular and arrow functions
- Classes (ES6)
- ES6 imports and CommonJS requires
- JSDoc comments

**JSON**
- Chunks by top-level keys
- Preserves valid JSON structure
- Handles large arrays intelligently

**YAML**
- Splits by top-level keys
- Preserves indentation
- Handles lists and mappings

**Markdown**
- Splits by header hierarchy
- Keeps code blocks with sections
- Preserves document structure

**Rust**
- Structs, enums, traits, impl blocks
- Functions (regular, async, unsafe)
- Doc comments and attributes
- Generics and lifetimes

**Generic (Fallback)**
- Paragraph and sentence-based splitting
- Configurable overlap for context
- Works for any text file

## Automatic Detection

All parsers work automatically based on file extension - no configuration needed!
