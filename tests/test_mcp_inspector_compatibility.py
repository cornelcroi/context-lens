"""Test MCP Inspector compatibility and lazy initialization.

This test suite validates:
- Fast server startup (< 2 seconds)
- Lazy initialization of DocumentService
- All 6 tools work correctly
- Error handling with invalid inputs
- Thread-safe initialization
"""

from context_lens import server
import asyncio
import os
import sys
import time
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestMCPInspectorCompatibility:
    """Test suite for MCP Inspector compatibility."""

    @pytest.fixture(autouse=True)
    async def setup_and_teardown(self):
        """Setup and teardown for each test."""
        # Reset global state before each test
        server._document_service = None

        # Set test environment
        os.environ["LANCE_DB_PATH"] = "./test_inspector_compat.db"
        os.environ["LOG_LEVEL"] = "DEBUG"

        yield

        # Cleanup
        server._document_service = None
        db_path = Path("./test_inspector_compat.db")
        if db_path.exists():
            import shutil

            shutil.rmtree(db_path)

    @pytest.mark.asyncio
    async def test_fast_startup(self):
        """Test that server starts quickly without loading heavy resources.

        Requirement 2.1: Server SHALL complete initialization within 2 seconds
        """
        start_time = time.time()

        # Import and setup should be fast (no model loading)
        from context_lens import server as test_server

        elapsed = time.time() - start_time

        # Should be very fast (< 0.5 seconds typically)
        assert elapsed < 2.0, f"Server startup took {elapsed:.2f}s, expected < 2s"

        # Document service should not be initialized yet
        assert (
            test_server._document_service is None
        ), "Document service should not be initialized on import"

    @pytest.mark.asyncio
    async def test_lazy_initialization(self):
        """Test that DocumentService is initialized on first tool invocation.

        Requirement 2.2: Server SHALL initialize document service on first tool invocation
        Requirement 2.3: Server SHALL NOT load resources until first tool invocation
        """
        # Initially, document service should be None
        assert server._document_service is None

        # First call should trigger initialization
        start_time = time.time()
        doc_service = await server.get_document_service()
        init_time = time.time() - start_time

        # Initialization should take some time (model loading)
        assert init_time > 0.1, "Initialization should take measurable time"

        # Document service should now be initialized
        assert server._document_service is not None
        assert doc_service is server._document_service

        # Second call should be instant (already initialized)
        start_time = time.time()
        doc_service2 = await server.get_document_service()
        second_call_time = time.time() - start_time

        assert second_call_time < 0.1, "Second call should be instant"
        assert doc_service2 is doc_service, "Should return same instance"

    @pytest.mark.asyncio
    async def test_concurrent_initialization(self):
        """Test thread-safe initialization with concurrent calls.

        Ensures only one initialization occurs even with concurrent requests.
        """
        # Reset state
        server._document_service = None

        # Call get_document_service concurrently
        results = await asyncio.gather(
            server.get_document_service(),
            server.get_document_service(),
            server.get_document_service(),
        )

        # All should return the same instance
        assert all(r is results[0] for r in results), "All calls should return same instance"
        assert server._document_service is not None

    @pytest.mark.asyncio
    async def test_list_documents_tool(self):
        """Test list_documents tool works correctly.

        Requirement 1.2: Server SHALL display all registered tools
        Requirement 1.3: Server SHALL execute tools and return results
        """
        # Access the underlying function from the FunctionTool
        list_docs_func = server.list_documents.fn
        result = await list_docs_func(limit=10, offset=0)

        assert result is not None
        assert "success" in result
        assert result["success"] is True
        assert "documents" in result
        assert isinstance(result["documents"], list)

    @pytest.mark.asyncio
    async def test_add_document_tool(self):
        """Test add_document tool with valid file.

        Requirement 1.3: Server SHALL execute tools and return results
        """
        # Use README.md which should exist
        readme_path = "./README.md"
        if not Path(readme_path).exists():
            pytest.skip("README.md not found")

        add_doc_func = server.add_document.fn
        result = await add_doc_func(readme_path)

        assert result is not None
        assert "success" in result
        # May succeed or fail depending on file, but should return proper structure
        if result["success"]:
            assert "document" in result
            assert "id" in result["document"]

    @pytest.mark.asyncio
    async def test_search_documents_tool(self):
        """Test search_documents tool works correctly.

        Requirement 1.3: Server SHALL execute tools and return results
        """
        search_func = server.search_documents.fn
        result = await search_func(query="test", limit=5)

        assert result is not None
        assert "success" in result
        assert result["success"] is True
        assert "results" in result
        assert isinstance(result["results"], list)

    @pytest.mark.asyncio
    async def test_get_document_info_tool(self):
        """Test get_document_info tool with error handling.

        Requirement 2.4: Server SHALL return clear error messages
        """
        get_info_func = server.get_document_info.fn
        result = await get_info_func("nonexistent_file.txt")

        assert result is not None
        assert "success" in result
        # Should fail gracefully with error message
        if not result["success"]:
            assert "error_message" in result or "error" in result or "message" in result

    @pytest.mark.asyncio
    async def test_remove_document_tool(self):
        """Test remove_document tool with error handling.

        Requirement 2.4: Server SHALL return clear error messages
        """
        remove_func = server.remove_document.fn
        result = await remove_func("nonexistent_file.txt")

        assert result is not None
        assert "success" in result
        # Should fail gracefully with error message
        if not result["success"]:
            assert "error_message" in result or "error" in result or "message" in result

    @pytest.mark.asyncio
    async def test_clear_knowledge_base_tool(self):
        """Test clear_knowledge_base tool works correctly.

        Requirement 1.3: Server SHALL execute tools and return results
        """
        clear_func = server.clear_knowledge_base.fn
        result = await clear_func()

        assert result is not None
        assert "success" in result
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_error_handling_invalid_inputs(self):
        """Test error handling with invalid inputs.

        Requirement 2.4: Server SHALL return clear error messages
        """
        # Test with empty file path
        add_doc_func = server.add_document.fn
        result = await add_doc_func("")
        assert result is not None
        assert "success" in result
        assert result["success"] is False
        assert "error_message" in result or "error" in result or "message" in result

        # Test with invalid limit
        list_docs_func = server.list_documents.fn
        result = await list_docs_func(limit=-1)
        assert result is not None
        assert "success" in result
        assert result["success"] is False

        # Test with empty query
        search_func = server.search_documents.fn
        result = await search_func(query="", limit=5)
        assert result is not None
        assert "success" in result
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_initialization_error_handling(self):
        """Test that initialization errors are handled gracefully.

        Requirement 2.4: Server SHALL return clear error messages on initialization failure
        """
        # Reset state
        server._document_service = None

        # Set invalid config to trigger initialization error
        original_path = os.environ.get("LANCE_DB_PATH")
        os.environ["LANCE_DB_PATH"] = "/invalid/path/that/cannot/be/created"

        try:
            # This should fail but not crash
            with pytest.raises(Exception):
                await server.get_document_service()
        finally:
            # Restore original config
            if original_path:
                os.environ["LANCE_DB_PATH"] = original_path
            server._document_service = None


