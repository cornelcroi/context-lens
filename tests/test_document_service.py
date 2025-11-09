"""Tests for the DocumentService class."""

import pytest

from context_lens.config import (
    Config,
    DatabaseConfig,
    EmbeddingConfig,
    ProcessingConfig,
    ServerConfig,
)
from context_lens.services.document_service import DocumentService


class TestDocumentService:
    """Test cases for DocumentService."""

    @pytest.fixture
    async def document_service(self, test_config):
        """Create and initialize DocumentService instance."""
        service = DocumentService(test_config)
        await service.initialize()
        yield service
        await service.cleanup()

    @pytest.fixture
    def sample_python_file(self, temp_dir):
        """Create a sample Python file for testing."""
        py_file = temp_dir / "sample.py"
        content = '''def hello_world():
    """A simple hello world function."""
    return "Hello, World!"

class Calculator:
    """A simple calculator class."""

    def add(self, a, b):
        """Add two numbers."""
        return a + b

    def multiply(self, a, b):
        """Multiply two numbers."""
        return a * b
'''
        py_file.write_text(content)
        return str(py_file)

    @pytest.fixture
    def sample_text_file(self, temp_dir):
        """Create a sample text file for testing."""
        txt_file = temp_dir / "sample.txt"
        content = """This is a sample text document.

It contains multiple paragraphs to test the chunking functionality.

The document service should be able to process this file and create appropriate chunks for embedding generation.

Each paragraph should be processed correctly and stored in the vector database."""
        txt_file.write_text(content)
        return str(txt_file)

    @pytest.mark.asyncio
    async def test_initialization(self, test_config):
        """Test DocumentService initialization."""
        service = DocumentService(test_config)
        assert not service._initialized

        await service.initialize()
        assert service._initialized

        await service.cleanup()
        assert not service._initialized

    @pytest.mark.asyncio
    async def test_add_document_python_file(self, document_service, sample_python_file):
        """Test adding a Python document to the knowledge base."""
        result = await document_service.add_document(sample_python_file)

        assert result["success"] is True
        assert "document" in result
        assert result["document"]["file_name"] == "sample.py"
        assert result["document"]["file_type"] == ".py"
        assert result["document"]["chunk_count"] > 0
        assert "message" in result

    @pytest.mark.asyncio
    async def test_add_document_text_file(self, document_service, sample_text_file):
        """Test adding a text document to the knowledge base."""
        result = await document_service.add_document(sample_text_file)

        assert result["success"] is True
        assert "document" in result
        assert result["document"]["file_name"] == "sample.txt"
        assert result["document"]["file_type"] == ".txt"
        assert result["document"]["chunk_count"] > 0
        assert "message" in result

    @pytest.mark.asyncio
    async def test_add_nonexistent_document(self, document_service):
        """Test adding a non-existent document."""
        result = await document_service.add_document("nonexistent.py")

        assert result["success"] is False
        assert result["error_type"] == "file_not_found"
        assert "error_message" in result

    @pytest.mark.asyncio
    async def test_add_unsupported_document(self, document_service, temp_dir):
        """Test adding an unsupported document type."""
        unsupported_file = temp_dir / "test.xyz"
        unsupported_file.write_text("content")

        result = await document_service.add_document(str(unsupported_file))

        assert result["success"] is False
        assert result["error_type"] == "no_reader_available"

    @pytest.mark.asyncio
    async def test_list_documents_empty(self, document_service):
        """Test listing documents when knowledge base is empty."""
        result = await document_service.list_documents()

        assert result["success"] is True
        assert result["documents"] == []
        assert result["pagination"]["total_count"] == 0

    @pytest.mark.asyncio
    async def test_list_documents_with_content(
        self, document_service, sample_python_file, sample_text_file
    ):
        """Test listing documents after adding some."""
        # Add documents
        await document_service.add_document(sample_python_file)
        await document_service.add_document(sample_text_file)

        # List documents
        result = await document_service.list_documents()

        assert result["success"] is True
        assert len(result["documents"]) == 2
        assert result["pagination"]["total_count"] == 2

        # Check document structure
        for doc in result["documents"]:
            assert "id" in doc
            assert "file_name" in doc
            assert "file_type" in doc
            assert "chunk_count" in doc

    @pytest.mark.asyncio
    async def test_list_documents_pagination(
        self, document_service, sample_python_file, sample_text_file
    ):
        """Test document listing with pagination."""
        # Add documents
        await document_service.add_document(sample_python_file)
        await document_service.add_document(sample_text_file)

        # Test limit
        result = await document_service.list_documents(limit=1)
        assert result["success"] is True
        assert len(result["documents"]) == 1
        assert result["pagination"]["total_count"] == 2

        # Test offset
        result = await document_service.list_documents(limit=1, offset=1)
        assert result["success"] is True
        assert len(result["documents"]) == 1
        assert result["pagination"]["offset"] == 1

    @pytest.mark.asyncio
    async def test_search_documents_empty(self, document_service):
        """Test searching when knowledge base is empty."""
        result = await document_service.search_documents("test query")

        assert result["success"] is True
        assert result["results"] == []
        assert result["result_count"] == 0

    @pytest.mark.asyncio
    async def test_search_documents_with_content(self, document_service, sample_python_file):
        """Test searching documents after adding content."""
        # Add document
        await document_service.add_document(sample_python_file)

        # Search for relevant content
        result = await document_service.search_documents("hello world function")

        assert result["success"] is True
        assert len(result["results"]) > 0

        # Check result structure
        for search_result in result["results"]:
            assert "document_id" in search_result
            assert "document_path" in search_result
            assert "relevance_score" in search_result
            assert "content_excerpt" in search_result
            assert "metadata" in search_result

    @pytest.mark.asyncio
    async def test_search_documents_empty_query(self, document_service):
        """Test searching with empty query."""
        result = await document_service.search_documents("")

        assert result["success"] is False
        assert result["error_type"] == "invalid_query"

    @pytest.mark.asyncio
    async def test_search_documents_with_limit(
        self, document_service, sample_python_file, sample_text_file
    ):
        """Test searching with result limit."""
        # Add documents
        await document_service.add_document(sample_python_file)
        await document_service.add_document(sample_text_file)

        # Search with limit
        result = await document_service.search_documents("function", limit=1)

        assert result["success"] is True
        assert len(result["results"]) <= 1

    @pytest.mark.asyncio
    async def test_clear_knowledge_base_empty(self, document_service):
        """Test clearing empty knowledge base."""
        result = await document_service.clear_knowledge_base()

        assert result["success"] is True
        assert result["documents_removed"] == 0

    @pytest.mark.asyncio
    async def test_clear_knowledge_base_with_content(
        self, document_service, sample_python_file, sample_text_file
    ):
        """Test clearing knowledge base with content."""
        # Add documents
        await document_service.add_document(sample_python_file)
        await document_service.add_document(sample_text_file)

        # Verify documents exist
        list_result = await document_service.list_documents()
        assert len(list_result["documents"]) == 2

        # Clear knowledge base
        clear_result = await document_service.clear_knowledge_base()

        assert clear_result["success"] is True
        assert clear_result["documents_removed"] == 2

        # Verify knowledge base is empty
        list_result = await document_service.list_documents()
        assert len(list_result["documents"]) == 0

    @pytest.mark.asyncio
    async def test_get_document_by_id(self, document_service, sample_python_file):
        """Test getting document by ID."""
        # Add document
        add_result = await document_service.add_document(sample_python_file)
        document_id = add_result["document"]["id"]

        # Get document by ID
        document = await document_service.get_document_by_id(document_id)

        assert document is not None
        assert document["id"] == document_id
        assert document["file_name"] == "sample.py"

    @pytest.mark.asyncio
    async def test_get_document_by_id_nonexistent(self, document_service):
        """Test getting non-existent document by ID."""
        document = await document_service.get_document_by_id("nonexistent-id")
        assert document is None

    @pytest.mark.asyncio
    async def test_get_statistics(self, document_service, sample_python_file):
        """Test getting knowledge base statistics."""
        # Get initial statistics
        stats = await document_service.get_statistics()
        assert stats["document_count"] == 0
        assert "embedding_model" in stats
        assert "chunk_size" in stats

        # Add document and check updated statistics
        await document_service.add_document(sample_python_file)
        stats = await document_service.get_statistics()
        assert stats["document_count"] == 1

    @pytest.mark.asyncio
    async def test_document_update_same_path(self, document_service, sample_python_file):
        """Test updating document with same file path."""
        # Add document first time
        result1 = await document_service.add_document(sample_python_file)
        assert result1["success"] is True

        # Verify one document exists
        list_result = await document_service.list_documents()
        assert len(list_result["documents"]) == 1

        # Add same document again (should update)
        result2 = await document_service.add_document(sample_python_file)
        assert result2["success"] is True

        # Should still have only one document
        list_result = await document_service.list_documents()
        assert len(list_result["documents"]) == 1

    @pytest.mark.asyncio
    async def test_service_not_initialized_error(self, test_config):
        """Test that operations fail when service is not initialized."""
        service = DocumentService(test_config)

        with pytest.raises(RuntimeError, match="not initialized"):
            await service.add_document("test.py")

        with pytest.raises(RuntimeError, match="not initialized"):
            await service.list_documents()

        with pytest.raises(RuntimeError, match="not initialized"):
            await service.search_documents("query")

        with pytest.raises(RuntimeError, match="not initialized"):
            await service.clear_knowledge_base()


