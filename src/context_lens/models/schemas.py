"""LanceDB table schemas for the MCP Knowledge Base Server."""

import pyarrow as pa

# Documents table schema
documents_schema = pa.schema(
    [
        pa.field("id", pa.string()),
        pa.field("file_path", pa.string()),
        pa.field("file_name", pa.string()),
        pa.field("file_size", pa.int64()),
        pa.field("file_type", pa.string()),
        pa.field("ingestion_timestamp", pa.timestamp("us")),
        pa.field("content_hash", pa.string()),
        pa.field("chunk_count", pa.int32()),
    ]
)

# Document chunks table schema
chunks_schema = pa.schema(
    [
        pa.field("id", pa.string()),
        pa.field("document_id", pa.string()),
        pa.field("content", pa.string()),
        pa.field("chunk_index", pa.int32()),
        pa.field("embedding", pa.list_(pa.float32())),
    ]
)


def get_documents_schema() -> pa.Schema:
    """Get the PyArrow schema for the documents table."""
    return documents_schema


def get_chunks_schema() -> pa.Schema:
    """Get the PyArrow schema for the document chunks table."""
    return chunks_schema
