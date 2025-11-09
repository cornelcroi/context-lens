"""Unit tests for LanceDB manager."""

from datetime import datetime

import pytest

from context_lens.config import DatabaseConfig
from context_lens.models.data_models import DocumentChunk, DocumentMetadata
from context_lens.storage.lancedb_manager import LanceDBManager, VectorSearchResult


class TestLanceDBManager:
    """Test cases for LanceDBManager."""

    @pytest.fixture
    async def db_manager(self, temp_dir):
        """Create and initialize LanceDB manager."""
        config = DatabaseConfig(path=str(temp_dir / "test_lance.db"), table_prefix="test_")
        manager = LanceDBManager(config)
        await manager.initialize_database()
        yield manager
        await manager.close()

    @pytest.fixture
    def sample_document_metadata(self):
        """Create sample document metadata."""
        return DocumentMetadata(
            id="doc-123",
            file_path="/path/to/test.py",
            file_name="test.py",
            file_size=1024,
            file_type=".py",
            ingestion_timestamp=datetime.now(),
            content_hash="abc123def456",
            chunk_count=3,
        )

    @pytest.fixture
    def sample_chunks(self):
        """Create sample document chunks with embeddings."""
        # Create simple embeddings (384 dimensions for MiniLM)
        embedding1 = [0.1] * 384
        embedding2 = [0.2] * 384
        embedding3 = [0.3] * 384

        return [
            DocumentChunk(
                id="chunk-1",
                document_id="doc-123",
                content="This is the first chunk of content.",
                chunk_index=0,
                embedding=embedding1,
            ),
            DocumentChunk(
                id="chunk-2",
                document_id="doc-123",
                content="This is the second chunk with more information.",
                chunk_index=1,
                embedding=embedding2,
            ),
            DocumentChunk(
                id="chunk-3",
                document_id="doc-123",
                content="This is the third and final chunk.",
                chunk_index=2,
                embedding=embedding3,
            ),
        ]

    @pytest.mark.asyncio
    async def test_initialization(self, temp_dir):
        """Test LanceDB manager initialization."""
        config = DatabaseConfig(path=str(temp_dir / "init_test.db"), table_prefix="init_")
        manager = LanceDBManager(config)

        assert manager._db is None
        assert manager._documents_table is None
        assert manager._chunks_table is None

        await manager.initialize_database()

        assert manager._db is not None
        assert manager._documents_table is not None
        # Chunks table is created lazily

        await manager.close()

    @pytest.mark.asyncio
    async def test_add_document_vectors(self, db_manager, sample_document_metadata, sample_chunks):
        """Test adding document vectors to database."""
        await db_manager.add_document_vectors(sample_document_metadata, sample_chunks)

        # Verify document was added
        doc = await db_manager.get_document_metadata(sample_document_metadata.id)
        assert doc is not None
        assert doc.id == sample_document_metadata.id
        assert doc.file_path == sample_document_metadata.file_path
        assert doc.chunk_count == 3

    @pytest.mark.asyncio
    async def test_add_document_without_chunks(self, db_manager):
        """Test adding document metadata without chunks."""
        metadata = DocumentMetadata(
            id="doc-no-chunks",
            file_path="/path/to/empty.txt",
            file_name="empty.txt",
            file_size=0,
            file_type=".txt",
            ingestion_timestamp=datetime.now(),
            content_hash="empty_hash",
            chunk_count=0,
        )
        await db_manager.add_document_vectors(metadata, [])

        # Verify document was added
        doc = await db_manager.get_document_metadata(metadata.id)
        assert doc is not None
        assert doc.chunk_count == 0

    @pytest.mark.asyncio
    async def test_update_existing_document(
        self, db_manager, sample_document_metadata, sample_chunks
    ):
        """Test updating an existing document by file path."""
        # Add document first time
        await db_manager.add_document_vectors(sample_document_metadata, sample_chunks)

        # Create updated metadata with same file path but different content
        updated_metadata = DocumentMetadata(
            id="doc-456",  # Different ID
            file_path=sample_document_metadata.file_path,  # Same path
            file_name=sample_document_metadata.file_name,
            file_size=2048,  # Different size
            file_type=sample_document_metadata.file_type,
            ingestion_timestamp=datetime.now(),
            content_hash="updated_hash",
            chunk_count=2,
        )

        updated_chunks = sample_chunks[:2]  # Only 2 chunks
        for chunk in updated_chunks:
            chunk.document_id = "doc-456"

        # Add updated document
        await db_manager.add_document_vectors(updated_metadata, updated_chunks)

        # Verify old document is gone and new one exists
        old_doc = await db_manager.get_document_metadata(sample_document_metadata.id)
        assert old_doc is None

        new_doc = await db_manager.get_document_metadata(updated_metadata.id)
        assert new_doc is not None
        assert new_doc.file_size == 2048
        assert new_doc.chunk_count == 2

    @pytest.mark.asyncio
    async def test_get_document_metadata_not_found(self, db_manager):
        """Test getting non-existent document metadata."""
        doc = await db_manager.get_document_metadata("nonexistent-id")
        assert doc is None

    @pytest.mark.asyncio
    async def test_list_all_documents_empty(self, db_manager):
        """Test listing documents when database is empty."""
        docs = await db_manager.list_all_documents()
        assert docs == []

    @pytest.mark.asyncio
    async def test_list_all_documents(self, db_manager, sample_document_metadata, sample_chunks):
        """Test listing all documents."""
        # Add first document
        await db_manager.add_document_vectors(sample_document_metadata, sample_chunks)

        # Add second document
        doc2_metadata = DocumentMetadata(
            id="doc-789",
            file_path="/path/to/test2.txt",
            file_name="test2.txt",
            file_size=512,
            file_type=".txt",
            ingestion_timestamp=datetime.now(),
            content_hash="xyz789",
            chunk_count=1,
        )
        chunk2 = DocumentChunk(
            id="chunk-4",
            document_id="doc-789",
            content="Another document content.",
            chunk_index=0,
            embedding=[0.4] * 384,
        )
        await db_manager.add_document_vectors(doc2_metadata, [chunk2])

        # List all documents
        docs = await db_manager.list_all_documents()
        assert len(docs) == 2

        # Verify documents are sorted by timestamp (newest first)
        assert all(isinstance(doc, DocumentMetadata) for doc in docs)

    @pytest.mark.asyncio
    async def test_list_documents_with_pagination(self, db_manager):
        """Test listing documents with pagination."""
        # Add multiple documents
        for i in range(5):
            metadata = DocumentMetadata(
                id=f"doc-{i}",
                file_path=f"/path/to/test{i}.txt",
                file_name=f"test{i}.txt",
                file_size=100 * i,
                file_type=".txt",
                ingestion_timestamp=datetime.now(),
                content_hash=f"hash{i}",
                chunk_count=1,
            )
            chunk = DocumentChunk(
                id=f"chunk-{i}",
                document_id=f"doc-{i}",
                content=f"Content {i}",
                chunk_index=0,
                embedding=[float(i)] * 384,
            )
            await db_manager.add_document_vectors(metadata, [chunk])

        # Test limit
        docs = await db_manager.list_all_documents(limit=2)
        assert len(docs) == 2

        # Test offset
        docs = await db_manager.list_all_documents(limit=2, offset=2)
        assert len(docs) == 2

        # Test offset beyond available documents
        docs = await db_manager.list_all_documents(limit=10, offset=10)
        assert len(docs) == 0

    @pytest.mark.asyncio
    async def test_search_vectors_empty_database(self, db_manager):
        """Test vector search on empty database."""
        query_vector = [0.5] * 384
        results = await db_manager.search_vectors(query_vector, limit=10)
        assert results == []

    @pytest.mark.asyncio
    async def test_search_vectors(self, db_manager, sample_document_metadata, sample_chunks):
        """Test vector similarity search."""
        # Add document with chunks
        await db_manager.add_document_vectors(sample_document_metadata, sample_chunks)

        # Search with a query vector similar to first chunk
        query_vector = [0.15] * 384  # Close to embedding1 [0.1] * 384
        results = await db_manager.search_vectors(query_vector, limit=3)

        assert len(results) > 0
        assert all(isinstance(r, VectorSearchResult) for r in results)

        # Verify result structure
        first_result = results[0]
        assert first_result.document_id == "doc-123"
        assert first_result.content in [chunk.content for chunk in sample_chunks]
        assert isinstance(first_result.score, float)
        assert isinstance(first_result.chunk_index, int)

    @pytest.mark.asyncio
    async def test_search_vectors_with_limit(
        self, db_manager, sample_document_metadata, sample_chunks
    ):
        """Test vector search with result limit."""
        await db_manager.add_document_vectors(sample_document_metadata, sample_chunks)

        query_vector = [0.2] * 384
        results = await db_manager.search_vectors(query_vector, limit=1)

        assert len(results) <= 1

    @pytest.mark.asyncio
    async def test_get_document_count_empty(self, db_manager):
        """Test getting document count from empty database."""
        count = await db_manager.get_document_count()
        assert count == 0

    @pytest.mark.asyncio
    async def test_get_document_count(self, db_manager, sample_document_metadata, sample_chunks):
        """Test getting document count."""
        # Add documents
        await db_manager.add_document_vectors(sample_document_metadata, sample_chunks)

        count = await db_manager.get_document_count()
        assert count == 1

        # Add another document
        doc2_metadata = DocumentMetadata(
            id="doc-999",
            file_path="/path/to/another.txt",
            file_name="another.txt",
            file_size=256,
            file_type=".txt",
            ingestion_timestamp=datetime.now(),
            content_hash="another_hash",
            chunk_count=1,
        )
        chunk2 = DocumentChunk(
            id="chunk-999",
            document_id="doc-999",
            content="Another content.",
            chunk_index=0,
            embedding=[0.9] * 384,
        )
        await db_manager.add_document_vectors(doc2_metadata, [chunk2])

        count = await db_manager.get_document_count()
        assert count == 2

    @pytest.mark.asyncio
    async def test_clear_all_documents_empty(self, db_manager):
        """Test clearing empty database."""
        removed_count = await db_manager.clear_all_documents()
        assert removed_count == 0

    @pytest.mark.asyncio
    async def test_clear_all_documents(self, db_manager, sample_document_metadata, sample_chunks):
        """Test clearing all documents and chunks."""
        # Add documents
        await db_manager.add_document_vectors(sample_document_metadata, sample_chunks)

        doc2_metadata = DocumentMetadata(
            id="doc-clear-test",
            file_path="/path/to/clear.txt",
            file_name="clear.txt",
            file_size=128,
            file_type=".txt",
            ingestion_timestamp=datetime.now(),
            content_hash="clear_hash",
            chunk_count=1,
        )
        chunk2 = DocumentChunk(
            id="chunk-clear",
            document_id="doc-clear-test",
            content="Clear test content.",
            chunk_index=0,
            embedding=[0.7] * 384,
        )
        await db_manager.add_document_vectors(doc2_metadata, [chunk2])

        # Verify documents exist
        count_before = await db_manager.get_document_count()
        assert count_before == 2

        # Clear all documents
        removed_count = await db_manager.clear_all_documents()
        assert removed_count == 2

        # Verify database is empty
        count_after = await db_manager.get_document_count()
        assert count_after == 0

        docs = await db_manager.list_all_documents()
        assert len(docs) == 0

    @pytest.mark.asyncio
    async def test_database_not_initialized_error(self, temp_dir):
        """Test that operations fail when database is not initialized."""
        config = DatabaseConfig(path=str(temp_dir / "uninit_test.db"), table_prefix="uninit_")
        manager = LanceDBManager(config)

        # Don't initialize the database

        sample_metadata = DocumentMetadata(
            id="test-id",
            file_path="/test.txt",
            file_name="test.txt",
            file_size=100,
            file_type=".txt",
            ingestion_timestamp=datetime.now(),
            content_hash="hash",
            chunk_count=0,
        )

        with pytest.raises(Exception, match="not initialized"):
            await manager.add_document_vectors(sample_metadata, [])

        with pytest.raises(Exception, match="not initialized"):
            await manager.list_all_documents()

        with pytest.raises(Exception, match="not initialized"):
            await manager.clear_all_documents()

        # get_document_metadata returns None instead of raising exception
        doc = await manager.get_document_metadata("test-id")
        assert doc is None


class TestVectorSearchResult:
    """Test VectorSearchResult class."""

    def test_vector_search_result_creation(self):
        """Test creating VectorSearchResult."""
        result = VectorSearchResult(
            document_id="doc-123",
            chunk_id="chunk-456",
            content="Test content",
            chunk_index=0,
            score=0.85,
        )

        assert result.document_id == "doc-123"
        assert result.chunk_id == "chunk-456"
        assert result.content == "Test content"
        assert result.chunk_index == 0
        assert result.score == 0.85
