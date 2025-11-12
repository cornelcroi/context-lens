#!/usr/bin/env python3
"""
Validation script for server.json against the MCP server schema.

This script:
1. Reads server.json from the repository root
2. Fetches the JSON schema from the $schema URL
3. Validates the configuration using jsonschema library
4. Exits with error code and detailed message on validation failure
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict

try:
    import requests
    from jsonschema import validate, ValidationError, SchemaError
except ImportError as e:
    print(f"Error: Required dependencies not installed: {e}", file=sys.stderr)
    print("Install with: pip install jsonschema requests", file=sys.stderr)
    sys.exit(1)


def load_server_json(file_path: Path) -> Dict[str, Any]:
    """Load and parse server.json file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {file_path} not found", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {file_path}: {e}", file=sys.stderr)
        sys.exit(1)


def fetch_schema(schema_url: str) -> Dict[str, Any]:
    """Fetch JSON schema from URL."""
    try:
        response = requests.get(schema_url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error: Failed to fetch schema from {schema_url}: {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON schema at {schema_url}: {e}", file=sys.stderr)
        sys.exit(1)


def validate_server_config(config: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """Validate server configuration against schema."""
    try:
        validate(instance=config, schema=schema)
        print("✓ server.json is valid")
    except ValidationError as e:
        print("✗ Validation failed:", file=sys.stderr)
        print(f"  Error: {e.message}", file=sys.stderr)
        if e.path:
            path = ".".join(str(p) for p in e.path)
            print(f"  Path: {path}", file=sys.stderr)
        if e.schema_path:
            schema_path = ".".join(str(p) for p in e.schema_path)
            print(f"  Schema path: {schema_path}", file=sys.stderr)
        sys.exit(1)
    except SchemaError as e:
        print(f"Error: Invalid schema: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Main validation function."""
    # Load server.json
    server_json_path = Path("server.json")
    print(f"Loading {server_json_path}...")
    config = load_server_json(server_json_path)
    
    # Get schema URL
    schema_url = config.get("$schema")
    if not schema_url:
        print("Error: $schema field not found in server.json", file=sys.stderr)
        sys.exit(1)
    
    # Fetch and validate schema
    print(f"Fetching schema from {schema_url}...")
    schema = fetch_schema(schema_url)
    
    # Validate configuration
    print("Validating server.json against schema...")
    validate_server_config(config, schema)
    
    # Additional validation checks
    print("\nPerforming additional validation checks...")
    
    # Check namespace format
    name = config.get("name", "")
    if not name.startswith("io.github."):
        print(f"Warning: Namespace '{name}' doesn't use GitHub format (io.github.*)", file=sys.stderr)
    
    # Check version consistency
    if "packages" in config:
        config_version = config.get("version")
        for pkg in config["packages"]:
            pkg_version = pkg.get("version")
            if pkg_version != config_version:
                print(f"Warning: Package version '{pkg_version}' doesn't match config version '{config_version}'", file=sys.stderr)
    
    print("\n✓ All validation checks passed!")


if __name__ == "__main__":
    main()
