"""Integration tests for Context Lens.

These tests verify end-to-end workflows including:
- Complete document ingestion workflow
- Search functionality with real document corpus
- Error scenarios and edge cases
- MCP tool integration with FastMCP framework
"""

from context_lens.config import (
    Config,
    DatabaseConfig,
    EmbeddingConfig,
    ProcessingConfig,
    ServerConfig,
)
import pytest

from context_lens.server import add_document as add_document_tool
from context_lens.server import clear_knowledge_base as clear_knowledge_base_tool
from context_lens.server import list_documents as list_documents_tool
from context_lens.server import search_documents as search_documents_tool

# Note: initialize_server and cleanup_server have been removed
# The server now uses lazy initialization - resources are initialized
# automatically on first tool invocation via get_document_service()


# Helper functions to call the FastMCP tools
async def add_document(file_path: str):
    """Call the add_document tool."""
    return await add_document_tool.fn(file_path)


async def list_documents(limit=100, offset=0):
    """Call the list_documents tool."""
    return await list_documents_tool.fn(limit=limit, offset=offset)


async def search_documents(query: str, limit=10):
    """Call the search_documents tool."""
    return await search_documents_tool.fn(query=query, limit=limit)


async def clear_knowledge_base():
    """Call the clear_knowledge_base tool."""
    return await clear_knowledge_base_tool.fn()


@pytest.fixture
async def integration_config(temp_dir):
    """Create integration test configuration with service reset."""
    from context_lens.server import reset_document_service

    # Reset service before each test
    await reset_document_service()

    config = Config(
        database=DatabaseConfig(
            path=str(temp_dir / "integration_kb.db"), table_prefix="integration_"
        ),
        embedding=EmbeddingConfig(
            model="sentence-transformers/all-MiniLM-L6-v2", cache_dir=str(temp_dir / "models")
        ),
        processing=ProcessingConfig(max_file_size_mb=5, chunk_size=500, chunk_overlap=100),
        server=ServerConfig(name="integration-test-server", log_level="DEBUG"),
    )
    return config


