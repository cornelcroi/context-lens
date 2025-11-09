"""Pytest configuration and fixtures for CodeLens tests."""

import pytest
import tempfile
import shutil
from pathlib import Path

from codelens.config import Config, DatabaseConfig, EmbeddingConfig, ProcessingConfig, ServerConfig


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def test_config(temp_dir):
    """Create a test configuration."""
    return Config(
        database=DatabaseConfig(
            path=str(temp_dir / "test_kb.db"),
            table_prefix="test_"
        ),
        embedding=EmbeddingConfig(
            model="sentence-transformers/all-MiniLM-L6-v2",
            cache_dir=str(temp_dir / "models")
        ),
        processing=ProcessingConfig(
            max_file_size_mb=1,
            chunk_size=100,
            chunk_overlap=20
        ),
        server=ServerConfig(
            name="test-knowledge-base",
            log_level="DEBUG"
        )
    )