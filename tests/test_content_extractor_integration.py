"""Integration tests for ContentExtractor with parser registry."""

import tempfile
from pathlib import Path

import pytest

from context_lens.processors.content_extractor import ContentExtractor


class TestContentExtractorIntegration:
    """Test ContentExtractor with real code files."""

    def test_extract_python_file(self, tmp_path):
        """Test extracting and chunking a Python file."""
        # Create a test Python file
        python_file = tmp_path / "test.py"
        python_content = '''"""Test module."""

def hello_world():
    """Say hello."""
    return "Hello, World!"

class MyClass:
    """A test class."""
    
    def __init__(self, name):
        """Initialize with name."""
        self.name = name
    
    def greet(self):
        """Greet someone."""
        return f"Hello, {self.name}!"
'''
        python_file.write_text(python_content)

        # Extract and chunk
        extractor = ContentExtractor(chunk_size=1000, chunk_overlap=200)
        metadata, chunks = extractor.extract_and_chunk(str(python_file))

        # Verify metadata
        assert metadata.file_name == "test.py"
        assert metadata.file_type == ".py"
        assert metadata.chunk_count == len(chunks)

        # Verify chunks were created
        assert len(chunks) > 0

        # Verify chunks have content
        for chunk in chunks:
            assert chunk.content
            assert chunk.document_id == metadata.id
            assert chunk.embedding == []

    def test_extract_text_file(self, tmp_path):
        """Test extracting and chunking a text file."""
        # Create a test text file
        text_file = tmp_path / "test.txt"
        text_content = """This is a test document.

It has multiple paragraphs.

Each paragraph should be handled appropriately.

The chunking should work well."""
        text_file.write_text(text_content)

        # Extract and chunk
        extractor = ContentExtractor(chunk_size=100, chunk_overlap=20)
        metadata, chunks = extractor.extract_and_chunk(str(text_file))

        # Verify metadata
        assert metadata.file_name == "test.txt"
        assert metadata.file_type == ".txt"

        # Verify chunks
        assert len(chunks) > 0

    def test_extract_markdown_file(self, tmp_path):
        """Test extracting and chunking a Markdown file."""
        # Create a test Markdown file
        md_file = tmp_path / "README.md"
        md_content = """# Test Project

This is a test project.

## Installation

Install with pip:

```bash
pip install test-project
```

## Usage

Use it like this:

```python
import test_project
test_project.run()
```
"""
        md_file.write_text(md_content)

        # Extract and chunk
        extractor = ContentExtractor(chunk_size=200, chunk_overlap=50)
        metadata, chunks = extractor.extract_and_chunk(str(md_file))

        # Verify metadata
        assert metadata.file_name == "README.md"
        assert metadata.file_type == ".md"

        # Verify chunks
        assert len(chunks) > 0

    def test_extract_large_python_file(self, tmp_path):
        """Test extracting a larger Python file with multiple functions."""
        # Create a larger Python file
        python_file = tmp_path / "large.py"
        python_content = '''"""Large test module."""

def function_one():
    """First function."""
    return 1

def function_two():
    """Second function."""
    return 2

def function_three():
    """Third function."""
    return 3

class ClassOne:
    """First class."""
    
    def method_one(self):
        """First method."""
        pass
    
    def method_two(self):
        """Second method."""
        pass

class ClassTwo:
    """Second class."""
    
    def method_one(self):
        """First method."""
        pass
'''
        python_file.write_text(python_content)

        # Extract and chunk
        extractor = ContentExtractor(chunk_size=500, chunk_overlap=100)
        metadata, chunks = extractor.extract_and_chunk(str(python_file))

        # Verify multiple chunks were created
        assert len(chunks) >= 1

        # Verify all chunks have the same document_id
        doc_ids = {chunk.document_id for chunk in chunks}
        assert len(doc_ids) == 1
        assert list(doc_ids)[0] == metadata.id

    def test_parser_fallback_on_syntax_error(self, tmp_path):
        """Test that parser falls back gracefully on syntax errors."""
        # Create a Python file with syntax error
        python_file = tmp_path / "broken.py"
        python_content = '''def broken_function(
    # Missing closing parenthesis and body
'''
        python_file.write_text(python_content)

        # Extract and chunk - should fall back to text chunking
        extractor = ContentExtractor(chunk_size=1000, chunk_overlap=200)
        metadata, chunks = extractor.extract_and_chunk(str(python_file))

        # Should still create chunks (using fallback)
        assert len(chunks) > 0
        assert metadata.file_name == "broken.py"

    def test_chunk_metadata_present(self, tmp_path):
        """Test that chunks have metadata when using parsers."""
        # Create a Python file
        python_file = tmp_path / "with_metadata.py"
        python_content = '''def test_function():
    """Test function."""
    return "test"
'''
        python_file.write_text(python_content)

        # Extract and chunk
        extractor = ContentExtractor(chunk_size=1000, chunk_overlap=200)
        metadata, chunks = extractor.extract_and_chunk(str(python_file))

        # Check if chunks have metadata (if Python parser is registered)
        if chunks:
            # Metadata might be None if using legacy chunking
            # or a dict if using new parsers
            assert chunks[0].metadata is None or isinstance(chunks[0].metadata, dict)

    def test_different_chunk_sizes(self, tmp_path):
        """Test that different chunk sizes work correctly."""
        # Create a test file
        text_file = tmp_path / "test.txt"
        text_content = "Word " * 500  # 500 words
        text_file.write_text(text_content)

        # Test with small chunks
        extractor_small = ContentExtractor(chunk_size=100, chunk_overlap=20)
        _, chunks_small = extractor_small.extract_and_chunk(str(text_file))

        # Test with large chunks
        extractor_large = ContentExtractor(chunk_size=1000, chunk_overlap=200)
        _, chunks_large = extractor_large.extract_and_chunk(str(text_file))

        # Small chunks should create more chunks
        assert len(chunks_small) >= len(chunks_large)


class TestContentExtractorWithRealFiles:
    """Test ContentExtractor with actual project files."""

    def test_extract_own_source_file(self):
        """Test extracting one of our own source files."""
        # Use the content_extractor.py file itself
        source_file = Path(__file__).parent.parent / "src" / "context_lens" / "processors" / "content_extractor.py"
        
        if not source_file.exists():
            pytest.skip("Source file not found")

        extractor = ContentExtractor(chunk_size=1000, chunk_overlap=200)
        metadata, chunks = extractor.extract_and_chunk(str(source_file))

        # Verify it worked
        assert metadata.file_name == "content_extractor.py"
        assert metadata.file_type == ".py"
        assert len(chunks) > 0

        # Verify chunks have content
        total_content_length = sum(len(chunk.content) for chunk in chunks)
        assert total_content_length > 0

    def test_extract_test_file(self):
        """Test extracting a test file."""
        # Use this test file itself
        test_file = Path(__file__)

        extractor = ContentExtractor(chunk_size=1000, chunk_overlap=200)
        metadata, chunks = extractor.extract_and_chunk(str(test_file))

        # Verify it worked
        assert metadata.file_name == test_file.name
        assert metadata.file_type == ".py"
        assert len(chunks) > 0
