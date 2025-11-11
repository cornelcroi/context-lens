"""Initialize and register all available parsers."""

import logging

from .javascript_parser import JavaScriptParser
from .json_parser import JSONParser
from .markdown_parser import MarkdownParser
from .python_parser import PythonParser
from .registry import get_parser_registry
from .rust_parser import RustParser
from .yaml_parser import YAMLParser

logger = logging.getLogger(__name__)


def register_all_parsers() -> None:
    """Register all available language parsers with the global registry."""
    registry = get_parser_registry()

    # Register Python parser
    try:
        registry.register(PythonParser)
        logger.info("Registered PythonParser")
    except Exception as e:
        logger.error(f"Failed to register PythonParser: {e}")

    # Register JavaScript/TypeScript parser
    try:
        registry.register(JavaScriptParser)
        logger.info("Registered JavaScriptParser")
    except Exception as e:
        logger.error(f"Failed to register JavaScriptParser: {e}")

    # Register JSON parser
    try:
        registry.register(JSONParser)
        logger.info("Registered JSONParser")
    except Exception as e:
        logger.error(f"Failed to register JSONParser: {e}")

    # Register YAML parser
    try:
        registry.register(YAMLParser)
        logger.info("Registered YAMLParser")
    except Exception as e:
        logger.error(f"Failed to register YAMLParser: {e}")

    # Register Markdown parser
    try:
        registry.register(MarkdownParser)
        logger.info("Registered MarkdownParser")
    except Exception as e:
        logger.error(f"Failed to register MarkdownParser: {e}")

    # Register Rust parser
    try:
        registry.register(RustParser)
        logger.info("Registered RustParser")
    except Exception as e:
        logger.error(f"Failed to register RustParser: {e}")

    # Future parsers will be registered here:
    # registry.register(GoParser)
    # registry.register(JavaParser)


# Auto-register parsers when module is imported
register_all_parsers()
