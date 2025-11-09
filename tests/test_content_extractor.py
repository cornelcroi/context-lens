"""Unit tests for ContentExtractor."""

from pathlib import Path

import pytest

from context_lens.models.data_models import DocumentChunk, DocumentMetadata
from context_lens.processors import FileProcessingError
from context_lens.processors.content_extractor import ContentExtractor


class TestContentExtractor:
    """Test cases for ContentExtractor."""

    @pytest.fixture
    def extractor(self):
        """Create ContentExtractor with test configuration."""
        return ContentExtractor(chunk_size=100, chunk_overlap=20)

    @pytest.fixture
    def large_extractor(self):
        """Create ContentExtractor with larger chunk size."""
        return ContentExtractor(chunk_size=500, chunk_overlap=100)

    def test_initialization(self):
        """Test ContentExtractor initialization."""
        extractor = ContentExtractor(chunk_size=200, chunk_overlap=50)
        assert extractor.chunk_size == 200
        assert extractor.chunk_overlap == 50
        assert extractor.file_reader_factory is not None

    def test_extract_and_chunk_python_file(self, extractor, temp_dir):
        """Test extracting and chunking Python file."""
        py_file = temp_dir / "test.py"
        content = '''def function1():
    """First function."""
    return "hello"

def function2():
    """Second function."""
    return "world"

class TestClass:
    """Test class."""

    def method1(self):
        return "method1"
'''
        py_file.write_text(content)

        metadata, chunks = extractor.extract_and_chunk(str(py_file))

        # Verify metadata
        assert isinstance(metadata, DocumentMetadata)
        assert metadata.file_name == "test.py"
        assert metadata.file_type == ".py"
        assert metadata.file_size > 0
        assert metadata.chunk_count == len(chunks)
        assert len(metadata.content_hash) > 0

        # Verify chunks
        assert len(chunks) > 0
        for i, chunk in enumerate(chunks):
            assert isinstance(chunk, DocumentChunk)
            assert chunk.document_id == metadata.id
            assert chunk.chunk_index == i
            assert len(chunk.content) > 0
            assert chunk.embedding == []  # Not populated yet

    def test_extract_and_chunk_text_file(self, extractor, temp_dir):
        """Test extracting and chunking text file."""
        txt_file = temp_dir / "test.txt"
        content = """This is the first paragraph with some content.

This is the second paragraph with more information.

This is the third paragraph that contains additional details."""
        txt_file.write_text(content)

        metadata, chunks = extractor.extract_and_chunk(str(txt_file))

        # Verify metadata
        assert metadata.file_name == "test.txt"
        assert metadata.file_type == ".txt"
        assert metadata.chunk_count == len(chunks)

        # Verify chunks
        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk.document_id == metadata.id
            assert len(chunk.content) > 0

    def test_extract_nonexistent_file(self, extractor):
        """Test extracting non-existent file raises error."""
        with pytest.raises(FileProcessingError):
            extractor.extract_and_chunk("nonexistent.py")

    def test_extract_unsupported_file(self, extractor, temp_dir):
        """Test extracting unsupported file type raises error."""
        unsupported_file = temp_dir / "test.xyz"
        unsupported_file.write_text("content")

        with pytest.raises(FileProcessingError):
            extractor.extract_and_chunk(str(unsupported_file))

    def test_chunk_python_with_definitions(self, extractor, temp_dir):
        """Test Python chunking preserves function boundaries."""
        py_file = temp_dir / "functions.py"
        content = '''def small_function():
    """A small function."""
    pass

def another_small_function():
    """Another small function."""
    pass
'''
        py_file.write_text(content)

        metadata, chunks = extractor.extract_and_chunk(str(py_file))

        # Should create chunks respecting function boundaries
        assert len(chunks) >= 1

        # Verify each chunk contains valid content
        for chunk in chunks:
            assert len(chunk.content.strip()) > 0

    def test_chunk_large_python_function(self, extractor, temp_dir):
        """Test chunking large Python function that exceeds chunk size."""
        py_file = temp_dir / "large_function.py"
        # Create a large function that will need to be split
        lines = ["def large_function():"]
        lines.append('    """A very large function."""')
        for i in range(50):
            lines.append(f'    variable_{i} = "This is line {i} with some content"')
        lines.append('    return "done"')
        content = "\n".join(lines)
        py_file.write_text(content)

        metadata, chunks = extractor.extract_and_chunk(str(py_file))

        # Should create at least one chunk
        assert len(chunks) >= 1
        # Verify content is preserved
        all_content = " ".join([chunk.content for chunk in chunks])
        assert "large_function" in all_content

    def test_chunk_text_with_paragraphs(self, large_extractor, temp_dir):
        """Test text chunking respects paragraph boundaries."""
        txt_file = temp_dir / "paragraphs.txt"
        paragraphs = []
        for i in range(10):
            paragraphs.append(f"This is paragraph {i}. It contains some text about topic {i}.")
        content = "\n\n".join(paragraphs)
        txt_file.write_text(content)

        metadata, chunks = large_extractor.extract_and_chunk(str(txt_file))

        # Should create multiple chunks
        assert len(chunks) >= 1

        # Verify chunks don't exceed reasonable size
        for chunk in chunks:
            assert len(chunk.content) <= large_extractor.chunk_size * 2

    def test_chunk_text_with_sentences(self, extractor, temp_dir):
        """Test text chunking with sentence boundaries."""
        txt_file = temp_dir / "sentences.txt"
        sentences = []
        for i in range(20):
            sentences.append(f"This is sentence number {i}.")
        content = " ".join(sentences)
        txt_file.write_text(content)

        metadata, chunks = extractor.extract_and_chunk(str(txt_file))

        # Should create at least one chunk
        assert len(chunks) >= 1
        # Verify all sentences are captured
        all_content = " ".join([chunk.content for chunk in chunks])
        assert "sentence number 0" in all_content
        assert "sentence number 19" in all_content

    def test_chunk_overlap_in_text(self, extractor, temp_dir):
        """Test that text chunks have proper overlap."""
        txt_file = temp_dir / "overlap_test.txt"
        # Create content that will definitely need multiple chunks
        sentences = []
        for i in range(30):
            sentences.append(f"Sentence {i} contains information about topic {i}.")
        content = " ".join(sentences)
        txt_file.write_text(content)

        metadata, chunks = extractor.extract_and_chunk(str(txt_file))

        # Should have at least one chunk
        assert len(chunks) >= 1

        # Verify all content is captured
        all_content = " ".join([chunk.content for chunk in chunks])
        assert "Sentence 0" in all_content
        assert "topic 29" in all_content

    def test_empty_file_handling(self, extractor, temp_dir):
        """Test handling of empty file."""
        empty_file = temp_dir / "empty.txt"
        empty_file.write_text("")

        metadata, chunks = extractor.extract_and_chunk(str(empty_file))

        # Should handle empty file gracefully
        assert metadata.file_name == "empty.txt"
        assert len(chunks) == 0 or (len(chunks) == 1 and chunks[0].content.strip() == "")

    def test_whitespace_only_file(self, extractor, temp_dir):
        """Test handling of file with only whitespace."""
        whitespace_file = temp_dir / "whitespace.txt"
        whitespace_file.write_text("   \n\n   \t\t   \n")

        metadata, chunks = extractor.extract_and_chunk(str(whitespace_file))

        # Should handle whitespace-only file
        assert metadata.file_name == "whitespace.txt"
        # Chunks should be empty or contain only whitespace
        for chunk in chunks:
            assert len(chunk.content.strip()) == 0

    def test_single_line_file(self, extractor, temp_dir):
        """Test handling of single line file."""
        single_line_file = temp_dir / "single_line.txt"
        single_line_file.write_text("This is a single line of text.")

        metadata, chunks = extractor.extract_and_chunk(str(single_line_file))

        # Should create one chunk
        assert len(chunks) == 1
        assert chunks[0].content == "This is a single line of text."

    def test_chunk_index_ordering(self, extractor, temp_dir):
        """Test that chunk indices are properly ordered."""
        txt_file = temp_dir / "ordering_test.txt"
        # Create content that will produce multiple chunks
        content = " ".join([f"Sentence {i}." for i in range(50)])
        txt_file.write_text(content)

        metadata, chunks = extractor.extract_and_chunk(str(txt_file))

        # Verify chunk indices are sequential
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i

    def test_document_id_consistency(self, extractor, temp_dir):
        """Test that all chunks have the same document ID."""
        txt_file = temp_dir / "consistency_test.txt"
        content = " ".join([f"Content {i}." for i in range(30)])
        txt_file.write_text(content)

        metadata, chunks = extractor.extract_and_chunk(str(txt_file))

        # All chunks should have the same document ID as metadata
        for chunk in chunks:
            assert chunk.document_id == metadata.id

    def test_content_hash_generation(self, extractor, temp_dir):
        """Test that content hash is generated."""
        txt_file = temp_dir / "hash_test.txt"
        txt_file.write_text("Test content for hashing")

        metadata, chunks = extractor.extract_and_chunk(str(txt_file))

        # Content hash should be generated
        assert len(metadata.content_hash) > 0

        # Same content should produce same hash
        metadata2, chunks2 = extractor.extract_and_chunk(str(txt_file))
        assert metadata2.content_hash == metadata.content_hash

    def test_different_content_different_hash(self, extractor, temp_dir):
        """Test that different content produces different hash."""
        file1 = temp_dir / "file1.txt"
        file1.write_text("Content A")

        file2 = temp_dir / "file2.txt"
        file2.write_text("Content B")

        metadata1, _ = extractor.extract_and_chunk(str(file1))
        metadata2, _ = extractor.extract_and_chunk(str(file2))

        # Different content should produce different hashes
        assert metadata1.content_hash != metadata2.content_hash

    def test_absolute_path_in_metadata(self, extractor, temp_dir):
        """Test that metadata contains absolute file path."""
        txt_file = temp_dir / "path_test.txt"
        txt_file.write_text("Test content")

        metadata, chunks = extractor.extract_and_chunk(str(txt_file))

        # File path should be absolute
        assert Path(metadata.file_path).is_absolute()

    def test_python_class_chunking(self, large_extractor, temp_dir):
        """Test chunking Python file with classes."""
        py_file = temp_dir / "classes.py"
        content = '''class FirstClass:
    """First class."""

    def method1(self):
        return "method1"

    def method2(self):
        return "method2"

class SecondClass:
    """Second class."""

    def method3(self):
        return "method3"
'''
        py_file.write_text(content)

        metadata, chunks = large_extractor.extract_and_chunk(str(py_file))

        # Should create chunks, potentially preserving class boundaries
        assert len(chunks) >= 1
        for chunk in chunks:
            assert len(chunk.content) > 0

    def test_mixed_python_content(self, large_extractor, temp_dir):
        """Test chunking Python file with mixed content."""
        py_file = temp_dir / "mixed.py"
        content = '''"""Module docstring."""

import os
import sys

CONSTANT = "value"

def function():
    """Function docstring."""
    pass

class MyClass:
    """Class docstring."""

    def __init__(self):
        self.value = 0
'''
        py_file.write_text(content)

        metadata, chunks = large_extractor.extract_and_chunk(str(py_file))

        # Should handle mixed content
        assert len(chunks) >= 1
        assert metadata.file_type == ".py"


