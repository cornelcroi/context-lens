# Publishing to MCP Registry

This document describes the automated publishing process for Context Lens to the official Model Context Protocol (MCP) Registry.

## Overview

Context Lens uses GitHub Actions to automatically publish new versions to the MCP Registry when version tags are pushed. The workflow handles validation, authentication, and publishing without requiring manual intervention or stored secrets.

## Publishing Process

### 1. Prepare for Release

Before publishing a new version:

1. **Update version numbers** in the following files:
   - `pyproject.toml` - Update the `version` field
   - `server.json` - Update both `version` and `packages[0].version` fields
   - Ensure all three versions match

2. **Test locally:**
   ```bash
   # Validate server.json against schema
   python validate_server_json.py
   
   # Run tests
   pytest
   
   # Test installation
   pip install -e .
   python -m context_lens.run --version
   ```

3. **Commit changes:**
   ```bash
   git add pyproject.toml server.json
   git commit -m "Bump version to X.Y.Z"
   git push origin main
   ```

### 2. Publish to PyPI

The MCP Registry validates package ownership via PyPI, so you must publish to PyPI first:

```bash
# Build the package
python -m build

# Upload to PyPI (requires PyPI credentials)
python -m twine upload dist/*
```

**Important:** Wait a few minutes for PyPI to process the upload before proceeding to the next step.

### 3. Trigger Registry Publishing

You can trigger the publishing workflow in two ways:

#### Option A: Manual Trigger (Recommended)

Trigger the workflow manually from GitHub Actions:

1. Go to: https://github.com/cornelcroi/context-lens/actions
2. Click on "Publish to MCP Registry" workflow
3. Click the "Run workflow" button
4. Enter the version number (e.g., `0.1.4`)
5. Click "Run workflow"

**Benefits:**
- No need to create/push tags
- Can republish any version
- Easier for testing
- More control over timing

#### Option B: Push Version Tag

Push a version tag to automatically trigger the workflow:

```bash
# Create and push a version tag
git tag v0.1.4
git push origin v0.1.4
```

**Tag format:** Must start with `v` followed by semantic version (e.g., `v0.1.4`, `v1.0.0`)

**Benefits:**
- Automatic on release
- Creates permanent version marker
- Standard Git workflow

### 4. Monitor Workflow

