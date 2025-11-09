"""Integration tests for configuration management."""

import os
import tempfile
from pathlib import Path

import pytest

from context_lens.config import Config
from context_lens.services.document_service import DocumentService


class TestConfigurationIntegration:
    """Integration tests for configuration with services."""

    def test_document_service_with_env_config(self):
        """Test that DocumentService can be initialized with environment-based config."""
        # Set custom environment variables
        os.environ["CHUNK_SIZE"] = "500"
        os.environ["CHUNK_OVERLAP"] = "100"

        try:
            config = Config.from_env()

            # Verify config loaded correctly
            assert config.processing.chunk_size == 500
            assert config.processing.chunk_overlap == 100

            # Create document service with config
            doc_service = DocumentService(config)

            # Verify service uses the config
            assert doc_service.config.processing.chunk_size == 500
            assert doc_service.content_extractor.chunk_size == 500

        finally:
            os.environ.pop("CHUNK_SIZE", None)
            os.environ.pop("CHUNK_OVERLAP", None)

    def test_document_service_with_yaml_config(self):
        """Test that DocumentService can be initialized with YAML-based config."""
        yaml_content = """
database:
  path: "./test_integration.db"

processing:
  chunk_size: 750
  chunk_overlap: 150

embedding:
  batch_size: 16
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            config = Config.from_file(temp_path)

            # Verify config loaded correctly
            assert config.database.path == "./test_integration.db"
            assert config.processing.chunk_size == 750
            assert config.embedding.batch_size == 16

            # Create document service with config
            doc_service = DocumentService(config)

            # Verify service uses the config
            assert doc_service.config.processing.chunk_size == 750
            assert doc_service.config.embedding.batch_size == 16

        finally:
            Path(temp_path).unlink()

    def test_config_load_priority(self):
        """Test configuration loading priority: file > env > defaults."""
        # Set environment variable
        os.environ["CHUNK_SIZE"] = "600"

        yaml_content = """
processing:
  chunk_size: 800
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            # Load with explicit file - should use file value
            config_from_file = Config.load(temp_path)
            assert config_from_file.processing.chunk_size == 800

            # Load without file - should use env value
            config_from_env = Config.load("nonexistent.yaml")
            assert config_from_env.processing.chunk_size == 600

        finally:
            Path(temp_path).unlink()
            os.environ.pop("CHUNK_SIZE", None)

    def test_config_validation_prevents_invalid_service_creation(self):
        """Test that invalid configuration prevents service creation."""
        yaml_content = """
processing:
  chunk_size: 100
  chunk_overlap: 200
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            # Should raise ConfigurationError due to invalid overlap
            from context_lens.config import ConfigurationError

            with pytest.raises(ConfigurationError):
                Config.from_file(temp_path)

        finally:
            Path(temp_path).unlink()

    def test_default_config_yaml_auto_loading(self):
        """Test that default config.yaml is automatically loaded if present."""
        yaml_content = """
server:
  name: "auto-loaded-server"
"""

        # Create config.yaml in current directory
        config_path = Path("config.yaml")
        original_exists = config_path.exists()
        original_content = None

        if original_exists:
            # Backup existing config
            original_content = config_path.read_text()

        try:
            config_path.write_text(yaml_content)

            # Load without specifying file - should auto-load config.yaml
            config = Config.load()
            assert config.server.name == "auto-loaded-server"

        finally:
            if original_exists and original_content:
                # Restore original config
                config_path.write_text(original_content)
            elif config_path.exists():
                # Remove test config
                config_path.unlink()

    def test_config_to_dict_round_trip(self):
        """Test that configuration can be converted to dict and back."""
        # Create config from environment
        config1 = Config.from_env()

        # Convert to dict
        config_dict = config1.to_dict()

        # Create new config from dict
        config2 = Config.from_dict(config_dict)

        # Verify they match
        assert config2.database.path == config1.database.path
        assert config2.embedding.model == config1.embedding.model
        assert config2.processing.chunk_size == config1.processing.chunk_size
        assert config2.server.name == config1.server.name
