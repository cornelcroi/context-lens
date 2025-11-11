# Smart Parsing Examples

This document provides detailed examples of how Context Lens's language-specific parsers work.

## Table of Contents

- [Parser Overview](#parser-overview)
- [Chunking Strategy by File Type](#chunking-strategy-by-file-type)
- [The Problem: Generic Chunking](#the-problem-generic-chunking)
- [The Solution: Smart Parsing](#the-solution-smart-parsing)
- [Python Parser](#python-parser)
- [JavaScript/TypeScript Parser](#javascripttypescript-parser)
- [JSON Parser](#json-parser)
- [YAML Parser](#yaml-parser)
- [Markdown Parser](#markdown-parser)
- [Rust Parser](#rust-parser)
- [Generic Parser](#generic-parser)

---

## Parser Overview

Context Lens includes **7 specialized parsers** that understand different programming languages and file formats:

### 🐍 Python Parser (AST-based)
Extracts functions, classes, methods, and imports while preserving docstrings and decorators. Uses Python's Abstract Syntax Tree for the most accurate parsing.

### ⚡ JavaScript/TypeScript Parser (Regex-based)
Handles `.js`, `.jsx`, `.ts`, `.tsx`, `.mjs`, `.cjs` files. Extracts functions (regular and arrow), classes, ES6 imports, CommonJS requires, and JSDoc comments.

### 📦 JSON Parser (Structure-aware)
Chunks JSON by top-level keys, intelligently handles large arrays, and preserves valid JSON structure in each chunk.

### 📋 YAML Parser (Structure-aware)
Splits YAML by top-level keys, handles lists and mappings. Perfect for CI/CD configs like GitHub Actions, Kubernetes manifests, and Docker Compose files.

### 📝 Markdown Parser (Header-based)
Splits by header hierarchy (`#`, `##`, `###`), keeps code blocks with their sections, and preserves document structure.

### 🦀 Rust Parser (Regex-based)
Extracts structs, enums, traits, impl blocks, and functions. Handles generics, lifetimes, doc comments (`///`, `//!`), and attributes.

### 📄 Generic Parser (Fallback)
For all other file types, uses intelligent paragraph and sentence-based splitting with configurable overlap to maintain context.

---

## Chunking Strategy by File Type

| File Type | Chunking Strategy | What's Preserved |
|-----------|------------------|------------------|
| **Python** | By functions, classes, imports | Docstrings, decorators, complete definitions |
| **JavaScript/TS** | By functions, classes, imports | JSDoc, arrow functions, complete code blocks |
| **JSON** | By top-level keys | Valid JSON structure, nested objects |
| **YAML** | By top-level keys | Indentation, lists, mappings |
| **Markdown** | By header hierarchy | Code blocks, section structure, links |
| **Rust** | By structs, traits, impls, functions | Doc comments, generics, lifetimes |
| **Other Files** | By paragraphs/sentences | Natural text boundaries, overlap for context |

---

## The Problem: Generic Chunking

Without language-specific parsing, code gets split arbitrarily by character count:

**Input Code:**
```python
def calculate_total(items):
    """Calculate the total price of items."""
    total = 0
    for item in items:
        total += item.price
    return total

class ShoppingCart:
    def __init__(self):
        self.items = []
```

**Generic Chunking Result (split at 100 chars):**

**Chunk 1:**
```python
def calculate_total(items):
    """Calculate the total price of items."""
    total = 0
    for item in items:
```

**Chunk 2:**
```python
        total += item.price
    return total

class ShoppingCart:
    def __init__(self):
```

❌ **Problems:**
- Function split in the middle
- Class incomplete
- Context lost
- Search results confusing

---

## The Solution: Smart Parsing

Language-specific parsers understand code structure:

**Smart Parsing Result:**

**Chunk 1: calculate_total function**
```python
def calculate_total(items):
    """Calculate the total price of items."""
    total = 0
    for item in items:
        total += item.price
    return total
```
*Metadata: type=function, name=calculate_total, has_docstring=true*

**Chunk 2: ShoppingCart class**
```python
class ShoppingCart:
    def __init__(self):
        self.items = []
```
*Metadata: type=class, name=ShoppingCart*

✅ **Benefits:**
- Complete, logical units
- Context preserved
- Better search results

---

## Python Parser

**Method:** AST-based (most accurate)  
**Extensions:** `.py`, `.pyw`

### Example: Complete Python Module

**Input File:**
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
*Metadata: type=import, start_line=3, end_line=4*

**Chunk 2: User Class**
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
*Metadata: type=class, name=User, has_docstring=true, has_methods=true*

**Chunk 3: create_user Function**
```python
def create_user(username: str, email: str) -> User:
    """Create a new user instance."""
    return User(username, email)
```
*Metadata: type=function, name=create_user, has_docstring=true*

### What Python Parser Extracts

- ✅ Functions (regular and async)
- ✅ Classes with all methods
- ✅ Decorators (`@property`, `@staticmethod`, etc.)
- ✅ Docstrings (preserved with code)
- ✅ Import statements
- ✅ Type hints

---

## JavaScript/TypeScript Parser

**Method:** Regex-based  
**Extensions:** `.js`, `.jsx`, `.ts`, `.tsx`, `.mjs`, `.cjs`

### Example: React Component

**Input File:**
```javascript
import React, { useState, useEffect } from 'react';
import './Button.css';

/**
 * A reusable button component.
 * @param {Object} props - Component props
 */
export const Button = ({ onClick, children }) => {
    const [isPressed, setIsPressed] = useState(false);
    
    useEffect(() => {
        console.log('Button mounted');
    }, []);
    
    return (
        <button 
            onClick={onClick}
            className={isPressed ? 'pressed' : ''}
        >
            {children}
        </button>
    );
};

export default Button;
```

**Parsed Chunks:**

**Chunk 1: Imports**
```javascript
import React, { useState, useEffect } from 'react';
import './Button.css';
```
*Metadata: type=import*

**Chunk 2: Button Component**
```javascript
/**
 * A reusable button component.
 * @param {Object} props - Component props
 */
export const Button = ({ onClick, children }) => {
    const [isPressed, setIsPressed] = useState(false);
    
    useEffect(() => {
        console.log('Button mounted');
    }, []);
    
    return (
        <button 
            onClick={onClick}
            className={isPressed ? 'pressed' : ''}
        >
            {children}
        </button>
    );
};
```
*Metadata: type=function, name=Button, function_type=arrow_function, has_jsdoc=true*

### What JavaScript Parser Extracts

- ✅ Regular functions
- ✅ Arrow functions
- ✅ Classes (ES6)
- ✅ ES6 imports
- ✅ CommonJS requires
- ✅ JSDoc comments
- ✅ Exported functions/classes

---

## JSON Parser

**Method:** Structure-aware (native JSON parsing)  
**Extensions:** `.json`, `.jsonc`

### Example: package.json

**Input File:**
```json
{
    "name": "my-app",
    "version": "1.0.0",
    "description": "My awesome application",
    "dependencies": {
        "react": "^18.0.0",
        "express": "^4.18.0",
        "lodash": "^4.17.21"
    },
    "scripts": {
        "start": "node index.js",
        "test": "jest",
        "build": "webpack"
    },
    "devDependencies": {
        "jest": "^29.0.0",
        "webpack": "^5.0.0"
    }
}
```

**Parsed Chunks:**

**Chunk 1: Basic Info**
```json
{
    "name": "my-app",
    "version": "1.0.0",
    "description": "My awesome application"
}
```
*Metadata: type=json, keys=[name, version, description]*

**Chunk 2: Dependencies**
```json
{
    "dependencies": {
        "react": "^18.0.0",
        "express": "^4.18.0",
        "lodash": "^4.17.21"
    }
}
```
*Metadata: type=json, keys=[dependencies], is_object=true*

**Chunk 3: Scripts**
```json
{
    "scripts": {
        "start": "node index.js",
        "test": "jest",
        "build": "webpack"
    }
}
```
*Metadata: type=json, keys=[scripts]*

**Chunk 4: Dev Dependencies**
```json
{
    "devDependencies": {
        "jest": "^29.0.0",
        "webpack": "^5.0.0"
    }
}
```
*Metadata: type=json, keys=[devDependencies]*

### What JSON Parser Does

- ✅ Chunks by top-level keys
- ✅ Preserves valid JSON structure
- ✅ Handles large arrays intelligently
- ✅ Keeps nested objects together

---

## YAML Parser

**Method:** Structure-aware (native YAML parsing)  
**Extensions:** `.yaml`, `.yml`

### Example: GitHub Actions Workflow

**Input File:**
```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install dependencies
        run: npm install
      - name: Run tests
        run: npm test
  build:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v2
      - name: Build
        run: npm run build
```

**Parsed Chunks:**

**Chunk 1: Workflow Name**
```yaml
name: CI
```
*Metadata: type=yaml, keys=[name]*

**Chunk 2: Triggers**
```yaml
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
```
*Metadata: type=yaml, keys=[on], is_mapping=true*

**Chunk 3: Jobs**
```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install dependencies
        run: npm install
      - name: Run tests
        run: npm test
  build:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v2
      - name: Build
        run: npm run build
```
*Metadata: type=yaml, keys=[jobs], is_mapping=true*

### What YAML Parser Does

- ✅ Chunks by top-level keys
- ✅ Preserves indentation structure
- ✅ Handles lists and mappings
- ✅ Perfect for CI/CD configs

---

## Markdown Parser

**Method:** Header-based  
**Extensions:** `.md`, `.markdown`, `.mdx`

### Example: README File

**Input File:**
```markdown
# My Project

A description of my awesome project.

## Installation

To install, run:

```bash
npm install my-project
```

## Usage

Import and use the library:

```javascript
import { myFunc } from 'my-project';
myFunc();
```

### Advanced Usage

For advanced features, see the docs.

## API Reference

### myFunc()

Does something useful.

## License

MIT
```

**Parsed Chunks:**

**Chunk 1: Main Title**
```markdown
# My Project

A description of my awesome project.
```
*Metadata: type=markdown, header_level=1, section=My Project*

**Chunk 2: Installation**
```markdown
## Installation

To install, run:

```bash
npm install my-project
```
```
*Metadata: type=markdown, header_level=2, section=Installation, has_code_blocks=true*

**Chunk 3: Usage**
```markdown
## Usage

Import and use the library:

```javascript
import { myFunc } from 'my-project';
myFunc();
```

### Advanced Usage

For advanced features, see the docs.
```
*Metadata: type=markdown, header_level=2, section=Usage, has_code_blocks=true*

**Chunk 4: API Reference**
```markdown
## API Reference

### myFunc()

Does something useful.
```
*Metadata: type=markdown, header_level=2, section=API Reference*

**Chunk 5: License**
```markdown
## License

MIT
```
*Metadata: type=markdown, header_level=2, section=License*

### What Markdown Parser Does

- ✅ Splits by header hierarchy
- ✅ Keeps code blocks with their sections
- ✅ Preserves document structure
- ✅ Maintains header relationships

---

## Rust Parser

**Method:** Regex-based  
**Extensions:** `.rs`

### Example: Rust Module

**Input File:**
```rust
use std::collections::HashMap;

/// User data structure
#[derive(Debug, Serialize)]
pub struct User {
    pub id: u64,
    pub name: String,
}

impl User {
    /// Create a new user
    pub fn new(id: u64, name: String) -> Self {
        User { id, name }
    }
    
    /// Validate user data
    pub fn validate(&self) -> bool {
        !self.name.is_empty()
    }
}

/// User repository trait
pub trait UserRepository {
    fn save(&self, user: User) -> Result<(), Error>;
    fn find(&self, id: u64) -> Option<User>;
}

/// Create a user with validation
pub async fn create_user(id: u64, name: String) -> Result<User, String> {
    let user = User::new(id, name);
    if user.validate() {
        Ok(user)
    } else {
        Err("Invalid user data".to_string())
    }
}
```

**Parsed Chunks:**

**Chunk 1: Uses**
```rust
use std::collections::HashMap;
```
*Metadata: type=import*

**Chunk 2: User Struct**
```rust
/// User data structure
#[derive(Debug, Serialize)]
pub struct User {
    pub id: u64,
    pub name: String,
}
```
*Metadata: type=struct, name=User, has_doc_comment=true, rust_type=struct*

**Chunk 3: User Impl**
```rust
impl User {
    /// Create a new user
    pub fn new(id: u64, name: String) -> Self {
        User { id, name }
    }
    
    /// Validate user data
    pub fn validate(&self) -> bool {
        !self.name.is_empty()
    }
}
```
*Metadata: type=impl, name=User, rust_type=impl*

**Chunk 4: UserRepository Trait**
```rust
/// User repository trait
pub trait UserRepository {
    fn save(&self, user: User) -> Result<(), Error>;
    fn find(&self, id: u64) -> Option<User>;
}
```
*Metadata: type=trait, name=UserRepository, has_doc_comment=true, rust_type=trait*

**Chunk 5: create_user Function**
```rust
/// Create a user with validation
pub async fn create_user(id: u64, name: String) -> Result<User, String> {
    let user = User::new(id, name);
    if user.validate() {
        Ok(user)
    } else {
        Err("Invalid user data".to_string())
    }
}
```
*Metadata: type=function, name=create_user, is_async=true, has_doc_comment=true*

### What Rust Parser Extracts

- ✅ Structs and enums
- ✅ Traits and impl blocks
- ✅ Functions (regular, async, unsafe)
- ✅ Use statements
- ✅ Doc comments (`///`, `//!`)
- ✅ Generics and lifetimes
- ✅ Attributes (`#[derive(...)]`)

---

## Generic Parser

**Method:** Paragraph and sentence-based  
**Extensions:** All other file types (`.txt`, `.log`, `.cpp`, `.java`, etc.)

### Example: Text File

**Input File:**
```
Project Overview

This project implements a web application for managing tasks.
It uses a modern tech stack including React for the frontend
and Node.js for the backend.

Key Features

The application supports user authentication, task creation,
and real-time updates. Users can organize tasks into projects
and collaborate with team members.

Technical Details

The backend uses Express.js with MongoDB for data storage.
Authentication is handled via JWT tokens. The frontend
communicates with the backend through a REST API.
```

**Parsed Chunks (with chunk_size=200, overlap=50):**

**Chunk 1:**
```
Project Overview

This project implements a web application for managing tasks.
It uses a modern tech stack including React for the frontend
and Node.js for the backend.
```

**Chunk 2:**
```
and Node.js for the backend.

Key Features

The application supports user authentication, task creation,
and real-time updates. Users can organize tasks into projects
and collaborate with team members.
```

**Chunk 3:**
```
and collaborate with team members.

Technical Details

The backend uses Express.js with MongoDB for data storage.
Authentication is handled via JWT tokens. The frontend
communicates with the backend through a REST API.
```

### What Generic Parser Does

- ✅ Splits by paragraphs (double newlines)
- ✅ Falls back to sentence boundaries
- ✅ Maintains overlap for context
- ✅ Respects natural text boundaries
- ✅ Works for any text-based file

---

## Summary

| Parser | Method | Best For | Key Feature |
|--------|--------|----------|-------------|
| **Python** | AST | Python code | Most accurate, preserves all structure |
| **JavaScript/TS** | Regex | Web development | Handles modern JS/TS features |
| **JSON** | Native | Config files | Preserves valid JSON structure |
| **YAML** | Native | CI/CD configs | Respects indentation and structure |
| **Markdown** | Header-based | Documentation | Keeps code blocks with sections |
| **Rust** | Regex | Systems programming | Handles traits, generics, lifetimes |
| **Generic** | Text-based | Everything else | Smart paragraph/sentence splitting |

All parsers work automatically based on file extension - no configuration needed!
