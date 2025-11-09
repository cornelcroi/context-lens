"""Tests for MCP server functionality."""

import pytest
from fastmcp import FastMCP

from codelens.server import mcp, app
from codelens.config import Config


class TestMCPServer:
    """Test MCP server setup and basic functionality."""
    
    def test_server_initialization(self):
        """Test that the MCP server is properly initialized."""
        # Verify mcp is a FastMCP instance
        assert isinstance(mcp, FastMCP)
        assert mcp.name == "CodeLens"
        
        # Verify app is the same as mcp
        assert app is mcp
    
    def test_tools_are_registered(self):
        """Test that all required tools are registered."""
        # Import the tool functions to verify they exist as FunctionTool objects
        from codelens.server import add_document, list_documents, search_documents, clear_knowledge_base
        
        # Verify they are FunctionTool objects (wrapped by FastMCP)
        from fastmcp.tools import FunctionTool
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
        from codelens.server import add_document, list_documents, search_documents, clear_knowledge_base
        
        # Verify tools have descriptions
        assert add_document.description is not None
        assert "Adds a document" in add_document.description
        
        assert list_documents.description is not None
        assert "Lists all documents" in list_documents.description
        
        assert search_documents.description is not None
        assert "Search documents" in search_documents.description
        
        assert clear_knowledge_base.description is not None
        assert "Clear all documents" in clear_knowledge_base.description
    
    def test_server_utility_functions(self):
        """Test that server utility functions exist."""
        from codelens.server import get_document_service
        
        # Verify get_document_service exists and is callable
        assert callable(get_document_service)


class TestMCPServerIntegration:
    """Test MCP server integration aspects."""
    
    def test_server_imports_successfully(self):
        """Test that the server can be imported without errors."""
        # This test verifies that all imports work correctly
        try:
            from codelens.server import (
                mcp, app, get_document_service,
                add_document, list_documents, search_documents, clear_knowledge_base
            )
            # If we get here, imports worked
            assert True
        except ImportError as e:
            pytest.fail(f"Server import failed: {e}")
    
    def test_config_integration(self):
        """Test that the server integrates properly with configuration."""
        # Verify that Config can be imported and used
        config = Config.from_env()
        assert config is not None
        assert hasattr(config, 'database')
        assert hasattr(config, 'embedding')
        assert hasattr(config, 'processing')
        assert hasattr(config, 'server')
    
    def test_document_service_integration(self):
        """Test that DocumentService can be imported and instantiated."""
        from codelens.services.document_service import DocumentService
        
        # Verify DocumentService can be instantiated
        config = Config.from_env()
        service = DocumentService(config)
        assert service is not None
        assert hasattr(service, 'add_document')
        assert hasattr(service, 'list_documents')
        assert hasattr(service, 'search_documents')
        assert hasattr(service, 'clear_knowledge_base')