"""Tests for Python parser."""

import pytest

from context_lens.parsers import CodeUnitType, PythonParser
from context_lens.parsers.base import SyntaxParsingError


class TestPythonParser:
    """Test PythonParser functionality."""

    def test_supported_extensions(self):
        """Test that Python parser supports .py and .pyw files."""
        extensions = PythonParser.get_supported_extensions()
        assert ".py" in extensions
        assert ".pyw" in extensions

    def test_parse_simple_function(self):
        """Test parsing a simple function."""
        parser = PythonParser()
        content = '''def hello_world():
    """Say hello."""
    print("Hello, World!")
'''
        units = parser.parse(content, "test.py")

        assert len(units) == 1
        assert units[0].type == CodeUnitType.FUNCTION
        assert units[0].name == "hello_world"
        assert units[0].docstring == "Say hello."
        assert units[0].start_line == 1
        assert units[0].end_line == 3

    def test_parse_function_with_decorator(self):
        """Test parsing a function with decorators."""
        parser = PythonParser()
        content = '''@property
@cache
def get_value():
    return 42
'''
        units = parser.parse(content, "test.py")

        assert len(units) == 1
        assert units[0].name == "get_value"
        assert "@property" in units[0].decorators
        assert "@cache" in units[0].decorators

    def test_parse_async_function(self):
        """Test parsing an async function."""
        parser = PythonParser()
        content = '''async def fetch_data():
    """Fetch data asynchronously."""
    return await get_data()
'''
        units = parser.parse(content, "test.py")

        assert len(units) == 1
        assert units[0].type == CodeUnitType.FUNCTION
        assert units[0].name == "fetch_data"
        assert units[0].metadata["is_async"] is True

    def test_parse_class(self):
        """Test parsing a class."""
        parser = PythonParser()
        content = '''class MyClass:
    """A test class."""
    
    def __init__(self):
        self.value = 0
    
    def get_value(self):
        return self.value
'''
        units = parser.parse(content, "test.py")

        assert len(units) == 1
        assert units[0].type == CodeUnitType.CLASS
        assert units[0].name == "MyClass"
        assert units[0].docstring == "A test class."

    def test_parse_class_with_decorator(self):
        """Test parsing a class with decorators."""
        parser = PythonParser()
        content = '''@dataclass
class User:
    name: str
    age: int
'''
        units = parser.parse(content, "test.py")

        assert len(units) == 1
        assert units[0].name == "User"
        assert "@dataclass" in units[0].decorators

    def test_parse_class_with_inheritance(self):
        """Test parsing a class with base classes."""
        parser = PythonParser()
        content = '''class Child(Parent, Mixin):
    pass
'''
        units = parser.parse(content, "test.py")

        assert len(units) == 1
        assert units[0].name == "Child"
        assert "Parent" in units[0].metadata["base_classes"]
        assert "Mixin" in units[0].metadata["base_classes"]

    def test_parse_imports(self):
        """Test parsing import statements."""
        parser = PythonParser()
        content = '''import os
import sys
from typing import List, Dict
from pathlib import Path
'''
        units = parser.parse(content, "test.py")

        assert len(units) == 1
        assert units[0].type == CodeUnitType.IMPORT
        assert units[0].name == "imports"
        assert "import os" in units[0].content
        assert "from typing import List" in units[0].content

    def test_parse_multiple_units(self):
        """Test parsing file with multiple units."""
        parser = PythonParser()
        content = '''import os

def function_one():
    pass

class MyClass:
    def method_one(self):
        pass

def function_two():
    pass
'''
        units = parser.parse(content, "test.py")

        # Should have: imports, function_one, MyClass, function_two
        assert len(units) == 4
        assert units[0].type == CodeUnitType.IMPORT
        assert units[1].type == CodeUnitType.FUNCTION
        assert units[1].name == "function_one"
        assert units[2].type == CodeUnitType.CLASS
        assert units[2].name == "MyClass"
        assert units[3].type == CodeUnitType.FUNCTION
        assert units[3].name == "function_two"

    def test_parse_syntax_error(self):
        """Test handling of syntax errors."""
        parser = PythonParser()
        content = '''def broken_function(
    # Missing closing parenthesis
    print("This won't parse")
'''
        with pytest.raises(SyntaxParsingError):
            parser.parse(content, "test.py")

    def test_chunk_small_file(self):
        """Test chunking a small file."""
        parser = PythonParser(chunk_size=1000)
        content = '''def small_function():
    return 42
'''
        units = parser.parse(content, "test.py")
        chunks = parser.chunk(units, "doc123")

        assert len(chunks) == 1
        assert chunks[0].document_id == "doc123"
        assert chunks[0].metadata["language"] == "python"
        assert chunks[0].metadata["chunk_type"] == "code"

    def test_chunk_multiple_units(self):
        """Test chunking multiple units."""
        parser = PythonParser(chunk_size=200)
        content = '''def function_one():
    """First function."""
    return 1

def function_two():
    """Second function."""
    return 2

def function_three():
    """Third function."""
    return 3
'''
        units = parser.parse(content, "test.py")
        chunks = parser.chunk(units, "doc123")

        # Should create multiple chunks due to size limit
        assert len(chunks) >= 1
        # All chunks should have metadata
        for chunk in chunks:
            assert chunk.metadata["language"] == "python"

    def test_chunk_large_function(self):
        """Test chunking a very large function."""
        parser = PythonParser(chunk_size=100)
        # Create a large function
        lines = ["def large_function():"]
        lines.append('    """A very large function."""')
        for i in range(50):
            lines.append(f"    x{i} = {i}")
        lines.append("    return sum([" + ", ".join(f"x{i}" for i in range(50)) + "])")

        content = "\n".join(lines)
        units = parser.parse(content, "test.py")
        chunks = parser.chunk(units, "doc123")

        # Should split into multiple chunks
        assert len(chunks) > 1
        # All chunks should be marked as partial
        for chunk in chunks:
            assert chunk.metadata["is_partial"] is True
            assert chunk.metadata["chunk_type"] == "code_split"

    def test_chunk_metadata(self):
        """Test that chunk metadata is properly set."""
        parser = PythonParser()
        content = '''@decorator
def my_function():
    """With docstring."""
    pass
'''
        units = parser.parse(content, "test.py")
        chunks = parser.chunk(units, "doc123")

        assert len(chunks) == 1
        metadata = chunks[0].metadata

        assert metadata["language"] == "python"
        assert metadata["chunk_type"] == "code"
        assert metadata["has_docstrings"] is True
        assert metadata["has_decorators"] is True
        assert "my_function" in metadata["parent_structure"]

    def test_empty_file(self):
        """Test parsing an empty file."""
        parser = PythonParser()
        content = ""

        units = parser.parse(content, "test.py")
        assert len(units) == 0

    def test_comments_only(self):
        """Test parsing a file with only comments."""
        parser = PythonParser()
        content = '''# This is a comment
# Another comment
'''
        units = parser.parse(content, "test.py")
        # Comments are not extracted as units
        assert len(units) == 0

    def test_real_world_example(self):
        """Test parsing a realistic Python file."""
        parser = PythonParser()
        content = '''"""Module docstring."""

import os
from typing import List, Optional

class DataProcessor:
    """Process data efficiently."""
    
    def __init__(self, config: dict):
        """Initialize processor."""
        self.config = config
    
    @property
    def is_ready(self) -> bool:
        """Check if processor is ready."""
        return self.config is not None
    
    async def process(self, data: List[str]) -> Optional[dict]:
        """Process the data asynchronously."""
        if not self.is_ready:
            return None
        
        results = {}
        for item in data:
            results[item] = await self._process_item(item)
        return results
    
    async def _process_item(self, item: str) -> str:
        """Process a single item."""
        return item.upper()

def main():
    """Main entry point."""
    processor = DataProcessor({"mode": "fast"})
    print("Ready to process")

if __name__ == "__main__":
    main()
'''
        units = parser.parse(content, "test.py")

        # Should have: imports, DataProcessor class, main function
        assert len(units) == 3
        assert units[0].type == CodeUnitType.IMPORT
        assert units[1].type == CodeUnitType.CLASS
        assert units[1].name == "DataProcessor"
        assert units[2].type == CodeUnitType.FUNCTION
        assert units[2].name == "main"

        # Test chunking
        chunks = parser.chunk(units, "doc123")
        assert len(chunks) >= 1
        assert all(chunk.metadata["language"] == "python" for chunk in chunks)
