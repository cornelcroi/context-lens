"""File reading components for different file types."""

import ast
import hashlib
import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Tuple

import chardet

from ..errors import (
    ErrorCategory,
    KnowledgeBaseError,
)

logger = logging.getLogger(__name__)


class FileProcessingError(KnowledgeBaseError):
    """Exception raised during file processing."""

    def __init__(
        self, message: str, error_type: str = "processing_error", details: Optional[dict] = None
    ):
        # Map old error_type strings to ErrorCategory
        error_category_map = {
            "file_not_found": ErrorCategory.FILE_NOT_FOUND,
            "invalid_file_type": ErrorCategory.UNSUPPORTED_FILE_TYPE,
            "file_too_large": ErrorCategory.FILE_TOO_LARGE,
            "unsupported_file_type": ErrorCategory.UNSUPPORTED_FILE_TYPE,
            "encoding_error": ErrorCategory.ENCODING_ERROR,
            "file_read_error": ErrorCategory.FILE_READ_ERROR,
            "python_processing_error": ErrorCategory.PYTHON_PROCESSING_ERROR,
            "text_processing_error": ErrorCategory.TEXT_PROCESSING_ERROR,
            "incompatible_reader": ErrorCategory.CONTENT_EXTRACTION_ERROR,
            "processing_error": ErrorCategory.CONTENT_EXTRACTION_ERROR,
        }

        error_category = error_category_map.get(error_type, ErrorCategory.CONTENT_EXTRACTION_ERROR)
        super().__init__(message=message, error_category=error_category, details=details or {})
        self.error_type = error_type  # Keep for backward compatibility


