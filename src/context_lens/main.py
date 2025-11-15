"""Main entry point for the MCP Knowledge Base Server with CLI argument parsing."""

import argparse
import os
import sys

from .config import Config, ConfigurationError
from .server import app


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed command-line arguments
    """
    parser = argparse.ArgumentParser(
        description="MCP Knowledge Base Server - Document ingestion and semantic search",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start server with default configuration (stdio transport)
  %(prog)s

  # Start with HTTP transport
  %(prog)s --transport http --port 8080

  # Start with HTTP transport on specific host and port
  %(prog)s --transport http --host 0.0.0.0 --port 8080

  # Start with custom config file
  %(prog)s --config config.yaml

  # Start with custom log level
  %(prog)s --log-level DEBUG

  # Start with custom database path
  %(prog)s --db-path ./my_knowledge_base.db

  # Combine multiple options
  %(prog)s --config config.yaml --log-level DEBUG --transport http --port 8080

Environment Variables:
  Configuration can also be set via environment variables.
  See README.md for full list of supported variables.
        """,
    )

    # Configuration file
    parser.add_argument(
        "--config",
        type=str,
        metavar="PATH",
        help="Path to YAML configuration file (default: config.yaml if exists, else env vars)",
    )

    # Server options
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: INFO or from config)",
    )

    # Database options
    parser.add_argument(
        "--db-path",
        type=str,
        metavar="PATH",
        help="Path to LanceDB database (default: ./knowledge_base.db or from config)",
    )

    # Transport options
    parser.add_argument(
        "--transport",
        type=str,
        choices=["stdio", "http", "sse", "streamable-http"],
        default="stdio",
        help="Transport protocol to use (default: stdio)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host address to bind to for HTTP/SSE transports (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to for HTTP/SSE transports (default: 8000)",
    )

    # Display options
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")

    parser.add_argument("--show-config", action="store_true", help="Display configuration and exit")

    return parser.parse_args()


def run() -> None:
    """CLI entry point for the MCP Knowledge Base Server.

    This function:
    1. Parses command-line arguments
    2. Loads configuration from file or environment
    3. Applies CLI overrides to configuration
    4. Sets environment variables for server.py to use
    5. Delegates to FastMCP's app.run() for server execution

    FastMCP handles:
    - Transport setup (stdio, http, sse, streamable-http)
    - Signal handling (SIGINT, SIGTERM)
    - Server lifecycle management
    - Graceful shutdown
    """
    try:
        # Parse command-line arguments
        args = parse_arguments()

        # Load configuration with CLI overrides
        config = Config.load(config_file=args.config)

        # Apply CLI overrides to configuration
        if args.log_level:
            config.server.log_level = args.log_level

        if args.db_path:
            config.database.path = args.db_path

        # Validate configuration after overrides
        config.validate()

        # Display configuration if requested
        if args.show_config:
            print("\n" + "=" * 80)
            print("MCP Knowledge Base Server Configuration")
            print("=" * 80)
            import json

            print(json.dumps(config.to_dict(), indent=2))
            print("=" * 80 + "\n")
            sys.exit(0)

        # Set environment variables from configuration
        # These will be read by server.py's Config.from_env()
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

        # Prepare transport arguments for FastMCP
        transport_kwargs = {}
        
        if args.transport == "stdio":
            # For stdio, no additional parameters needed
            # (host and port are ignored for stdio transport)
            transport_kwargs = {}
        else:
            # For HTTP/SSE transports, include host and port
            transport_kwargs = {
                "transport": args.transport,
                "host": args.host,
                "port": args.port,
            }
        
        # Override log level if specified via CLI
        if args.log_level:
            transport_kwargs["log_level"] = args.log_level

        # Run the FastMCP server
        # FastMCP handles transport setup, signal handling, and lifecycle
        app.run(**transport_kwargs)

    except ConfigurationError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Failed to start server: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run()
