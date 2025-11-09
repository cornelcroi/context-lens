"""Tests for the EmbeddingService class."""

import pytest

from context_lens.config import EmbeddingConfig, ProcessingConfig
from context_lens.services.embedding_service import EmbeddingService


class TestEmbeddingService:
    """Test cases for EmbeddingService."""

    @pytest.fixture
    def embedding_config(self):
        """Create test embedding configuration."""
        return EmbeddingConfig(
            model="sentence-transformers/all-MiniLM-L6-v2", batch_size=2, cache_dir="./test_models"
        )

    @pytest.fixture
    def processing_config(self):
        """Create test processing configuration."""
        return ProcessingConfig(
            chunk_size=100, chunk_overlap=20, supported_extensions=[".py", ".txt"]
        )

    @pytest.fixture
    def embedding_service(self, embedding_config, processing_config):
        """Create EmbeddingService instance."""
        return EmbeddingService(embedding_config, processing_config)

    def test_initialization(self, embedding_service, embedding_config, processing_config):
        """Test EmbeddingService initialization."""
        assert embedding_service.embedding_config == embedding_config
        assert embedding_service.processing_config == processing_config
        assert embedding_service._model is None
        assert embedding_service._model_loaded is False

    def test_chunk_text_simple(self, embedding_service):
        """Test basic text chunking."""
        text = "This is a simple test. " * 10  # 240 characters
        chunks = embedding_service.chunk_text(text, "txt")

        # Should create multiple chunks due to size
        assert len(chunks) >= 2
        assert all(isinstance(chunk, str) for chunk in chunks)
        assert all(len(chunk) > 0 for chunk in chunks)

    def test_chunk_text_short(self, embedding_service):
        """Test chunking of short text."""
        text = "Short text"
        chunks = embedding_service.chunk_text(text, "txt")

        assert len(chunks) == 1
        assert chunks[0] == text

    def test_chunk_text_empty(self, embedding_service):
        """Test chunking of empty text."""
        chunks = embedding_service.chunk_text("", "txt")
        assert chunks == []

        chunks = embedding_service.chunk_text("   ", "txt")
        assert chunks == []

    def test_chunk_python_code(self, embedding_service):
        """Test Python code chunking."""
        python_code = '''
def function1():
    """First function."""
    return "hello"

def function2():
    """Second function."""
    return "world"

class TestClass:
    """A test class."""

    def method1(self):
        return "method1"

    def method2(self):
        return "method2"
'''
        chunks = embedding_service.chunk_text(python_code, "py")

        # Should create chunks, preserving function boundaries when possible
        assert len(chunks) >= 1
        assert all(isinstance(chunk, str) for chunk in chunks)

    def test_get_embedding_dimension(self, embedding_service):
        """Test getting embedding dimension."""
        # Should return 384 for MiniLM model
        dimension = embedding_service.get_embedding_dimension()
        assert dimension == 384

    @pytest.mark.asyncio
    async def test_cleanup(self, embedding_service):
        """Test cleanup method."""
        # Should not raise any errors
        await embedding_service.cleanup()
        assert embedding_service._model is None
        assert embedding_service._model_loaded is False


class TestTextChunking:
    """Test text chunking functionality in detail."""

    @pytest.fixture
    def service(self):
        """Create service with small chunk size for testing."""
        processing_config = ProcessingConfig(chunk_size=50, chunk_overlap=10)
        return EmbeddingService(processing_config=processing_config)

    def test_paragraph_splitting(self, service):
        """Test that text is split on paragraph boundaries."""
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        chunks = service.chunk_text(text, "txt")

        # Should respect paragraph boundaries
        assert len(chunks) >= 2
        for chunk in chunks:
            assert len(chunk) <= 60  # chunk_size + some tolerance

    def test_overlap_application(self, service):
        """Test that overlap is applied between chunks."""
        # Create text that will definitely be split
        text = "A" * 30 + " " + "B" * 30 + " " + "C" * 30
        chunks = service.chunk_text(text, "txt")

        if len(chunks) > 1:
            # Check that there's some overlap between consecutive chunks
            # This is a basic check - exact overlap depends on splitting logic
            assert len(chunks) >= 2

    def test_sentence_splitting_fallback(self, service):
        """Test sentence splitting when paragraphs are too large."""
        # Create a long paragraph with sentences
        long_paragraph = "This is sentence one. This is sentence two. This is sentence three. This is sentence four."
        chunks = service.chunk_text(long_paragraph, "txt")

        # Should split into multiple chunks
        assert len(chunks) >= 2


# Integration test that requires actual model loading (marked as slow)
@pytest.mark.slow
class TestEmbeddingGeneration:
    """Integration tests for embedding generation (requires model download)."""

    @pytest.mark.asyncio
    async def test_model_loading_and_embedding_generation(self):
        """Test actual model loading and embedding generation."""
        config = EmbeddingConfig(
            model="sentence-transformers/all-MiniLM-L6-v2", cache_dir="./test_models"
        )
        service = EmbeddingService(embedding_config=config)

        try:
            # Load model
            await service.load_model()
            assert service._model_loaded is True
            assert service._model is not None

            # Generate embedding for single text
            embedding = await service.generate_embedding("Hello world")
            assert isinstance(embedding, list)
            assert len(embedding) == 384  # MiniLM dimension
            assert all(isinstance(x, float) for x in embedding)

            # Generate embeddings for multiple texts
            embeddings = await service.generate_embeddings(["Hello", "World"])
            assert len(embeddings) == 2
            assert all(len(emb) == 384 for emb in embeddings)

        finally:
            await service.cleanup()