@pytest.fixture
def sample_documents(temp_dir):
    """Create a corpus of sample documents for testing."""
    documents = {}

    # Python file with functions
    py_file = temp_dir / "algorithms.py"
    py_content = '''"""Algorithm implementations for common problems."""

def binary_search(arr, target):
    """
    Perform binary search on a sorted array.

    Args:
        arr: Sorted array to search
        target: Value to find

    Returns:
        Index of target or -1 if not found
    """
    left, right = 0, len(arr) - 1

    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1

    return -1


def quicksort(arr):
    """
    Sort an array using quicksort algorithm.

    Args:
        arr: Array to sort

    Returns:
        Sorted array
    """
    if len(arr) <= 1:
        return arr

    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]

    return quicksort(left) + middle + quicksort(right)


class Graph:
    """Graph data structure with basic operations."""

    def __init__(self):
        """Initialize an empty graph."""
        self.adjacency_list = {}

    def add_vertex(self, vertex):
        """Add a vertex to the graph."""
        if vertex not in self.adjacency_list:
            self.adjacency_list[vertex] = []

    def add_edge(self, v1, v2):
        """Add an edge between two vertices."""
        self.add_vertex(v1)
        self.add_vertex(v2)
        self.adjacency_list[v1].append(v2)
        self.adjacency_list[v2].append(v1)
'''
    py_file.write_text(py_content)
    documents["algorithms"] = str(py_file)

    # Text file with documentation
    txt_file = temp_dir / "documentation.txt"
    txt_content = """Algorithm Documentation

Binary Search Algorithm:
Binary search is an efficient algorithm for finding an item from a sorted list of items.
It works by repeatedly dividing in half the portion of the list that could contain the item.
Time complexity: O(log n)
Space complexity: O(1)

Quicksort Algorithm:
Quicksort is a divide-and-conquer algorithm that works by selecting a pivot element
and partitioning the array around the pivot. It recursively sorts the sub-arrays.
Time complexity: O(n log n) average case, O(n²) worst case
Space complexity: O(log n)

Graph Data Structure:
A graph is a data structure consisting of vertices (nodes) and edges connecting them.
Graphs can be directed or undirected, weighted or unweighted.
Common operations include adding vertices, adding edges, and traversing the graph.

Applications:
- Binary search is used in database indexing and search operations
- Quicksort is widely used for general-purpose sorting
- Graphs are used in social networks, routing algorithms, and dependency resolution
"""
    txt_file.write_text(txt_content)
    documents["documentation"] = str(txt_file)

    # Another Python file with different content
    py_file2 = temp_dir / "data_structures.py"
    py_content2 = '''"""Data structure implementations."""

class Stack:
    """Stack implementation using a list."""

    def __init__(self):
        """Initialize an empty stack."""
        self.items = []

    def push(self, item):
        """Push an item onto the stack."""
        self.items.append(item)

    def pop(self):
        """Pop an item from the stack."""
        if not self.is_empty():
            return self.items.pop()
        raise IndexError("Pop from empty stack")

    def peek(self):
        """Return the top item without removing it."""
        if not self.is_empty():
            return self.items[-1]
        raise IndexError("Peek from empty stack")

    def is_empty(self):
        """Check if the stack is empty."""
        return len(self.items) == 0


class Queue:
    """Queue implementation using a list."""

    def __init__(self):
        """Initialize an empty queue."""
        self.items = []

    def enqueue(self, item):
        """Add an item to the rear of the queue."""
        self.items.insert(0, item)

    def dequeue(self):
        """Remove and return the front item."""
        if not self.is_empty():
            return self.items.pop()
        raise IndexError("Dequeue from empty queue")

    def is_empty(self):
        """Check if the queue is empty."""
        return len(self.items) == 0
'''
    py_file2.write_text(py_content2)
    documents["data_structures"] = str(py_file2)

    return documents


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""

    @pytest.mark.asyncio
    async def test_complete_document_ingestion_workflow(
        self, integration_config, sample_documents, temp_dir
    ):
        """Test the complete workflow of ingesting multiple documents."""
        # Set up environment for this test
        import os

        os.environ["LANCE_DB_PATH"] = str(temp_dir / "test_workflow.db")
        os.environ["EMBEDDING_CACHE_DIR"] = str(temp_dir / "models")

        try:
            # Initialize server
            pass  # await initialize_server() - No longer needed, lazy initialization

            # Add all documents
            results = []
            for doc_name, doc_path in sample_documents.items():
                result = await add_document(doc_path)
                results.append(result)
                assert (
                    result["success"] is True
                ), f"Failed to add {doc_name}: {result.get('error_message')}"
                assert "document" in result
                assert result["document"]["file_name"] in doc_path
                assert result["document"]["chunk_count"] > 0

            # Verify all documents were added
            assert len(results) == 3

            # List all documents
            list_result = await list_documents()
            assert list_result["success"] is True
            assert len(list_result["documents"]) == 3
            assert list_result["pagination"]["total_count"] == 3

            # Verify document metadata
            for doc in list_result["documents"]:
                assert "id" in doc
                assert "file_name" in doc
                assert "file_path" in doc
                assert "file_type" in doc
                assert "chunk_count" in doc
                assert "ingestion_timestamp" in doc

        finally:
            pass  # await cleanup_server() - No longer needed, lazy initialization

    @pytest.mark.asyncio
    async def test_document_update_workflow(self, integration_config, temp_dir):
        """Test updating an existing document."""
        import os

        os.environ["LANCE_DB_PATH"] = str(temp_dir / "test_update.db")
        os.environ["EMBEDDING_CACHE_DIR"] = str(temp_dir / "models")

        # Create initial document
        doc_file = temp_dir / "update_test.py"
        doc_file.write_text("def old_function():\n    pass")

        try:
            pass  # await initialize_server() - No longer needed, lazy initialization

            # Add document first time
            result1 = await add_document(str(doc_file))
            assert result1["success"] is True
            result1["document"]["id"]

            # Verify one document exists
            list_result = await list_documents()
            assert len(list_result["documents"]) == 1

            # Update the file content
            doc_file.write_text("def new_function():\n    return 'updated'")

            # Add same document again (should update)
            result2 = await add_document(str(doc_file))
            assert result2["success"] is True

            # Should still have only one document
            list_result = await list_documents()
            assert len(list_result["documents"]) == 1

        finally:
            pass  # await cleanup_server() - No longer needed, lazy initialization


