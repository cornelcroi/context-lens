# Contributing to Context Lens

Thank you for your interest in contributing to Context Lens! This document provides guidelines and information for contributors.

## Table of Contents

- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Ways to Contribute](#ways-to-contribute)
- [Roadmap](#roadmap)
- [Questions](#questions)

---

## How to Contribute

**Before submitting a pull request, please:**

1. **Open an issue first** - Describe what you'd like to add or fix
2. **Discuss the approach** - I'll review and provide feedback on how it fits into the project
3. **Get approval** - Once approved, you can start working on your contribution
4. **Submit a PR** - Reference the issue in your pull request

This process helps ensure:
- Your time isn't wasted on changes that might not be accepted
- The contribution aligns with the project's goals and architecture
- I can provide guidance and avoid duplicate work

---

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Git
- pip or uv

### Setup Steps

```bash
# Clone the repository
git clone https://github.com/cornelcroi/context-lens.git
cd context-lens

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests to verify setup
pytest tests/
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=context_lens --cov-report=html

# Run specific test file
pytest tests/test_python_parser.py

# Run specific test
pytest tests/test_python_parser.py::TestPythonParser::test_parse_simple_function
```

### Code Quality

```bash
# Format code with black
black src/ tests/

# Sort imports
isort src/ tests/

# Type checking
mypy src/

# Linting
flake8 src/ tests/
```

---

## Ways to Contribute

### 🐛 Report Bugs

Found an issue? Let me know!

**Include:**
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Error messages and logs
- System information (OS, Python version)

### 💡 Suggest Features

Have an idea? Open an issue to discuss it!

**Include:**
- Use case and motivation
- Proposed solution
- Alternative approaches considered
- Impact on existing functionality

### 📝 Improve Documentation

Help make the docs clearer!

**Areas:**
- Fix typos and grammar
- Add examples
- Clarify confusing sections
- Add missing information
- Improve organization

### 🧪 Add Tests

Improve test coverage!

**Focus on:**
- Edge cases
- Error handling
- Integration tests
- Performance tests
- Real-world scenarios

### 🔧 Fix Bugs

Pick an issue and submit a fix!

**Process:**
1. Comment on the issue to claim it
2. Create a branch for your fix
3. Write tests that reproduce the bug
4. Fix the bug
5. Verify tests pass
6. Submit PR

### ✨ Add Features

Implement approved feature requests!

**Process:**
1. Get feature approved in an issue first
2. Discuss implementation approach
3. Create a branch
4. Implement with tests
5. Update documentation
6. Submit PR

---

## Roadmap

I'm actively working on making Context Lens even more powerful. Here's what's coming:

### 🎯 Planned Features

#### Cloud Storage Integration
- 📦 **S3 Support** - Store LanceDB database in AWS S3 for team sharing and backup
- ☁️ **Cloud Sync** - Sync knowledge base across multiple machines
- 🔄 **Remote Databases** - Access shared knowledge bases from anywhere

#### Enhanced Embedding Options
- 🤖 **API-based Models** - Use OpenAI, Cohere, or other API providers for embeddings
- 🔄 **Model Switching** - Change embedding models without re-indexing
- 🎛️ **Custom Models** - Bring your own fine-tuned models
- 📊 **Model Comparison** - Test different models to find the best fit

#### Document Format Support
- 📄 **PDF Support** - Extract and index PDF documents (local and from URLs)
- 📊 **Excel/Spreadsheets** - Index `.xls`, `.xlsx` files (local and from URLs)
- 📝 **Word Documents** - Support for `.doc`, `.docx` files (local and from URLs)
- 📑 **PowerPoint** - Index `.ppt`, `.pptx` presentations (local and from URLs)
- 🌐 **HTML/Web** - Extract content from HTML files and web pages
- 🔗 **Direct URL Support** - Fetch and index documents directly from URLs

#### Advanced Features
- 🔍 **Hybrid Search** - Combine semantic and keyword search for better results
- 📈 **Search Analytics** - Track what queries work best
- 🏷️ **Document Tagging** - Organize documents with custom tags
- 🔗 **Cross-References** - Automatically link related documents
- 📝 **Incremental Updates** - Smart re-indexing of changed files

#### Developer Experience
- 🐳 **Docker Support** - Containerized deployment
- 🔌 **REST API** - Use Context Lens outside of MCP
- 📚 **Python SDK** - Programmatic access to all features
- 🧪 **Testing Tools** - Evaluate search quality

#### Enterprise Features
- 👥 **Multi-user Support** - Shared knowledge bases with access control
- 🔐 **Authentication** - Secure access to knowledge bases
- 📊 **Usage Metrics** - Track usage and performance
- 🔄 **Backup & Restore** - Automated backup strategies

### Priority Order

**High Priority (Next 3 months):**
1. PDF support
2. Hybrid search
3. Docker support
4. REST API

**Medium Priority (3-6 months):**
1. S3 storage integration
2. API-based embedding models
3. Document tagging
4. Incremental updates

**Low Priority (6+ months):**
1. Multi-user support
2. Authentication
3. Usage metrics
4. Office document support

### 💡 Have Ideas?

I'd love to hear your suggestions! Open an issue on GitHub to:
- Request new features
- Suggest improvements
- Share your use cases
- Report bugs

---

## Pull Request Guidelines

### Before Submitting

- [ ] Tests pass locally
- [ ] Code follows project style
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (if applicable)
- [ ] Issue referenced in PR description

### PR Description Template

```markdown
## Description
Brief description of changes

## Related Issue
Fixes #123

## Changes Made
- Change 1
- Change 2

## Testing
How was this tested?

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code follows style guidelines
```

### Review Process

1. **Automated checks** - Tests and linting must pass
2. **Code review** - I'll review and provide feedback
3. **Revisions** - Make requested changes
4. **Approval** - Once approved, I'll merge
5. **Release** - Changes included in next release

---

## Code Style

### Python Style

- Follow [PEP 8](https://pep8.org/)
- Use [Black](https://black.readthedocs.io/) for formatting
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Type hints for all functions
- Docstrings for all public functions

### Example

```python
from typing import List, Optional

def parse_document(
    content: str,
    file_path: str,
    chunk_size: int = 1000
) -> List[str]:
    """Parse document content into chunks.
    
    Args:
        content: The document content to parse
        file_path: Path to the document file
        chunk_size: Maximum size of each chunk
        
    Returns:
        List of content chunks
        
    Raises:
        ValueError: If content is empty
    """
    if not content:
        raise ValueError("Content cannot be empty")
    
    # Implementation here
    return chunks
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add PDF support
fix: resolve database connection issue
docs: update setup instructions
test: add tests for JSON parser
refactor: simplify chunking logic
```

---

## Questions?

- Open an issue for questions about contributing
- Check existing issues to see if your question has been answered
- Star the repo if you find it useful! ⭐

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

## Thank You!

Thank you for contributing to Context Lens! Your help makes this project better for everyone.
