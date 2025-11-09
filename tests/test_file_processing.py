"""Tests for file processing components."""

import pytest

from context_lens.processors import (
    ContentExtractor,
    FileProcessingError,
    FileReaderFactory,
    PythonFileReader,
    TextFileReader,
)


class TestFileReader:
    """Test base FileReader functionality."""

    def test_validate_file_not_found(self):
        """Test validation fails for non-existent file."""
        reader = PythonFileReader()

        with pytest.raises(FileProcessingError) as exc_info:
            reader.validate_file("nonexistent.py")

        assert exc_info.value.error_type == "file_not_found"

    def test_validate_file_too_large(self, temp_dir):
        """Test validation fails for oversized file."""
        # Create a large file
        large_file = temp_dir / "large.py"
        with open(large_file, "w") as f:
            f.write("# " + "x" * (11 * 1024 * 1024))  # 11MB file

        reader = PythonFileReader()

        with pytest.raises(FileProcessingError) as exc_info:
            reader.validate_file(str(large_file))

        assert exc_info.value.error_type == "file_too_large"

    def test_validate_unsupported_extension(self, temp_dir):
        """Test validation fails for unsupported file type."""
        unsupported_file = temp_dir / "test.xyz"
        unsupported_file.write_text("content")

        reader = PythonFileReader()

        with pytest.raises(FileProcessingError) as exc_info:
            reader.validate_file(str(unsupported_file))

        assert exc_info.value.error_type == "unsupported_file_type"

    def test_detect_encoding_utf8(self, temp_dir):
        """Test encoding detection for UTF-8 file."""
        test_file = temp_dir / "utf8.txt"
        test_file.write_text("Hello, 世界!", encoding="utf-8")

        reader = TextFileReader()
        encoding = reader.detect_encoding(str(test_file))

        assert encoding in ["utf-8", "UTF-8"]

    def test_read_file_content(self, temp_dir):
        """Test reading file content."""
        test_file = temp_dir / "test.txt"
        content = "Hello, World!"
        test_file.write_text(content)

        reader = TextFileReader()
        read_content = reader.read_file_content(str(test_file))

        assert read_content == content


class TestPythonFileReader:
    """Test PythonFileReader functionality."""

    def test_can_read_python_file(self):
        """Test that PythonFileReader can read .py files."""
        reader = PythonFileReader()

        assert reader.can_read("test.py")
        assert reader.can_read("TEST.PY")
        assert not reader.can_read("test.txt")

    def test_extract_valid_python_content(self, temp_dir):
        """Test extracting content from valid Python file."""
        py_file = temp_dir / "test.py"
        content = '''def hello():
    """Say hello."""
    print("Hello, World!")

class Test:
    pass
'''
        py_file.write_text(content)

        reader = PythonFileReader()
        extracted = reader.extract_content(str(py_file))

        assert extracted == content

    def test_extract_invalid_python_syntax(self, temp_dir):
        """Test extracting content from Python file with syntax errors."""
        py_file = temp_dir / "invalid.py"
        content = """def hello(
    print("Missing closing parenthesis"
"""
        py_file.write_text(content)

        reader = PythonFileReader()
        # Should still return content even with syntax errors
        extracted = reader.extract_content(str(py_file))

        assert extracted == content


class TestTextFileReader:
    """Test TextFileReader functionality."""

    def test_can_read_text_file(self):
        """Test that TextFileReader can read .txt files."""
        reader = TextFileReader()

        assert reader.can_read("test.txt")
        assert reader.can_read("TEST.TXT")
        assert not reader.can_read("test.py")

    def test_extract_text_content(self, temp_dir):
        """Test extracting content from text file."""
        txt_file = temp_dir / "test.txt"
        content = "This is a test file.\n\nWith multiple paragraphs."
        txt_file.write_text(content)

        reader = TextFileReader()
        extracted = reader.extract_content(str(txt_file))

        assert extracted == content


class TestFileReaderFactory:
    """Test FileReaderFactory functionality."""

    def test_get_python_reader(self):
        """Test getting reader for Python file."""
        factory = FileReaderFactory()
        reader = factory.get_reader("test.py")

        assert isinstance(reader, PythonFileReader)

    def test_get_text_reader(self):
        """Test getting reader for text file."""
        factory = FileReaderFactory()
        reader = factory.get_reader("test.txt")

        assert isinstance(reader, TextFileReader)

    def test_unsupported_file_type(self):
        """Test error for unsupported file type."""
        factory = FileReaderFactory()

        with pytest.raises(FileProcessingError) as exc_info:
            factory.get_reader("test.xyz")

        assert exc_info.value.error_type == "no_reader_available"


class TestContentExtractor:
    """Test ContentExtractor functionality."""

    def test_extract_and_chunk_python_file(self, temp_dir):
        """Test extracting and chunking Python file."""
        py_file = temp_dir / "test.py"
        content = '''def function1():
    """First function."""
    pass

def function2():
    """Second function."""
    pass

class TestClass:
    """Test class."""

    def method(self):
        pass
'''
        py_file.write_text(content)

        extractor = ContentExtractor(chunk_size=100, chunk_overlap=20)
        metadata, chunks = extractor.extract_and_chunk(str(py_file))

        assert metadata.file_name == "test.py"
        assert metadata.file_type == ".py"
        assert metadata.chunk_count == len(chunks)
        assert len(chunks) > 0

        # Check that chunks have proper structure
        for i, chunk in enumerate(chunks):
            assert chunk.document_id == metadata.id
            assert chunk.chunk_index == i
            assert len(chunk.content) > 0

    def test_extract_and_chunk_text_file(self, temp_dir):
        """Test extracting and chunking text file."""
        txt_file = temp_dir / "test.txt"
        content = """This is the first paragraph.

This is the second paragraph with more content.

This is the third paragraph that should be in a separate chunk."""
        txt_file.write_text(content)

        extractor = ContentExtractor(chunk_size=100, chunk_overlap=20)
        metadata, chunks = extractor.extract_and_chunk(str(txt_file))

        assert metadata.file_name == "test.txt"
        assert metadata.file_type == ".txt"
        assert metadata.chunk_count == len(chunks)
        assert len(chunks) > 0

        # Check that chunks have proper structure
        for i, chunk in enumerate(chunks):
            assert chunk.document_id == metadata.id
            assert chunk.chunk_index == i
            assert len(chunk.content) > 0

    def test_chunk_overlap(self, temp_dir):
        """Test that chunking creates proper overlap."""
        txt_file = temp_dir / "overlap_test.txt"
        # Create content with paragraph breaks that will definitely need multiple chunks
        paragraphs = []
        for i in range(10):
            sentences = ["This is sentence {} in paragraph {}.".format(j, i) for j in range(3)]
            paragraphs.append(" ".join(sentences))
        content = "\n\n".join(paragraphs)  # Much longer content with paragraph breaks
        txt_file.write_text(content)

        extractor = ContentExtractor(chunk_size=100, chunk_overlap=20)
        metadata, chunks = extractor.extract_and_chunk(str(txt_file))

        # Should have multiple chunks due to size
        assert len(chunks) > 1

        # Check that chunks are reasonable size
        for chunk in chunks:
            assert len(chunk.content) <= 200  # Allow some flexibility for overlap

    def test_file_processing_error_propagation(self, temp_dir):
        """Test that file processing errors are properly propagated."""
        extractor = ContentExtractor()

        with pytest.raises(FileProcessingError):
            extractor.extract_and_chunk("nonexistent.py")
