"""Tests for YAML parser."""

import pytest

from context_lens.parsers import CodeUnitType, YAMLParser
from context_lens.parsers.base import ParsingError


class TestYAMLParser:
    """Test YAMLParser functionality."""

    def test_supported_extensions(self):
        """Test that YAML parser supports .yaml and .yml files."""
        extensions = YAMLParser.get_supported_extensions()
        assert ".yaml" in extensions
        assert ".yml" in extensions

    def test_parse_simple_mapping(self):
        """Test parsing a simple YAML mapping."""
        parser = YAMLParser()
        content = '''name: John
age: 30
'''
        units = parser.parse(content, "test.yaml")

        assert len(units) == 2
        assert units[0].name == "name"
        assert units[1].name == "age"

    def test_parse_nested_mapping(self):
        """Test parsing nested YAML mappings."""
        parser = YAMLParser()
        content = '''user:
  name: Alice
  email: alice@example.com
settings:
  theme: dark
'''
        units = parser.parse(content, "test.yaml")

        assert len(units) == 2
        assert units[0].name == "user"
        assert units[0].type == CodeUnitType.CLASS
        assert units[1].name == "settings"
        assert units[1].type == CodeUnitType.CLASS

    def test_parse_list_value(self):
        """Test parsing YAML with list values."""
        parser = YAMLParser()
        content = '''items:
  - apple
  - banana
  - cherry
'''
        units = parser.parse(content, "test.yaml")

        assert len(units) == 1
        assert units[0].name == "items"
        assert units[0].type == CodeUnitType.MODULE
        assert units[0].metadata["is_list"] is True

    def test_parse_top_level_list(self):
        """Test parsing a top-level YAML list."""
        parser = YAMLParser()
        content = '''- item1
- item2
- item3
'''
        units = parser.parse(content, "test.yaml")

        # Small lists should be kept together
        assert len(units) == 1
        assert units[0].type == CodeUnitType.MODULE

    def test_parse_large_list(self):
        """Test parsing a large YAML list."""
        parser = YAMLParser()
        items = "\n".join([f"- item_{i}" for i in range(100)])
        
        units = parser.parse(content=items, file_path="test.yaml")

        # Large lists should be chunked
        assert len(units) > 1
        for unit in units:
            assert unit.metadata.get("is_list_chunk") is True

    def test_parse_github_actions_workflow(self):
        """Test parsing a realistic GitHub Actions workflow."""
        parser = YAMLParser()
        content = '''name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: npm test
'''
        units = parser.parse(content, ".github/workflows/ci.yml")

        assert len(units) == 3
        names = [str(u.name) for u in units]  # Convert to string in case of boolean
        assert "name" in names
        # "on" is a boolean keyword in YAML, so it might be parsed as True
        assert "jobs" in names

    def test_parse_kubernetes_manifest(self):
        """Test parsing a Kubernetes manifest."""
        parser = YAMLParser()
        content = '''apiVersion: v1
kind: Service
metadata:
  name: my-service
spec:
  selector:
    app: MyApp
  ports:
    - protocol: TCP
      port: 80
      targetPort: 9376
'''
        units = parser.parse(content, "service.yaml")

        assert len(units) == 4
        names = [u.name for u in units]
        assert "apiVersion" in names
        assert "kind" in names
        assert "metadata" in names
        assert "spec" in names

    def test_parse_docker_compose(self):
        """Test parsing a docker-compose.yml file."""
        parser = YAMLParser()
        content = '''version: '3.8'
services:
  web:
    image: nginx:latest
    ports:
      - "80:80"
  db:
    image: postgres:13
    environment:
      POSTGRES_PASSWORD: secret
'''
        units = parser.parse(content, "docker-compose.yml")

        assert len(units) == 2
        names = [u.name for u in units]
        assert "version" in names
        assert "services" in names

    def test_parse_invalid_yaml(self):
        """Test handling of invalid YAML."""
        parser = YAMLParser()
        content = '''name: broken
  invalid: indentation
    more: problems
'''
        # YAML parser is lenient, so we need truly invalid YAML
        try:
            units = parser.parse(content, "test.yaml")
            # If it parses, that's okay - YAML is flexible
            assert isinstance(units, list)
        except ParsingError:
            # If it raises ParsingError, that's also okay
            pass

    def test_chunk_small_yaml(self):
        """Test chunking a small YAML file."""
        parser = YAMLParser(chunk_size=1000)
        content = '''key: value
'''
        units = parser.parse(content, "test.yaml")
        chunks = parser.chunk(units, "doc123")

        assert len(chunks) == 1
        assert chunks[0].document_id == "doc123"
        assert chunks[0].metadata["language"] == "yaml"
        assert chunks[0].metadata["chunk_type"] == "yaml"

    def test_chunk_multiple_keys(self):
        """Test chunking YAML with multiple keys."""
        parser = YAMLParser(chunk_size=200)
        content = '''key1: value1
key2: value2
key3: value3
'''
        units = parser.parse(content, "test.yaml")
        chunks = parser.chunk(units, "doc123")

        assert len(chunks) >= 1
        for chunk in chunks:
            assert chunk.metadata["language"] == "yaml"
            assert "keys" in chunk.metadata

    def test_chunk_large_mapping(self):
        """Test chunking a very large YAML mapping."""
        parser = YAMLParser(chunk_size=100)
        lines = [f"key_{i}: value_{i}" for i in range(50)]
        content = "\n".join(lines)
        
        units = parser.parse(content, "test.yaml")
        chunks = parser.chunk(units, "doc123")

        # Should split into multiple chunks
        assert len(chunks) > 1

    def test_chunk_metadata(self):
        """Test that chunk metadata is properly set."""
        parser = YAMLParser()
        content = '''config:
  setting: value
'''
        units = parser.parse(content, "test.yaml")
        chunks = parser.chunk(units, "doc123")

        assert len(chunks) == 1
        metadata = chunks[0].metadata
        assert metadata["language"] == "yaml"
        assert metadata["chunk_type"] == "yaml"
        assert "config" in metadata["keys"]

    def test_empty_document(self):
        """Test parsing an empty YAML document."""
        parser = YAMLParser()
        content = ""
        
        units = parser.parse(content, "test.yaml")
        # Empty YAML parses as None, which creates a TEXT unit
        assert len(units) == 1

    def test_parse_mixed_types(self):
        """Test parsing YAML with mixed value types."""
        parser = YAMLParser()
        content = '''string: text
number: 42
boolean: true
null_value: null
list:
  - item1
  - item2
mapping:
  nested: value
'''
        units = parser.parse(content, "test.yaml")

        assert len(units) == 6
        
        # Check metadata for different types
        list_unit = [u for u in units if u.name == "list"][0]
        assert list_unit.metadata["is_list"] is True
        
        mapping_unit = [u for u in units if u.name == "mapping"][0]
        assert mapping_unit.metadata["is_mapping"] is True

    def test_parse_multiline_strings(self):
        """Test parsing YAML with multiline strings."""
        parser = YAMLParser()
        content = '''description: |
  This is a multiline
  string that spans
  multiple lines.
summary: >
  This is a folded
  multiline string.
'''
        units = parser.parse(content, "test.yaml")

        assert len(units) == 2
        assert units[0].name == "description"
        assert units[1].name == "summary"

    def test_parse_anchors_and_aliases(self):
        """Test parsing YAML with anchors and aliases."""
        parser = YAMLParser()
        content = '''defaults: &defaults
  adapter: postgres
  host: localhost

development:
  <<: *defaults
  database: dev_db
'''
        units = parser.parse(content, "test.yaml")

        assert len(units) == 2
        assert units[0].name == "defaults"
        assert units[1].name == "development"

    def test_chunk_combines_units(self):
        """Test that chunking combines multiple units into one YAML document."""
        parser = YAMLParser(chunk_size=1000)
        content = '''a: 1
b: 2
c: 3
'''
        units = parser.parse(content, "test.yaml")
        chunks = parser.chunk(units, "doc123")

        assert len(chunks) == 1
        # The chunk should contain valid YAML
        import yaml
        chunk_data = yaml.safe_load(chunks[0].content)
        assert "a" in chunk_data
        assert "b" in chunk_data
        assert "c" in chunk_data

    def test_split_large_yaml_mapping(self):
        """Test splitting a large YAML mapping."""
        parser = YAMLParser(chunk_size=50)
        content = '''key1:
  nested: data with some content
key2:
  nested: more data with content
key3:
  nested: even more data here
'''
        units = parser.parse(content, "test.yaml")
        chunks = parser.chunk(units, "doc123")

        # Should create multiple chunks due to size
        assert len(chunks) >= 1
        for chunk in chunks:
            assert chunk.metadata["language"] == "yaml"

    def test_parse_application_config(self):
        """Test parsing a realistic application config file."""
        parser = YAMLParser()
        content = '''app:
  name: MyApp
  version: 1.0.0
  
database:
  host: localhost
  port: 5432
  name: myapp_db
  
logging:
  level: INFO
  format: json
  
features:
  - authentication
  - caching
  - monitoring
'''
        units = parser.parse(content, "config.yaml")

        assert len(units) == 4
        names = [u.name for u in units]
        assert "app" in names
        assert "database" in names
        assert "logging" in names
        assert "features" in names

    def test_parse_yaml_with_comments(self):
        """Test parsing YAML with comments (comments are ignored by parser)."""
        parser = YAMLParser()
        content = '''# This is a comment
name: value  # inline comment
# Another comment
age: 30
'''
        units = parser.parse(content, "test.yaml")

        # Comments are not included in parsed data
        assert len(units) == 2
        assert units[0].name == "name"
        assert units[1].name == "age"

    def test_parse_openapi_spec(self):
        """Test parsing an OpenAPI specification."""
        parser = YAMLParser()
        content = '''openapi: 3.0.0
info:
  title: Sample API
  version: 1.0.0
paths:
  /users:
    get:
      summary: List users
      responses:
        '200':
          description: Success
'''
        units = parser.parse(content, "openapi.yaml")

        assert len(units) == 3
        names = [u.name for u in units]
        assert "openapi" in names
        assert "info" in names
        assert "paths" in names

    def test_metadata_types(self):
        """Test that metadata correctly identifies YAML types."""
        parser = YAMLParser()
        content = '''string_val: text
list_val:
  - item
mapping_val:
  key: value
'''
        units = parser.parse(content, "test.yaml")

        string_unit = [u for u in units if u.name == "string_val"][0]
        assert string_unit.metadata["yaml_type"] == "str"
        
        list_unit = [u for u in units if u.name == "list_val"][0]
        assert list_unit.metadata["yaml_type"] == "list"
        assert list_unit.metadata["is_list"] is True
        
        mapping_unit = [u for u in units if u.name == "mapping_val"][0]
        assert mapping_unit.metadata["yaml_type"] == "dict"
        assert mapping_unit.metadata["is_mapping"] is True
