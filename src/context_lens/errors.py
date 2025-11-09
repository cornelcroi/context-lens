"""Centralized error handling and structured error responses for the MCP Knowledge Base Server."""

import logging
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ErrorCategory(str, Enum):
    """Categories of errors that can occur in the system."""

    # File-related errors
    FILE_NOT_FOUND = "file_not_found"
    FILE_ACCESS_DENIED = "file_access_denied"
    FILE_TOO_LARGE = "file_too_large"
    UNSUPPORTED_FILE_TYPE = "unsupported_file_type"
    FILE_READ_ERROR = "file_read_error"
    ENCODING_ERROR = "encoding_error"

    # Processing errors
    CONTENT_EXTRACTION_ERROR = "content_extraction_error"
    PYTHON_PROCESSING_ERROR = "python_processing_error"
    TEXT_PROCESSING_ERROR = "text_processing_error"
    CHUNKING_ERROR = "chunking_error"

    # Database errors
    DATABASE_CONNECTION_ERROR = "database_connection_error"
    DATABASE_INITIALIZATION_ERROR = "database_initialization_error"
    DATABASE_OPERATION_ERROR = "database_operation_error"
    SCHEMA_MISMATCH_ERROR = "schema_mismatch_error"

    # Embedding errors
    EMBEDDING_MODEL_LOAD_ERROR = "embedding_model_load_error"
    EMBEDDING_GENERATION_ERROR = "embedding_generation_error"
    INSUFFICIENT_MEMORY_ERROR = "insufficient_memory_error"

    # MCP protocol errors
    INVALID_PARAMETER = "invalid_parameter"
    MISSING_PARAMETER = "missing_parameter"
    MCP_TOOL_ERROR = "mcp_tool_error"
    SERIALIZATION_ERROR = "serialization_error"

    # Service errors
    SERVICE_NOT_INITIALIZED = "service_not_initialized"
    SERVICE_INITIALIZATION_ERROR = "service_initialization_error"
    DOCUMENT_INGESTION_ERROR = "document_ingestion_error"
    DOCUMENT_LISTING_ERROR = "document_listing_error"
    DOCUMENT_SEARCH_ERROR = "document_search_error"
    KNOWLEDGE_BASE_CLEAR_ERROR = "knowledge_base_clear_error"

    # Configuration errors
    CONFIGURATION_ERROR = "configuration_error"
    INVALID_CONFIGURATION = "invalid_configuration"

    # Validation errors
    VALIDATION_ERROR = "validation_error"
    INVALID_QUERY = "invalid_query"
    INVALID_FILE_PATH = "invalid_file_path"
    LIMIT_EXCEEDED = "limit_exceeded"

    # General errors
    UNKNOWN_ERROR = "unknown_error"
    INTERNAL_ERROR = "internal_error"


class KnowledgeBaseError(Exception):
    """Base exception for all knowledge base errors."""

    def __init__(
        self,
        message: str,
        error_category: ErrorCategory = ErrorCategory.UNKNOWN_ERROR,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
    ):
        """Initialize knowledge base error.

        Args:
            message: Human-readable error message
            error_category: Category of the error
            details: Additional error details
            original_error: Original exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.error_category = error_category
        self.details = details or {}
        self.original_error = original_error

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format for API responses.

        Returns:
            Dictionary containing error information
        """
        error_dict = {
            "success": False,
            "error_type": self.error_category.value,
            "error_message": self.message,
            "error_details": self.details,
        }

        # Add original error information if available
        if self.original_error:
            error_dict["error_details"]["original_error"] = str(self.original_error)
            error_dict["error_details"]["original_error_type"] = type(self.original_error).__name__

        return error_dict

    def log_error(self, logger_instance: Optional[logging.Logger] = None) -> None:
        """Log the error with appropriate level and context.

        Args:
            logger_instance: Logger to use (defaults to module logger)
        """
        log = logger_instance or logger

        log_message = f"[{self.error_category.value}] {self.message}"
        if self.details:
            log_message += f" | Details: {self.details}"

        if self.original_error:
            log.error(log_message, exc_info=self.original_error)
        else:
            log.error(log_message)


