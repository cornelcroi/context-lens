"""Core data models for the MCP Knowledge Base Server."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class DocumentMetadata:
    """Metadata for a document in the knowledge base."""

    id: str
    file_path: str
    file_name: str
    file_size: int
    file_type: str
    ingestion_timestamp: datetime
    content_hash: str
    chunk_count: int


@dataclass
class DocumentChunk:
    """A chunk of document content with its embedding."""

    id: str
    document_id: str
    content: str
    chunk_index: int
    embedding: List[float]
    metadata: Optional[dict] = None


@dataclass
class SearchResult:
    """Result from a vector similarity search."""

    document_id: str
    document_path: str
    relevance_score: float
    content_excerpt: str
    metadata: DocumentMetadata


@dataclass
class ClearResult:
    """Result from clearing the knowledge base."""

    success: bool
    documents_removed: int
    message: str


@dataclass
class ErrorResponse:
    """Structured error response for MCP tools."""

    success: bool = False
    error_type: str = ""
    error_message: str = ""
    error_details: Optional[dict] = None
