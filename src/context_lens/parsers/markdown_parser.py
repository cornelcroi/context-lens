"""Markdown parser for header-based chunking."""

import re
import uuid
from typing import Any, Dict, List

from ..models.data_models import DocumentChunk
from .base import CodeUnit, CodeUnitType, LanguageParser

import logging

logger = logging.getLogger(__name__)


class MarkdownParser(LanguageParser):
    """Parser for Markdown files with structure-aware chunking."""

    @classmethod
    def get_supported_extensions(cls) -> List[str]:
        """Get supported file extensions."""
        return [".md", ".markdown", ".mdx"]

    def parse(self, content: str, file_path: str) -> List[CodeUnit]:
        """Parse Markdown into logical sections."""
        sections = self._split_by_headers(content)
        code_units = []

        for section in sections:
            unit = self._create_markdown_unit(section)
            if unit:
                code_units.append(unit)

        return code_units

    def _split_by_headers(self, content: str) -> List[Dict[str, Any]]:
        """Split markdown by header hierarchy."""
        lines = content.split("\n")
        sections = []
        current_section = {"level": 0, "title": "Introduction", "content": [], "start_line": 1}

        for i, line in enumerate(lines, 1):
            # Check for ATX headers (# Header)
            atx_match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if atx_match:
                # Save previous section
                if current_section["content"]:
                    current_section["end_line"] = i - 1
                    sections.append(current_section)

                # Start new section
                level = len(atx_match.group(1))
                title = atx_match.group(2).strip()
                current_section = {"level": level, "title": title, "content": [line], "start_line": i}
            else:
                current_section["content"].append(line)

        # Add final section
        if current_section["content"]:
            current_section["end_line"] = len(lines)
            sections.append(current_section)

        return sections

    def _create_markdown_unit(self, section: Dict[str, Any]) -> CodeUnit:
        """Create a code unit from a markdown section."""
        content = "\n".join(section["content"])

        # Determine unit type based on header level
        if section["level"] == 1:
            unit_type = CodeUnitType.MODULE
        elif section["level"] == 2:
            unit_type = CodeUnitType.CLASS
        else:
            unit_type = CodeUnitType.FUNCTION

        # Extract code blocks
        code_blocks = re.findall(r"```[\s\S]*?```", content)

        return CodeUnit(
            type=unit_type,
            name=section["title"],
            content=content,
            start_line=section["start_line"],
            end_line=section["end_line"],
            metadata={
                "header_level": section["level"],
                "has_code_blocks": len(code_blocks) > 0,
                "code_block_count": len(code_blocks),
                "word_count": len(content.split()),
            },
        )

    def chunk(self, code_units: List[CodeUnit], document_id: str) -> List[DocumentChunk]:
        """Convert markdown sections into chunks."""
        if not code_units:
            return []

        chunks = []
        current_units = []
        current_size = 0

        for unit in code_units:
            unit_size = len(unit.content)

            if unit_size > self.chunk_size * 1.5:
                if current_units:
                    chunks.append(self._create_markdown_chunk(current_units, document_id, len(chunks)))
                    current_units = []
                    current_size = 0
                chunks.extend(self._split_large_markdown_section(unit, document_id, len(chunks)))
                continue

            if current_size + unit_size > self.chunk_size and current_units:
                chunks.append(self._create_markdown_chunk(current_units, document_id, len(chunks)))
                current_units = []
                current_size = 0

            current_units.append(unit)
            current_size += unit_size

        if current_units:
            chunks.append(self._create_markdown_chunk(current_units, document_id, len(chunks)))

        return chunks

    def _create_markdown_chunk(
        self, units: List[CodeUnit], document_id: str, index: int
    ) -> DocumentChunk:
        """Create a chunk from markdown sections."""
        content = "\n\n".join(unit.content for unit in units)
        section_hierarchy = " > ".join(unit.name for unit in units)

        return DocumentChunk(
            id=str(uuid.uuid4()),
            document_id=document_id,
            content=content,
            chunk_index=index,
            embedding=[],
            metadata={
                "chunk_type": "markdown",
                "language": "markdown",
                "sections": [u.name for u in units],
                "section_hierarchy": section_hierarchy,
                "header_levels": [u.metadata.get("header_level", 0) for u in units],
                "start_line": units[0].start_line,
                "end_line": units[-1].end_line,
            },
        )

    def _split_large_markdown_section(
        self, unit: CodeUnit, document_id: str, start_index: int
    ) -> List[DocumentChunk]:
        """Split a large markdown section by paragraphs."""
        paragraphs = re.split(r"\n\s*\n", unit.content)
        chunks = []
        current_paras = []
        current_size = 0

        for para in paragraphs:
            para_size = len(para)

            if current_size + para_size > self.chunk_size and current_paras:
                chunk_content = "\n\n".join(current_paras)
                chunks.append(
                    DocumentChunk(
                        id=str(uuid.uuid4()),
                        document_id=document_id,
                        content=chunk_content,
                        chunk_index=start_index + len(chunks),
                        embedding=[],
                        metadata={
                            "chunk_type": "markdown_split",
                            "language": "markdown",
                            "parent_section": unit.name,
                            "header_level": unit.metadata.get("header_level", 0),
                            "is_partial": True,
                        },
                    )
                )

                # Start new chunk with overlap
                current_paras = [current_paras[-1], para] if current_paras else [para]
                current_size = sum(len(p) for p in current_paras)
            else:
                current_paras.append(para)
                current_size += para_size

        if current_paras:
            chunk_content = "\n\n".join(current_paras)
            chunks.append(
                DocumentChunk(
                    id=str(uuid.uuid4()),
                    document_id=document_id,
                    content=chunk_content,
                    chunk_index=start_index + len(chunks),
                    embedding=[],
                    metadata={
                        "chunk_type": "markdown_split",
                        "language": "markdown",
                        "parent_section": unit.name,
                        "header_level": unit.metadata.get("header_level", 0),
                        "is_partial": True,
                    },
                )
            )

        return chunks
