# Publishing Guide

Guide for publishing the MCP Knowledge Base Server to GitHub and PyPI.

## Prerequisites

1. **GitHub Account** with repository access
2. **PyPI Account** - Sign up at https://pypi.org/account/register/
3. **PyPI API Token** - Create at https://pypi.org/manage/account/token/

## Setup

### 1. Create PyPI API Token

1. Go to https://pypi.org/manage/account/token/
2. Click "Add API token"
3. Name: `mcp-knowledge-base-github-actions`
4. Scope: Select "Entire account" (or specific project after first upload)
5. Copy the token (starts with `pypi-`)

### 2. Add Token to GitHub Secrets

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `PYPI_API_TOKEN`
5. Value: Paste your PyPI token
6. Click **Add secret**

### 3. Update Package Metadata

Edit `pyproject.toml` and update:

```toml
[project]
name = "mcp-knowledge-base"
version = "0.1.0"  # Update version for each release
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]

[project.urls]
Homepage = "https://github.com/yourusername/mcp-knowledge-base"
Repository = "https://github.com/yourusername/mcp-knowledge-base"
Issues = "https://github.com/yourusername/mcp-knowledge-base/issues"
```

## Publishing Workflow

### Option 1: Automatic Release (Recommended)

This workflow automatically publishes to PyPI when you create a GitHub release.

1. **Update version** in `pyproject.toml`:
   ```toml
   version = "0.1.0"
   ```

2. **Commit and push** changes:
   ```bash
   git add pyproject.toml
   git commit -m "Bump version to 0.1.0"
   git push origin main
   ```

3. **Create and push a tag**:
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

4. **GitHub Actions will automatically**:
   - Run tests
   - Create a GitHub release
   - Build the package
   - Publish to PyPI

5. **Verify the release**:
   - Check GitHub releases: `https://github.com/yourusername/mcp-knowledge-base/releases`
   - Check PyPI: `https://pypi.org/project/mcp-knowledge-base/`

### Option 2: Manual Release

If you prefer manual control:

1. **Update version** in `pyproject.toml`

2. **Build the package**:
   ```bash
   python -m pip install --upgrade build twine
   python -m build
   ```

3. **Check the build**:
   ```bash
   twine check dist/*
   ```

4. **Upload to TestPyPI** (optional, for testing):
   ```bash
   twine upload --repository testpypi dist/*
   ```

5. **Upload to PyPI**:
   ```bash
   twine upload dist/*
   ```

6. **Create GitHub release**:
   - Go to GitHub repository
   - Click "Releases" → "Create a new release"
   - Tag: `v0.1.0`
   - Title: `Release v0.1.0`
   - Description: List changes
   - Attach `dist/*` files
   - Click "Publish release"

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (1.0.0): Breaking changes
- **MINOR** (0.1.0): New features, backwards compatible
- **PATCH** (0.0.1): Bug fixes, backwards compatible

Examples:
- `0.1.0` - Initial release
- `0.1.1` - Bug fix
- `0.2.0` - New feature
- `1.0.0` - Stable release

## Release Checklist

Before each release:

- [ ] Update version in `pyproject.toml`
- [ ] Update `CHANGELOG.md` (if you have one)
- [ ] Run tests locally: `pytest`
- [ ] Check code formatting: `black src tests && isort src tests`
- [ ] Update documentation if needed
- [ ] Commit all changes
- [ ] Create and push tag
- [ ] Verify GitHub Actions pass
- [ ] Verify package on PyPI
- [ ] Test installation: `pip install mcp-knowledge-base`
- [ ] Update documentation to remove "local development" notes

## Testing Before Release

### Test on TestPyPI

1. **Upload to TestPyPI**:
   ```bash
   twine upload --repository testpypi dist/*
   ```

2. **Install from TestPyPI**:
   ```bash
   pip install --index-url https://test.pypi.org/simple/ mcp-knowledge-base
   ```

3. **Test the installation**:
   ```bash
   mcp-knowledge-base --version
   mcp-knowledge-base --show-config
   ```

### Test with uvx

After publishing to PyPI:

```bash
uvx mcp-knowledge-base --version
```

## Post-Release Tasks

After successful release:

1. **Update documentation**:
   - Remove "local development" sections
   - Update installation instructions to use `uvx`
   - Update version numbers in examples

2. **Announce the release**:
   - GitHub Discussions
   - Social media
   - Relevant communities

3. **Monitor for issues**:
   - Check GitHub Issues
   - Monitor PyPI download stats

## Troubleshooting

### Build Fails

```bash
# Clean old builds
rm -rf dist/ build/ *.egg-info

# Rebuild
python -m build
```

### Upload Fails

**Invalid token:**
- Verify token in GitHub Secrets
- Regenerate token on PyPI if needed

**Package already exists:**
- Increment version number
- Cannot overwrite existing versions on PyPI

**Missing dependencies:**
```bash
pip install --upgrade build twine
```

### GitHub Actions Fail

1. Check workflow logs in GitHub Actions tab
2. Verify secrets are set correctly
3. Ensure all tests pass locally first
4. Check Python version compatibility

## GitHub Actions Workflows

### Test Workflow (`.github/workflows/test.yml`)

Runs on every push and pull request:
- Tests on multiple Python versions (3.8-3.12)
- Tests on multiple OS (Ubuntu, macOS, Windows)
- Code formatting checks
- Coverage reports

### Release Workflow (`.github/workflows/release.yml`)

Triggers on version tags (`v*.*.*`):
- Creates GitHub release
- Generates changelog
- Attaches build artifacts

### Publish Workflow (`.github/workflows/publish.yml`)

Triggers when GitHub release is published:
- Builds package
- Validates package
- Publishes to PyPI

## Security

- **Never commit** PyPI tokens to the repository
- Use GitHub Secrets for sensitive data
- Use PyPI trusted publishing when possible
- Regularly rotate API tokens

## Resources

- [PyPI Publishing Guide](https://packaging.python.org/tutorials/packaging-projects/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Semantic Versioning](https://semver.org/)
- [Python Packaging Guide](https://packaging.python.org/)

## Support

For issues with publishing:
- Check GitHub Actions logs
- Review PyPI upload errors
- Open an issue in the repository