class TestSearchFunctionality:
    """Test search functionality with real document corpus."""

    @pytest.mark.asyncio
    async def test_search_with_relevant_results(
        self, integration_config, sample_documents, temp_dir
    ):
        """Test searching for content that exists in documents."""
        import os

        os.environ["LANCE_DB_PATH"] = str(temp_dir / "test_search.db")
        os.environ["EMBEDDING_CACHE_DIR"] = str(temp_dir / "models")

        try:
            pass  # await initialize_server() - No longer needed, lazy initialization

            # Add documents
            for doc_path in sample_documents.values():
                await add_document(doc_path)

            # Search for binary search algorithm
            result = await search_documents("binary search algorithm sorted array")
            assert result["success"] is True
            assert len(result["results"]) > 0
            assert result["result_count"] > 0

            # Verify result structure
            for search_result in result["results"]:
                assert "document_id" in search_result
                assert "document_path" in search_result
                assert "relevance_score" in search_result
                assert "content_excerpt" in search_result
                assert "metadata" in search_result
                # Cosine similarity can range from -1 to 1
                assert -1 <= search_result["relevance_score"] <= 1

            # Verify relevant content is found
            found_binary_search = any(
                "binary" in r["content_excerpt"].lower() for r in result["results"]
            )
            assert found_binary_search, "Should find binary search related content"

        finally:
            pass  # await cleanup_server() - No longer needed, lazy initialization

    @pytest.mark.asyncio
    async def test_search_with_different_queries(
        self, integration_config, sample_documents, temp_dir
    ):
        """Test multiple search queries on the same corpus."""
        import os

        os.environ["LANCE_DB_PATH"] = str(temp_dir / "test_multi_search.db")
        os.environ["EMBEDDING_CACHE_DIR"] = str(temp_dir / "models")

        try:
            pass  # await initialize_server() - No longer needed, lazy initialization

            # Add documents
            for doc_path in sample_documents.values():
                await add_document(doc_path)

            # Test different search queries - just verify they return results
            # Semantic search may not always return exact matches
            queries = [
                "sorting algorithm",
                "graph data structure",
                "stack operations",
                "queue implementation",
            ]

            for query in queries:
                result = await search_documents(query)
                assert result["success"] is True
                assert len(result["results"]) > 0, f"No results for query: {query}"

                # Verify result structure
                for search_result in result["results"]:
                    assert "document_id" in search_result
                    assert "content_excerpt" in search_result
                    assert "relevance_score" in search_result

        finally:
            pass  # await cleanup_server() - No longer needed, lazy initialization

    @pytest.mark.asyncio
    async def test_search_with_limit(self, integration_config, sample_documents, temp_dir):
        """Test search result limiting."""
        import os

        os.environ["LANCE_DB_PATH"] = str(temp_dir / "test_search_limit.db")
        os.environ["EMBEDDING_CACHE_DIR"] = str(temp_dir / "models")

        try:
            pass  # await initialize_server() - No longer needed, lazy initialization

            # Add documents
            for doc_path in sample_documents.values():
                await add_document(doc_path)

            # Search with different limits
            result_5 = await search_documents("algorithm", limit=5)
            assert result_5["success"] is True
            assert len(result_5["results"]) <= 5

            result_2 = await search_documents("algorithm", limit=2)
            assert result_2["success"] is True
            assert len(result_2["results"]) <= 2

            result_1 = await search_documents("algorithm", limit=1)
            assert result_1["success"] is True
            assert len(result_1["results"]) == 1

        finally:
            pass  # await cleanup_server() - No longer needed, lazy initialization

    @pytest.mark.asyncio
    async def test_search_empty_knowledge_base(self, integration_config, temp_dir):
        """Test searching when knowledge base is empty."""
        import os

        os.environ["LANCE_DB_PATH"] = str(temp_dir / "test_search_empty.db")
        os.environ["EMBEDDING_CACHE_DIR"] = str(temp_dir / "models")

        try:
            pass  # await initialize_server() - No longer needed, lazy initialization

            # Search without adding any documents
            result = await search_documents("test query")
            assert result["success"] is True
            assert result["results"] == []
            assert result["result_count"] == 0

        finally:
            pass  # await cleanup_server() - No longer needed, lazy initialization


