"""ContextLens MCP Server - Give your LLM glasses to understand meaning, not just read words."""

import asyncio
import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional

from fastmcp import FastMCP

from .config import Config
from .errors import (
    KnowledgeBaseError,
    ParameterValidationError,
    create_error_response,
    log_operation_failure,
    log_operation_start,
    log_operation_success,
    validate_file_path,
    validate_limit_parameter,
    validate_offset_parameter,
    validate_query_parameter,
)
from .services.document_service import DocumentService


def setup_file_logging(log_level: str = "INFO") -> None:
    """Configure logging to write only to files (not stdout).

    This ensures stdio remains clean for MCP protocol communication.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    import os
    
    # Use LOG_DIR env var if set, otherwise use a writable location
    if "LOG_DIR" in os.environ:
        log_path = Path(os.environ["LOG_DIR"]).expanduser()
    else:
        # Try current directory first, fall back to home directory if not writable
        try:
            log_path = Path("logs")
            log_path.mkdir(parents=True, exist_ok=True)
            # Test if writable
            test_file = log_path / ".write_test"
            test_file.touch()
            test_file.unlink()
        except (OSError, PermissionError):
            # Fall back to user's home directory
            log_path = Path.home() / ".context-lens" / "logs"
    
    log_path.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # File handler for all logs
    file_handler = logging.FileHandler(log_path / "mcp_knowledge_base.log")
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Error file handler
    error_handler = logging.FileHandler(log_path / "errors.log")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


# Setup file-only logging when module is imported
setup_file_logging()

logger = logging.getLogger(__name__)

# Initialize FastMCP server
# Semantic search knowledge base for AI assistants - add documents and search by meaning, not just keywords
mcp = FastMCP("Context Lens")

# Global document service instance and initialization lock
_document_service: Optional[DocumentService] = None
_initialization_lock = asyncio.Lock()


async def get_document_service() -> DocumentService:
    """Get or initialize the document service instance.

    Uses lazy initialization with thread-safe locking to ensure:
    - Fast server startup (< 1 second)
    - Resources loaded only on first tool invocation
    - Thread-safe initialization with double-check pattern

    Returns:
        Initialized DocumentService instance

    Raises:
        Exception: If initialization fails
    """
    global _document_service

    if _document_service is None:
        async with _initialization_lock:
            # Double-check pattern to prevent race conditions
            if _document_service is None:
                try:
                    logger.info("Initializing document service (lazy initialization)...")
                    config = Config.from_env()
                    _document_service = DocumentService(config)
                    await _document_service.initialize()
                    logger.info("Document service initialized successfully")
                except Exception as e:
                    logger.error(f"Failed to initialize document service: {e}", exc_info=True)
                    raise

    return _document_service


async def reset_document_service() -> None:
    """Reset the global document service instance for testing.

    This function is intended for use in test fixtures to ensure test isolation.
    It safely clears the global service instance using the initialization lock
    to prevent race conditions during concurrent access.

    Note: This is a test-only function and should not be used in production code.
    The function is idempotent and safe to call multiple times.
    """
    global _document_service

    async with _initialization_lock:
        logger.debug("Resetting document service for test isolation")
        _document_service = None


@mcp.tool()
async def add_document(file_path: str) -> Dict[str, Any]:
    """Adds a document or GitHub repository to the knowledge base.

    Supports local files, GitHub repositories, files, and directories.

    Args:
        file_path (str): Path to document file or GitHub URL

    Returns:
        dict: Success status and document metadata or error details
    """
    try:
        log_operation_start("add_document", file_path=file_path)

        validate_file_path(file_path)
        file_path = file_path.strip()

        doc_service = await get_document_service()
        result = await doc_service.add_document(file_path)

        if result.get("success"):
            log_operation_success(
                "add_document",
                file_path=file_path,
                document_id=result.get("document", {}).get("id"),
            )

        return result

    except ParameterValidationError as e:
        log_operation_failure("add_document", e, file_path=file_path)
        return e.to_dict()
    except KnowledgeBaseError as e:
        log_operation_failure("add_document", e, file_path=file_path)
        return e.to_dict()
    except Exception as e:
        log_operation_failure("add_document", e, file_path=file_path)
        return create_error_response(
            e, context={"file_path": file_path, "operation": "add_document"}
        )


@mcp.tool()
async def list_documents(limit: Optional[int] = 100, offset: int = 0) -> Dict[str, Any]:
    """Lists all documents in the knowledge base with pagination support.

    Args:
        limit (int, optional): Maximum number of documents to return. Default is 100
        offset (int, optional): Number of documents to skip for pagination. Default is 0

    Returns:
        dict: Success status and list of documents with pagination info
    """
    try:
        log_operation_start("list_documents", limit=limit, offset=offset)

        if limit == 0:
            limit = None

        validate_limit_parameter(limit, min_value=1, max_value=1000, parameter_name="limit")
        validate_offset_parameter(offset, max_value=100000)

        doc_service = await get_document_service()
        result = await doc_service.list_documents(limit=limit, offset=offset)

        if result.get("success"):
            log_operation_success(
                "list_documents",
                document_count=result.get("pagination", {}).get("returned_count", 0),
            )

        return result

    except ParameterValidationError as e:
        log_operation_failure("list_documents", e, limit=limit, offset=offset)
        return e.to_dict()
    except KnowledgeBaseError as e:
        log_operation_failure("list_documents", e, limit=limit, offset=offset)
        return e.to_dict()
    except Exception as e:
        log_operation_failure("list_documents", e, limit=limit, offset=offset)
        return create_error_response(
            e, context={"limit": limit, "offset": offset, "operation": "list_documents"}
        )


@mcp.tool()
async def search_documents(query: str, limit: int = 10) -> Dict[str, Any]:
    """Searches documents using semantic vector similarity to find relevant content.

    Uses AI embeddings to understand meaning, not just keywords. Finds related concepts
    even without exact word matches (e.g., "authentication" finds "login", "credentials").

    Args:
        query (str): Natural language search query (1-10,000 characters)
                    Examples: "How does authentication work?", "database connection patterns"
        limit (int, optional): Maximum number of results to return (1-100). Default is 10

    Returns:
        dict: Success status, ranked results with relevance scores (0.0-1.0), 
              content excerpts, document metadata, and search operation metadata
    """
    try:
        log_operation_start(
            "search_documents", query=query[:50] + "..." if len(query) > 50 else query, limit=limit
        )

        validate_query_parameter(query, min_length=1, max_length=10000)
        validate_limit_parameter(limit, min_value=1, max_value=100, parameter_name="limit")

        query = query.strip()

        # Capture start time for timing measurement
        start_time = time.perf_counter()

        doc_service = await get_document_service()
        result = await doc_service.search_documents(query=query, limit=limit)

        # Capture end time and calculate elapsed time in milliseconds
        end_time = time.perf_counter()
        search_time_ms = int((end_time - start_time) * 1000)

        # Enrich successful responses with search_metadata
        if result.get("success"):
            try:
                # Extract values from service response _search_stats
                search_stats = result.get("_search_stats", {})
                
                # Use fallback values if metadata fields are missing
                embedding_model = search_stats.get("embedding_model")
                if not embedding_model:
                    logger.warning("Embedding model name not available in search stats, using fallback")
                    embedding_model = "unknown"
                
                total_documents = search_stats.get("total_documents")
                if total_documents is None:
                    logger.warning("Total documents count not available in search stats, using fallback")
                    total_documents = -1
                
                # Create search_metadata dictionary with all required fields
                result["search_metadata"] = {
                    "query_processed": query,  # Already stripped above
                    "embedding_model": embedding_model,
                    "search_time_ms": search_time_ms,
                    "total_documents_searched": total_documents
                }
                
                # Remove internal _search_stats fields from response
                result.pop("_search_stats", None)
                
            except Exception as metadata_error:
                # Log warning for metadata collection failures
                logger.warning(
                    f"Failed to collect search metadata: {metadata_error}",
                    exc_info=True
                )
                # Ensure search operation succeeds even if metadata fails
                # Remove any partial metadata that might have been added
                result.pop("search_metadata", None)
                result.pop("_search_stats", None)
            
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
        return create_error_response(
            e, context={"query": query[:100], "limit": limit, "operation": "search_documents"}
        )


@mcp.tool()
async def remove_document(file_path: str) -> Dict[str, Any]:
    """Removes a document from the knowledge base.

    Args:
        file_path (str): Path of the document to remove

    Returns:
        dict: Success status and removal confirmation
    """
    try:
        log_operation_start("remove_document", file_path=file_path)

        validate_file_path(file_path)
        file_path = file_path.strip()

        doc_service = await get_document_service()
        result = await doc_service.remove_document(file_path)

        if result.get("success"):
            log_operation_success("remove_document", file_path=file_path)

        return result

    except ParameterValidationError as e:
        log_operation_failure("remove_document", e, file_path=file_path)
        return e.to_dict()
    except KnowledgeBaseError as e:
        log_operation_failure("remove_document", e, file_path=file_path)
        return e.to_dict()
    except Exception as e:
        log_operation_failure("remove_document", e, file_path=file_path)
        return create_error_response(
            e, context={"file_path": file_path, "operation": "remove_document"}
        )


@mcp.tool()
async def get_document_info(file_path: str) -> Dict[str, Any]:
    """Gets metadata and statistics about a document in the knowledge base.

    Args:
        file_path (str): Path of the document

    Returns:
        dict: Document metadata including size, type, and chunk count
    """
    try:
        log_operation_start("get_document_info", file_path=file_path)

        validate_file_path(file_path)
        file_path = file_path.strip()

        doc_service = await get_document_service()
        result = await doc_service.get_document_info(file_path)

        if result.get("success"):
            log_operation_success("get_document_info", file_path=file_path)

        return result

    except ParameterValidationError as e:
        log_operation_failure("get_document_info", e, file_path=file_path)
        return e.to_dict()
    except KnowledgeBaseError as e:
        log_operation_failure("get_document_info", e, file_path=file_path)
        return e.to_dict()
    except Exception as e:
        log_operation_failure("get_document_info", e, file_path=file_path)
        return create_error_response(
            e, context={"file_path": file_path, "operation": "get_document_info"}
        )


@mcp.tool()
async def clear_knowledge_base() -> Dict[str, Any]:
    """Removes all documents from the knowledge base.

    Returns:
        dict: Success status and count of documents removed
    """
    try:
        log_operation_start("clear_knowledge_base")

        doc_service = await get_document_service()
        result = await doc_service.clear_knowledge_base()

        if result.get("success"):
            log_operation_success(
                "clear_knowledge_base", documents_removed=result.get("documents_removed", 0)
            )

        return result

    except KnowledgeBaseError as e:
        log_operation_failure("clear_knowledge_base", e)
        return e.to_dict()
    except Exception as e:
        log_operation_failure("clear_knowledge_base", e)
        return create_error_response(e, context={"operation": "clear_knowledge_base"})


# Export the FastMCP app instance
app = mcp


if __name__ == "__main__":
    """Direct execution entry point for MCP Inspector compatibility.

    This allows running the server with:
        python -m context_lens.server

    FastMCP's run() method handles:
    - stdio transport setup
    - Signal handling
    - Server lifecycle management
    """
    logger.info("Starting Context Lens MCP Server in stdio mode...")
    mcp.run()
