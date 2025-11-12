"""URL fetching utilities for downloading files from HTTP/HTTPS URLs."""

import logging
import tempfile
from pathlib import Path
from typing import Tuple
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = [
    ".py", ".txt", ".md",
    ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
    ".java", ".cpp", ".c", ".h", ".hpp",
    ".go", ".rs", ".rb", ".php",
    ".json", ".yaml", ".yml", ".toml",
    ".sh", ".bash", ".zsh",
]


class URLFetchError(Exception):
    """Exception raised for URL fetching errors."""


def is_direct_file_url(url: str) -> bool:
    """Check if the given string is a direct file URL (not GitHub).

    Args:
        url: String to check

    Returns:
        True if it's a direct HTTP/HTTPS URL (not GitHub), False otherwise
    """
    if not url or not isinstance(url, str):
        return False

    url = url.strip()
    
    if not (url.startswith("http://") or url.startswith("https://")):
        return False
    
    parsed = urlparse(url)
    if parsed.netloc in ["github.com", "raw.githubusercontent.com"]:
        return False
    
    return True


async def fetch_file_from_url(url: str, max_file_size_mb: int = 10) -> Tuple[Path, str]:
    """Fetch a file from a URL and save it to a temporary location.

    Args:
        url: URL to fetch the file from
        max_file_size_mb: Maximum file size in MB (default: 10)

    Returns:
        Tuple of (temp_file_path, original_filename)

    Raises:
        URLFetchError: If fetching fails or file type is unsupported
    """
    max_file_size_bytes = max_file_size_mb * 1024 * 1024
    
    try:
        logger.info(f"Fetching file from URL: {url}")
        
        parsed = urlparse(url)
        path_parts = parsed.path.split("/")
        filename = path_parts[-1] if path_parts[-1] else "downloaded_file"
        
        # Validate file extension
        suffix = Path(filename).suffix.lower()
        if not suffix or suffix not in SUPPORTED_EXTENSIONS:
            raise URLFetchError(
                f"Unsupported file type '{suffix}'. Supported types: {', '.join(SUPPORTED_EXTENSIONS)}"
            )
        
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            # Check file size
            content_length = len(response.content)
            if content_length > max_file_size_bytes:
                size_mb = round(content_length / (1024 * 1024), 2)
                raise URLFetchError(
                    f"File too large ({size_mb} MB). Maximum size: {max_file_size_mb} MB"
                )
            
            temp_file = tempfile.NamedTemporaryFile(mode="wb", suffix=suffix, delete=False)
            temp_path = Path(temp_file.name)
            
            temp_file.write(response.content)
            temp_file.close()
            
            logger.info(f"File fetched: {filename} ({content_length} bytes)")
            return temp_path, filename
            
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching URL {url}: {e}")
        raise URLFetchError(f"HTTP error {e.response.status_code}: {e.response.reason_phrase}")
    except httpx.RequestError as e:
        logger.error(f"Request error fetching URL {url}: {e}")
        raise URLFetchError(f"Failed to fetch URL: {str(e)}")
    except URLFetchError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching URL {url}: {e}")
        raise URLFetchError(f"Failed to fetch file from URL: {str(e)}")
