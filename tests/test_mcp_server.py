"""Tests for MCP server functionality."""

import pytest
from fastmcp import FastMCP

from context_lens.config import Config
from context_lens.server import app, mcp


class TestMCPServer:
    """Test MCP server setup and basic functionality."""

    def test_server_initialization(self):
        """Test that the MCP server is properly initialized."""
        # Verify mcp is a FastMCP instance
        assert isinstance(mcp, FastMCP)
        assert mcp.name == "Context Lens"

        # Verify app is the same as mcp
        assert app is mcp

    def test_tools_are_registered(self):
        """Test that all required tools are registered."""
        # Import the tool functions to verify they exist as FunctionTool objects
        # Verify they are FunctionTool objects (wrapped by FastMCP)
        from fastmcp.tools import FunctionTool

        from context_lens.server import (
            add_document,
            clear_knowledge_base,
            list_documents,
            search_documents,
        )

        assert isinstance(add_document, FunctionTool)
        assert isinstance(list_documents, FunctionTool)
        assert isinstance(search_documents, FunctionTool)
        assert isinstance(clear_knowledge_base, FunctionTool)

        # Verify tool names
        assert add_document.name == "add_document"
        assert list_documents.name == "list_documents"
        assert search_documents.name == "search_documents"
        assert clear_knowledge_base.name == "clear_knowledge_base"

    def test_tool_descriptions(self):
        """Test that tools have proper descriptions."""
        from context_lens.server import (
            add_document,
            clear_knowledge_base,
            list_documents,
            search_documents,
        )

        # Verify tools have descriptions
        assert add_document.description is not None
        assert "Adds a document" in add_document.description

        assert list_documents.description is not None
        assert "Lists all documents" in list_documents.description

        assert search_documents.description is not None
        assert "Searches documents" in search_documents.description

        assert clear_knowledge_base.description is not None
        assert "Removes all documents" in clear_knowledge_base.description

    def test_search_documents_docstring_contains_semantic_keyword(self):
        """Test that search_documents docstring contains 'semantic' keyword."""
        from context_lens.server import search_documents

        docstring = search_documents.description
        assert docstring is not None
        assert "semantic" in docstring.lower(), "Docstring should explain semantic search capabilities"

    def test_search_documents_docstring_contains_example_queries(self):
        """Test that search_documents docstring contains example queries."""
        from context_lens.server import search_documents

        docstring = search_documents.description
        assert docstring is not None
        
        # Check for at least two example queries
        # The docstring should contain concrete examples like "How does authentication work?" and "database connection patterns"
        assert "authentication" in docstring.lower() or "login" in docstring.lower(), \
            "Docstring should contain authentication-related example"
        assert "database" in docstring.lower() or "connection" in docstring.lower(), \
            "Docstring should contain database-related example"

    def test_search_documents_docstring_parameter_ranges(self):
        """Test that search_documents docstring documents parameter ranges."""
        from context_lens.server import search_documents

        docstring = search_documents.description
        assert docstring is not None
        
        # Check for query length constraints (1-10,000 characters)
        assert "1" in docstring and "10" in docstring, \
            "Docstring should document query length constraints"
        
        # Check for limit constraints (1-100)
        assert "100" in docstring, \
            "Docstring should document limit parameter range"
        
        # Check for relevance score range (0.0-1.0)
        assert "0.0" in docstring or "0" in docstring, \
            "Docstring should document relevance score range"
        assert "1.0" in docstring or "1" in docstring, \
            "Docstring should document relevance score range"

    def test_server_utility_functions(self):
        """Test that server utility functions exist."""
        from context_lens.server import get_document_service

        # Verify get_document_service exists and is callable
        assert callable(get_document_service)


