# Error Handling Documentation

## Overview

The MCP Knowledge Base Server implements comprehensive error handling with structured error responses, centralized validation, and detailed logging throughout the application.

## Error Categories

All errors in the system are categorized using the `ErrorCategory` enum:

### File-Related Errors
- `FILE_NOT_FOUND`: File does not exist at the specified path
- `FILE_ACCESS_DENIED`: Permission denied when accessing file
- `FILE_TOO_LARGE`: File exceeds maximum size limit
- `UNSUPPORTED_FILE_TYPE`: File type is not supported
- `FILE_READ_ERROR`: Error occurred while reading file
- `ENCODING_ERROR`: File encoding detection or decoding failed

### Processing Errors
- `CONTENT_EXTRACTION_ERROR`: Failed to extract content from file
- `PYTHON_PROCESSING_ERROR`: Error processing Python file
- `TEXT_PROCESSING_ERROR`: Error processing text file
- `CHUNKING_ERROR`: Error during text chunking

### Database Errors
- `DATABASE_CONNECTION_ERROR`: Failed to connect to database
- `DATABASE_INITIALIZATION_ERROR`: Database initialization failed
- `DATABASE_OPERATION_ERROR`: Database operation failed
- `SCHEMA_MISMATCH_ERROR`: Database schema mismatch

### Embedding Errors
- `EMBEDDING_MODEL_LOAD_ERROR`: Failed to load embedding model
- `EMBEDDING_GENERATION_ERROR`: Failed to generate embeddings
- `INSUFFICIENT_MEMORY_ERROR`: Insufficient memory for operation

### MCP Protocol Errors
- `INVALID_PARAMETER`: Invalid parameter value
- `MISSING_PARAMETER`: Required parameter missing
- `MCP_TOOL_ERROR`: MCP tool execution failed
- `SERIALIZATION_ERROR`: Failed to serialize response

### Service Errors
- `SERVICE_NOT_INITIALIZED`: Service not initialized
- `SERVICE_INITIALIZATION_ERROR`: Service initialization failed
- `DOCUMENT_INGESTION_ERROR`: Document ingestion failed
- `DOCUMENT_LISTING_ERROR`: Document listing failed
- `DOCUMENT_SEARCH_ERROR`: Document search failed
- `KNOWLEDGE_BASE_CLEAR_ERROR`: Knowledge base clear failed

### Configuration Errors
- `CONFIGURATION_ERROR`: Configuration error
- `INVALID_CONFIGURATION`: Invalid configuration

### Validation Errors
- `VALIDATION_ERROR`: Validation failed
- `INVALID_QUERY`: Invalid search query
- `INVALID_FILE_PATH`: Invalid file path
- `LIMIT_EXCEEDED`: Limit exceeded

## Error Response Format

All errors return a standardized JSON response:

```json
{
  "success": false,
  "error_type": "file_not_found",
  "error_message": "File not found: /path/to/file.txt",
  "error_details": {
    "file_path": "/path/to/file.txt",
    "additional_context": "..."
  }
}
```

## Exception Classes

### Base Exception: `KnowledgeBaseError`

All custom exceptions inherit from `KnowledgeBaseError`:

```python
from src.mcp_knowledge_base.errors import KnowledgeBaseError, ErrorCategory

raise KnowledgeBaseError(
    message="Operation failed",
    error_category=ErrorCategory.DATABASE_OPERATION_ERROR,
    details={"operation": "insert", "table": "documents"},
    original_error=original_exception  # Optional
)
```

### Specialized Exceptions

#### FileValidationError
```python
from src.mcp_knowledge_base.errors import FileValidationError

raise FileValidationError(
    message="File not found",
    file_path="/path/to/file.txt"
)
```

#### ParameterValidationError
```python
from src.mcp_knowledge_base.errors import ParameterValidationError

raise ParameterValidationError(
    message="Invalid limit value",
    parameter_name="limit",
    parameter_value=1000
)
```

#### DatabaseError
```python
from src.mcp_knowledge_base.errors import DatabaseError

raise DatabaseError(
    message="Insert operation failed",
    operation="insert",
    details={"table": "documents"}
)
```

#### EmbeddingError
```python
from src.mcp_knowledge_base.errors import EmbeddingError

raise EmbeddingError(
    message="Failed to generate embedding",
    details={"model": "all-MiniLM-L6-v2"}
)
```

## Validation Functions

The error handling module provides centralized validation functions:

### File Path Validation
```python
from src.mcp_knowledge_base.errors import validate_file_path

validate_file_path(file_path)  # Raises ParameterValidationError if invalid
```

Validates:
- Non-empty string
- Not whitespace only
- Length <= 4096 characters
- Warns about dangerous patterns (../, ~)

### Query Parameter Validation
```python
from src.mcp_knowledge_base.errors import validate_query_parameter

validate_query_parameter(query, min_length=1, max_length=10000)
```

Validates:
- Non-empty string
- Not whitespace only
- Length within specified range

### Limit Parameter Validation
```python
from src.mcp_knowledge_base.errors import validate_limit_parameter

validate_limit_parameter(limit, min_value=1, max_value=1000)
```

Validates:
- Integer or None
- Within specified range

### Offset Parameter Validation
```python
from src.mcp_knowledge_base.errors import validate_offset_parameter

validate_offset_parameter(offset, max_value=100000)
```

Validates:
- Non-negative integer
- Below maximum value

## Logging

### Log Levels

