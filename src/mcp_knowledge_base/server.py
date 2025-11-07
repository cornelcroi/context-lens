"""Main MCP server entry point."""

import logging
from typing import Dict, Any, Optional

from fastmcp import FastMCP

from .services.document_service import DocumentService
from .config import Config
from .errors import (
    validate_file_path,
    validate_query_parameter,
    validate_limit_parameter,
    validate_offset_parameter,
    create_error_response,
    log_operation_start,
    log_operation_success,
    log_operation_failure,
    ParameterValidationError,
    KnowledgeBaseError
)

logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("Knowledge Base Server")

# Global document service instance
_document_service: Optional[DocumentService] = None


async def get_document_service() -> DocumentService:
    """Get or initialize the document service instance."""
    global _document_service
    
    if _document_service is None:
        config = Config.from_env()
        _document_service = DocumentService(config)
        await _document_service.initialize()
        logger.info("Document service initialized for MCP server")
    
    return _document_service


@mcp.tool()
async def add_document(file_path: str) -> Dict[str, Any]:
    """Add a document to the knowledge base.
    
    Args:
        file_path: Path to the document file (.py or .txt)
        
    Returns:
        Dictionary containing success status and document metadata or error details
    """
    try:
        log_operation_start("add_document", file_path=file_path)
        
        # Validate input parameters using centralized validation
        validate_file_path(file_path)
        file_path = file_path.strip()
        
        # Get document service and add document
        doc_service = await get_document_service()
        result = await doc_service.add_document(file_path)
        
        if result.get("success"):
            log_operation_success("add_document", file_path=file_path, 
                                document_id=result.get("document", {}).get("id"))
        
        return result
        
    except ParameterValidationError as e:
        log_operation_failure("add_document", e, file_path=file_path)
        return e.to_dict()
    except KnowledgeBaseError as e:
        log_operation_failure("add_document", e, file_path=file_path)
        return e.to_dict()
    except Exception as e:
        log_operation_failure("add_document", e, file_path=file_path)
        return create_error_response(e, context={"file_path": file_path, "operation": "add_document"})


@mcp.tool()
async def list_documents(limit: Optional[int] = 100, offset: int = 0) -> Dict[str, Any]:
    """List all documents in the knowledge base with pagination support.
    
    Args:
        limit: Maximum number of documents to return (default: 100, None for no limit)
        offset: Number of documents to skip for pagination (default: 0)
        
    Returns:
        Dictionary containing success status and list of documents or error details
    """
    try:
        log_operation_start("list_documents", limit=limit, offset=offset)
        
        # Validate input parameters using centralized validation
        # Convert 0 to None for no limit
        if limit == 0:
            limit = None
        
        validate_limit_parameter(limit, min_value=1, max_value=1000, parameter_name="limit")
        validate_offset_parameter(offset, max_value=100000)
        
        # Get document service and list documents
        doc_service = await get_document_service()
        result = await doc_service.list_documents(limit=limit, offset=offset)
        
        if result.get("success"):
            log_operation_success("list_documents", 
                                document_count=result.get("pagination", {}).get("returned_count", 0))
        
        return result
        
    except ParameterValidationError as e:
        log_operation_failure("list_documents", e, limit=limit, offset=offset)
        return e.to_dict()
    except KnowledgeBaseError as e:
        log_operation_failure("list_documents", e, limit=limit, offset=offset)
        return e.to_dict()
    except Exception as e:
        log_operation_failure("list_documents", e, limit=limit, offset=offset)
        return create_error_response(e, context={"limit": limit, "offset": offset, "operation": "list_documents"})


@mcp.tool()
async def search_documents(query: str, limit: int = 10) -> Dict[str, Any]:
    """Search documents in the knowledge base using vector similarity search.
    
    Args:
        query: Search query text
        limit: Maximum number of results to return (default: 10)
        
    Returns:
        Dictionary containing success status and search results or error details
    """
    try:
        log_operation_start("search_documents", query=query[:50] + "..." if len(query) > 50 else query, 
                          limit=limit)
        
        # Validate input parameters using centralized validation
        validate_query_parameter(query, min_length=1, max_length=10000)
        validate_limit_parameter(limit, min_value=1, max_value=100, parameter_name="limit")
        
        query = query.strip()
        
        # Get document service and search documents
        doc_service = await get_document_service()
        result = await doc_service.search_documents(query=query, limit=limit)
        
        if result.get("success"):
            log_operation_success("search_documents", result_count=result.get("result_count", 0))
        
        return result
        
    except ParameterValidationError as e:
        log_operation_failure("search_documents", e, query=query[:50], limit=limit)
        return e.to_dict()
    except KnowledgeBaseError as e:
        log_operation_failure("search_documents", e, query=query[:50], limit=limit)
        return e.to_dict()
    except Exception as e:
        log_operation_failure("search_documents", e, query=query[:50], limit=limit)
        return create_error_response(e, context={"query": query[:100], "limit": limit, "operation": "search_documents"})


@mcp.tool()
async def clear_knowledge_base() -> Dict[str, Any]:
    """Clear all documents from the knowledge base.
    
    Returns:
        Dictionary containing success status and clear result or error details
    """
    try:
        log_operation_start("clear_knowledge_base")
        
        # Get document service and clear knowledge base
        doc_service = await get_document_service()
        result = await doc_service.clear_knowledge_base()
        
        if result.get("success"):
            log_operation_success("clear_knowledge_base", 
                                documents_removed=result.get("documents_removed", 0))
        
        return result
        
    except KnowledgeBaseError as e:
        log_operation_failure("clear_knowledge_base", e)
        return e.to_dict()
    except Exception as e:
        log_operation_failure("clear_knowledge_base", e)
        return create_error_response(e, context={"operation": "clear_knowledge_base"})


# Additional utility functions for server management
async def initialize_server() -> None:
    """Initialize the MCP server and its components."""
    try:
        logger.info("Initializing MCP Knowledge Base Server...")
        
        # Initialize document service
        await get_document_service()
        
        logger.info("MCP Knowledge Base Server initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize MCP server: {e}")
        raise


async def cleanup_server() -> None:
    """Clean up server resources."""
    global _document_service
    
    try:
        logger.info("Cleaning up MCP Knowledge Base Server...")
        
        if _document_service:
            await _document_service.cleanup()
            _document_service = None
        
        logger.info("MCP Knowledge Base Server cleanup completed")
        
    except Exception as e:
        logger.error(f"Error during server cleanup: {e}")


# Export the FastMCP app instance
app = mcp