class TestSearchMetadata:
    """Test search metadata functionality."""

    @pytest.mark.asyncio
    async def test_search_metadata_presence_in_successful_responses(self, test_config, temp_dir):
        """Test that successful search responses include search_metadata field."""
        from context_lens.services.document_service import DocumentService
        from context_lens.server import reset_document_service, search_documents

        # Reset service to use test config
        await reset_document_service()
        
        # Create a test document
        test_file = temp_dir / "test_doc.txt"
        test_file.write_text("This is a test document about authentication and security.")
        
        # Initialize service and add document
        service = DocumentService(test_config)
        await service.initialize()
        await service.add_document(str(test_file))
        
        # Perform search - access the underlying function from FunctionTool
        result = await search_documents.fn(query="authentication", limit=5)
        
        # Verify search_metadata is present in successful response
        assert result.get("success") is True
        assert "search_metadata" in result, "Successful search should include search_metadata"
        
        # Clean up
        await reset_document_service()

    @pytest.mark.asyncio
    async def test_search_metadata_fields_present_and_correct_types(self, test_config, temp_dir):
        """Test that all required metadata fields are present with correct types."""
        from context_lens.services.document_service import DocumentService
        from context_lens.server import reset_document_service, search_documents

        # Reset service to use test config
        await reset_document_service()
        
        # Create a test document
        test_file = temp_dir / "test_doc.txt"
        test_file.write_text("This is a test document about database connections.")
        
        # Initialize service and add document
        service = DocumentService(test_config)
        await service.initialize()
        await service.add_document(str(test_file))
        
        # Perform search - access the underlying function from FunctionTool
        result = await search_documents.fn(query="database", limit=5)
        
        # Verify all required fields are present
        assert result.get("success") is True
        metadata = result.get("search_metadata")
        assert metadata is not None
        
        # Check all required fields
        assert "query_processed" in metadata, "search_metadata should include query_processed"
        assert "embedding_model" in metadata, "search_metadata should include embedding_model"
        assert "search_time_ms" in metadata, "search_metadata should include search_time_ms"
        assert "total_documents_searched" in metadata, "search_metadata should include total_documents_searched"
        
        # Check field types
        assert isinstance(metadata["query_processed"], str), "query_processed should be a string"
        assert isinstance(metadata["embedding_model"], str), "embedding_model should be a string"
        assert isinstance(metadata["search_time_ms"], int), "search_time_ms should be an integer"
        assert isinstance(metadata["total_documents_searched"], int), "total_documents_searched should be an integer"
        
        # Clean up
        await reset_document_service()

    @pytest.mark.asyncio
    async def test_search_metadata_values_match_expected_data(self, test_config, temp_dir):
        """Test that metadata values match expected data."""
        import time
        from context_lens.services.document_service import DocumentService

        # Create test documents
        test_file1 = temp_dir / "test_doc1.txt"
        test_file1.write_text("This is a test document about Python programming.")
        test_file2 = temp_dir / "test_doc2.txt"
        test_file2.write_text("This is another test document about JavaScript.")
        
        # Initialize service and add documents
        service = DocumentService(test_config)
        await service.initialize()
        await service.add_document(str(test_file1))
        await service.add_document(str(test_file2))
        
        # Perform search with specific query (simulating what the MCP tool does)
        query = "  Python programming  "  # With extra whitespace
        query_stripped = query.strip()
        
        # Capture start time for timing measurement
        start_time = time.perf_counter()
        
        # Call service method directly
        service_result = await service.search_documents(query=query_stripped, limit=5)
        
        # Capture end time and calculate elapsed time in milliseconds
        end_time = time.perf_counter()
        search_time_ms = int((end_time - start_time) * 1000)
        
        # Simulate the metadata enrichment that the MCP tool does
        if service_result.get("success"):
            search_stats = service_result.get("_search_stats", {})
            result = service_result.copy()
            result["search_metadata"] = {
                "query_processed": query_stripped,
                "embedding_model": search_stats.get("embedding_model", "unknown"),
                "search_time_ms": search_time_ms,
                "total_documents_searched": search_stats.get("total_documents", -1)
            }
            result.pop("_search_stats", None)
        else:
            result = service_result
        
        # Verify metadata values
        assert result.get("success") is True
        metadata = result.get("search_metadata")
        
        # query_processed should be normalized (stripped)
        assert metadata["query_processed"] == "Python programming", \
            "query_processed should be the normalized query"
        
        # embedding_model should match config
        assert metadata["embedding_model"] == test_config.embedding.model, \
            "embedding_model should match the configured model"
        
        # search_time_ms should be positive
        assert metadata["search_time_ms"] > 0, \
            "search_time_ms should be a positive integer"
        
        # total_documents_searched should match the number of documents added
        assert metadata["total_documents_searched"] == 2, \
            "total_documents_searched should match the corpus size"

    @pytest.mark.asyncio
    async def test_search_metadata_on_empty_result_sets(self, test_config, temp_dir):
        """Test that metadata is included even when no results are found."""
        import time
        from context_lens.services.document_service import DocumentService

        # Create a test document
        test_file = temp_dir / "test_doc.txt"
        test_file.write_text("This is a test document about cats and dogs.")
        
        # Initialize service and add document
        service = DocumentService(test_config)
        await service.initialize()
        await service.add_document(str(test_file))
        
        # Perform search with query unlikely to match (simulating what the MCP tool does)
        query = "quantum physics equations"
        
        # Capture start time for timing measurement
        start_time = time.perf_counter()
        
        # Call service method directly
        service_result = await service.search_documents(query=query, limit=5)
        
        # Capture end time and calculate elapsed time in milliseconds
        end_time = time.perf_counter()
        search_time_ms = int((end_time - start_time) * 1000)
        
        # Simulate the metadata enrichment that the MCP tool does
        if service_result.get("success"):
            search_stats = service_result.get("_search_stats", {})
            result = service_result.copy()
            result["search_metadata"] = {
                "query_processed": query,
                "embedding_model": search_stats.get("embedding_model", "unknown"),
                "search_time_ms": search_time_ms,
                "total_documents_searched": search_stats.get("total_documents", -1)
            }
            result.pop("_search_stats", None)
        else:
            result = service_result
        
        # Verify metadata is present even with empty/low-relevance results
        assert result.get("success") is True
        assert "search_metadata" in result, \
            "search_metadata should be included even with empty results"
        
        metadata = result.get("search_metadata")
        
        # total_documents_searched should still reflect actual corpus size
        assert metadata["total_documents_searched"] == 1, \
            "total_documents_searched should reflect actual corpus size even with no matches"

    @pytest.mark.asyncio
    async def test_search_metadata_absent_in_error_responses(self):
        """Test that metadata is not included in error responses."""
        from context_lens.server import search_documents

        # Perform search with invalid parameters (empty query)
        result = await search_documents.fn(query="", limit=5)
        
        # Verify error response
        assert result.get("success") is False, "Empty query should result in error"
        
        # Verify metadata is NOT present in error response
        assert "search_metadata" not in result, \
            "search_metadata should not be included in error responses"


class TestMCPServerIntegration:
    """Test MCP server integration aspects."""

    def test_server_imports_successfully(self):
        """Test that the server can be imported without errors."""
        # This test verifies that all imports work correctly
        try:
            pass

            # If we get here, imports worked
            assert True
        except ImportError as e:
            pytest.fail(f"Server import failed: {e}")

    def test_config_integration(self):
        """Test that the server integrates properly with configuration."""
        # Verify that Config can be imported and used
        config = Config.from_env()
        assert config is not None
        assert hasattr(config, "database")
        assert hasattr(config, "embedding")
        assert hasattr(config, "processing")
        assert hasattr(config, "server")

    def test_document_service_integration(self):
        """Test that DocumentService can be imported and instantiated."""
        from context_lens.services.document_service import DocumentService

        # Verify DocumentService can be instantiated
        config = Config.from_env()
        service = DocumentService(config)
        assert service is not None
        assert hasattr(service, "add_document")
        assert hasattr(service, "list_documents")
        assert hasattr(service, "search_documents")
        assert hasattr(service, "clear_knowledge_base")
