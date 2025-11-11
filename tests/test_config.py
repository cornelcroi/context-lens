"""Tests for configuration management."""

import os
import tempfile
from pathlib import Path

import pytest

from context_lens.config import (
    Config,
    ConfigurationError,
    DatabaseConfig,
    EmbeddingConfig,
    ProcessingConfig,
    ServerConfig,
)


class TestDatabaseConfig:
    """Tests for DatabaseConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = DatabaseConfig()
        # Path should use platform-specific directory
        assert "context-lens" in config.path
        assert "knowledge_base.db" in config.path
        assert config.table_prefix == "kb_"

    def test_validation_success(self):
        """Test successful validation."""
        config = DatabaseConfig(path="./test.db", table_prefix="test_")
        config.validate()  # Should not raise

    def test_validation_empty_path(self):
        """Test validation fails with empty path."""
        config = DatabaseConfig(path="", table_prefix="kb_")
        with pytest.raises(ConfigurationError, match="path cannot be empty"):
            config.validate()

    def test_validation_empty_prefix(self):
        """Test validation fails with empty prefix."""
        config = DatabaseConfig(path="./test.db", table_prefix="")
        with pytest.raises(ConfigurationError, match="prefix cannot be empty"):
            config.validate()


class TestEmbeddingConfig:
    """Tests for EmbeddingConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = EmbeddingConfig()
        assert config.model == "sentence-transformers/all-MiniLM-L6-v2"
        assert config.batch_size == 32
        # Cache dir should use platform-specific directory
        assert "context-lens" in config.cache_dir
        assert "models" in config.cache_dir

    def test_validation_success(self):
        """Test successful validation."""
        config = EmbeddingConfig(model="test-model", batch_size=16, cache_dir="./cache")
        config.validate()  # Should not raise

    def test_validation_empty_model(self):
        """Test validation fails with empty model."""
        config = EmbeddingConfig(model="", batch_size=32, cache_dir="./cache")
        with pytest.raises(ConfigurationError, match="model cannot be empty"):
            config.validate()

    def test_validation_invalid_batch_size(self):
        """Test validation fails with invalid batch size."""
        config = EmbeddingConfig(model="test", batch_size=0, cache_dir="./cache")
        with pytest.raises(ConfigurationError, match="batch size must be positive"):
            config.validate()


class TestProcessingConfig:
    """Tests for ProcessingConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = ProcessingConfig()
        assert config.max_file_size_mb == 10
        assert config.chunk_size == 1000
        assert config.chunk_overlap == 200
        # Check that default extensions include common file types
        assert ".py" in config.supported_extensions
        assert ".txt" in config.supported_extensions
        assert ".md" in config.supported_extensions
        assert ".js" in config.supported_extensions
        assert len(config.supported_extensions) > 10  # Should have 20+ types

    def test_validation_success(self):
        """Test successful validation."""
        config = ProcessingConfig(
            max_file_size_mb=5,
            chunk_size=500,
            chunk_overlap=100,
            supported_extensions=[".py", ".txt", ".md"],
        )
        config.validate()  # Should not raise

    def test_validation_invalid_chunk_overlap(self):
        """Test validation fails when overlap >= chunk size."""
        config = ProcessingConfig(chunk_size=100, chunk_overlap=100)
        with pytest.raises(ConfigurationError, match="overlap.*must be less than chunk size"):
            config.validate()

    def test_validation_invalid_extension_format(self):
        """Test validation fails with invalid extension format."""
        config = ProcessingConfig(supported_extensions=["py", ".txt"])
        with pytest.raises(ConfigurationError, match="extension must start with"):
            config.validate()


class TestServerConfig:
    """Tests for ServerConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = ServerConfig()
        assert config.name == "knowledge-base"
        assert config.log_level == "INFO"

    def test_validation_success(self):
        """Test successful validation."""
        config = ServerConfig(name="test-server", log_level="DEBUG")
        config.validate()  # Should not raise
        assert config.log_level == "DEBUG"  # Should be normalized to uppercase

    def test_validation_invalid_log_level(self):
        """Test validation fails with invalid log level."""
        config = ServerConfig(name="test", log_level="INVALID")
        with pytest.raises(ConfigurationError, match="Invalid log level"):
            config.validate()


