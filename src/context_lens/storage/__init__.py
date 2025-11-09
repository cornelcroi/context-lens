"""Storage layer components for the MCP Knowledge Base Server."""

from .lancedb_manager import LanceDBManager, VectorSearchResult

__all__ = ["LanceDBManager", "VectorSearchResult"]
