"""Base classes and interfaces for language-specific parsers."""

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from ..models.data_models import DocumentChunk


class CodeUnitType(Enum):
    """Types of code units that can be extracted from source code."""

    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    MODULE = "module"
    IMPORT = "import"
    COMMENT = "comment"
    TEXT = "text"


@dataclass
class CodeUnit:
    """Represents a parsed code unit (function, class, etc.)."""

    type: CodeUnitType
    name: str
    content: str
    start_line: int
    end_line: int
    parent: Optional[str] = None  # e.g., "MyClass" for a method
    docstring: Optional[str] = None
    decorators: Optional[List[str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Ensure decorators is a list if provided."""
        if self.decorators is None:
            self.decorators = []


class ParsingError(Exception):
    """Base exception for parsing errors."""

    pass


class SyntaxParsingError(ParsingError):
    """Raised when source code has syntax errors."""

    pass


class UnsupportedLanguageError(ParsingError):
    """Raised when language is not supported."""

    pass


class LanguageParser(ABC):
    """Abstract base class for language-specific parsers.

    All language parsers must inherit from this class and implement
    the required methods.
    """

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """Initialize the parser with chunking parameters.

        Args:
            chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    @abstractmethod
    def parse(self, content: str, file_path: str) -> List[CodeUnit]:
        """Parse content into code units.

        Args:
            content: Source code content to parse
            file_path: Path to the file (for error reporting)

        Returns:
            List of CodeUnit objects representing parsed code structures

        Raises:
            ParsingError: If parsing fails
        """
        pass

    @abstractmethod
    def chunk(self, code_units: List[CodeUnit], document_id: str) -> List[DocumentChunk]:
        """Convert code units into document chunks.

        Args:
            code_units: List of parsed code units
            document_id: ID of the document being chunked

        Returns:
            List of DocumentChunk objects ready for embedding
        """
        pass

    @classmethod
    @abstractmethod
    def get_supported_extensions(cls) -> List[str]:
        """Get list of file extensions this parser supports.

        Returns:
            List of file extensions (e.g., [".py", ".pyw"])
        """
        pass

    def should_split_unit(self, unit: CodeUnit) -> bool:
        """Determine if a code unit should be split into smaller chunks.

        Args:
            unit: Code unit to check

        Returns:
            True if the unit exceeds the chunk size threshold
        """
        return len(unit.content) > self.chunk_size * 1.5

    def _find_matching_brace(self, content: str, start: int) -> int:
        """Find the position of the matching closing brace.

        Args:
            content: Source code content
            start: Position of the opening brace

        Returns:
            Position of the matching closing brace, or -1 if not found
        """
        count = 1
        i = start + 1

        while i < len(content) and count > 0:
            if content[i] == "{":
                count += 1
            elif content[i] == "}":
                count -= 1
            i += 1

        return i - 1 if count == 0 else -1

    def _create_chunk_metadata(
        self, units: List[CodeUnit], language: str, chunk_type: str = "code"
    ) -> Dict[str, Any]:
        """Create metadata dictionary for a chunk.

        Args:
            units: List of code units in this chunk
            language: Programming language name
            chunk_type: Type of chunk (code, text, etc.)

        Returns:
            Dictionary of metadata
        """
        # Build parent structure string
        parent_structure = " > ".join(
            f"{unit.type.value} {unit.name}"
            for unit in units
            if unit.type in (CodeUnitType.CLASS, CodeUnitType.FUNCTION, CodeUnitType.METHOD)
        )

        return {
            "chunk_type": chunk_type,
            "language": language,
            "parent_structure": parent_structure,
            "start_line": units[0].start_line if units else 0,
            "end_line": units[-1].end_line if units else 0,
            "unit_types": [u.type.value for u in units],
            "unit_names": [u.name for u in units],
        }
