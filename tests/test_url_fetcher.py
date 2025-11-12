"""Tests for URL fetching functionality."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path

from context_lens.utils.url_fetcher import (
    is_direct_file_url,
    fetch_file_from_url,
    URLFetchError,
)


class TestIsDirectFileURL:
    """Tests for is_direct_file_url function."""

    def test_valid_http_url(self):
        assert is_direct_file_url("http://example.com/file.json") is True

    def test_valid_https_url(self):
        assert is_direct_file_url("https://example.com/data.yaml") is True

    def test_github_url_excluded(self):
        assert is_direct_file_url("https://github.com/user/repo") is False

    def test_raw_github_url_excluded(self):
        assert is_direct_file_url("https://raw.githubusercontent.com/user/repo/main/file.py") is False

    def test_local_path(self):
        assert is_direct_file_url("/path/to/file.txt") is False

    def test_empty_string(self):
        assert is_direct_file_url("") is False

    def test_none(self):
        assert is_direct_file_url(None) is False


@pytest.mark.asyncio
class TestFetchFileFromURL:
    """Tests for fetch_file_from_url function."""

    async def test_successful_fetch(self):
        mock_response = MagicMock()
        mock_response.content = b"test content"
        mock_response.raise_for_status = MagicMock()

        with patch("context_lens.utils.url_fetcher.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            temp_path, filename = await fetch_file_from_url("https://example.com/test.json")
            
            assert temp_path.exists()
            assert filename == "test.json"
            assert temp_path.suffix == ".json"
            
            # Cleanup
            temp_path.unlink()

    async def test_unsupported_file_type(self):
        with pytest.raises(URLFetchError, match="Unsupported file type"):
            await fetch_file_from_url("https://example.com/file.exe")

    async def test_no_extension(self):
        with pytest.raises(URLFetchError, match="Unsupported file type"):
            await fetch_file_from_url("https://example.com/file")

    async def test_http_error(self):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.reason_phrase = "Not Found"
        
        from httpx import HTTPStatusError, Request, Response
        
        with patch("context_lens.utils.url_fetcher.httpx.AsyncClient") as mock_client:
            mock_get = AsyncMock(side_effect=HTTPStatusError(
                "404", request=MagicMock(), response=mock_response
            ))
            mock_client.return_value.__aenter__.return_value.get = mock_get
            
            with pytest.raises(URLFetchError, match="HTTP error"):
                await fetch_file_from_url("https://example.com/test.json")

    async def test_file_too_large(self):
        # Create mock response with content larger than 10MB
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        mock_response = MagicMock()
        mock_response.content = large_content
        mock_response.raise_for_status = MagicMock()

        with patch("context_lens.utils.url_fetcher.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            with pytest.raises(URLFetchError, match="File too large.*11.*MB.*Maximum size: 10 MB"):
                await fetch_file_from_url("https://example.com/large.json")
