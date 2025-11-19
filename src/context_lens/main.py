"""Main entry point for the MCP Knowledge Base Server."""

import os
import sys

from .config import Config, ConfigurationError
from .server import app


def run() -> None:
    """Entry point for the MCP Knowledge Base Server.
    
    Runs the server with http transport for cloud deployment.
    """
    try:
        # Auto-detect cloud environment and set optimal defaults
        if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
            print("🌐 AWS Lambda environment detected")
            # Set cloud-optimized paths
            os.environ.setdefault("EMBEDDING_CACHE_DIR", "/var/task/models")
            os.environ.setdefault("HF_HOME", "/var/task/huggingface")
            os.environ.setdefault("TRANSFORMERS_CACHE", "/var/task/transformers")
            os.environ.setdefault("LANCE_DB_PATH", "/tmp/context-lens/knowledge_base.db")
        
        # Load configuration from environment
        config = Config.load()

        # Validate configuration
        config.validate()

        # Set environment variables from configuration
        os.environ["LOG_LEVEL"] = config.server.log_level
        os.environ["LANCE_DB_PATH"] = config.database.path
        os.environ["LANCE_DB_TABLE_PREFIX"] = config.database.table_prefix
        os.environ["EMBEDDING_MODEL"] = config.embedding.model
        os.environ["EMBEDDING_BATCH_SIZE"] = str(config.embedding.batch_size)
        os.environ["EMBEDDING_CACHE_DIR"] = config.embedding.cache_dir
        os.environ["MAX_FILE_SIZE_MB"] = str(config.processing.max_file_size_mb)
        os.environ["CHUNK_SIZE"] = str(config.processing.chunk_size)
        os.environ["CHUNK_OVERLAP"] = str(config.processing.chunk_overlap)
        os.environ["SUPPORTED_EXTENSIONS"] = ",".join(config.processing.supported_extensions)
        os.environ["MCP_SERVER_NAME"] = config.server.name

        # Print startup information
        print("🚀 Starting Context Lens MCP Server")
        print("=" * 60)
        print(f"📡 Transport: http")
        print(f"🌐 Host: 0.0.0.0")
        print(f"🔌 Port: 8000")
        print(f"📊 Log level: {config.server.log_level}")
        print(f"💾 Database: {config.database.path}")
        print(f"🤖 Embedding model: {config.embedding.model}")
        print("=" * 60)

        # Run the FastMCP server with http transport
        # This explicit pattern matches the FastMCP best practices
        app.run(transport="http", host="0.0.0.0", port=8000)

    except ConfigurationError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Failed to start server: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run()