class FileValidationError(KnowledgeBaseError):
    """Error raised during file validation."""

    def __init__(self, message: str, file_path: str, details: Optional[Dict[str, Any]] = None):
        error_details = {"file_path": file_path}
        if details:
            error_details.update(details)

        super().__init__(
            message=message, error_category=ErrorCategory.VALIDATION_ERROR, details=error_details
        )


class ParameterValidationError(KnowledgeBaseError):
    """Error raised during parameter validation."""

    def __init__(
        self,
        message: str,
        parameter_name: str,
        parameter_value: Any,
        details: Optional[Dict[str, Any]] = None,
    ):
        error_details = {"parameter_name": parameter_name, "parameter_value": parameter_value}
        if details:
            error_details.update(details)

        super().__init__(
            message=message, error_category=ErrorCategory.INVALID_PARAMETER, details=error_details
        )


class DatabaseError(KnowledgeBaseError):
    """Error raised during database operations."""

    def __init__(
        self,
        message: str,
        operation: str,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
    ):
        error_details = {"operation": operation}
        if details:
            error_details.update(details)

        super().__init__(
            message=message,
            error_category=ErrorCategory.DATABASE_OPERATION_ERROR,
            details=error_details,
            original_error=original_error,
        )


class EmbeddingError(KnowledgeBaseError):
    """Error raised during embedding operations."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(
            message=message,
            error_category=ErrorCategory.EMBEDDING_GENERATION_ERROR,
            details=details or {},
            original_error=original_error,
        )


def create_error_response(
    error: Exception,
    default_message: str = "An error occurred",
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a standardized error response from any exception.

    Args:
        error: The exception that occurred
        default_message: Default message if error has no message
        context: Additional context to include in error details

    Returns:
        Dictionary containing structured error response
    """
    # If it's already a KnowledgeBaseError, use its to_dict method
    if isinstance(error, KnowledgeBaseError):
        error.log_error()
        return error.to_dict()

    # For other exceptions, create a generic error response
    error_message = str(error) if str(error) else default_message
    error_details = context or {}
    error_details["error_type"] = type(error).__name__

    logger.error(f"Unexpected error: {error_message}", exc_info=error)

    return {
        "success": False,
        "error_type": ErrorCategory.INTERNAL_ERROR.value,
        "error_message": error_message,
        "error_details": error_details,
    }


def validate_file_path(file_path: str, max_length: int = 4096) -> None:
    """Validate file path parameter.

    Args:
        file_path: File path to validate
        max_length: Maximum allowed path length

    Raises:
        ParameterValidationError: If file path is invalid
    """
    if not file_path:
        raise ParameterValidationError(
            message="File path cannot be empty",
            parameter_name="file_path",
            parameter_value=file_path,
        )

    if not isinstance(file_path, str):
        raise ParameterValidationError(
            message=f"File path must be a string, got {type(file_path).__name__}",
            parameter_name="file_path",
            parameter_value=file_path,
        )

    file_path_stripped = file_path.strip()
    if not file_path_stripped:
        raise ParameterValidationError(
            message="File path cannot be empty or whitespace only",
            parameter_name="file_path",
            parameter_value=file_path,
        )

    if len(file_path_stripped) > max_length:
        raise ParameterValidationError(
            message=f"File path too long: {len(file_path_stripped)} characters (max: {max_length})",
            parameter_name="file_path",
            parameter_value=file_path[:100] + "...",
            details={"path_length": len(file_path_stripped), "max_length": max_length},
        )

    # Check for potentially dangerous path patterns
    dangerous_patterns = ["../", "..\\", "~"]
    for pattern in dangerous_patterns:
        if pattern in file_path_stripped:
            logger.warning(
                f"File path contains potentially dangerous pattern '{pattern}': {file_path_stripped}"
            )


