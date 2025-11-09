"""Embedding service for generating vector embeddings using sentence-transformers."""

import logging
import re
from pathlib import Path
from typing import List, Optional

try:
    import torch
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    raise ImportError(
        "sentence-transformers and torch are required. "
        "Install with: pip install sentence-transformers torch"
    ) from e

from ..config import EmbeddingConfig, ProcessingConfig

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings and chunking text content."""

    def __init__(
        self,
        embedding_config: Optional[EmbeddingConfig] = None,
        processing_config: Optional[ProcessingConfig] = None,
    ):
        """Initialize the embedding service.

        Args:
            embedding_config: Configuration for embedding model
            processing_config: Configuration for text processing
        """
        self.embedding_config = embedding_config or EmbeddingConfig()
        self.processing_config = processing_config or ProcessingConfig()
        self._model: Optional[SentenceTransformer] = None
        self._model_loaded = False

    async def load_model(self) -> None:
        """Load the sentence transformer model with caching."""
        if self._model_loaded:
            return

        try:
            logger.info(f"Loading embedding model: {self.embedding_config.model}")

            # Ensure cache directory exists
            cache_dir = Path(self.embedding_config.cache_dir)
            cache_dir.mkdir(parents=True, exist_ok=True)

            # Load model with caching
            self._model = SentenceTransformer(
                self.embedding_config.model, cache_folder=str(cache_dir)
            )

            # Set device (CPU or GPU)
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self._model = self._model.to(device)

            self._model_loaded = True
            logger.info(f"Model loaded successfully on device: {device}")

        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise RuntimeError(f"Failed to load embedding model: {e}") from e

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors (one per input text)

        Raises:
            RuntimeError: If model is not loaded or embedding generation fails
        """
        if not self._model_loaded or self._model is None:
            await self.load_model()

        if not texts:
            return []

        try:
            logger.debug(f"Generating embeddings for {len(texts)} texts")

            # Generate embeddings in batches
            embeddings = self._model.encode(
                texts,
                batch_size=self.embedding_config.batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
            )

            # Convert to list of lists for JSON serialization
            return [embedding.tolist() for embedding in embeddings]

        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise RuntimeError(f"Failed to generate embeddings: {e}") from e

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text.

        Args:
            text: Text string to embed

        Returns:
            Embedding vector as list of floats
        """
        embeddings = await self.generate_embeddings([text])
        return embeddings[0] if embeddings else []

    def chunk_text(self, text: str, file_type: str = "txt") -> List[str]:
        """Chunk text into smaller pieces with overlap.

        Args:
            text: Input text to chunk
            file_type: Type of file (affects chunking strategy)

        Returns:
            List of text chunks
        """
        if not text.strip():
            return []

        chunk_size = self.processing_config.chunk_size
        chunk_overlap = self.processing_config.chunk_overlap

        # Handle different file types with specialized chunking
        if file_type == "py":
            return self._chunk_python_code(text, chunk_size, chunk_overlap)
        else:
            return self._chunk_text_content(text, chunk_size, chunk_overlap)

    def _chunk_python_code(self, code: str, chunk_size: int, overlap: int) -> List[str]:
        """Chunk Python code preserving function/class boundaries when possible.

        Args:
            code: Python source code
            chunk_size: Target chunk size in characters
            overlap: Overlap between chunks in characters

        Returns:
            List of code chunks
        """
        chunks = []

        # Try to split on function/class definitions first
        function_pattern = r"^(def |class |async def )"
        lines = code.split("\n")

        current_chunk = ""
        current_size = 0

        i = 0
        while i < len(lines):
            line = lines[i]
            line_with_newline = line + "\n" if i < len(lines) - 1 else line

            # Check if this line starts a function/class
            if re.match(function_pattern, line.strip()):
                # If current chunk is getting large, save it
                if current_size > chunk_size * 0.8:  # 80% of target size
                    if current_chunk.strip():
                        chunks.append(current_chunk.strip())
                    current_chunk = ""
                    current_size = 0

            # Add line to current chunk
            current_chunk += line_with_newline
            current_size += len(line_with_newline)

            # If chunk is too large, split it
            if current_size >= chunk_size:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())

                # Start new chunk with overlap
                if overlap > 0 and chunks:
                    overlap_text = current_chunk[-overlap:]
                    current_chunk = overlap_text
                    current_size = len(overlap_text)
                else:
                    current_chunk = ""
                    current_size = 0

            i += 1

        # Add remaining chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        # Fallback to simple chunking if no chunks were created
        if not chunks:
            return self._chunk_text_content(code, chunk_size, overlap)

        return chunks

    def _chunk_text_content(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """Chunk plain text content with paragraph and sentence awareness.

        Args:
            text: Input text
            chunk_size: Target chunk size in characters
            overlap: Overlap between chunks in characters

        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]

        chunks = []

        # Try to split on paragraphs first
        paragraphs = text.split("\n\n")

        current_chunk = ""
        current_size = 0

        for paragraph in paragraphs:
            paragraph_with_breaks = paragraph + "\n\n"

            # If adding this paragraph would exceed chunk size
            if current_size + len(paragraph_with_breaks) > chunk_size:
                # Save current chunk if it has content
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())

                # If paragraph itself is too large, split it by sentences
                if len(paragraph) > chunk_size:
                    sentence_chunks = self._split_by_sentences(paragraph, chunk_size, overlap)
                    chunks.extend(sentence_chunks)
                    current_chunk = ""
                    current_size = 0
                else:
                    # Start new chunk with this paragraph
                    current_chunk = paragraph_with_breaks
                    current_size = len(paragraph_with_breaks)
            else:
                # Add paragraph to current chunk
                current_chunk += paragraph_with_breaks
                current_size += len(paragraph_with_breaks)

        # Add remaining chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        # Apply overlap between chunks
        if overlap > 0 and len(chunks) > 1:
            chunks = self._apply_overlap(chunks, overlap)

        return chunks

    def _split_by_sentences(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """Split text by sentences when paragraphs are too large.

        Args:
            text: Input text
            chunk_size: Target chunk size
            overlap: Overlap between chunks

        Returns:
            List of sentence-based chunks
        """
        # Simple sentence splitting on periods, exclamation marks, question marks
        sentence_endings = r"[.!?]+\s+"
        sentences = re.split(sentence_endings, text)

        chunks = []
        current_chunk = ""

        for sentence in sentences:
            sentence_with_space = sentence + ". "

            if len(current_chunk) + len(sentence_with_space) > chunk_size:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = sentence_with_space
            else:
                current_chunk += sentence_with_space

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        # Apply overlap
        if overlap > 0 and len(chunks) > 1:
            chunks = self._apply_overlap(chunks, overlap)

        return chunks

    def _apply_overlap(self, chunks: List[str], overlap: int) -> List[str]:
        """Apply overlap between consecutive chunks.

        Args:
            chunks: List of text chunks
            overlap: Number of characters to overlap

        Returns:
            List of chunks with overlap applied
        """
        if len(chunks) <= 1 or overlap <= 0:
            return chunks

        overlapped_chunks = [chunks[0]]

        for i in range(1, len(chunks)):
            prev_chunk = chunks[i - 1]
            current_chunk = chunks[i]

            # Get overlap from previous chunk
            if len(prev_chunk) >= overlap:
                overlap_text = prev_chunk[-overlap:]
                overlapped_chunk = overlap_text + " " + current_chunk
                overlapped_chunks.append(overlapped_chunk)
            else:
                overlapped_chunks.append(current_chunk)

        return overlapped_chunks

    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by the model.

        Returns:
            Embedding dimension
        """
        # For all-MiniLM-L6-v2, dimension is 384
        if "all-MiniLM-L6-v2" in self.embedding_config.model:
            return 384

        # For other models, we need to load the model to get dimension
        if self._model is not None:
            return self._model.get_sentence_embedding_dimension()

        # Default fallback (most sentence-transformers models use 384 or 768)
        return 384

    async def cleanup(self) -> None:
        """Clean up resources used by the embedding service."""
        if self._model is not None:
            # Move model to CPU to free GPU memory
            self._model = self._model.to("cpu")
            del self._model
            self._model = None
            self._model_loaded = False

        # Clear CUDA cache if available
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        logger.info("Embedding service cleaned up")
