"""Integration tests for parser registry with language parsers."""

import pytest

from context_lens.parsers import PythonParser, get_parser_registry
from context_lens.parsers.generic_chunker import GenericChunker


class TestParserIntegration:
    """Test integration of parsers with registry."""

    def test_register_python_parser(self):
        """Test registering Python parser."""
        registry = get_parser_registry()
        registry.clear()  # Start fresh

        registry.register(PythonParser)

        assert registry.is_extension_supported(".py")
        assert registry.is_extension_supported(".pyw")

    def test_get_python_parser_for_py_file(self):
        """Test getting Python parser for .py file."""
        registry = get_parser_registry()
        registry.clear()
        registry.register(PythonParser)

        parser = registry.get_parser("example.py")

        assert isinstance(parser, PythonParser)

    def test_get_generic_chunker_for_unknown_file(self):
        """Test fallback to generic chunker for unknown file type."""
        registry = get_parser_registry()
        registry.clear()
        registry.register(PythonParser)

        parser = registry.get_parser("example.unknown")

        assert isinstance(parser, GenericChunker)

    def test_end_to_end_python_parsing(self):
        """Test complete flow: register, get parser, parse, chunk."""
        registry = get_parser_registry()
        registry.clear()
        registry.register(PythonParser)

        # Get parser
        parser = registry.get_parser("example.py", chunk_size=1000, chunk_overlap=200)

        # Parse Python code
        content = '''import os

class Calculator:
    """A simple calculator."""
    
    def add(self, a, b):
        """Add two numbers."""
        return a + b
    
    def subtract(self, a, b):
        """Subtract two numbers."""
        return a - b

def main():
    """Main function."""
    calc = Calculator()
    print(calc.add(5, 3))
'''
        units = parser.parse(content, "example.py")

        # Should have: imports, Calculator class, main function
        assert len(units) == 3

        # Chunk the units
        chunks = parser.chunk(units, "doc123")

        # Should create at least one chunk
        assert len(chunks) >= 1

        # All chunks should have Python metadata
        for chunk in chunks:
            assert chunk.metadata["language"] == "python"
            assert chunk.document_id == "doc123"

    def test_parser_statistics(self):
        """Test that parser usage is tracked."""
        registry = get_parser_registry()
        registry.clear()
        registry.register(PythonParser)

        # Use parsers
        registry.get_parser("file1.py")
        registry.get_parser("file2.py")
        registry.get_parser("file3.txt")  # Falls back to generic

        stats = registry.get_stats()

        assert "PythonParser" in stats
        assert stats["PythonParser"]["success"] == 2
        assert "GenericChunker" in stats
        assert stats["GenericChunker"]["success"] == 1

    def test_multiple_file_types(self):
        """Test handling multiple file types."""
        registry = get_parser_registry()
        registry.clear()
        registry.register(PythonParser)

        files = [
            ("script.py", PythonParser),
            ("module.pyw", PythonParser),
            ("readme.txt", GenericChunker),
            ("data.json", GenericChunker),
        ]

        for filename, expected_type in files:
            parser = registry.get_parser(filename)
            assert isinstance(parser, expected_type), f"Failed for {filename}"

    def test_parser_with_syntax_error_fallback(self):
        """Test that parser can handle syntax errors gracefully."""
        registry = get_parser_registry()
        registry.clear()
        registry.register(PythonParser)

        parser = registry.get_parser("broken.py")

        # This should raise SyntaxParsingError
        content = "def broken("  # Syntax error

        from context_lens.parsers.base import SyntaxParsingError

        with pytest.raises(SyntaxParsingError):
            parser.parse(content, "broken.py")

        # In real usage, ContentExtractor would catch this and fall back to generic chunker
        # Record the fallback
        registry.record_fallback("PythonParser")

        stats = registry.get_stats()
        assert stats["PythonParser"]["fallback"] == 1
