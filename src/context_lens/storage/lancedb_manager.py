"""LanceDB vector store manager for the MCP Knowledge Base Server."""

import logging
from pathlib import Path
from typing import List, Optional

import lancedb
import pandas as pd
from lancedb.table import Table

from ..config import DatabaseConfig
from ..models.data_models import DocumentChunk, DocumentMetadata

logger = logging.getLogger(__name__)


class VectorSearchResult:
    """Internal result from vector search operations."""

    def __init__(
        self, document_id: str, chunk_id: str, content: str, chunk_index: int, score: float
    ):
        self.document_id = document_id
        self.chunk_id = chunk_id
        self.content = content
        self.chunk_index = chunk_index
        self.score = score


class LanceDBManager:
    """Manages LanceDB operations and vector storage for the knowledge base."""

    def __init__(self, config: DatabaseConfig):
        """Initialize the LanceDB manager with configuration.

        Args:
            config: Database configuration containing path and table prefix
        """
        self.config = config
        self.db_path = Path(config.path)
        self.table_prefix = config.table_prefix
        self._db: Optional[lancedb.DBConnection] = None
        self._documents_table: Optional[Table] = None
        self._chunks_table: Optional[Table] = None

    async def initialize_database(self) -> None:
        """Initialize the LanceDB database and create tables if they don't exist.

        Raises:
            Exception: If database initialization fails
        """
        try:
            # Create database directory if it doesn't exist
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            # Connect to LanceDB
            self._db = lancedb.connect(str(self.db_path))
            logger.info(f"Connected to LanceDB at {self.db_path}")

            # Initialize tables
            await self._initialize_documents_table()
            await self._initialize_chunks_table()

            logger.info("LanceDB initialization completed successfully")

        except Exception as e:
            logger.error(f"Failed to initialize LanceDB: {e}")
            raise Exception(f"Database initialization failed: {str(e)}")

    async def _initialize_documents_table(self) -> None:
        """Initialize the documents table."""
        table_name = f"{self.table_prefix}documents"

        try:
            # Check if table exists
            if table_name in self._db.table_names():
                self._documents_table = self._db.open_table(table_name)
                logger.info(f"Opened existing documents table: {table_name}")
            else:
                # Create empty DataFrame with correct schema
                empty_df = pd.DataFrame(
                    {
                        "id": pd.Series([], dtype="string"),
                        "file_path": pd.Series([], dtype="string"),
                        "file_name": pd.Series([], dtype="string"),
                        "file_size": pd.Series([], dtype="int64"),
                        "file_type": pd.Series([], dtype="string"),
                        "ingestion_timestamp": pd.Series([], dtype="datetime64[us]"),
                        "content_hash": pd.Series([], dtype="string"),
                        "chunk_count": pd.Series([], dtype="int32"),
                    }
                )

                self._documents_table = self._db.create_table(table_name, empty_df)
                logger.info(f"Created new documents table: {table_name}")

        except Exception as e:
            logger.error(f"Failed to initialize documents table: {e}")
            raise

    async def _initialize_chunks_table(self) -> None:
        """Initialize the document chunks table."""
        table_name = f"{self.table_prefix}chunks"

        try:
            # Check if table exists
            if table_name in self._db.table_names():
                self._chunks_table = self._db.open_table(table_name)
                logger.info(f"Opened existing chunks table: {table_name}")
            else:
                # Create table with first chunk to establish schema
                # We'll create it when we add the first document
                self._chunks_table = None
                logger.info(f"Chunks table {table_name} will be created on first document add")

        except Exception as e:
            logger.error(f"Failed to initialize chunks table: {e}")
            raise

    async def _create_chunks_table_with_data(self, chunks: List[DocumentChunk]) -> None:
        """Create chunks table with actual data to establish proper schema."""
        table_name = f"{self.table_prefix}chunks"

        try:
            # Create DataFrame with actual data to establish schema
            chunk_data = {
                "id": [chunk.id for chunk in chunks],
                "document_id": [chunk.document_id for chunk in chunks],
                "content": [chunk.content for chunk in chunks],
                "chunk_index": [chunk.chunk_index for chunk in chunks],
                "embedding": [chunk.embedding for chunk in chunks],
            }

            chunks_df = pd.DataFrame(chunk_data)

            # Create table with the data
            self._chunks_table = self._db.create_table(table_name, chunks_df)
            logger.info(f"Created chunks table {table_name} with {len(chunks)} initial chunks")

        except Exception as e:
            logger.error(f"Failed to create chunks table with data: {e}")
            raise

    async def add_document_vectors(
        self, document_metadata: DocumentMetadata, chunks: List[DocumentChunk]
    ) -> None:
        """Add document metadata and its vector chunks to the database.

        Args:
            document_metadata: Metadata for the document
            chunks: List of document chunks with embeddings

        Raises:
            Exception: If adding document vectors fails
        """
        try:
            if self._documents_table is None:
                raise Exception("Database not initialized")

            # Check if document already exists and remove it
            all_docs = self._documents_table.to_pandas()
            existing_docs = all_docs[all_docs["file_path"] == document_metadata.file_path]

            if not existing_docs.empty:
                await self._remove_document_by_path(document_metadata.file_path)
                logger.info(f"Removed existing document: {document_metadata.file_path}")

            # Add document metadata
            doc_data = {
                "id": [document_metadata.id],
                "file_path": [document_metadata.file_path],
                "file_name": [document_metadata.file_name],
                "file_size": [document_metadata.file_size],
                "file_type": [document_metadata.file_type],
                "ingestion_timestamp": [document_metadata.ingestion_timestamp],
                "content_hash": [document_metadata.content_hash],
                "chunk_count": [document_metadata.chunk_count],
            }

            doc_df = pd.DataFrame(doc_data)
            self._documents_table.add(doc_df)

            # Add document chunks
            if chunks:
                # Create chunks table if it doesn't exist
                if self._chunks_table is None:
                    await self._create_chunks_table_with_data(chunks)
                else:
                    chunk_data = {
                        "id": [chunk.id for chunk in chunks],
                        "document_id": [chunk.document_id for chunk in chunks],
                        "content": [chunk.content for chunk in chunks],
                        "chunk_index": [chunk.chunk_index for chunk in chunks],
                        "embedding": [chunk.embedding for chunk in chunks],
                    }

                    chunks_df = pd.DataFrame(chunk_data)
                    self._chunks_table.add(chunks_df)

            logger.info(f"Added document {document_metadata.file_path} with {len(chunks)} chunks")

        except Exception as e:
            logger.error(f"Failed to add document vectors: {e}")
            raise Exception(f"Failed to add document vectors: {str(e)}")

    async def remove_document(self, file_path: str) -> None:
        """Remove a document and its chunks by file path.

        Args:
            file_path: Path to the document to remove

        Raises:
            Exception: If removal fails
        """
        await self._remove_document_by_path(file_path)

    async def _remove_document_by_path(self, file_path: str) -> None:
        """Remove a document and its chunks by file path."""
        try:
            # Get document ID
            all_docs = self._documents_table.to_pandas()
            existing_docs = all_docs[all_docs["file_path"] == file_path]

            if not existing_docs.empty:
                doc_id = existing_docs.iloc[0]["id"]

                # Remove chunks if table exists
                if self._chunks_table is not None:
                    self._chunks_table.delete(f"document_id = '{doc_id}'")

                # Remove document
                self._documents_table.delete(f"file_path = '{file_path}'")

        except Exception as e:
            logger.error(f"Failed to remove document by path {file_path}: {e}")
            raise

    async def search_vectors(
        self, query_vector: List[float], limit: int = 10
    ) -> List[VectorSearchResult]:
        """Perform vector similarity search against document chunks.

        Args:
            query_vector: Query embedding vector
            limit: Maximum number of results to return

        Returns:
            List of VectorSearchResult objects sorted by relevance

        Raises:
            Exception: If vector search fails
        """
        try:
            if self._chunks_table is None:
                # No chunks table means no documents have been added yet
                return []

            # Perform vector search
            results = self._chunks_table.search(query_vector).limit(limit).to_pandas()

            if results.empty:
                return []

            # Convert to VectorSearchResult objects
            search_results = []
            for _, row in results.iterrows():
                result = VectorSearchResult(
                    document_id=row["document_id"],
                    chunk_id=row["id"],
                    content=row["content"],
                    chunk_index=row["chunk_index"],
                    score=row.get("_distance", 0.0),  # LanceDB returns distance, lower is better
                )
                search_results.append(result)

            # Sort by score (distance) - lower distance means higher similarity
            search_results.sort(key=lambda x: x.score)

            logger.info(f"Vector search returned {len(search_results)} results")
            return search_results

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise Exception(f"Vector search failed: {str(e)}")

    async def get_document_metadata(self, document_id: str) -> Optional[DocumentMetadata]:
        """Get document metadata by document ID.

        Args:
            document_id: ID of the document

        Returns:
            DocumentMetadata object or None if not found
        """
        try:
            if self._documents_table is None:
                raise Exception("Database not initialized")

            all_docs = self._documents_table.to_pandas()
            results = all_docs[all_docs["id"] == document_id]

            if results.empty:
                return None

            row = results.iloc[0]
            return DocumentMetadata(
                id=row["id"],
                file_path=row["file_path"],
                file_name=row["file_name"],
                file_size=row["file_size"],
                file_type=row["file_type"],
                ingestion_timestamp=row["ingestion_timestamp"],
                content_hash=row["content_hash"],
                chunk_count=row["chunk_count"],
            )

        except Exception as e:
            logger.error(f"Failed to get document metadata for {document_id}: {e}")
            return None

    async def list_all_documents(
        self, limit: Optional[int] = None, offset: int = 0
    ) -> List[DocumentMetadata]:
        """List all documents in the knowledge base.

        Args:
            limit: Maximum number of documents to return
            offset: Number of documents to skip

        Returns:
            List of DocumentMetadata objects

        Raises:
            Exception: If listing documents fails
        """
        try:
            if self._documents_table is None:
                raise Exception("Database not initialized")

            # Get all documents using to_pandas() directly on the table
            results_df = self._documents_table.to_pandas()

            if results_df.empty:
                return []

            # Sort by ingestion timestamp (newest first)
            results_df = results_df.sort_values("ingestion_timestamp", ascending=False)

            # Apply pagination
            if offset > 0:
                results_df = results_df.iloc[offset:]

            if limit is not None:
                results_df = results_df.head(limit)

            # Convert to DocumentMetadata objects
            documents = []
            for _, row in results_df.iterrows():
                doc = DocumentMetadata(
                    id=row["id"],
                    file_path=row["file_path"],
                    file_name=row["file_name"],
                    file_size=row["file_size"],
                    file_type=row["file_type"],
                    ingestion_timestamp=row["ingestion_timestamp"],
                    content_hash=row["content_hash"],
                    chunk_count=row["chunk_count"],
                )
                documents.append(doc)

            logger.info(f"Listed {len(documents)} documents")
            return documents

        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            raise Exception(f"Failed to list documents: {str(e)}")

    async def clear_all_documents(self) -> int:
        """Clear all documents and chunks from the knowledge base.

        Returns:
            Number of documents removed

        Raises:
            Exception: If clearing documents fails
        """
        try:
            if self._documents_table is None:
                raise Exception("Database not initialized")

            # Count documents before clearing
            doc_count = len(self._documents_table.to_pandas())

            # Clear all chunks first if table exists
            if self._chunks_table is not None:
                chunk_results = self._chunks_table.to_pandas()
                if not chunk_results.empty:
                    # Delete all chunks
                    self._chunks_table.delete("chunk_index >= 0")  # Delete all rows

            # Clear all documents
            doc_results = self._documents_table.to_pandas()
            if not doc_results.empty:
                # Delete all documents
                self._documents_table.delete("chunk_count >= 0")  # Delete all rows

            logger.info(f"Cleared {doc_count} documents from knowledge base")
            return doc_count

        except Exception as e:
            logger.error(f"Failed to clear documents: {e}")
            raise Exception(f"Failed to clear documents: {str(e)}")

    async def get_document_count(self) -> int:
        """Get the total number of documents in the knowledge base.

        Returns:
            Number of documents
        """
        try:
            if self._documents_table is None:
                return 0

            results = self._documents_table.to_pandas()
            return len(results)

        except Exception as e:
            logger.error(f"Failed to get document count: {e}")
            return 0

    async def close(self) -> None:
        """Close the database connection and cleanup resources."""
        try:
            # LanceDB connections are automatically managed
            # We don't need to explicitly close them, just log
            logger.info("LanceDB connection cleanup completed")

        except Exception as e:
            logger.error(f"Error during LanceDB cleanup: {e}")