def validate_query_parameter(query: str, min_length: int = 1, max_length: int = 10000) -> None:
    """Validate search query parameter.

    Args:
        query: Query string to validate
        min_length: Minimum allowed query length
        max_length: Maximum allowed query length

    Raises:
        ParameterValidationError: If query is invalid
    """
    if not query:
        raise ParameterValidationError(
            message="Query cannot be empty", parameter_name="query", parameter_value=query
        )

    if not isinstance(query, str):
        raise ParameterValidationError(
            message=f"Query must be a string, got {type(query).__name__}",
            parameter_name="query",
            parameter_value=query,
        )

    query_stripped = query.strip()
    if not query_stripped:
        raise ParameterValidationError(
            message="Query cannot be empty or whitespace only",
            parameter_name="query",
            parameter_value=query,
        )

    if len(query_stripped) < min_length:
        raise ParameterValidationError(
            message=f"Query too short: {len(query_stripped)} characters (min: {min_length})",
            parameter_name="query",
            parameter_value=query_stripped,
            details={"query_length": len(query_stripped), "min_length": min_length},
        )

    if len(query_stripped) > max_length:
        raise ParameterValidationError(
            message=f"Query too long: {len(query_stripped)} characters (max: {max_length})",
            parameter_name="query",
            parameter_value=query_stripped[:100] + "...",
            details={"query_length": len(query_stripped), "max_length": max_length},
        )


def validate_limit_parameter(
    limit: Optional[int], min_value: int = 1, max_value: int = 1000, parameter_name: str = "limit"
) -> None:
    """Validate limit parameter for pagination or result limiting.

    Args:
        limit: Limit value to validate (None is allowed)
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        parameter_name: Name of the parameter for error messages

    Raises:
        ParameterValidationError: If limit is invalid
    """
    if limit is None:
        return  # None is valid (means no limit)

    if not isinstance(limit, int):
        raise ParameterValidationError(
            message=f"{parameter_name} must be an integer or None, got {type(limit).__name__}",
            parameter_name=parameter_name,
            parameter_value=limit,
        )

    if limit < min_value:
        raise ParameterValidationError(
            message=f"{parameter_name} must be at least {min_value}, got {limit}",
            parameter_name=parameter_name,
            parameter_value=limit,
            details={"min_value": min_value, "max_value": max_value},
        )

    if limit > max_value:
        raise ParameterValidationError(
            message=f"{parameter_name} cannot exceed {max_value}, got {limit}",
            parameter_name=parameter_name,
            parameter_value=limit,
            details={"min_value": min_value, "max_value": max_value},
        )


def validate_offset_parameter(offset: int, max_value: int = 100000) -> None:
    """Validate offset parameter for pagination.

    Args:
        offset: Offset value to validate
        max_value: Maximum allowed offset value

    Raises:
        ParameterValidationError: If offset is invalid
    """
    if not isinstance(offset, int):
        raise ParameterValidationError(
            message=f"offset must be an integer, got {type(offset).__name__}",
            parameter_name="offset",
            parameter_value=offset,
        )

    if offset < 0:
        raise ParameterValidationError(
            message=f"offset cannot be negative, got {offset}",
            parameter_name="offset",
            parameter_value=offset,
        )

    if offset > max_value:
        raise ParameterValidationError(
            message=f"offset too large: {offset} (max: {max_value})",
            parameter_name="offset",
            parameter_value=offset,
            details={"max_value": max_value},
        )


def log_operation_start(operation: str, **kwargs) -> None:
    """Log the start of an operation with parameters.

    Args:
        operation: Name of the operation
        **kwargs: Operation parameters to log
    """
    params_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.info(f"Starting operation: {operation} | Parameters: {params_str}")


def log_operation_success(operation: str, **kwargs) -> None:
    """Log successful completion of an operation.

    Args:
        operation: Name of the operation
        **kwargs: Result details to log
    """
    details_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.info(f"Operation completed successfully: {operation} | {details_str}")


def log_operation_failure(operation: str, error: Exception, **kwargs) -> None:
    """Log failure of an operation.

    Args:
        operation: Name of the operation
        error: Exception that caused the failure
        **kwargs: Additional context to log
    """
    context_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.error(
        f"Operation failed: {operation} | Error: {str(error)} | Context: {context_str}",
        exc_info=error,
    )