The application uses standard Python logging levels:
- `DEBUG`: Detailed diagnostic information
- `INFO`: General informational messages
- `WARNING`: Warning messages for potentially problematic situations
- `ERROR`: Error messages for failures
- `CRITICAL`: Critical errors that may cause system failure

### Log Configuration

Logging is configured in `main.py`:
- Console output: Configured log level (default: INFO)
- File output: Always DEBUG level (`logs/mcp_knowledge_base.log`)
- Error file: ERROR level only (`logs/errors.log`)

### Operation Logging

Use the provided logging utilities for consistent operation logging:

```python
from src.mcp_knowledge_base.errors import (
    log_operation_start,
    log_operation_success,
    log_operation_failure
)

# Log operation start
log_operation_start("add_document", file_path="/path/to/file.txt")

# Log operation success
log_operation_success("add_document", document_id="abc123")

# Log operation failure
log_operation_failure("add_document", error, file_path="/path/to/file.txt")
```

### Component-Level Logging

Each module has its own logger:

```python
import logging

logger = logging.getLogger(__name__)

logger.debug("Detailed debug information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error message", exc_info=True)  # Include stack trace
```

## Error Handling Best Practices

### 1. Use Specific Error Categories

Always use the most specific error category:

```python
# Good
raise KnowledgeBaseError(
    message="File not found",
    error_category=ErrorCategory.FILE_NOT_FOUND
)

# Avoid
raise KnowledgeBaseError(
    message="File not found",
    error_category=ErrorCategory.UNKNOWN_ERROR
)
```

### 2. Include Contextual Details

Provide relevant context in error details:

```python
raise KnowledgeBaseError(
    message="Database operation failed",
    error_category=ErrorCategory.DATABASE_OPERATION_ERROR,
    details={
        "operation": "insert",
        "table": "documents",
        "document_id": doc_id,
        "timestamp": datetime.utcnow().isoformat()
    }
)
```

### 3. Preserve Original Exceptions

When wrapping exceptions, preserve the original:

```python
try:
    # Some operation
    pass
except Exception as e:
    raise KnowledgeBaseError(
        message="Operation failed",
        error_category=ErrorCategory.INTERNAL_ERROR,
        original_error=e
    )
```

### 4. Log Before Raising

Log errors before raising them:

```python
logger.error(f"Failed to process file: {file_path}")
raise FileProcessingError(
    message=f"Failed to process file: {file_path}",
    error_type="processing_error"
)
```

### 5. Use Validation Functions

Use centralized validation functions instead of manual checks:

```python
# Good
from src.mcp_knowledge_base.errors import validate_file_path

validate_file_path(file_path)

# Avoid
if not file_path or not isinstance(file_path, str):
    raise ValueError("Invalid file path")
```

## System Limits

The following system limits are enforced:

### File Processing
- Maximum file size: 10 MB (configurable)
- Maximum file path length: 4096 characters
- Supported file types: .py, .txt (configurable)

### Query Parameters
- Maximum query length: 10,000 characters
- Minimum query length: 1 character

### Pagination
- Maximum limit: 1000 documents
- Maximum offset: 100,000

### Search
- Maximum search results: 100
- Default search results: 10

## Testing Error Handling

The error handling module includes comprehensive tests in `tests/test_error_handling.py`:

```bash
# Run error handling tests
python -m pytest tests/test_error_handling.py -v

# Run all tests
python -m pytest tests/ -v
```

## Examples

### Example 1: Handling File Not Found

```python
from src.mcp_knowledge_base.errors import (
    KnowledgeBaseError,
    ErrorCategory,
    create_error_response
)

try:
    # Attempt to process file
    process_file(file_path)
except FileNotFoundError as e:
    error = KnowledgeBaseError(
        message=f"File not found: {file_path}",
        error_category=ErrorCategory.FILE_NOT_FOUND,
        details={"file_path": file_path},
        original_error=e
    )
    return error.to_dict()
```

### Example 2: Parameter Validation in MCP Tool

```python
from src.mcp_knowledge_base.errors import (
    validate_query_parameter,
    validate_limit_parameter,
    ParameterValidationError
)

@mcp.tool()
async def search_documents(query: str, limit: int = 10):
    try:
        # Validate parameters
        validate_query_parameter(query)
        validate_limit_parameter(limit, min_value=1, max_value=100)
        
        # Process search
        results = await perform_search(query, limit)
        return {"success": True, "results": results}
        
    except ParameterValidationError as e:
        return e.to_dict()
```

### Example 3: Database Error Handling

```python
from src.mcp_knowledge_base.errors import DatabaseError, ErrorCategory

try:
    # Database operation
    db.insert(document)
except Exception as e:
    raise DatabaseError(
        message="Failed to insert document",
        operation="insert",
        details={"table": "documents", "document_id": doc_id},
        original_error=e
    )
```

## Monitoring and Debugging

### Log Files

Check log files for detailed error information:

```bash
# View main log
tail -f logs/mcp_knowledge_base.log

# View errors only
tail -f logs/errors.log

# Search for specific errors
grep "FILE_NOT_FOUND" logs/mcp_knowledge_base.log
```

### Error Patterns

Common error patterns to monitor:
- Repeated file access errors (permission issues)
- Embedding generation failures (memory issues)
- Database operation failures (connection issues)
- Parameter validation errors (client issues)

### Performance Impact

Error handling has minimal performance impact:
- Validation functions: < 1ms overhead
- Error object creation: < 1ms overhead
- Logging: Asynchronous, non-blocking
