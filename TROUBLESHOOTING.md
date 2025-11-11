# Troubleshooting Guide

Common issues and solutions for Context Lens.

## Common Issues

### First run is slow?

The embedding model (~100MB) downloads on first use. This only happens once.

### Do I need an API key?

No. Context Lens runs completely locally.

### Where is my data stored?

Platform-specific directories:
- **macOS**: `~/Library/Application Support/context-lens/`
- **Linux**: `~/.local/share/context-lens/`
- **Windows**: `%LOCALAPPDATA%\context-lens\`

Change with `CONTEXT_LENS_HOME` environment variable. See [SETUP.md](SETUP.md#custom-data-location).

### Can I use this with private code?

Yes. All processing happens locally.

### How much disk space?

- Embedding model: ~100MB (one-time)
- Database: ~1KB per text chunk
- Example: 10MB codebase = ~5-10MB database

## Server Issues

### Server not starting?

Check installation:
```bash
context-lens --version
```

Common causes:
- Python version (need 3.11+)
- Missing dependencies: `pip install -e .`
- Port already in use

### MCP Inspector not connecting?

Use the correct command:
```bash
npx @modelcontextprotocol/inspector python -m context_lens.server
```

## Database Issues

### Database errors?

Reset the database:
```bash
# On macOS
rm -rf ~/Library/Application\ Support/context-lens/knowledge_base.db

# On Linux
rm -rf ~/.local/share/context-lens/knowledge_base.db
```

Server will create a new one on next run.

### Database too large?

- Remove unused documents with `remove_document()`
- Clear and rebuild with `clear_knowledge_base()`
- Increase chunk size to reduce chunks

## Performance Issues

### Search is slow?

- Reduce database size
- Use SSD instead of HDD
- Increase chunk size

### Large files being skipped?

Default limit is 10MB. Change with:
```json
{
  "env": {
    "MAX_FILE_SIZE_MB": "50"
  }
}
```

## Configuration Issues

### Configuration not working?

Check priority order:
1. CLI parameters (highest)
2. Environment variables
3. Config file (YAML)
4. Defaults (lowest)

Verify with:
```bash
context-lens --show-config
```

## Getting Help

1. Check [GitHub Issues](https://github.com/cornelcroi/context-lens/issues)
2. Open a new issue with:
   - Error messages
   - Your configuration
   - Steps to reproduce
   - System info (OS, Python version)

## Additional Resources

- [Setup Guide](SETUP.md) - Configuration details
- [Usage Guide](USAGE_GUIDE.md) - How to use effectively
- [Technical Details](TECHNICAL.md) - Architecture