class FileReader(ABC):
    """Base class for file readers."""

    SUPPORTED_EXTENSIONS = [
        ".py",
        ".txt",
        ".md",  # Python, text, markdown
        ".js",
        ".jsx",
        ".ts",
        ".tsx",  # JavaScript/TypeScript
        ".java",
        ".cpp",
        ".c",
        ".h",
        ".hpp",  # Java, C/C++
        ".go",
        ".rs",
        ".rb",
        ".php",  # Go, Rust, Ruby, PHP
        ".json",
        ".yaml",
        ".yml",
        ".toml",  # Config files
        ".sh",
        ".bash",
        ".zsh",  # Shell scripts
    ]
    MAX_FILE_SIZE_MB = 10

    def __init__(self):
        self.max_file_size_bytes = self.MAX_FILE_SIZE_MB * 1024 * 1024

    @abstractmethod
    def can_read(self, file_path: str) -> bool:
        """Check if this reader can handle the given file type."""

    @abstractmethod
    def extract_content(self, file_path: str) -> str:
        """Extract content from the file."""

    def validate_file(self, file_path: str) -> None:
        """Validate file before processing.

        Raises:
            FileProcessingError: If file validation fails
        """
        logger.debug(f"Validating file: {file_path}")
        path = Path(file_path)

        # Check if file exists
        if not path.exists():
            logger.error(f"File not found: {file_path}")
            raise FileProcessingError(
                f"File not found: {file_path}",
                error_type="file_not_found",
                details={"file_path": file_path},
            )

        # Check if it's a file (not directory)
        if not path.is_file():
            logger.error(f"Path is not a file: {file_path}")
            raise FileProcessingError(
                f"Path is not a file: {file_path}",
                error_type="invalid_file_type",
                details={"file_path": file_path, "is_directory": path.is_dir()},
            )

        # Check file permissions
        if not os.access(file_path, os.R_OK):
            logger.error(f"File access denied: {file_path}")
            raise FileProcessingError(
                f"Permission denied: Cannot read file {file_path}",
                error_type="file_access_denied",
                details={"file_path": file_path},
            )

        # Check file size
        try:
            file_size = path.stat().st_size
            if file_size == 0:
                logger.warning(f"File is empty: {file_path}")

            if file_size > self.max_file_size_bytes:
                logger.error(f"File too large: {file_size} bytes (max: {self.max_file_size_bytes})")
                raise FileProcessingError(
                    f"File too large: {file_size} bytes (max: {self.max_file_size_bytes} bytes)",
                    error_type="file_too_large",
                    details={
                        "file_path": file_path,
                        "file_size": file_size,
                        "max_size": self.max_file_size_bytes,
                        "file_size_mb": round(file_size / (1024 * 1024), 2),
                        "max_size_mb": self.MAX_FILE_SIZE_MB,
                    },
                )
        except OSError as e:
            logger.error(f"Failed to get file stats for {file_path}: {e}")
            raise FileProcessingError(
                f"Failed to access file: {str(e)}",
                error_type="file_read_error",
                details={"file_path": file_path, "error": str(e)},
            )

        # Check file extension
        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            logger.error(f"Unsupported file type: {path.suffix}")
            raise FileProcessingError(
                f"Unsupported file type: {path.suffix}. Supported types: {', '.join(self.SUPPORTED_EXTENSIONS)}",
                error_type="unsupported_file_type",
                details={
                    "file_path": file_path,
                    "extension": path.suffix,
                    "supported_extensions": self.SUPPORTED_EXTENSIONS,
                },
            )

        logger.debug(f"File validation successful: {file_path}")

    def detect_encoding(self, file_path: str) -> str:
        """Detect file encoding with fallback options.

        Args:
            file_path: Path to the file

        Returns:
            Detected encoding string
        """
        try:
            logger.debug(f"Detecting encoding for: {file_path}")

            with open(file_path, "rb") as f:
                raw_data = f.read(10000)  # Read first 10KB for detection

            # Use chardet for detection
            detection = chardet.detect(raw_data)
            encoding = detection.get("encoding", "utf-8")
            confidence = detection.get("confidence", 0)

            logger.debug(f"Detected encoding: {encoding} (confidence: {confidence:.2f})")

            # If confidence is low, try common encodings
            if confidence < 0.7:
                logger.debug(f"Low confidence ({confidence:.2f}), trying fallback encodings")
                for fallback_encoding in ["utf-8", "utf-16", "latin-1", "cp1252"]:
                    try:
                        with open(file_path, "r", encoding=fallback_encoding) as f:
                            f.read(1000)  # Try to read some content
                        logger.debug(
                            f"Successfully validated fallback encoding: {fallback_encoding}"
                        )
                        return fallback_encoding
                    except (UnicodeDecodeError, UnicodeError):
                        continue

            return encoding or "utf-8"

        except Exception as e:
            logger.warning(f"Encoding detection failed for {file_path}, defaulting to utf-8: {e}")
            # Default to utf-8 if detection fails
            return "utf-8"

    def read_file_content(self, file_path: str) -> str:
        """Read file content with encoding detection.

        Args:
            file_path: Path to the file

        Returns:
            File content as string

        Raises:
            FileProcessingError: If file reading fails
        """
        encoding = self.detect_encoding(file_path)

        try:
            logger.debug(f"Reading file content with encoding {encoding}: {file_path}")
            with open(file_path, "r", encoding=encoding) as f:
                content = f.read()
            logger.debug(f"Successfully read {len(content)} characters from {file_path}")
            return content
        except UnicodeDecodeError as e:
            logger.warning(
                f"Unicode decode error with {encoding}, trying with error replacement: {e}"
            )
            # Try with error handling
            try:
                with open(file_path, "r", encoding=encoding, errors="replace") as f:
                    content = f.read()
                logger.info(f"Read file with character replacement: {file_path}")
                return content
            except Exception as inner_e:
                logger.error(f"Failed to read file even with error replacement: {inner_e}")
                raise FileProcessingError(
                    f"Failed to read file with encoding {encoding}: {str(inner_e)}",
                    error_type="encoding_error",
                    details={
                        "file_path": file_path,
                        "encoding": encoding,
                        "error": str(inner_e),
                        "original_error": str(e),
                    },
                )
        except PermissionError as e:
            logger.error(f"Permission denied reading file: {file_path}")
            raise FileProcessingError(
                f"Permission denied: Cannot read file {file_path}",
                error_type="file_access_denied",
                details={"file_path": file_path, "error": str(e)},
            )
        except FileNotFoundError as e:
            logger.error(f"File not found during read: {file_path}")
            raise FileProcessingError(
                f"File not found: {file_path}",
                error_type="file_not_found",
                details={"file_path": file_path, "error": str(e)},
            )
        except Exception as e:
            logger.error(f"Unexpected error reading file {file_path}: {e}")
            raise FileProcessingError(
                f"Failed to read file: {str(e)}",
                error_type="file_read_error",
                details={"file_path": file_path, "encoding": encoding, "error": str(e)},
            )

    def get_file_hash(self, content: str) -> str:
        """Generate hash for file content."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def process_file(self, file_path: str) -> Tuple[str, str]:
        """Process file and return content and hash.

        Args:
            file_path: Path to the file to process

        Returns:
            Tuple of (content, content_hash)

        Raises:
            FileProcessingError: If file processing fails
        """
        logger.debug(f"Processing file: {file_path}")

        self.validate_file(file_path)

        if not self.can_read(file_path):
            logger.error(f"Reader {self.__class__.__name__} cannot handle file: {file_path}")
            raise FileProcessingError(
                f"This reader cannot handle file: {file_path}",
                error_type="incompatible_reader",
                details={"file_path": file_path, "reader_type": self.__class__.__name__},
            )

        content = self.extract_content(file_path)
        content_hash = self.get_file_hash(content)

        logger.debug(f"File processed successfully: {file_path} (hash: {content_hash[:16]}...)")
        return content, content_hash


class PythonFileReader(FileReader):
    """Specialized reader for Python (.py) files."""

    def can_read(self, file_path: str) -> bool:
        """Check if this is a Python file."""
        return Path(file_path).suffix.lower() == ".py"

    def extract_content(self, file_path: str) -> str:
        """Extract content from Python file with syntax awareness."""
        raw_content = self.read_file_content(file_path)

        try:
            # Parse the Python file to validate syntax
            ast.parse(raw_content)

            # For now, return the raw content
            # Future enhancement: could extract docstrings, comments separately
            return raw_content

        except SyntaxError:
            # If syntax is invalid, still return content but log the issue
            # This allows processing of incomplete or malformed Python files
            return raw_content
        except Exception as e:
            raise FileProcessingError(
                f"Failed to process Python file: {str(e)}",
                error_type="python_processing_error",
                details={"file_path": file_path, "error": str(e)},
            )


class TextFileReader(FileReader):
    """Reader for plain text and text-based files (.txt, .md, .json, .yaml, etc.)."""

    # All text-based file extensions we support
    TEXT_EXTENSIONS = {
        ".txt",
        ".md",
        ".markdown",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".java",
        ".cpp",
        ".c",
        ".h",
        ".hpp",
        ".go",
        ".rs",
        ".rb",
        ".php",
        ".json",
        ".yaml",
        ".yml",
        ".toml",
        ".sh",
        ".bash",
        ".zsh",
        ".css",
        ".html",
    }

    def can_read(self, file_path: str) -> bool:
        """Check if this is a text-based file."""
        return Path(file_path).suffix.lower() in self.TEXT_EXTENSIONS

    def extract_content(self, file_path: str) -> str:
        """Extract content from text file."""
        try:
            return self.read_file_content(file_path)
        except Exception as e:
            raise FileProcessingError(
                f"Failed to process text file: {str(e)}",
                error_type="text_processing_error",
                details={"file_path": file_path, "error": str(e)},
            )


class FileReaderFactory:
    """Factory for creating appropriate file readers."""

    def __init__(self):
        self._readers = [PythonFileReader(), TextFileReader()]

    def get_reader(self, file_path: str) -> FileReader:
        """Get appropriate reader for the file type."""
        for reader in self._readers:
            if reader.can_read(file_path):
                return reader

        # If no specific reader found, check if it's a supported extension
        path = Path(file_path)
        if path.suffix.lower() in FileReader.SUPPORTED_EXTENSIONS:
            # Default to text reader for supported extensions
            return TextFileReader()

        raise FileProcessingError(
            f"No reader available for file type: {path.suffix}",
            error_type="no_reader_available",
            details={"file_path": file_path, "extension": path.suffix},
        )
