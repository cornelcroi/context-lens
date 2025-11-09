"""Tests for GitHub repository handling."""

import pytest

from context_lens.utils.github_handler import (
    GitHubHandlerError,
    is_github_url,
    parse_github_url,
)


class TestGitHubURLDetection:
    """Test GitHub URL detection."""

    def test_valid_github_urls(self):
        """Test detection of valid GitHub URLs."""
        valid_urls = [
            "https://github.com/user/repo",
            "https://github.com/user/repo.git",
            "https://github.com/user/repo/tree/main",
            "https://github.com/user/repo/blob/main/file.py",
            "http://github.com/user/repo",
            "git@github.com:user/repo.git",
        ]

        for url in valid_urls:
            assert is_github_url(url), f"Should detect {url} as GitHub URL"

    def test_invalid_github_urls(self):
        """Test rejection of invalid URLs."""
        invalid_urls = [
            "/path/to/file.py",
            "https://gitlab.com/user/repo",
            "https://bitbucket.org/user/repo",
            "not a url",
            "",
            None,
        ]

        for url in invalid_urls:
            assert not is_github_url(url), f"Should not detect {url} as GitHub URL"


class TestGitHubURLParsing:
    """Test GitHub URL parsing."""

    def test_parse_simple_repo_url(self):
        """Test parsing simple repository URL."""
        url = "https://github.com/user/repo"
        repo_url, branch, subpath = parse_github_url(url)

        assert repo_url == "https://github.com/user/repo"
        assert branch is None
        assert subpath is None

    def test_parse_repo_with_git_extension(self):
        """Test parsing repository URL with .git extension."""
        url = "https://github.com/user/repo.git"
        repo_url, branch, subpath = parse_github_url(url)

        assert repo_url == "https://github.com/user/repo"
        assert branch is None
        assert subpath is None

    def test_parse_repo_with_branch(self):
        """Test parsing repository URL with branch."""
        url = "https://github.com/user/repo/tree/develop"
        repo_url, branch, subpath = parse_github_url(url)

        assert repo_url == "https://github.com/user/repo"
        assert branch == "develop"
        assert subpath is None

    def test_parse_repo_with_subpath(self):
        """Test parsing repository URL with subdirectory."""
        url = "https://github.com/user/repo/tree/main/src/utils"
        repo_url, branch, subpath = parse_github_url(url)

        assert repo_url == "https://github.com/user/repo"
        assert branch == "main"
        assert subpath == "src/utils"

    def test_parse_file_url(self):
        """Test parsing file URL."""
        url = "https://github.com/user/repo/blob/main/src/file.py"
        repo_url, branch, subpath = parse_github_url(url)

        assert repo_url == "https://github.com/user/repo"
        assert branch == "main"
        assert subpath == "src/file.py"

    def test_parse_git_ssh_url(self):
        """Test parsing git@ SSH URL."""
        url = "git@github.com:user/repo.git"
        repo_url, branch, subpath = parse_github_url(url)

        assert repo_url == "https://github.com/user/repo"
        assert branch is None
        assert subpath is None

    def test_parse_invalid_url(self):
        """Test parsing invalid URL raises error."""
        with pytest.raises(GitHubHandlerError):
            parse_github_url("https://gitlab.com/user/repo")

        with pytest.raises(GitHubHandlerError):
            parse_github_url("https://github.com/")

        with pytest.raises(GitHubHandlerError):
            parse_github_url("not a url")


class TestGitHubFileFiltering:
    """Test file filtering logic."""

    def test_ignore_patterns_defined(self):
        """Test that common ignore patterns are defined."""
        import inspect

        from context_lens.utils.github_handler import get_repository_files

        # Get the source code of the function
        source = inspect.getsource(get_repository_files)

        # Verify critical ignore patterns are present
        assert "node_modules" in source, "Should ignore node_modules"
        assert "venv" in source or ".venv" in source, "Should ignore venv"
        assert "__pycache__" in source, "Should ignore __pycache__"
        assert ".git" in source, "Should ignore .git"
        assert "dist" in source, "Should ignore dist"
        assert "build" in source, "Should ignore build"

    def test_supported_extensions(self):
        """Test that only supported extensions are included."""
        # This would require actual file system or mocking
        # Placeholder for integration test