# Integration test that requires actual model loading (marked as slow)
@pytest.mark.slow
class TestDocumentServiceIntegration:
    """Integration tests for DocumentService with real embedding model."""

    @pytest.mark.asyncio
    async def test_full_workflow_with_real_embeddings(self, temp_dir):
        """Test complete workflow with real embedding generation."""
        # Create test config with real model
        config = Config(
            database=DatabaseConfig(
                path=str(temp_dir / "integration_test.db"), table_prefix="test_"
            ),
            embedding=EmbeddingConfig(
                model="sentence-transformers/all-MiniLM-L6-v2", cache_dir=str(temp_dir / "models")
            ),
            processing=ProcessingConfig(chunk_size=200, chunk_overlap=50),
            server=ServerConfig(name="test-integration-server", log_level="DEBUG"),
        )

        # Create test files
        py_file = temp_dir / "integration_test.py"
        py_content = '''def calculate_fibonacci(n):
    """Calculate the nth Fibonacci number."""
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

def factorial(n):
    """Calculate factorial of n."""
    if n <= 1:
        return 1
    return n * factorial(n-1)
'''
        py_file.write_text(py_content)

        txt_file = temp_dir / "integration_test.txt"
        txt_content = """Mathematical Functions

This document describes various mathematical functions including:

Fibonacci Sequence:
The Fibonacci sequence is a series of numbers where each number is the sum of the two preceding ones.

Factorial Function:
The factorial of a number n is the product of all positive integers less than or equal to n."""
        txt_file.write_text(txt_content)

        service = DocumentService(config)

        try:
            # Initialize service
            await service.initialize()

            # Add documents
            py_result = await service.add_document(str(py_file))
            assert py_result["success"] is True

            txt_result = await service.add_document(str(txt_file))
            assert txt_result["success"] is True

            # List documents
            list_result = await service.list_documents()
            assert len(list_result["documents"]) == 2

            # Search for Fibonacci
            search_result = await service.search_documents("Fibonacci sequence calculation")
            assert search_result["success"] is True
            assert len(search_result["results"]) > 0

            # Verify search results contain relevant content
            found_fibonacci = False
            for result in search_result["results"]:
                if "fibonacci" in result["content_excerpt"].lower():
                    found_fibonacci = True
                    break
            assert found_fibonacci, "Should find Fibonacci-related content"

            # Search for factorial
            search_result = await service.search_documents("factorial function")
            assert search_result["success"] is True
            assert len(search_result["results"]) > 0

            # Clear knowledge base
            clear_result = await service.clear_knowledge_base()
            assert clear_result["success"] is True
            assert clear_result["documents_removed"] == 2

            # Verify empty
            list_result = await service.list_documents()
            assert len(list_result["documents"]) == 0

        finally:
            await service.cleanup()