class TestConfig:
    """Tests for main Config class."""

    def test_from_env_defaults(self):
        """Test loading configuration from environment with defaults."""
        # Clear any existing environment variables
        env_vars = [
            "LANCE_DB_PATH",
            "LANCE_DB_TABLE_PREFIX",
            "EMBEDDING_MODEL",
            "EMBEDDING_BATCH_SIZE",
            "EMBEDDING_CACHE_DIR",
            "MAX_FILE_SIZE_MB",
            "CHUNK_SIZE",
            "CHUNK_OVERLAP",
            "SUPPORTED_EXTENSIONS",
            "MCP_SERVER_NAME",
            "LOG_LEVEL",
        ]
        for var in env_vars:
            os.environ.pop(var, None)
        
        # Also clear CONTEXT_LENS_HOME to ensure platform defaults
        os.environ.pop("CONTEXT_LENS_HOME", None)

        config = Config.from_env()

        # Path should use platform-specific directory
        assert "context-lens" in config.database.path
        assert "knowledge_base.db" in config.database.path
        assert config.embedding.model == "sentence-transformers/all-MiniLM-L6-v2"
        assert config.processing.chunk_size == 1000
        assert config.server.name == "knowledge-base"

    def test_from_env_custom_values(self):
        """Test loading configuration from environment with custom values."""
        os.environ["LANCE_DB_PATH"] = "./custom.db"
        os.environ["EMBEDDING_MODEL"] = "custom-model"
        os.environ["CHUNK_SIZE"] = "500"
        os.environ["LOG_LEVEL"] = "DEBUG"

        try:
            config = Config.from_env()

            assert config.database.path == "./custom.db"
            assert config.embedding.model == "custom-model"
            assert config.processing.chunk_size == 500
            assert config.server.log_level == "DEBUG"
        finally:
            # Cleanup
            os.environ.pop("LANCE_DB_PATH", None)
            os.environ.pop("EMBEDDING_MODEL", None)
            os.environ.pop("CHUNK_SIZE", None)
            os.environ.pop("LOG_LEVEL", None)

    def test_from_file_yaml(self):
        """Test loading configuration from YAML file."""
        yaml_content = """
database:
  path: "./test.db"
  table_prefix: "test_"

embedding:
  model: "test-model"
  batch_size: 16
  cache_dir: "./test_cache"

processing:
  max_file_size_mb: 5
  chunk_size: 500
  chunk_overlap: 100
  supported_extensions: [".py", ".txt", ".md"]

server:
  name: "test-server"
  log_level: "DEBUG"
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            config = Config.from_file(temp_path)

            assert config.database.path == "./test.db"
            assert config.database.table_prefix == "test_"
            assert config.embedding.model == "test-model"
            assert config.embedding.batch_size == 16
            assert config.processing.chunk_size == 500
            assert config.processing.supported_extensions == [".py", ".txt", ".md"]
            assert config.server.name == "test-server"
            assert config.server.log_level == "DEBUG"
        finally:
            Path(temp_path).unlink()

    def test_from_file_not_found(self):
        """Test loading from non-existent file raises error."""
        with pytest.raises(ConfigurationError, match="not found"):
            Config.from_file("nonexistent.yaml")

    def test_from_dict(self):
        """Test loading configuration from dictionary."""
        config_dict = {
            "database": {"path": "./dict.db", "table_prefix": "dict_"},
            "embedding": {"model": "dict-model", "batch_size": 8},
            "processing": {"chunk_size": 750},
            "server": {"name": "dict-server"},
        }

        config = Config.from_dict(config_dict)

        assert config.database.path == "./dict.db"
        assert config.embedding.model == "dict-model"
        assert config.processing.chunk_size == 750
        assert config.server.name == "dict-server"

    def test_load_with_explicit_file(self):
        """Test load method with explicit file path."""
        yaml_content = """
server:
  name: "explicit-file-server"
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            config = Config.load(temp_path)
            assert config.server.name == "explicit-file-server"
        finally:
            Path(temp_path).unlink()

    def test_load_fallback_to_env(self):
        """Test load method falls back to environment when no file exists."""
        os.environ["MCP_SERVER_NAME"] = "env-fallback-server"

        try:
            config = Config.load("nonexistent.yaml")
            assert config.server.name == "env-fallback-server"
        finally:
            os.environ.pop("MCP_SERVER_NAME", None)

    def test_to_dict(self):
        """Test converting configuration to dictionary."""
        config = Config.from_env()
        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert "database" in config_dict
        assert "embedding" in config_dict
        assert "processing" in config_dict
        assert "server" in config_dict
        assert config_dict["database"]["path"] == config.database.path
        assert config_dict["server"]["name"] == config.server.name

    def test_validation_called_on_load(self):
        """Test that validation is called when loading configuration."""
        yaml_content = """
processing:
  chunk_size: 100
  chunk_overlap: 100
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            with pytest.raises(ConfigurationError, match="overlap.*must be less than chunk size"):
                Config.from_file(temp_path)
        finally:
            Path(temp_path).unlink()