class TestErrorScenarios:
    """Test error scenarios and edge cases."""

    @pytest.mark.asyncio
    async def test_add_nonexistent_file(self, integration_config, temp_dir):
        """Test adding a file that doesn't exist."""
        import os

        os.environ["LANCE_DB_PATH"] = str(temp_dir / "test_error_nonexistent.db")
        os.environ["EMBEDDING_CACHE_DIR"] = str(temp_dir / "models")

        try:
            pass  # await initialize_server() - No longer needed, lazy initialization

            result = await add_document("/nonexistent/path/file.py")
            assert result["success"] is False
            assert result["error_type"] == "file_not_found"
            assert "error_message" in result

        finally:
            pass  # await cleanup_server() - No longer needed, lazy initialization

    @pytest.mark.asyncio
    async def test_add_unsupported_file_type(self, integration_config, temp_dir):
        """Test adding an unsupported file type."""
        import os

        os.environ["LANCE_DB_PATH"] = str(temp_dir / "test_error_unsupported.db")
        os.environ["EMBEDDING_CACHE_DIR"] = str(temp_dir / "models")

        # Create unsupported file
        unsupported_file = temp_dir / "test.xyz"
        unsupported_file.write_text("content")

        try:
            pass  # await initialize_server() - No longer needed, lazy initialization

            result = await add_document(str(unsupported_file))
            assert result["success"] is False
            assert result["error_type"] == "no_reader_available"

        finally:
            pass  # await cleanup_server() - No longer needed, lazy initialization

    @pytest.mark.asyncio
    async def test_add_empty_file(self, integration_config, temp_dir):
        """Test adding an empty file."""
        import os

        os.environ["LANCE_DB_PATH"] = str(temp_dir / "test_error_empty.db")
        os.environ["EMBEDDING_CACHE_DIR"] = str(temp_dir / "models")

        # Create empty file
        empty_file = temp_dir / "empty.py"
        empty_file.write_text("")

        try:
            pass  # await initialize_server() - No longer needed, lazy initialization

            result = await add_document(str(empty_file))
            # Empty files may be accepted with a warning or rejected
            # Check that either it succeeds with 0 chunks or fails with empty_content error
            if result["success"]:
                # If accepted, should have 0 chunks
                assert result["document"]["chunk_count"] == 0
            else:
                assert result["error_type"] in ["empty_content", "processing_error"]

        finally:
            pass  # await cleanup_server() - No longer needed, lazy initialization

    @pytest.mark.asyncio
    async def test_search_with_empty_query(self, integration_config, temp_dir):
        """Test searching with an empty query."""
        import os

        os.environ["LANCE_DB_PATH"] = str(temp_dir / "test_error_empty_query.db")
        os.environ["EMBEDDING_CACHE_DIR"] = str(temp_dir / "models")

        try:
            pass  # await initialize_server() - No longer needed, lazy initialization

            result = await search_documents("")
            assert result["success"] is False
            assert result["error_type"] == "invalid_parameter"

        finally:
            pass  # await cleanup_server() - No longer needed, lazy initialization

    @pytest.mark.asyncio
    async def test_search_with_whitespace_query(self, integration_config, temp_dir):
        """Test searching with whitespace-only query."""
        import os

        os.environ["LANCE_DB_PATH"] = str(temp_dir / "test_error_whitespace.db")
        os.environ["EMBEDDING_CACHE_DIR"] = str(temp_dir / "models")

        try:
            pass  # await initialize_server() - No longer needed, lazy initialization

            result = await search_documents("   ")
            assert result["success"] is False
            assert result["error_type"] == "invalid_parameter"

        finally:
            pass  # await cleanup_server() - No longer needed, lazy initialization

    @pytest.mark.asyncio
    async def test_invalid_limit_parameter(self, integration_config, temp_dir):
        """Test with invalid limit parameters."""
        import os

        os.environ["LANCE_DB_PATH"] = str(temp_dir / "test_error_limit.db")
        os.environ["EMBEDDING_CACHE_DIR"] = str(temp_dir / "models")

        try:
            pass  # await initialize_server() - No longer needed, lazy initialization

            # Test negative limit
            result = await search_documents("test", limit=-1)
            assert result["success"] is False
            assert result["error_type"] == "invalid_parameter"

            # Test limit too large
            result = await search_documents("test", limit=1000)
            assert result["success"] is False
            assert result["error_type"] == "invalid_parameter"

        finally:
            pass  # await cleanup_server() - No longer needed, lazy initialization

    @pytest.mark.asyncio
    async def test_invalid_offset_parameter(self, integration_config, temp_dir):
        """Test with invalid offset parameters."""
        import os

        os.environ["LANCE_DB_PATH"] = str(temp_dir / "test_error_offset.db")
        os.environ["EMBEDDING_CACHE_DIR"] = str(temp_dir / "models")

        try:
            pass  # await initialize_server() - No longer needed, lazy initialization

            # Test negative offset
            result = await list_documents(offset=-1)
            assert result["success"] is False
            assert result["error_type"] == "invalid_parameter"

        finally:
            pass  # await cleanup_server() - No longer needed, lazy initialization

    @pytest.mark.asyncio
    async def test_add_file_with_invalid_encoding(self, integration_config, temp_dir):
        """Test adding a file with invalid encoding."""
        import os

        os.environ["LANCE_DB_PATH"] = str(temp_dir / "test_error_encoding.db")
        os.environ["EMBEDDING_CACHE_DIR"] = str(temp_dir / "models")

        # Create file with binary content
        binary_file = temp_dir / "binary.py"
        binary_file.write_bytes(b"\x80\x81\x82\x83")

        try:
            pass  # await initialize_server() - No longer needed, lazy initialization

            result = await add_document(str(binary_file))
            # Should either succeed with encoding detection or fail gracefully
            assert "success" in result
            if not result["success"]:
                assert "error_type" in result
                assert "error_message" in result

        finally:
            pass  # await cleanup_server() - No longer needed, lazy initialization


