# Release Checklist

Quick checklist for releasing a new version of MCP Knowledge Base Server.

## Pre-Release

- [ ] All tests passing locally: `pytest`
- [ ] Code formatted: `black src tests && isort src tests`
- [ ] Documentation updated
- [ ] Version number decided (following semver)
- [ ] CHANGELOG updated (if you have one)

## Release Process

### Automated (Recommended)

1. **Run the release preparation script:**
   ```bash
   ./scripts/prepare_release.sh 0.1.0
   ```

2. **Review and commit:**
   ```bash
   git add pyproject.toml
   git commit -m "Bump version to 0.1.0"
   ```

3. **Create and push tag:**
   ```bash
   git tag v0.1.0
   git push origin main
   git push origin v0.1.0
   ```

4. **Wait for GitHub Actions:**
   - Check Actions tab on GitHub
   - Verify release is created
   - Verify package is on PyPI

### Manual

See [PUBLISHING.md](PUBLISHING.md) for detailed manual instructions.

## Post-Release

- [ ] Verify package on PyPI: https://pypi.org/project/mcp-knowledge-base/
- [ ] Test installation: `pip install mcp-knowledge-base`
- [ ] Test with uvx: `uvx mcp-knowledge-base --version`
- [ ] Update documentation to remove "local development" notes
- [ ] Announce release (GitHub Discussions, social media, etc.)
- [ ] Monitor for issues

## Version History

- `0.1.0` - Initial release (planned)

## Quick Commands

```bash
# Prepare release
./scripts/prepare_release.sh 0.1.0

# Manual build and check
python -m build
twine check dist/*

# Upload to TestPyPI (for testing)
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*

# Create tag
git tag v0.1.0
git push origin v0.1.0
```

## Troubleshooting

**Tests fail:**
- Fix the failing tests before releasing
- Run `pytest -v` to see details

**Build fails:**
- Clean old builds: `rm -rf dist/ build/ *.egg-info`
- Check pyproject.toml syntax
- Ensure all dependencies are listed

**Upload fails:**
- Check PyPI token in GitHub Secrets
- Verify version number is unique
- Check network connection

**GitHub Actions fail:**
- Check workflow logs
- Verify secrets are set
- Ensure tag format is correct (`v*.*.*`)

## Resources

- [PUBLISHING.md](PUBLISHING.md) - Detailed publishing guide
- [GitHub Actions](https://github.com/yourusername/mcp-knowledge-base/actions)
- [PyPI Project](https://pypi.org/project/mcp-knowledge-base/)
