"""Main entry point for the MCP Knowledge Base Server with logging configuration."""

import sys
import logging
import asyncio
import argparse
import signal
from pathlib import Path
from typing import Optional

from .server import app, initialize_server, cleanup_server
from .config import Config, ConfigurationError


# Global flag for graceful shutdown
_shutdown_requested = False


def setup_logging(log_level: str = "INFO", log_dir: Optional[str] = None) -> None:
    """Configure logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Optional custom log directory path
    """
    # Create logs directory if it doesn't exist
    if log_dir:
        log_path = Path(log_dir)
    else:
        log_path = Path("logs")
    
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler with formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler for detailed logs
    file_handler = logging.FileHandler(log_path / "mcp_knowledge_base.log")
    file_handler.setLevel(logging.DEBUG)  # Always log DEBUG to file
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Error file handler for errors only
    error_handler = logging.FileHandler(log_path / "errors.log")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    logging.info(f"Logging configured with level: {log_level}")
    logging.info(f"Log files location: {log_path.absolute()}")


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
  # Start server with default configuration
  %(prog)s

  # Start with custom config file
  %(prog)s --config config.yaml

  # Start with custom log level
  %(prog)s --log-level DEBUG

  # Start with custom database path
  %(prog)s --db-path ./my_knowledge_base.db

  # Combine multiple options
  %(prog)s --config config.yaml --log-level DEBUG --log-dir ./logs

Environment Variables:
  Configuration can also be set via environment variables.
  See README.md for full list of supported variables.
        """
    )
    
    # Configuration file
    parser.add_argument(
        "--config",
        type=str,
        metavar="PATH",
        help="Path to YAML configuration file (default: config.yaml if exists, else env vars)"
    )
    
    # Server options
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: INFO or from config)"
    )
    
    parser.add_argument(
        "--log-dir",
        type=str,
        metavar="PATH",
        help="Directory for log files (default: ./logs)"
    )
    
    # Database options
    parser.add_argument(
        "--db-path",
        type=str,
        metavar="PATH",
        help="Path to LanceDB database (default: ./knowledge_base.db or from config)"
    )
    
    # Display options
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0"
    )
    
    parser.add_argument(
        "--show-config",
        action="store_true",
        help="Display configuration and exit"
    )
    
    return parser.parse_args()


def setup_signal_handlers() -> None:
    """Setup signal handlers for graceful shutdown."""
    global _shutdown_requested
    
    def signal_handler(signum, frame):
        """Handle shutdown signals."""
        global _shutdown_requested
        signal_name = signal.Signals(signum).name
        logger = logging.getLogger(__name__)
        
        if not _shutdown_requested:
            logger.info(f"Received {signal_name}, initiating graceful shutdown...")
            _shutdown_requested = True
        else:
            logger.warning(f"Received {signal_name} again, forcing shutdown...")
            sys.exit(1)
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal


async def main() -> int:
    """Main entry point for the MCP Knowledge Base Server.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    global _shutdown_requested
    
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
        
        # Setup logging based on configuration
        setup_logging(config.server.log_level, log_dir=args.log_dir)
        
        logger = logging.getLogger(__name__)
        
        # Display configuration if requested
        if args.show_config:
            print("\n" + "=" * 80)
            print("MCP Knowledge Base Server Configuration")
            print("=" * 80)
            import json
            print(json.dumps(config.to_dict(), indent=2))
            print("=" * 80 + "\n")
            return 0
        
        # Setup signal handlers for graceful shutdown
        setup_signal_handlers()
        
        logger.info("=" * 80)
        logger.info("MCP Knowledge Base Server Starting")
        logger.info("=" * 80)
        logger.info(f"Version: 0.1.0")
        logger.info(f"Python: {sys.version}")
        logger.info(f"Configuration: {config.to_dict()}")
        
        # Initialize server
        await initialize_server()
        
        logger.info("Server initialized successfully")
        logger.info("MCP Knowledge Base Server is ready to accept requests")
        logger.info("Press Ctrl+C to shutdown gracefully")
        
        # The FastMCP framework will handle the actual server lifecycle
        # This is just for initialization
        return 0
        
    except ConfigurationError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        logger = logging.getLogger(__name__)
        logger.info("Shutdown requested by user")
        return 0
    except Exception as e:
        print(f"Failed to start server: {e}", file=sys.stderr)
        logging.error(f"Server startup failed: {e}", exc_info=True)
        return 1
    finally:
        # Cleanup
        logger = logging.getLogger(__name__)
        try:
            if not _shutdown_requested:
                logger.info("Performing cleanup...")
            await cleanup_server()
            logger.info("Cleanup completed successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}", exc_info=True)


def run() -> None:
    """Run the server (synchronous wrapper for async main)."""
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        print("\nShutdown complete.", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    run()
