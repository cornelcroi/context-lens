"""Generic text-based chunker for unsupported file types."""

import re
import uuid
from typing import List

from ..models.data_models import DocumentChunk
from .base import CodeUnit, CodeUnitType, LanguageParser


class GenericChunker(LanguageParser):
    """Generic text-based chunker for unsupported file types.

    Falls back to text-based chunking strategies when no language-specific
    parser is available.
    """

    @classmethod
    def get_supported_extensions(cls) -> List[str]:
        """Generic chunker supports all extensions as fallback."""
        return []  # Empty list indicates it's a fallback

    def parse(self, content: str, file_path: str) -> List[CodeUnit]:
        """Parse content as generic text.

        Args:
            content: Text content to parse
            file_path: Path to the file

        Returns:
            Single CodeUnit representing the entire document
        """
        return [
            CodeUnit(
                type=CodeUnitType.TEXT,
                name="document",
                content=content,
                start_line=1,
                end_line=content.count("\n") + 1,
            )
        ]

    def chunk(self, code_units: List[CodeUnit], document_id: str) -> List[DocumentChunk]:
        """Convert text into chunks with smart boundaries.

        Args:
            code_units: List of code units (typically just one for generic text)
            document_id: ID of the document

        Returns:
            List of document chunks
        """
        if not code_units:
            return []

        content = code_units[0].content

        # Try paragraph-based chunking first
        if "\n\n" in content:
            return self._chunk_by_paragraphs(content, document_id)

        # Fall back to sentence-based chunking
        return self._chunk_by_sentences(content, document_id)

    def _chunk_by_paragraphs(self, content: str, document_id: str) -> List[DocumentChunk]:
        """Chunk text by paragraph boundaries.

        Args:
            content: Text content
            document_id: Document ID

        Returns:
            List of chunks split by paragraphs
        """
        paragraphs = re.split(r"\n\s*\n", content)
        chunks = []
        current_chunk = ""
        chunk_index = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # If adding this paragraph would exceed chunk size
            if current_chunk and len(current_chunk) + len(para) + 2 > self.chunk_size:
                # Save current chunk
                chunks.append(self._create_text_chunk(current_chunk, document_id, chunk_index))
                chunk_index += 1

                # Start new chunk with overlap
                overlap = self._get_overlap(current_chunk)
                current_chunk = f"{overlap}\n\n{para}" if overlap else para
            else:
                current_chunk = f"{current_chunk}\n\n{para}" if current_chunk else para

        # Add final chunk
        if current_chunk:
            chunks.append(self._create_text_chunk(current_chunk, document_id, chunk_index))

        return chunks

    def _chunk_by_sentences(self, content: str, document_id: str) -> List[DocumentChunk]:
        """Chunk text by sentence boundaries.

        Args:
            content: Text content
            document_id: Document ID

        Returns:
            List of chunks split by sentences
        """
        # Simple sentence splitting
        sentences = re.split(r"[.!?]+\s+", content)
        chunks = []
        current_chunk = ""
        chunk_index = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # If adding this sentence would exceed chunk size
            if current_chunk and len(current_chunk) + len(sentence) + 1 > self.chunk_size:
                # Save current chunk
                chunks.append(self._create_text_chunk(current_chunk, document_id, chunk_index))
                chunk_index += 1

                # Start new chunk with overlap
                overlap = self._get_overlap(current_chunk)
                current_chunk = f"{overlap} {sentence}" if overlap else sentence
            else:
                current_chunk = f"{current_chunk} {sentence}" if current_chunk else sentence

        # Add final chunk
        if current_chunk:
            chunks.append(self._create_text_chunk(current_chunk, document_id, chunk_index))

        return chunks

    def _get_overlap(self, text: str) -> str:
        """Get overlap text from the end of current chunk.

        Args:
            text: Current chunk text

        Returns:
            Overlap text to include in next chunk
        """
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

    def _create_text_chunk(
        self, content: str, document_id: str, index: int
    ) -> DocumentChunk:
        """Create a document chunk from text content.

        Args:
            content: Chunk content
            document_id: Document ID
            index: Chunk index

        Returns:
            DocumentChunk object
        """
        return DocumentChunk(
            id=str(uuid.uuid4()),
            document_id=document_id,
            content=content.strip(),
            chunk_index=index,
            embedding=[],
            metadata={"chunk_type": "text", "language": "generic"},
        )
