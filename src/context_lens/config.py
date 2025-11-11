"""Configuration management for the MCP Knowledge Base Server."""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import platformdirs

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Exception raised for configuration errors."""


def get_base_dir() -> Path:
    """Get the base directory for Context-Lens data.
    
    Can be overridden with CONTEXT_LENS_HOME environment variable.
    Otherwise uses platform-specific data directory.
    """
    if home := os.getenv("CONTEXT_LENS_HOME"):
        return Path(home)
    return Path(platformdirs.user_data_dir("context-lens"))


@dataclass
class DatabaseConfig:
    """Database configuration settings."""

    path: str = str(get_base_dir() / "knowledge_base.db")
    table_prefix: str = "kb_"

    def validate(self) -> None:
        """Validate database configuration."""
        if not self.path:
            raise ConfigurationError("Database path cannot be empty")

        if not self.table_prefix:
            raise ConfigurationError("Database table prefix cannot be empty")

        # Ensure parent directory exists or can be created
        db_path = Path(self.path)
        try:
            db_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise ConfigurationError(f"Cannot create database directory: {e}")


@dataclass
class EmbeddingConfig:
    """Embedding model configuration settings."""

    model: str = "sentence-transformers/all-MiniLM-L6-v2"
    batch_size: int = 32
    cache_dir: str = str(get_base_dir() / "models")

    def validate(self) -> None:
        """Validate embedding configuration."""
        if not self.model:
            raise ConfigurationError("Embedding model cannot be empty")

        if self.batch_size <= 0:
            raise ConfigurationError(
                f"Embedding batch size must be positive, got {self.batch_size}"
            )

        if self.batch_size > 1000:
            logger.warning(
                f"Large embedding batch size ({self.batch_size}) may cause memory issues"
            )

        if not self.cache_dir:
            raise ConfigurationError("Embedding cache directory cannot be empty")

        # Ensure cache directory exists or can be created
        cache_path = Path(self.cache_dir)
        try:
            cache_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise ConfigurationError(f"Cannot create cache directory: {e}")


@dataclass
class ProcessingConfig:
    """Document processing configuration settings."""

    max_file_size_mb: int = 10
    chunk_size: int = 1000
    chunk_overlap: int = 200
    supported_extensions: List[str] = field(
        default_factory=lambda: [
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
    )

    def validate(self) -> None:
        """Validate processing configuration."""
        if self.max_file_size_mb <= 0:
            raise ConfigurationError(f"Max file size must be positive, got {self.max_file_size_mb}")

        if self.max_file_size_mb > 100:
            logger.warning(
                f"Large max file size ({self.max_file_size_mb}MB) may cause memory issues"
            )

        if self.chunk_size <= 0:
            raise ConfigurationError(f"Chunk size must be positive, got {self.chunk_size}")

        if self.chunk_size < 100:
            logger.warning(
                f"Small chunk size ({self.chunk_size}) may result in poor search quality"
            )

        if self.chunk_overlap < 0:
            raise ConfigurationError(f"Chunk overlap cannot be negative, got {self.chunk_overlap}")

        if self.chunk_overlap >= self.chunk_size:
            raise ConfigurationError(
                f"Chunk overlap ({self.chunk_overlap}) must be less than "
                f"chunk size ({self.chunk_size})"
            )

        if not self.supported_extensions:
            raise ConfigurationError("Supported extensions list cannot be empty")

        # Validate extension format
        for ext in self.supported_extensions:
            if not ext.startswith("."):
                raise ConfigurationError(f"File extension must start with '.', got '{ext}'")


@dataclass
class ServerConfig:
    """Server configuration settings."""

    name: str = "knowledge-base"
    log_level: str = "INFO"

    def validate(self) -> None:
        """Validate server configuration."""
        if not self.name:
            raise ConfigurationError("Server name cannot be empty")

        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_log_levels:
            raise ConfigurationError(
                f"Invalid log level '{self.log_level}'. "
                f"Must be one of: {', '.join(valid_log_levels)}"
            )

        # Normalize log level to uppercase
        self.log_level = self.log_level.upper()


@dataclass
class Config:
    """Main configuration class."""

    database: DatabaseConfig
    embedding: EmbeddingConfig
    processing: ProcessingConfig
    server: ServerConfig

    def validate(self) -> None:
        """Validate all configuration sections."""
        try:
            self.database.validate()
            self.embedding.validate()
            self.processing.validate()
            self.server.validate()
            logger.info("Configuration validation successful")
        except ConfigurationError as e:
            logger.error(f"Configuration validation failed: {e}")
            raise

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables with defaults.

        Returns:
            Config: Configuration object loaded from environment variables

        Raises:
            ConfigurationError: If configuration validation fails
        """
        try:
            # Parse supported extensions from environment
            extensions_str = os.getenv("SUPPORTED_EXTENSIONS", ".py,.txt")
            supported_extensions = [ext.strip() for ext in extensions_str.split(",") if ext.strip()]

            # Parse batch size with error handling
            try:
                batch_size = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))
            except ValueError:
                logger.warning("Invalid EMBEDDING_BATCH_SIZE, using default: 32")
                batch_size = 32

            # Parse numeric values with error handling
            try:
                max_file_size = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
            except ValueError:
                logger.warning("Invalid MAX_FILE_SIZE_MB, using default: 10")
                max_file_size = 10

            try:
                chunk_size = int(os.getenv("CHUNK_SIZE", "1000"))
            except ValueError:
                logger.warning("Invalid CHUNK_SIZE, using default: 1000")
                chunk_size = 1000

            try:
                chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "200"))
            except ValueError:
                logger.warning("Invalid CHUNK_OVERLAP, using default: 200")
                chunk_overlap = 200

            config = cls(
                database=DatabaseConfig(
                    path=os.getenv(
                        "LANCE_DB_PATH",
                        str(get_base_dir() / "knowledge_base.db")
                    ),
                    table_prefix=os.getenv("LANCE_DB_TABLE_PREFIX", "kb_"),
                ),
                embedding=EmbeddingConfig(
                    model=os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
                    batch_size=batch_size,
                    cache_dir=os.getenv(
                        "EMBEDDING_CACHE_DIR",
                        str(get_base_dir() / "models")
                    ),
                ),
                processing=ProcessingConfig(
                    max_file_size_mb=max_file_size,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    supported_extensions=supported_extensions,
                ),
                server=ServerConfig(
                    name=os.getenv("MCP_SERVER_NAME", "knowledge-base"),
                    log_level=os.getenv("LOG_LEVEL", "INFO"),
                ),
            )

            # Validate configuration
            config.validate()

            logger.info("Configuration loaded from environment variables")
            return config

        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration from environment: {e}")

    @classmethod
    def from_file(cls, config_path: str) -> "Config":
        """Load configuration from YAML file.

        Args:
            config_path: Path to the YAML configuration file

        Returns:
            Config: Configuration object loaded from file

        Raises:
            ConfigurationError: If file not found or configuration is invalid
        """
        config_file = Path(config_path)

        if not config_file.exists():
            raise ConfigurationError(f"Configuration file not found: {config_path}")

        if not config_file.is_file():
            raise ConfigurationError(f"Configuration path is not a file: {config_path}")

        try:
            import yaml
        except ImportError:
            raise ConfigurationError(
                "PyYAML is required to load configuration from file. "
                "Install it with: pip install pyyaml"
            )

        try:
            with open(config_file, "r") as f:
                config_data = yaml.safe_load(f)

            if not config_data:
                raise ConfigurationError(f"Configuration file is empty: {config_path}")

            if not isinstance(config_data, dict):
                raise ConfigurationError(
                    f"Configuration file must contain a YAML dictionary: {config_path}"
                )

            # Extract configuration sections with defaults
            db_config = config_data.get("database", {})
            emb_config = config_data.get("embedding", {})
            proc_config = config_data.get("processing", {})
            srv_config = config_data.get("server", {})

            # Create configuration with explicit defaults
            config = cls(
                database=DatabaseConfig(
                    path=db_config.get(
                        "path",
                        str(get_base_dir() / "knowledge_base.db")
                    ),
                    table_prefix=db_config.get("table_prefix", "kb_"),
                ),
                embedding=EmbeddingConfig(
                    model=emb_config.get("model", "sentence-transformers/all-MiniLM-L6-v2"),
                    batch_size=emb_config.get("batch_size", 32),
                    cache_dir=emb_config.get(
                        "cache_dir",
                        str(get_base_dir() / "models")
                    ),
                ),
                processing=ProcessingConfig(
                    max_file_size_mb=proc_config.get("max_file_size_mb", 10),
                    chunk_size=proc_config.get("chunk_size", 1000),
                    chunk_overlap=proc_config.get("chunk_overlap", 200),
                    supported_extensions=proc_config.get("supported_extensions", [".py", ".txt"]),
                ),
                server=ServerConfig(
                    name=srv_config.get("name", "knowledge-base"),
                    log_level=srv_config.get("log_level", "INFO"),
                ),
            )

            # Validate configuration
            config.validate()

            logger.info(f"Configuration loaded from file: {config_path}")
            return config

        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in configuration file: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration from file: {e}")

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Config":
        """Load configuration from a dictionary.

        Args:
            config_dict: Dictionary containing configuration data

        Returns:
            Config: Configuration object

        Raises:
            ConfigurationError: If configuration is invalid
        """
        try:
            db_config = config_dict.get("database", {})
            emb_config = config_dict.get("embedding", {})
            proc_config = config_dict.get("processing", {})
            srv_config = config_dict.get("server", {})

            config = cls(
                database=DatabaseConfig(**db_config) if db_config else DatabaseConfig(),
                embedding=EmbeddingConfig(**emb_config) if emb_config else EmbeddingConfig(),
                processing=ProcessingConfig(**proc_config) if proc_config else ProcessingConfig(),
                server=ServerConfig(**srv_config) if srv_config else ServerConfig(),
            )

            config.validate()
            return config

        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration from dictionary: {e}")

    @classmethod
    def load(cls, config_file: Optional[str] = None) -> "Config":
        """Load configuration with fallback priority.

        Priority: specified file -> default config.yaml -> env -> defaults.

        Args:
            config_file: Optional path to configuration file

        Returns:
            Config: Configuration object

        Raises:
            ConfigurationError: If configuration loading or validation fails
        """
        # If specific config file is provided, try to load it
        if config_file:
            if Path(config_file).exists():
                logger.info(f"Loading configuration from specified file: {config_file}")
                return cls.from_file(config_file)
            else:
                logger.warning(
                    f"Specified config file not found: {config_file}, falling back to defaults"
                )

        # Check for default config.yaml in current directory
        default_config = Path("config.yaml")
        if default_config.exists():
            logger.info("Loading configuration from default config.yaml")
            return cls.from_file(str(default_config))

        # Fall back to environment variables
        logger.info("Loading configuration from environment variables")
        return cls.from_env()

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary format.

        Returns:
            Dictionary representation of configuration
        """
        return {
            "database": {"path": self.database.path, "table_prefix": self.database.table_prefix},
            "embedding": {
                "model": self.embedding.model,
                "batch_size": self.embedding.batch_size,
                "cache_dir": self.embedding.cache_dir,
            },
            "processing": {
                "max_file_size_mb": self.processing.max_file_size_mb,
                "chunk_size": self.processing.chunk_size,
                "chunk_overlap": self.processing.chunk_overlap,
                "supported_extensions": self.processing.supported_extensions,
            },
            "server": {"name": self.server.name, "log_level": self.server.log_level},
        }
