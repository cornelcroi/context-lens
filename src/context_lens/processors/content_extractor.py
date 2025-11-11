"""Content extraction and chunking for document processing."""

import logging
import re
import uuid
from pathlib import Path
from typing import List, Tuple

from ..models.data_models import DocumentChunk, DocumentMetadata
from ..parsers import ParsingError, get_parser_registry
from .file_readers import FileProcessingError, FileReaderFactory

logger = logging.getLogger(__name__)


class ContentExtractor:
    """Extracts and chunks content for embedding generation."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """Initialize content extractor with chunking parameters."""
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.file_reader_factory = FileReaderFactory()
        self.parser_registry = get_parser_registry()

    def extract_and_chunk(self, file_path: str) -> Tuple[DocumentMetadata, List[DocumentChunk]]:
        """Extract content from file and create chunks.

        Args:
            file_path: Path to the file to process

        Returns:
            Tuple of (DocumentMetadata, List[DocumentChunk])

        Raises:
            FileProcessingError: If extraction or chunking fails
        """
        try:
            logger.info(f"Extracting and chunking content from: {file_path}")

            # Get appropriate reader and process file
            reader = self.file_reader_factory.get_reader(file_path)
            content, content_hash = reader.process_file(file_path)

            logger.debug(
                f"Content extracted: {len(content)} characters, hash: {content_hash[:16]}..."
            )

            # Create document metadata
            path = Path(file_path)
            doc_id = str(uuid.uuid4())

            # Get file stats
            file_stats = path.stat()

            # Create chunks using parser registry
            chunks = self._create_chunks_with_parser(content, doc_id, file_path)

            logger.info(f"Created {len(chunks)} chunks from {file_path}")

            # Create document metadata
            metadata = DocumentMetadata(
                id=doc_id,
                file_path=str(path.absolute()),
                file_name=path.name,
                file_size=file_stats.st_size,
                file_type=path.suffix.lower(),
                ingestion_timestamp=None,  # Will be set by the service layer
                content_hash=content_hash,
                chunk_count=len(chunks),
            )

            return metadata, chunks

        except FileProcessingError:
            # Re-raise file processing errors as-is
            logger.error(f"File processing error for {file_path}")
            raise
        except Exception as e:
            logger.error(f"Failed to extract and chunk content from {file_path}: {e}")
            raise FileProcessingError(
                f"Failed to extract and chunk content: {str(e)}",
                error_type="content_extraction_error",
                details={"file_path": file_path, "error": str(e)},
            )

    def _create_chunks_with_parser(
        self, content: str, document_id: str, file_path: str
    ) -> List[DocumentChunk]:
        """Create chunks using language-specific parser from registry.

        Args:
            content: File content to chunk
            document_id: Document ID
            file_path: Path to the file

        Returns:
            List of document chunks
        """
        try:
            # Get appropriate parser from registry
            parser = self.parser_registry.get_parser(
                file_path, chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap
            )

            # Parse content into code units
            code_units = parser.parse(content, file_path)

            # Convert code units to chunks
            chunks = parser.chunk(code_units, document_id)

            logger.debug(
                f"Used {parser.__class__.__name__} to create {len(chunks)} chunks from {file_path}"
            )

            return chunks

        except ParsingError as e:
            # If parsing fails, fall back to old chunking method
            logger.warning(
                f"Parser failed for {file_path}: {e}. Falling back to legacy chunking."
            )
            parser_name = parser.__class__.__name__ if "parser" in locals() else "Unknown"
            self.parser_registry.record_fallback(parser_name)
            return self._create_chunks(content, document_id, file_path)
        except Exception as e:
            # Unexpected error - fall back to legacy chunking
            logger.error(
                f"Unexpected error in parser for {file_path}: {e}. Falling back to legacy chunking."
            )
            return self._create_chunks(content, document_id, file_path)

    def _create_chunks(self, content: str, document_id: str, file_path: str) -> List[DocumentChunk]:
        """Create chunks from content based on file type (legacy method).

        This is kept as a fallback when parser registry fails.
        """
        path = Path(file_path)

        if path.suffix.lower() == ".py":
            return self._chunk_python_content(content, document_id)
        else:
            return self._chunk_text_content(content, document_id)

    def _chunk_python_content(self, content: str, document_id: str) -> List[DocumentChunk]:
        """Chunk Python content preserving function/class boundaries when possible."""
        chunks = []

        # Try to split by functions and classes first
        python_chunks = self._split_python_by_definitions(content)

        # If we couldn't split by definitions or chunks are too large, fall back to text chunking
        if not python_chunks or any(len(chunk) > self.chunk_size * 2 for chunk in python_chunks):
            return self._chunk_text_content(content, document_id)

        # Process Python-aware chunks
        current_chunk = ""
        chunk_index = 0

        for python_chunk in python_chunks:
            # If adding this chunk would exceed size, finalize current chunk
            if current_chunk and len(current_chunk) + len(python_chunk) > self.chunk_size:
                if current_chunk.strip():
                    chunks.append(
                        DocumentChunk(
                            id=str(uuid.uuid4()),
                            document_id=document_id,
                            content=current_chunk.strip(),
                            chunk_index=chunk_index,
                            embedding=[],  # Will be populated by embedding service
                        )
                    )
                    chunk_index += 1
                current_chunk = python_chunk
            else:
                current_chunk += python_chunk

        # Add final chunk
        if current_chunk.strip():
            chunks.append(
                DocumentChunk(
                    id=str(uuid.uuid4()),
                    document_id=document_id,
                    content=current_chunk.strip(),
                    chunk_index=chunk_index,
                    embedding=[],
                )
            )

        return chunks if chunks else self._chunk_text_content(content, document_id)

    def _split_python_by_definitions(self, content: str) -> List[str]:
        """Split Python content by function and class definitions."""
        lines = content.split("\n")
        chunks = []
        current_chunk_lines = []

        for line in lines:
            # Check if line starts a new function or class (accounting for decorators)
            stripped = line.strip()
            if (
                stripped.startswith("def ")
                or stripped.startswith("class ")
                or stripped.startswith("async def ")
            ) and current_chunk_lines:

                # Save current chunk
                if current_chunk_lines:
                    chunks.append("\n".join(current_chunk_lines))
                current_chunk_lines = [line]
            else:
                current_chunk_lines.append(line)

        # Add final chunk
        if current_chunk_lines:
            chunks.append("\n".join(current_chunk_lines))

        return chunks

    def _chunk_text_content(self, content: str, document_id: str) -> List[DocumentChunk]:
        """Chunk text content with overlap."""
        chunks = []

        # First try to split by paragraphs
        paragraphs = self._split_by_paragraphs(content)

        if paragraphs:
            chunks_text = self._create_overlapping_chunks_from_paragraphs(paragraphs)
        else:
            # Fall back to sentence-based chunking
            chunks_text = self._create_overlapping_chunks_from_text(content)

        # Create DocumentChunk objects
        for i, chunk_text in enumerate(chunks_text):
            if chunk_text.strip():
                chunks.append(
                    DocumentChunk(
                        id=str(uuid.uuid4()),
                        document_id=document_id,
                        content=chunk_text.strip(),
                        chunk_index=i,
                        embedding=[],  # Will be populated by embedding service
                    )
                )

        return chunks

    def _split_by_paragraphs(self, content: str) -> List[str]:
        """Split content by paragraphs."""
        # Split by double newlines (paragraph breaks)
        paragraphs = re.split(r"\n\s*\n", content)
        return [p.strip() for p in paragraphs if p.strip()]

    def _create_overlapping_chunks_from_paragraphs(self, paragraphs: List[str]) -> List[str]:
        """Create overlapping chunks from paragraphs."""
        chunks = []
        current_chunk = ""

        for paragraph in paragraphs:
            # If adding this paragraph would exceed chunk size
            if current_chunk and len(current_chunk) + len(paragraph) + 2 > self.chunk_size:
                chunks.append(current_chunk)

                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk)
                current_chunk = overlap_text + "\n\n" + paragraph if overlap_text else paragraph
            else:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph

        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def _create_overlapping_chunks_from_text(self, content: str) -> List[str]:
        """Create overlapping chunks from raw text."""
        chunks = []

        # Split by sentences for better chunking
        sentences = self._split_by_sentences(content)

        if not sentences:
            # If no sentences found, chunk by character count
            return self._chunk_by_characters(content)

        current_chunk = ""

        for sentence in sentences:
            # If adding this sentence would exceed chunk size
            if current_chunk and len(current_chunk) + len(sentence) + 1 > self.chunk_size:
                chunks.append(current_chunk)

                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk)
                current_chunk = overlap_text + " " + sentence if overlap_text else sentence
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence

        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def _split_by_sentences(self, content: str) -> List[str]:
        """Split content by sentences."""
        # Simple sentence splitting - could be enhanced with more sophisticated NLP
        sentences = re.split(r"[.!?]+\s+", content)
        return [s.strip() for s in sentences if s.strip()]

    def _get_overlap_text(self, text: str) -> str:
        """Get overlap text from the end of current chunk."""
        if len(text) <= self.chunk_overlap:
            return text

        # Try to find a good break point (sentence or word boundary)
        overlap_start = len(text) - self.chunk_overlap

        # Look for sentence boundary
        sentence_match = re.search(r"[.!?]\s+", text[overlap_start:])
        if sentence_match:
            return text[overlap_start + sentence_match.end() :]

        # Look for word boundary
        word_boundary = text.rfind(" ", overlap_start, overlap_start + 50)
        if word_boundary > overlap_start:
            return text[word_boundary + 1 :]

        # Fall back to character-based overlap
        return text[-self.chunk_overlap :]

    def _chunk_by_characters(self, content: str) -> List[str]:
        """Chunk content by character count with overlap."""
        chunks = []
        start = 0

        while start < len(content):
            end = start + self.chunk_size

            if end >= len(content):
                # Last chunk
                chunks.append(content[start:])
                break

            # Try to find a good break point
            break_point = content.rfind(" ", start, end)
            if break_point > start:
                chunks.append(content[start:break_point])
                start = break_point + 1 - self.chunk_overlap
            else:
                chunks.append(content[start:end])
                start = end - self.chunk_overlap

            # Ensure we don't go backwards
            if start < 0:
                start = 0

        return chunks