1. Go to the [GitHub Actions page](https://github.com/cornelcroi/context-lens/actions)
2. Find the "Publish to MCP Registry" workflow run
3. Monitor the workflow steps:
   - ✅ Checkout code
   - ✅ Setup Python
   - ✅ Validate server.json
   - ✅ Download mcp-publisher CLI
   - ✅ Authenticate with GitHub OIDC
   - ✅ Publish to MCP Registry

### 5. Verify Publication

After the workflow completes successfully:

1. **Check the registry:**
   - Visit https://registry.modelcontextprotocol.io/
   - Search for "context-lens"
   - Verify the new version appears

2. **Test installation:**
   ```bash
   # Clear any cached versions
   rm -rf ~/.cache/uv
   
   # Install and verify version
   uvx context-lens --version
   ```

## Workflow Details

### Workflow File

Location: `.github/workflows/publish-mcp.yml`

### Trigger

The workflow can be triggered in two ways:

1. **Automatically** when a tag matching `v*` is pushed
2. **Manually** via GitHub Actions UI with workflow_dispatch

```yaml
on:
  push:
    tags: ["v*"]
  workflow_dispatch:
    inputs:
      version:
        description: 'Version to publish (e.g., 0.1.4)'
        required: true
        type: string
```

### Workflow Steps

1. **Checkout Code**
   - Checks out the repository at the tagged commit

2. **Setup Python**
   - Installs Python 3.11
   - Required for validation script

3. **Validate server.json**
   - Installs `jsonschema` and `requests` libraries
   - Runs `validate_server_json.py` to check schema compliance
   - Fails workflow if validation errors are found

4. **Download mcp-publisher CLI**
   - Downloads the latest Linux binary from GitHub releases
   - Makes it executable
   - Adds to PATH

5. **Authenticate with GitHub OIDC**
   - Uses GitHub's OIDC token for authentication
   - No secrets required - authentication is automatic
   - Requires `id-token: write` permission

6. **Update server.json Version (Optional)**
   - Extracts version from git tag
   - Updates `version` and `packages[0].version` in server.json
   - Ensures consistency between tag and metadata

7. **Publish to MCP Registry**
   - Runs `mcp-publisher publish` command
   - Uploads server.json and metadata to registry
   - Registry validates PyPI package ownership

## Troubleshooting

### Common Issues

#### Validation Fails

**Error:** `server.json validation failed`

**Causes:**
- Missing required fields in server.json
- Invalid JSON syntax
- Schema URL is incorrect
- Version format is invalid

**Solution:**
```bash
# Run validation locally
python validate_server_json.py

# Check JSON syntax
cat server.json | jq .

# Verify schema URL is accessible
curl -I https://static.modelcontextprotocol.io/schemas/2025-10-17/server.schema.json
```

#### Authentication Fails

**Error:** `Failed to authenticate with GitHub OIDC`

**Causes:**
- Missing `id-token: write` permission in workflow
- GitHub OIDC token expired or invalid
- Network connectivity issues

**Solution:**
1. Verify workflow permissions in `.github/workflows/publish-mcp.yml`:
   ```yaml
   permissions:
     id-token: write
     contents: read
   ```

2. Re-run the workflow from GitHub Actions UI

3. Check GitHub's status page for OIDC service issues

#### Publishing Fails

**Error:** `Failed to publish to MCP Registry`

**Causes:**
- PyPI package not found or not public
- Version mismatch between server.json and PyPI
- Missing validation metadata in PyPI package README
- Namespace authorization failure

**Solution:**

1. **Verify PyPI package exists:**
   ```bash
   curl https://pypi.org/pypi/context-lens/json | jq .info.version
   ```

2. **Check validation metadata:**
   - Ensure README.md contains: `mcp-name: io.github.cornelcroi/context-lens`
   - Verify README is included in PyPI package

3. **Verify version consistency:**
   ```bash
   # Check server.json version
   cat server.json | jq .version
   
   # Check PyPI version
   curl https://pypi.org/pypi/context-lens/json | jq .info.version
   ```

4. **Check namespace authorization:**
   - Namespace `io.github.cornelcroi/*` must match GitHub username
   - Verify you're pushing from the correct repository

#### Version Already Published

**Error:** `Version already exists in registry`

**Causes:**
- Attempting to republish the same version
- Tag was pushed multiple times

**Solution:**
- This is usually not an error - the registry may be idempotent
- If you need to update metadata, increment the version number
- Delete and recreate the tag if necessary:
  ```bash
  git tag -d v0.1.4
  git push origin :refs/tags/v0.1.4
  git tag v0.1.4
  git push origin v0.1.4
  ```

#### Workflow Doesn't Trigger

**Error:** Workflow doesn't run after pushing tag

**Causes:**
- Tag format doesn't match trigger pattern
- Workflow file has syntax errors
- GitHub Actions is disabled for the repository

**Solution:**

1. **Verify tag format:**
   ```bash
   # Correct format
   git tag v0.1.4
   
   # Incorrect formats
   git tag 0.1.4      # Missing 'v' prefix
   git tag version-0.1.4  # Wrong prefix
   ```

2. **Check workflow syntax:**
   ```bash
   # Use GitHub's workflow validator
   gh workflow view publish-mcp.yml
   ```

3. **Verify Actions are enabled:**
   - Go to repository Settings → Actions → General
   - Ensure "Allow all actions and reusable workflows" is selected

### Debug Mode

To enable detailed logging in the workflow:

1. Go to repository Settings → Secrets and variables → Actions
2. Add a new variable: `ACTIONS_STEP_DEBUG` = `true`
3. Re-run the workflow to see detailed logs

### Manual Publishing

If automated publishing fails, you can publish manually:

```bash
# Install mcp-publisher
# Download from: https://github.com/modelcontextprotocol/mcp-publisher/releases

# Authenticate
./mcp-publisher login github

# Publish
./mcp-publisher publish
```

## Version Synchronization

The workflow automatically synchronizes the version from the git tag to server.json:

```yaml
- name: Update server.json version
  run: |
    VERSION=${GITHUB_REF#refs/tags/v}
    jq --arg v "$VERSION" '.version = $v | .packages[0].version = $v' server.json > tmp && mv tmp server.json
```

This ensures consistency even if you forget to update server.json manually.

**Best Practice:** Always update server.json manually before tagging to avoid confusion, but the workflow will correct any mismatches.

## Security

### No Secrets Required

The workflow uses GitHub OIDC authentication, which means:
- ✅ No API keys or tokens to store
- ✅ No secrets to rotate or manage
- ✅ Automatic authentication via GitHub
- ✅ Scoped to specific repository and namespace

### Permissions

The workflow requires minimal permissions:
- `id-token: write` - For OIDC authentication
- `contents: read` - For checking out code

### Namespace Authorization

The namespace `io.github.cornelcroi/*` is automatically authorized because:
1. The workflow runs in the `cornelcroi/context-lens` repository
2. GitHub OIDC token includes repository information
3. MCP Registry verifies the token matches the namespace

## Best Practices

1. **Always publish to PyPI first** - The registry validates package ownership via PyPI

2. **Keep versions synchronized** - Ensure pyproject.toml, server.json, and git tags match

3. **Test locally before tagging** - Run validation and tests before creating a release tag

4. **Use semantic versioning** - Follow semver format: MAJOR.MINOR.PATCH

5. **Monitor workflow runs** - Check GitHub Actions after pushing tags

6. **Verify publication** - Always verify the new version appears in the registry

7. **Document changes** - Update CHANGELOG.md or release notes for each version

## Related Files

- `.github/workflows/publish-mcp.yml` - Automated publishing workflow
- `server.json` - MCP server metadata and configuration
- `validate_server_json.py` - Schema validation script
- `pyproject.toml` - Python package version and metadata
- `README.md` - User-facing verification instructions

## Support

If you encounter issues not covered in this guide:

1. Check the [GitHub Actions logs](https://github.com/cornelcroi/context-lens/actions)
2. Review [MCP Registry documentation](https://modelcontextprotocol.io/docs/registry)
3. Open an issue in the repository with workflow logs and error messages