class TestFastMCPIntegration:
    """Test FastMCP integration and stdio compatibility."""

    def test_fastmcp_app_exists(self):
        """Test that FastMCP app instance is properly exported.

        Requirement 3.1: Server SHALL expose FastMCP app instance
        """
        assert hasattr(server, "app")
        assert hasattr(server, "mcp")
        assert server.app is server.mcp

    def test_tools_registered(self):
        """Test that all 6 tools are registered with FastMCP.

        Requirement 1.2: Server SHALL display all registered tools
        """
        # Check that all tool functions exist and are FunctionTool instances
        expected_tools = [
            "add_document",
            "list_documents",
            "search_documents",
            "remove_document",
            "get_document_info",
            "clear_knowledge_base",
        ]

        for tool_name in expected_tools:
            assert hasattr(server, tool_name), f"Tool {tool_name} not found in server module"
            tool = getattr(server, tool_name)
            # FastMCP wraps functions in FunctionTool objects
            assert hasattr(tool, "fn"), f"Tool {tool_name} is not a FunctionTool"

    def test_logging_configuration(self):
        """Test that logging is configured for file-only output.

        Requirement 4.4: Server SHALL write to log files while keeping stdio clean
        """
        import logging

        root_logger = logging.getLogger()

        # Should have file handlers
        file_handlers = [h for h in root_logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) > 0, "Should have file handlers configured"

        # Should not have stream handlers writing to stdout
        stream_handlers = [
            h
            for h in root_logger.handlers
            if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
        ]
        stdout_handlers = [h for h in stream_handlers if h.stream == sys.stdout]
        assert len(stdout_handlers) == 0, "Should not have stdout handlers"
