"""GitHub repository handling utilities."""

import logging
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class GitHubHandlerError(Exception):
    """Exception raised for GitHub handling errors."""


def is_github_url(url: str) -> bool:
    """Check if the given string is a GitHub URL.

    Args:
        url: String to check

    Returns:
        True if it's a GitHub URL, False otherwise
    """
    if not url or not isinstance(url, str):
        return False

    github_patterns = [
        r"^https?://github\.com/",
        r"^https?://raw\.githubusercontent\.com/",
        r"^git@github\.com:",
    ]

    return any(re.match(pattern, url.strip()) for pattern in github_patterns)


def parse_github_url(url: str) -> Tuple[str, Optional[str], Optional[str]]:
    """Parse a GitHub URL to extract repository info.

    Args:
        url: GitHub URL

    Returns:
        Tuple of (repo_url, branch, subpath)

    Examples:
        https://github.com/user/repo -> (repo_url, None, None)
        https://github.com/user/repo/tree/main/src -> (repo_url, 'main', 'src')
        https://github.com/user/repo/blob/main/file.py -> (repo_url, 'main', 'file.py')
    """
    url = url.strip()

    # Handle git@ URLs
    if url.startswith("git@github.com:"):
        repo_path = url.replace("git@github.com:", "").replace(".git", "")
        repo_url = f"https://github.com/{repo_path}"
        return repo_url, None, None

    # Parse HTTPS URLs
    parsed = urlparse(url)
    if parsed.netloc not in ["github.com", "raw.githubusercontent.com"]:
        raise GitHubHandlerError(f"Not a valid GitHub URL: {url}")

    path_parts = [p for p in parsed.path.split("/") if p]

    if len(path_parts) < 2:
        raise GitHubHandlerError(f"Invalid GitHub URL format: {url}")

    user = path_parts[0]
    repo = path_parts[1].replace(".git", "")
    repo_url = f"https://github.com/{user}/{repo}"

    branch = None
    subpath = None

    # Check for tree/blob patterns
    if len(path_parts) > 3 and path_parts[2] in ["tree", "blob"]:
        branch = path_parts[3]
        if len(path_parts) > 4:
            subpath = "/".join(path_parts[4:])

    return repo_url, branch, subpath


def clone_repository(
    repo_url: str, branch: Optional[str] = None, target_dir: Optional[Path] = None
) -> Path:
    """Clone a GitHub repository.

    Args:
        repo_url: Repository URL
        branch: Optional branch name
        target_dir: Optional target directory (uses temp dir if not provided)

    Returns:
        Path to cloned repository

    Raises:
        GitHubHandlerError: If cloning fails
    """
    if target_dir is None:
        target_dir = Path(tempfile.mkdtemp(prefix="mcp_kb_repo_"))

    target_dir.mkdir(parents=True, exist_ok=True)

    try:
        cmd = ["git", "clone", "--depth", "1"]

        if branch:
            cmd.extend(["--branch", branch])

        cmd.extend([repo_url, str(target_dir)])

        logger.info(f"Cloning repository: {repo_url}")
        if branch:
            logger.info(f"Branch: {branch}")

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=300  # 5 minute timeout
        )

        if result.returncode != 0:
            error_msg = result.stderr or result.stdout
            raise GitHubHandlerError(f"Failed to clone repository: {error_msg}")

        logger.info(f"Repository cloned to: {target_dir}")
        return target_dir

    except subprocess.TimeoutExpired:
        raise GitHubHandlerError("Repository cloning timed out (5 minutes)")
    except FileNotFoundError:
        raise GitHubHandlerError("Git is not installed or not in PATH")
    except Exception as e:
        if target_dir and target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)
        raise GitHubHandlerError(f"Error cloning repository: {e}")


def get_repository_files(
    repo_path: Path, subpath: Optional[str] = None, supported_extensions: Optional[List[str]] = None
) -> List[Path]:
    """Get list of files from repository, excluding common ignore patterns.

    Automatically skips:
    - Dependencies: node_modules, venv, vendor, etc.
    - Build outputs: dist, build, target, etc.
    - Version control: .git, .svn, etc.
    - IDE files: .idea, .vscode, etc.
    - Cache directories: __pycache__, .cache, etc.

    Args:
        repo_path: Path to cloned repository
        subpath: Optional subdirectory within repo
        supported_extensions: List of file extensions to include (e.g., ['.py', '.txt'])

    Returns:
        List of file paths (filtered and sorted)
    """
    if supported_extensions is None:
        supported_extensions = [".py", ".txt", ".md"]

    base_path = repo_path / subpath if subpath else repo_path

    if not base_path.exists():
        raise GitHubHandlerError(f"Path does not exist in repository: {subpath}")

    # If it's a single file
    if base_path.is_file():
        if base_path.suffix in supported_extensions:
            return [base_path]
        else:
            raise GitHubHandlerError(
                f"File type {base_path.suffix} not supported. "
                f"Supported: {', '.join(supported_extensions)}"
            )

    # Collect files recursively
    files = []
    ignore_patterns = {
        # Version control
        ".git",
        ".svn",
        ".hg",
        # Python
        "__pycache__",
        "venv",
        ".venv",
        "env",
        ".env",
        "virtualenv",
        ".pytest_cache",
        ".mypy_cache",
        ".tox",
        ".nox",
        "dist",
        "build",
        "*.egg-info",
        ".eggs",
        "htmlcov",
        ".coverage",
        ".hypothesis",
        # JavaScript/Node
        "node_modules",
        "bower_components",
        ".npm",
        ".yarn",
        "jspm_packages",
        "web_modules",
        # Build outputs
        "target",
        "out",
        "bin",
        "obj",
        ".next",
        ".nuxt",
        ".cache",
        ".parcel-cache",
        ".webpack",
        # IDE
        ".idea",
        ".vscode",
        ".vs",
        "*.swp",
        "*.swo",
        # OS
        ".DS_Store",
        "Thumbs.db",
        # Logs
        "logs",
        "*.log",
        # Dependencies (other languages)
        "vendor",
        "packages",
        ".bundle",
    }

    for file_path in base_path.rglob("*"):
        # Skip if in ignored directory
        if any(ignored in file_path.parts for ignored in ignore_patterns):
            continue

        # Skip if not a file
        if not file_path.is_file():
            continue

        # Skip if extension not supported
        if file_path.suffix not in supported_extensions:
            continue

        # Skip if file is too large (>10MB)
        try:
            if file_path.stat().st_size > 10 * 1024 * 1024:
                logger.warning(f"Skipping large file: {file_path.name} (>10MB)")
                continue
        except OSError:
            continue

        files.append(file_path)

    return sorted(files)


def cleanup_repository(repo_path: Path) -> None:
    """Clean up cloned repository.

    Args:
        repo_path: Path to repository to remove
    """
    try:
        if repo_path.exists():
            shutil.rmtree(repo_path)
            logger.info(f"Cleaned up repository: {repo_path}")
    except Exception as e:
        logger.warning(f"Failed to cleanup repository {repo_path}: {e}")
