"""Data models for the MCP Knowledge Base Server."""

from .data_models import (
    DocumentMetadata,
    DocumentChunk,
    SearchResult,
    ClearResult,
    ErrorResponse
)
from .schemas import (
    documents_schema,
    chunks_schema,
    get_documents_schema,
    get_chunks_schema
)

__all__ = [
    # Data models
    "DocumentMetadata",
    "DocumentChunk", 
    "SearchResult",
    "ClearResult",
    "ErrorResponse",
    # Schemas
    "documents_schema",
    "chunks_schema",
    "get_documents_schema",
    "get_chunks_schema"
]