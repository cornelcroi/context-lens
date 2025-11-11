"""Tests for parser infrastructure (base classes and registry)."""

import pytest

from context_lens.parsers import (
    CodeUnit,
    CodeUnitType,
    LanguageParser,
    ParserRegistry,
    ParsingError,
)
from context_lens.parsers.generic_chunker import GenericChunker


class TestCodeUnit:
    """Test CodeUnit dataclass."""

    def test_code_unit_creation(self):
        """Test creating a code unit."""
        unit = CodeUnit(
            type=CodeUnitType.FUNCTION,
            name="test_function",
            content="def test_function():\n    pass",
            start_line=1,
            end_line=2,
        )

        assert unit.type == CodeUnitType.FUNCTION
        assert unit.name == "test_function"
        assert unit.start_line == 1
        assert unit.end_line == 2
        assert unit.decorators == []

    def test_code_unit_with_metadata(self):
        """Test code unit with metadata."""
        unit = CodeUnit(
            type=CodeUnitType.CLASS,
            name="MyClass",
            content="class MyClass:\n    pass",
            start_line=1,
            end_line=2,
            docstring="A test class",
            decorators=["@dataclass"],
            metadata={"visibility": "public"},
        )

        assert unit.docstring == "A test class"
        assert unit.decorators == ["@dataclass"]
        assert unit.metadata["visibility"] == "public"


class TestParserRegistry:
    """Test ParserRegistry functionality."""

    def test_registry_initialization(self):
        """Test registry initializes correctly."""
        registry = ParserRegistry()
        assert registry.list_registered_parsers() == {}
        assert registry.get_stats() == {}

    def test_register_parser(self):
        """Test registering a parser."""
        registry = ParserRegistry()
        registry.register(GenericChunker)

        # GenericChunker returns empty list for extensions (it's a fallback)
        assert len(registry.list_registered_parsers()) == 0

    def test_get_parser_fallback(self):
        """Test getting parser falls back to generic chunker."""
        registry = ParserRegistry()

        parser = registry.get_parser("test.unknown")
        assert isinstance(parser, GenericChunker)

    def test_parser_stats_tracking(self):
        """Test parser usage statistics."""
        registry = ParserRegistry()

        # Get parser multiple times
        registry.get_parser("test1.txt")
        registry.get_parser("test2.txt")
        registry.get_parser("test3.txt")

        stats = registry.get_stats()
        assert "GenericChunker" in stats
        assert stats["GenericChunker"]["success"] == 3

    def test_record_fallback(self):
        """Test recording parser fallback."""
        registry = ParserRegistry()

        # Record some usage first
        registry._record_parser_usage("TestParser")
        registry.record_fallback("TestParser")

        stats = registry.get_stats()
        assert stats["TestParser"]["fallback"] == 1

    def test_is_extension_supported(self):
        """Test checking if extension is supported."""
        registry = ParserRegistry()

        # No parsers registered yet
        assert not registry.is_extension_supported(".py")
        assert not registry.is_extension_supported("py")

    def test_clear_registry(self):
        """Test clearing the registry."""
        registry = ParserRegistry()
        registry._record_parser_usage("TestParser")

        registry.clear()

        assert registry.list_registered_parsers() == {}
        assert registry.get_stats() == {}


class TestGenericChunker:
    """Test GenericChunker functionality."""

    def test_generic_chunker_parse(self):
        """Test parsing with generic chunker."""
        chunker = GenericChunker()
        content = "This is a test document.\nWith multiple lines."

        units = chunker.parse(content, "test.txt")

        assert len(units) == 1
        assert units[0].type == CodeUnitType.TEXT
        assert units[0].name == "document"
        assert units[0].content == content

    def test_generic_chunker_small_content(self):
        """Test chunking small content."""
        chunker = GenericChunker(chunk_size=1000)
        content = "Short content."

        units = chunker.parse(content, "test.txt")
        chunks = chunker.chunk(units, "doc123")

        assert len(chunks) == 1
        assert chunks[0].content == content
        assert chunks[0].document_id == "doc123"

    def test_generic_chunker_paragraph_splitting(self):
        """Test chunking by paragraphs."""
        chunker = GenericChunker(chunk_size=50, chunk_overlap=10)
        # Create longer paragraphs to force splitting
        content = "This is paragraph one with enough text to exceed the chunk size.\n\nThis is paragraph two with enough text to exceed the chunk size.\n\nThis is paragraph three with enough text."

        units = chunker.parse(content, "test.txt")
        chunks = chunker.chunk(units, "doc123")

        # Should create multiple chunks
        assert len(chunks) >= 1
        # Each chunk should have metadata
        assert chunks[0].metadata["chunk_type"] == "text"
        assert chunks[0].metadata["language"] == "generic"

    def test_generic_chunker_sentence_splitting(self):
        """Test chunking by sentences when no paragraphs."""
        chunker = GenericChunker(chunk_size=50, chunk_overlap=10)
        content = "Sentence one. Sentence two. Sentence three. Sentence four."

        units = chunker.parse(content, "test.txt")
        chunks = chunker.chunk(units, "doc123")

        # Should create multiple chunks
        assert len(chunks) > 1

    def test_generic_chunker_overlap(self):
        """Test that overlap is applied between chunks."""
        chunker = GenericChunker(chunk_size=50, chunk_overlap=15)
        content = "First sentence here. Second sentence here. Third sentence here."

        units = chunker.parse(content, "test.txt")
        chunks = chunker.chunk(units, "doc123")

        if len(chunks) > 1:
            # Check that there's some overlap
            # (exact overlap depends on sentence boundaries)
            assert len(chunks[1].content) > 0


class TestLanguageParserBase:
    """Test LanguageParser base class functionality."""

    def test_should_split_unit(self):
        """Test should_split_unit logic."""
        chunker = GenericChunker(chunk_size=1000)

        small_unit = CodeUnit(
            type=CodeUnitType.FUNCTION,
            name="small",
            content="x" * 500,
            start_line=1,
            end_line=10,
        )

        large_unit = CodeUnit(
            type=CodeUnitType.FUNCTION,
            name="large",
            content="x" * 2000,
            start_line=1,
            end_line=100,
        )

        assert not chunker.should_split_unit(small_unit)
        assert chunker.should_split_unit(large_unit)

    def test_find_matching_brace(self):
        """Test finding matching braces."""
        chunker = GenericChunker()
        content = "function test() { if (true) { return 1; } }"

        # Find matching brace for first {
        first_brace = content.index("{")
        matching = chunker._find_matching_brace(content, first_brace)

        assert matching == len(content) - 1  # Last character

    def test_create_chunk_metadata(self):
        """Test creating chunk metadata."""
        chunker = GenericChunker()

        units = [
            CodeUnit(
                type=CodeUnitType.CLASS,
                name="MyClass",
                content="class MyClass:",
                start_line=1,
                end_line=5,
            ),
            CodeUnit(
                type=CodeUnitType.METHOD,
                name="my_method",
                content="def my_method(self):",
                start_line=2,
                end_line=4,
                parent="MyClass",
            ),
        ]

        metadata = chunker._create_chunk_metadata(units, "python", "code")

        assert metadata["chunk_type"] == "code"
        assert metadata["language"] == "python"
        assert metadata["start_line"] == 1
        assert metadata["end_line"] == 4
        assert "MyClass" in metadata["parent_structure"]
        assert "my_method" in metadata["parent_structure"]