class TestMCPToolIntegration:
    """Test MCP tool integration with FastMCP framework."""

    @pytest.mark.asyncio
    async def test_all_tools_callable(self, integration_config, temp_dir):
        """Test that all MCP tools are callable."""
        import os

        os.environ["LANCE_DB_PATH"] = str(temp_dir / "test_tools_callable.db")
        os.environ["EMBEDDING_CACHE_DIR"] = str(temp_dir / "models")

        try:
            pass  # await initialize_server() - No longer needed, lazy initialization

            # Test that all tools can be called
            # add_document
            test_file = temp_dir / "test.py"
            test_file.write_text("def test(): pass")
            result = await add_document(str(test_file))
            assert "success" in result

            # list_documents
            result = await list_documents()
            assert "success" in result

            # search_documents
            result = await search_documents("test")
            assert "success" in result

            # clear_knowledge_base
            result = await clear_knowledge_base()
            assert "success" in result

        finally:
            pass  # await cleanup_server() - No longer needed, lazy initialization

    @pytest.mark.asyncio
    async def test_tool_parameter_validation(self, integration_config, temp_dir):
        """Test that tools properly validate parameters."""
        import os

        os.environ["LANCE_DB_PATH"] = str(temp_dir / "test_param_validation.db")
        os.environ["EMBEDDING_CACHE_DIR"] = str(temp_dir / "models")

        try:
            pass  # await initialize_server() - No longer needed, lazy initialization

            # Test add_document with empty path
            result = await add_document("")
            assert result["success"] is False
            assert result["error_type"] == "invalid_parameter"

            # Test search_documents with empty query
            result = await search_documents("")
            assert result["success"] is False
            assert result["error_type"] == "invalid_parameter"

            # Test list_documents with invalid limit
            result = await list_documents(limit=-5)
            assert result["success"] is False
            assert result["error_type"] == "invalid_parameter"

        finally:
            pass  # await cleanup_server() - No longer needed, lazy initialization

    @pytest.mark.asyncio
    async def test_tool_error_responses(self, integration_config, temp_dir):
        """Test that tools return proper error responses."""
        import os

        os.environ["LANCE_DB_PATH"] = str(temp_dir / "test_error_responses.db")
        os.environ["EMBEDDING_CACHE_DIR"] = str(temp_dir / "models")

        try:
            pass  # await initialize_server() - No longer needed, lazy initialization

            # Test various error scenarios
            errors = []

            # File not found error
            result = await add_document("/nonexistent/file.py")
            errors.append(result)

            # Invalid query error
            result = await search_documents("")
            errors.append(result)

            # Invalid parameter error
            result = await list_documents(limit=-1)
            errors.append(result)

            # Verify all errors have proper structure
            for error in errors:
                assert error["success"] is False
                assert "error_type" in error
                assert "error_message" in error
                assert isinstance(error["error_message"], str)
                assert len(error["error_message"]) > 0

        finally:
            pass  # await cleanup_server() - No longer needed, lazy initialization


