# Troubleshooting Guide

Solutions to common issues and problems with Context Lens.

## Table of Contents

- [Common Issues](#common-issues)
- [Server Issues](#server-issues)
- [Connection Issues](#connection-issues)
- [Database Issues](#database-issues)
- [Performance Issues](#performance-issues)
- [Configuration Issues](#configuration-issues)
- [Getting Help](#getting-help)

---

## Common Issues

### Why is the first run slow?

The embedding model (~100MB) downloads on first use. This only happens once. Subsequent runs are fast.

**Solution:** Just wait for the initial download to complete. It's a one-time setup.

---

### Why is the first tool call slow?

The server uses lazy initialization - it starts quickly but loads the embedding model on the first tool invocation. This takes 5-10 seconds and only happens once per session.

**Why:** This is intentional to provide fast startup times for MCP Inspector and other tools.

**Solution:** The first query will be slow, but all subsequent queries will be fast.

---

### Do I need an API key?

No! Context Lens runs completely locally. No API keys, no cloud services, no subscriptions.

---

### Where is my data stored?

Context-Lens stores data in platform-specific directories:
- **macOS**: `~/Library/Application Support/context-lens/`
- **Linux**: `~/.local/share/context-lens/`
- **Windows**: `%LOCALAPPDATA%\context-lens\`

You can change this location using the `CONTEXT_LENS_HOME` environment variable.

See [SETUP.md](SETUP.md#custom-data-location) for details.

---

### Can I use this with private/proprietary code?

Yes! All processing happens locally on your machine. Nothing is sent to external services.

---

### How much disk space does it use?

- **Embedding model**: ~100MB (one-time download)
- **Database**: ~1KB per text chunk (varies by content)
- **Example**: A 10MB codebase typically uses ~5-10MB of database space

---

### Can I share my knowledge base with my team?

Currently, the database is local. Team sharing via S3 or cloud storage is on the roadmap.

See [CONTRIBUTING.md](CONTRIBUTING.md#roadmap) for planned features.

---

## Server Issues

### Server not starting?

**Check installation:**
```bash
context-lens --version
```

**View detailed logs:**
```bash
tail -f logs/context-lens.log
```

**Check for errors:**
```bash
tail -f logs/errors.log
```

**Common causes:**
- Python not installed or wrong version (need 3.11+)
- Missing dependencies
- Port already in use
- Permissions issues

---

### MCP Inspector not connecting?

**Make sure you're using the correct command:**
```bash
npx @modelcontextprotocol/inspector python -m context_lens.server
```

**NOT this (incorrect):**
```bash
npx @modelcontextprotocol/inspector fastmcp run context_lens.server:app
```

**Check that Python can find the module:**
```bash
python -m context_lens.server --help
```

---

### Logs show "stdio transport" errors?

This usually means something is writing to stdout when it shouldn't. The server is configured to log only to files to keep stdio clean for MCP protocol communication.

**Solutions:**
1. Check for any `print()` statements in your code
2. Verify logging is configured correctly (should only write to files)
3. Check third-party libraries aren't writing to stdout

---

## Connection Issues

### Tools not appearing in LLM client?

**Troubleshooting steps:**

1. **Verify configuration** - Check the server is configured correctly in your client's MCP settings
2. **Restart client** - Restart your LLM client after configuration changes
3. **Check logs** - Look for connection errors in the client's logs
4. **For Kiro IDE** - Use Command Palette → "MCP: Reload Servers"

**Common causes:**
- Incorrect config file location
- Syntax errors in JSON config
- Server not running
- Wrong command or args in config

---

### Connection timeout?

**Possible causes:**
- Server taking too long to start
- Network issues (if using remote server)
- Firewall blocking connection

**Solutions:**
- Check server logs for startup errors
- Increase timeout in client settings
- Verify firewall rules

---

## Database Issues

### Database errors?

**Check database location:**
```bash
# On macOS
ls -la ~/Library/Application\ Support/context-lens/knowledge_base.db

# On Linux
ls -la ~/.local/share/context-lens/knowledge_base.db

# Or if you set CONTEXT_LENS_HOME
ls -la $CONTEXT_LENS_HOME/knowledge_base.db
```

**If corrupted, reset it:**
```bash
# On macOS
rm -rf ~/Library/Application\ Support/context-lens/knowledge_base.db

# On Linux
rm -rf ~/.local/share/context-lens/knowledge_base.db

# The server will create a new database on next run
```

**Backup before resetting:**
```bash
# On macOS
cp ~/Library/Application\ Support/context-lens/knowledge_base.db ~/knowledge_base.db.backup

# On Linux
cp ~/.local/share/context-lens/knowledge_base.db ~/knowledge_base.db.backup
```

---

### Database too large?

**Check database size:**
```bash
# On macOS
du -h ~/Library/Application\ Support/context-lens/knowledge_base.db

# On Linux
du -h ~/.local/share/context-lens/knowledge_base.db
```

**Solutions:**
- Remove unused documents with `remove_document()`
- Clear and rebuild with `clear_knowledge_base()`
- Increase chunk size to reduce number of chunks
- Filter out unnecessary files before adding

---

### Can't write to database?

**Common causes:**
- Permissions issues
- Disk full
- Database locked by another process

**Solutions:**
```bash
# Check permissions (macOS)
ls -la ~/Library/Application\ Support/context-lens/knowledge_base.db

# Check disk space
df -h

# Check for locks (macOS)
lsof ~/Library/Application\ Support/context-lens/knowledge_base.db
```

---

## Performance Issues

### First document addition is slow?

**Expected behavior:** The first document addition loads the embedding model, which takes 5-10 seconds. This is normal.

**Subsequent operations** should be fast (< 1 second).

---

### Search is slow?

**Possible causes:**
- Very large database (millions of chunks)
- Slow disk I/O
- Insufficient RAM

**Solutions:**
- Reduce database size by removing unused documents
- Use SSD instead of HDD
- Increase chunk size to reduce total chunks
- Close other memory-intensive applications

---

### Large files being skipped?

**Default behavior:** Files over 10MB are automatically skipped to prevent performance issues.

**To change:**
Set `MAX_FILE_SIZE_MB` environment variable:
```json
{
  "env": {
    "MAX_FILE_SIZE_MB": "50"
  }
}
```

See [SETUP.md](SETUP.md#environment-variables) for details.

---

### Many files taking too long?

**Expected behavior:** Files are processed in batches. Large repositories may take several minutes.

**Progress indicators:**
- Check logs for progress: `tail -f logs/context-lens.log`
- Server will report number of files processed

**Tips:**
- Add specific directories instead of entire repository
- Use `.gitignore` patterns to exclude unnecessary files
- Process in smaller batches

---

## Configuration Issues

### Configuration not being applied?

**Check configuration priority:**
1. CLI parameters (highest priority)
2. Environment variables
3. Config file (YAML)
4. Defaults (lowest priority)

**Verify configuration:**
```bash
context-lens --show-config
```

---

### Environment variables not working?

**Check they're set correctly:**
```bash
env | grep LANCE
env | grep MCP
```

**In MCP config:**
```json
{
  "mcpServers": {
    "context-lens": {
      "command": "uvx",
      "args": ["context-lens"],
      "env": {
        "CONTEXT_LENS_HOME": "/path/to/your/data"
      }
    }
  }
}
```

---

### Config file not being loaded?

**Verify file path:**
```bash
ls -la config.yaml
```

**Check syntax:**
```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

**Specify explicitly:**
```json
{
  "args": ["context-lens", "--config", "/absolute/path/to/config.yaml"]
}
```

---

## Import Errors

### Missing dependencies?

**Reinstall dependencies:**
```bash
pip install -r requirements.txt
```

**For development installation:**
```bash
pip install -e .
```

**Check Python version:**
```bash
python --version  # Should be 3.11+
```

---

### Module not found?

**Check installation:**
```bash
pip list | grep context-lens
```

**Reinstall:**
```bash
pip uninstall context-lens
pip install context-lens
```

---

## Getting Help

### Still having issues?

1. **Check logs** - Review `./logs/` directory for detailed error messages
2. **Search issues** - Check [GitHub Issues](https://github.com/cornelcroi/context-lens/issues) for similar problems
3. **Try MCP Inspector** - Use MCP Inspector to isolate the issue
4. **Report bugs** - Open a new issue with:
   - Error messages from logs
   - Your configuration
   - Steps to reproduce
   - System information (OS, Python version)

### Useful debugging commands

```bash
# Check version
context-lens --version

# Show configuration
context-lens --show-config

# View logs
tail -f logs/context-lens.log
tail -f logs/errors.log

# Check Python environment
python --version
pip list | grep context-lens

# Test server directly
python -m context_lens.server --help
```

---

## FAQ

### How does this compare to GitHub's MCP server?

Context Lens and GitHub's MCP server serve different purposes:

**Context Lens is better for:**
- 🧠 Semantic understanding - Find related concepts without exact keywords
- 📚 Learning codebases - Understand how things work across entire projects
- 🔍 Pattern discovery - Find similar code patterns and approaches
- 💾 Offline development - Works without internet after indexing
- 🔒 Privacy - All processing happens locally

**GitHub's MCP server is better for:**
- 🔧 Repository management - Create issues, manage PRs, CI/CD
- 📊 Real-time state - Always fetches latest from GitHub
- 🌐 GitHub features - Integrates with Actions, Projects, etc.
- 📁 Precise file access - When you know exactly which file you need

**They complement each other!** Use Context Lens for semantic exploration and GitHub's MCP for repository management.

---

## Additional Resources

- 📖 [Setup Guide](SETUP.md) - Configuration and setup details
- 📚 [Usage Guide](USAGE_GUIDE.md) - How to use Context Lens effectively
- ⚙️ [Technical Details](TECHNICAL.md) - Architecture and implementation
- 🤝 [Contributing](CONTRIBUTING.md) - How to contribute and report issues
