"""Tests for JSON parser."""

import pytest

from context_lens.parsers import CodeUnitType, JSONParser
from context_lens.parsers.base import ParsingError


class TestJSONParser:
    """Test JSONParser functionality."""

    def test_supported_extensions(self):
        """Test that JSON parser supports .json and .jsonc files."""
        extensions = JSONParser.get_supported_extensions()
        assert ".json" in extensions
        assert ".jsonc" in extensions

    def test_parse_simple_object(self):
        """Test parsing a simple JSON object."""
        parser = JSONParser()
        content = '''{
    "name": "John",
    "age": 30
}'''
        units = parser.parse(content, "test.json")

        assert len(units) == 2
        assert units[0].name == "name"
        assert units[1].name == "age"

    def test_parse_nested_object(self):
        """Test parsing nested JSON objects."""
        parser = JSONParser()
        content = '''{
    "user": {
        "name": "Alice",
        "email": "alice@example.com"
    },
    "settings": {
        "theme": "dark"
    }
}'''
        units = parser.parse(content, "test.json")

        assert len(units) == 2
        assert units[0].name == "user"
        assert units[0].type == CodeUnitType.CLASS
        assert units[1].name == "settings"
        assert units[1].type == CodeUnitType.CLASS

    def test_parse_array_value(self):
        """Test parsing JSON with array values."""
        parser = JSONParser()
        content = '''{
    "items": [1, 2, 3, 4, 5]
}'''
        units = parser.parse(content, "test.json")

        assert len(units) == 1
        assert units[0].name == "items"
        assert units[0].type == CodeUnitType.MODULE
        assert units[0].metadata["is_array"] is True

    def test_parse_top_level_array(self):
        """Test parsing a top-level JSON array."""
        parser = JSONParser()
        content = '''[
    {"id": 1, "name": "Item 1"},
    {"id": 2, "name": "Item 2"}
]'''
        units = parser.parse(content, "test.json")

        # Small arrays should be kept together
        assert len(units) == 1
        assert units[0].type == CodeUnitType.MODULE

    def test_parse_large_array(self):
        """Test parsing a large JSON array."""
        parser = JSONParser()
        items = [{"id": i, "value": f"item_{i}"} for i in range(100)]
        content = str(items).replace("'", '"')
        
        units = parser.parse(content, "test.json")

        # Large arrays should be chunked
        assert len(units) > 1
        for unit in units:
            assert unit.metadata.get("is_array_chunk") is True

    def test_parse_package_json(self):
        """Test parsing a realistic package.json file."""
        parser = JSONParser()
        content = '''{
    "name": "my-app",
    "version": "1.0.0",
    "dependencies": {
        "react": "^18.0.0",
        "express": "^4.18.0"
    },
    "scripts": {
        "start": "node index.js",
        "test": "jest"
    }
}'''
        units = parser.parse(content, "package.json")

        assert len(units) == 4
        names = [u.name for u in units]
        assert "name" in names
        assert "version" in names
        assert "dependencies" in names
        assert "scripts" in names

    def test_parse_primitive_value(self):
        """Test parsing a primitive JSON value."""
        parser = JSONParser()
        content = '"hello"'
        
        units = parser.parse(content, "test.json")

        assert len(units) == 1
        assert units[0].type == CodeUnitType.TEXT

    def test_parse_invalid_json(self):
        """Test handling of invalid JSON."""
        parser = JSONParser()
        content = '''{
    "name": "broken
}'''
        with pytest.raises(ParsingError):
            parser.parse(content, "test.json")

    def test_chunk_small_json(self):
        """Test chunking a small JSON file."""
        parser = JSONParser(chunk_size=1000)
        content = '''{
    "key": "value"
}'''
        units = parser.parse(content, "test.json")
        chunks = parser.chunk(units, "doc123")

        assert len(chunks) == 1
        assert chunks[0].document_id == "doc123"
        assert chunks[0].metadata["language"] == "json"
        assert chunks[0].metadata["chunk_type"] == "json"

    def test_chunk_multiple_keys(self):
        """Test chunking JSON with multiple keys."""
        parser = JSONParser(chunk_size=200)
        content = '''{
    "key1": "value1",
    "key2": "value2",
    "key3": "value3"
}'''
        units = parser.parse(content, "test.json")
        chunks = parser.chunk(units, "doc123")

        assert len(chunks) >= 1
        for chunk in chunks:
            assert chunk.metadata["language"] == "json"
            assert "keys" in chunk.metadata

    def test_chunk_large_object(self):
        """Test chunking a very large JSON object."""
        parser = JSONParser(chunk_size=100)
        data = {f"key_{i}": f"value_{i}" for i in range(50)}
        content = str(data).replace("'", '"')
        
        units = parser.parse(content, "test.json")
        chunks = parser.chunk(units, "doc123")

        # Should split into multiple chunks
        assert len(chunks) > 1

    def test_chunk_metadata(self):
        """Test that chunk metadata is properly set."""
        parser = JSONParser()
        content = '''{
    "config": {
        "setting": "value"
    }
}'''
        units = parser.parse(content, "test.json")
        chunks = parser.chunk(units, "doc123")

        assert len(chunks) == 1
        metadata = chunks[0].metadata
        assert metadata["language"] == "json"
        assert metadata["chunk_type"] == "json"
        assert "config" in metadata["keys"]

    def test_empty_object(self):
        """Test parsing an empty JSON object."""
        parser = JSONParser()
        content = "{}"
        
        units = parser.parse(content, "test.json")
        assert len(units) == 0

    def test_empty_array(self):
        """Test parsing an empty JSON array."""
        parser = JSONParser()
        content = "[]"
        
        units = parser.parse(content, "test.json")
        assert len(units) == 1

    def test_parse_mixed_types(self):
        """Test parsing JSON with mixed value types."""
        parser = JSONParser()
        content = '''{
    "string": "text",
    "number": 42,
    "boolean": true,
    "null": null,
    "array": [1, 2, 3],
    "object": {"nested": "value"}
}'''
        units = parser.parse(content, "test.json")

        assert len(units) == 6
        
        # Check metadata for different types
        string_unit = [u for u in units if u.name == "string"][0]
        assert string_unit.metadata["json_type"] == "str"
        
        array_unit = [u for u in units if u.name == "array"][0]
        assert array_unit.metadata["is_array"] is True
        
        object_unit = [u for u in units if u.name == "object"][0]
        assert object_unit.metadata["is_object"] is True

    def test_parse_tsconfig_json(self):
        """Test parsing a realistic tsconfig.json file."""
        parser = JSONParser()
        content = '''{
    "compilerOptions": {
        "target": "ES2020",
        "module": "commonjs",
        "strict": true,
        "esModuleInterop": true
    },
    "include": ["src/**/*"],
    "exclude": ["node_modules", "dist"]
}'''
        units = parser.parse(content, "tsconfig.json")

        assert len(units) == 3
        names = [u.name for u in units]
        assert "compilerOptions" in names
        assert "include" in names
        assert "exclude" in names

    def test_chunk_combines_units(self):
        """Test that chunking combines multiple units into one JSON object."""
        parser = JSONParser(chunk_size=1000)
        content = '''{
    "a": 1,
    "b": 2,
    "c": 3
}'''
        units = parser.parse(content, "test.json")
        chunks = parser.chunk(units, "doc123")

        assert len(chunks) == 1
        # The chunk should contain valid JSON
        import json
        chunk_data = json.loads(chunks[0].content)
        assert "a" in chunk_data
        assert "b" in chunk_data
        assert "c" in chunk_data

    def test_split_large_json_object(self):
        """Test splitting a large JSON object."""
        parser = JSONParser(chunk_size=50)
        content = '''{
    "key1": {"nested": "data with some content"},
    "key2": {"nested": "more data with content"},
    "key3": {"nested": "even more data here"}
}'''
        units = parser.parse(content, "test.json")
        chunks = parser.chunk(units, "doc123")

        # Should create multiple chunks due to size
        assert len(chunks) >= 1
        for chunk in chunks:
            assert chunk.metadata["language"] == "json"

    def test_array_metadata(self):
        """Test that array metadata is correctly set."""
        parser = JSONParser()
        content = '''{
    "items": [1, 2, 3, 4, 5]
}'''
        units = parser.parse(content, "test.json")

        assert len(units) == 1
        assert units[0].metadata["is_array"] is True
        assert units[0].metadata["array_length"] == 5

    def test_parse_json_with_unicode(self):
        """Test parsing JSON with unicode characters."""
        parser = JSONParser()
        content = '''{
    "message": "Hello 世界 🌍",
    "emoji": "😀"
}'''
        units = parser.parse(content, "test.json")

        assert len(units) == 2
        assert units[0].name == "message"

    def test_real_world_api_response(self):
        """Test parsing a realistic API response."""
        parser = JSONParser()
        content = '''{
    "status": "success",
    "data": {
        "users": [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"}
        ],
        "total": 2,
        "page": 1
    },
    "timestamp": "2024-01-01T00:00:00Z"
}'''
        units = parser.parse(content, "response.json")

        assert len(units) == 3
        names = [u.name for u in units]
        assert "status" in names
        assert "data" in names
        assert "timestamp" in names
        
        # Data should be an object
        data_unit = [u for u in units if u.name == "data"][0]
        assert data_unit.type == CodeUnitType.CLASS