class TestPaginationAndLimits:
    """Test pagination and result limiting functionality."""

    @pytest.mark.asyncio
    async def test_list_documents_pagination(self, integration_config, sample_documents, temp_dir):
        """Test document listing with pagination."""
        import os

        os.environ["LANCE_DB_PATH"] = str(temp_dir / "test_pagination.db")
        os.environ["EMBEDDING_CACHE_DIR"] = str(temp_dir / "models")

        try:
            pass  # await initialize_server() - No longer needed, lazy initialization

            # Add documents
            for doc_path in sample_documents.values():
                await add_document(doc_path)

            # Test pagination
            # Get first page
            result_page1 = await list_documents(limit=2, offset=0)
            assert result_page1["success"] is True
            assert len(result_page1["documents"]) == 2
            assert result_page1["pagination"]["total_count"] == 3
            assert result_page1["pagination"]["offset"] == 0
            assert result_page1["pagination"]["returned_count"] == 2

            # Get second page
            result_page2 = await list_documents(limit=2, offset=2)
            assert result_page2["success"] is True
            assert len(result_page2["documents"]) == 1
            assert result_page2["pagination"]["total_count"] == 3
            assert result_page2["pagination"]["offset"] == 2
            assert result_page2["pagination"]["returned_count"] == 1

            # Verify different documents on each page
            page1_ids = {doc["id"] for doc in result_page1["documents"]}
            page2_ids = {doc["id"] for doc in result_page2["documents"]}
            assert len(page1_ids.intersection(page2_ids)) == 0

        finally:
            pass  # await cleanup_server() - No longer needed, lazy initialization

    @pytest.mark.asyncio
    async def test_list_documents_no_limit(self, integration_config, sample_documents, temp_dir):
        """Test listing all documents without limit."""
        import os

        os.environ["LANCE_DB_PATH"] = str(temp_dir / "test_no_limit.db")
        os.environ["EMBEDDING_CACHE_DIR"] = str(temp_dir / "models")

        try:
            pass  # await initialize_server() - No longer needed, lazy initialization

            # Add documents
            for doc_path in sample_documents.values():
                await add_document(doc_path)

            # List all documents (limit=None or 0)
            result = await list_documents(limit=None)
            assert result["success"] is True
            assert len(result["documents"]) == 3
            assert result["pagination"]["total_count"] == 3

        finally:
            pass  # await cleanup_server() - No longer needed, lazy initialization


class TestClearKnowledgeBase:
    """Test clearing the knowledge base."""

    @pytest.mark.asyncio
    async def test_clear_with_documents(self, integration_config, sample_documents, temp_dir):
        """Test clearing knowledge base with documents."""
        import os

        os.environ["LANCE_DB_PATH"] = str(temp_dir / "test_clear_with_docs.db")
        os.environ["EMBEDDING_CACHE_DIR"] = str(temp_dir / "models")

        try:
            pass  # await initialize_server() - No longer needed, lazy initialization

            # Add documents
            for doc_path in sample_documents.values():
                await add_document(doc_path)

            # Verify documents exist
            list_result = await list_documents()
            assert len(list_result["documents"]) == 3

            # Clear knowledge base
            clear_result = await clear_knowledge_base()
            assert clear_result["success"] is True
            assert clear_result["documents_removed"] == 3
            assert "message" in clear_result

            # Verify knowledge base is empty
            list_result = await list_documents()
            assert len(list_result["documents"]) == 0
            assert list_result["pagination"]["total_count"] == 0

            # Verify search returns no results
            search_result = await search_documents("algorithm")
            assert search_result["success"] is True
            assert len(search_result["results"]) == 0

        finally:
            pass  # await cleanup_server() - No longer needed, lazy initialization

    @pytest.mark.asyncio
    async def test_clear_empty_knowledge_base(self, integration_config, temp_dir):
        """Test clearing an already empty knowledge base."""
        import os

        os.environ["LANCE_DB_PATH"] = str(temp_dir / "test_clear_empty.db")
        os.environ["EMBEDDING_CACHE_DIR"] = str(temp_dir / "models")

        try:
            pass  # await initialize_server() - No longer needed, lazy initialization

            # Clear without adding any documents
            result = await clear_knowledge_base()
            assert result["success"] is True
            assert result["documents_removed"] == 0

        finally:
            pass  # await cleanup_server() - No longer needed, lazy initialization

    @pytest.mark.asyncio
    async def test_add_after_clear(self, integration_config, sample_documents, temp_dir):
        """Test adding documents after clearing."""
        import os

        os.environ["LANCE_DB_PATH"] = str(temp_dir / "test_add_after_clear.db")
        os.environ["EMBEDDING_CACHE_DIR"] = str(temp_dir / "models")

        try:
            pass  # await initialize_server() - No longer needed, lazy initialization

            # Add documents
            doc_path = list(sample_documents.values())[0]
            await add_document(doc_path)

            # Clear
            await clear_knowledge_base()

            # Add document again
            result = await add_document(doc_path)
            assert result["success"] is True

            # Verify document exists
            list_result = await list_documents()
            assert len(list_result["documents"]) == 1

        finally:
            pass  # await cleanup_server() - No longer needed, lazy initialization