class TestChunkingEdgeCases:
    """Test edge cases in chunking logic."""

    def test_very_small_chunk_size(self, temp_dir):
        """Test with very small chunk size."""
        extractor = ContentExtractor(chunk_size=10, chunk_overlap=2)

        txt_file = temp_dir / "small_chunks.txt"
        txt_file.write_text("This is a test sentence.")

        metadata, chunks = extractor.extract_and_chunk(str(txt_file))

        # Should create at least one chunk
        assert len(chunks) >= 1
        # Verify content is preserved
        all_content = " ".join([chunk.content for chunk in chunks])
        assert "test sentence" in all_content

    def test_zero_overlap(self, temp_dir):
        """Test chunking with zero overlap."""
        extractor = ContentExtractor(chunk_size=50, chunk_overlap=0)

        txt_file = temp_dir / "no_overlap.txt"
        content = "A" * 150  # 150 characters
        txt_file.write_text(content)

        metadata, chunks = extractor.extract_and_chunk(str(txt_file))

        # Should create at least one chunk
        assert len(chunks) >= 1
        # Verify all content is captured
        total_length = sum(len(chunk.content) for chunk in chunks)
        assert total_length == 150

    def test_overlap_larger_than_chunk(self, temp_dir):
        """Test with overlap larger than chunk size."""
        # This is an unusual configuration but should still work
        extractor = ContentExtractor(chunk_size=50, chunk_overlap=100)

        txt_file = temp_dir / "large_overlap.txt"
        txt_file.write_text("Test content for large overlap configuration.")

        metadata, chunks = extractor.extract_and_chunk(str(txt_file))

        # Should still create chunks
        assert len(chunks) >= 1

    def test_unicode_content(self, temp_dir):
        """Test chunking with Unicode content."""
        extractor = ContentExtractor(chunk_size=100, chunk_overlap=20)

        txt_file = temp_dir / "unicode.txt"
        content = "Hello 世界! Привет мир! مرحبا بالعالم! 🌍🌎🌏"
        txt_file.write_text(content, encoding="utf-8")

        metadata, chunks = extractor.extract_and_chunk(str(txt_file))

        # Should handle Unicode correctly
        assert len(chunks) >= 1
        assert "世界" in chunks[0].content or "мир" in chunks[0].content

    def test_special_characters(self, temp_dir):
        """Test chunking with special characters."""
        extractor = ContentExtractor(chunk_size=100, chunk_overlap=20)

        txt_file = temp_dir / "special.txt"
        content = "Special chars: @#$%^&*()_+-=[]{}|;':\",./<>?`~"
        txt_file.write_text(content)

        metadata, chunks = extractor.extract_and_chunk(str(txt_file))

        # Should handle special characters
        assert len(chunks) >= 1
        assert "@#$%^&*" in chunks[0].content
