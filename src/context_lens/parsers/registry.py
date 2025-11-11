"""Parser registry for managing language-specific parsers."""

import logging
from pathlib import Path
from typing import Dict, Optional, Type

from .base import LanguageParser

logger = logging.getLogger(__name__)


class ParserRegistry:
    """Registry for language-specific parsers.

    Manages registration and selection of parsers based on file extensions.
    Provides fallback to generic chunker when no specific parser is available.
    """

    def __init__(self):
        """Initialize the parser registry."""
        self._parsers: Dict[str, Type[LanguageParser]] = {}
        self._generic_chunker: Optional[LanguageParser] = None
        self._parser_stats: Dict[str, Dict[str, int]] = {}

    def register(self, parser_class: Type[LanguageParser]) -> None:
        """Register a language parser.

        Args:
            parser_class: Parser class to register (must inherit from LanguageParser)
        """
        if not issubclass(parser_class, LanguageParser):
            raise TypeError(f"{parser_class.__name__} must inherit from LanguageParser")

        extensions = parser_class.get_supported_extensions()
        for ext in extensions:
            # Normalize extension (ensure it starts with .)
            normalized_ext = ext if ext.startswith(".") else f".{ext}"
            self._parsers[normalized_ext.lower()] = parser_class
            logger.info(f"Registered {parser_class.__name__} for {normalized_ext}")

    def get_parser(
        self, file_path: str, chunk_size: int = 1000, chunk_overlap: int = 200
    ) -> LanguageParser:
        """Get appropriate parser for a file.

        Args:
            file_path: Path to the file
            chunk_size: Maximum chunk size in characters
            chunk_overlap: Overlap between chunks in characters

        Returns:
            Language-specific parser or generic chunker as fallback
        """
        ext = Path(file_path).suffix.lower()

        if ext in self._parsers:
            parser_class = self._parsers[ext]
            logger.debug(f"Using {parser_class.__name__} for {file_path}")
            self._record_parser_usage(parser_class.__name__)
            return parser_class(chunk_size, chunk_overlap)
        else:
            logger.debug(f"Using GenericChunker for {file_path} (extension: {ext})")
            self._record_parser_usage("GenericChunker")

            if self._generic_chunker is None:
                # Import here to avoid circular dependency
                from .generic_chunker import GenericChunker

                return GenericChunker(chunk_size, chunk_overlap)

            return self._generic_chunker

    def set_generic_chunker(self, chunker: LanguageParser) -> None:
        """Set the generic chunker for fallback.

        Args:
            chunker: Generic chunker instance
        """
        self._generic_chunker = chunker
        logger.info(f"Set generic chunker: {chunker.__class__.__name__}")

    def _record_parser_usage(self, parser_name: str) -> None:
        """Record parser usage for statistics.

        Args:
            parser_name: Name of the parser being used
        """
        if parser_name not in self._parser_stats:
            self._parser_stats[parser_name] = {"success": 0, "fallback": 0}
        self._parser_stats[parser_name]["success"] += 1

    def record_fallback(self, parser_name: str) -> None:
        """Record when a parser falls back to generic chunker.

        Args:
            parser_name: Name of the parser that failed
        """
        if parser_name in self._parser_stats:
            self._parser_stats[parser_name]["fallback"] += 1
        logger.warning(f"{parser_name} fell back to generic chunker")

    def get_stats(self) -> Dict[str, Dict[str, int]]:
        """Get parser usage statistics.

        Returns:
            Dictionary mapping parser names to usage statistics
        """
        return self._parser_stats.copy()

    def list_registered_parsers(self) -> Dict[str, str]:
        """List all registered parsers and their supported extensions.

        Returns:
            Dictionary mapping extensions to parser class names
        """
        return {ext: parser.__name__ for ext, parser in self._parsers.items()}

    def is_extension_supported(self, extension: str) -> bool:
        """Check if a file extension has a registered parser.

        Args:
            extension: File extension to check (with or without leading dot)

        Returns:
            True if a parser is registered for this extension
        """
        normalized_ext = extension if extension.startswith(".") else f".{extension}"
        return normalized_ext.lower() in self._parsers

    def clear(self) -> None:
        """Clear all registered parsers and statistics."""
        self._parsers.clear()
        self._parser_stats.clear()
        self._generic_chunker = None
        logger.info("Parser registry cleared")


# Global parser registry instance
_global_registry: Optional[ParserRegistry] = None


def get_parser_registry() -> ParserRegistry:
    """Get the global parser registry instance.

    Returns:
        Global ParserRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = ParserRegistry()
    return _global_registry


def reset_parser_registry() -> None:
    """Reset the global parser registry (mainly for testing)."""
    global _global_registry
    _global_registry = None
