"""Tests for Markdown parser."""

import pytest

from context_lens.parsers import CodeUnitType, MarkdownParser


class TestMarkdownParser:
    """Test MarkdownParser functionality."""

    def test_supported_extensions(self):
        """Test that Markdown parser supports all markdown extensions."""
        extensions = MarkdownParser.get_supported_extensions()
        assert ".md" in extensions
        assert ".markdown" in extensions
        assert ".mdx" in extensions

    def test_parse_simple_header(self):
        """Test parsing a simple markdown header."""
        parser = MarkdownParser()
        content = '''# Main Title

Some content here.
'''
        units = parser.parse(content, "test.md")

        assert len(units) == 1
        assert units[0].name == "Main Title"
        assert units[0].metadata["header_level"] == 1
        assert units[0].type == CodeUnitType.MODULE

    def test_parse_multiple_headers(self):
        """Test parsing multiple headers."""
        parser = MarkdownParser()
        content = '''# Title

Introduction text.

## Section 1

Section 1 content.

## Section 2

Section 2 content.
'''
        units = parser.parse(content, "test.md")

        assert len(units) == 3
        assert units[0].name == "Title"
        assert units[1].name == "Section 1"
        assert units[2].name == "Section 2"

    def test_parse_header_hierarchy(self):
        """Test parsing nested header hierarchy."""
        parser = MarkdownParser()
        content = '''# Level 1

Content 1

## Level 2

Content 2

### Level 3

Content 3
'''
        units = parser.parse(content, "test.md")

        assert len(units) == 3
        assert units[0].metadata["header_level"] == 1
        assert units[1].metadata["header_level"] == 2
        assert units[2].metadata["header_level"] == 3

    def test_parse_code_blocks(self):
        """Test parsing markdown with code blocks."""
        parser = MarkdownParser()
        content = '''# Code Example

Here's some code:

```python
def hello():
    print("Hello")
```

More text.
'''
        units = parser.parse(content, "test.md")

        assert len(units) == 1
        assert units[0].metadata["has_code_blocks"] is True
        assert units[0].metadata["code_block_count"] == 1
        assert "```python" in units[0].content

    def test_parse_multiple_code_blocks(self):
        """Test parsing markdown with multiple code blocks."""
        parser = MarkdownParser()
        content = '''# Examples

Python example:

```python
print("Hello")
```

JavaScript example:

```javascript
console.log("Hello");
```
'''
        units = parser.parse(content, "test.md")

        assert len(units) == 1
        assert units[0].metadata["code_block_count"] == 2

    def test_parse_readme(self):
        """Test parsing a realistic README file."""
        parser = MarkdownParser()
        content = '''# My Project

A description of my project.

## Installation

```bash
npm install my-project
```

## Usage

Import and use:

```javascript
import { myFunc } from 'my-project';
```

## API

### myFunc()

Does something useful.

## License

MIT
'''
        units = parser.parse(content, "README.md")

        # Parser creates separate sections for each header including ###
        assert len(units) == 6
        assert units[0].name == "My Project"
        assert units[1].name == "Installation"
        assert units[2].name == "Usage"
        assert units[3].name == "API"
        assert units[4].name == "myFunc()"
        assert units[5].name == "License"

    def test_parse_no_headers(self):
        """Test parsing markdown without headers."""
        parser = MarkdownParser()
        content = '''Just some text without any headers.

Another paragraph.
'''
        units = parser.parse(content, "test.md")

        # Should create an "Introduction" section
        assert len(units) == 1
        assert units[0].name == "Introduction"
        assert units[0].metadata["header_level"] == 0

    def test_chunk_small_document(self):
        """Test chunking a small markdown document."""
        parser = MarkdownParser(chunk_size=1000)
        content = '''# Title

Small content.
'''
        units = parser.parse(content, "test.md")
        chunks = parser.chunk(units, "doc123")

        assert len(chunks) == 1
        assert chunks[0].document_id == "doc123"
        assert chunks[0].metadata["language"] == "markdown"
        assert chunks[0].metadata["chunk_type"] == "markdown"

    def test_chunk_multiple_sections(self):
        """Test chunking multiple sections."""
        parser = MarkdownParser(chunk_size=200)
        content = '''# Title

## Section 1

Content 1

## Section 2

Content 2

## Section 3

Content 3
'''
        units = parser.parse(content, "test.md")
        chunks = parser.chunk(units, "doc123")

        assert len(chunks) >= 1
        for chunk in chunks:
            assert chunk.metadata["language"] == "markdown"
            assert "sections" in chunk.metadata

    def test_chunk_large_section(self):
        """Test chunking a very large section."""
        parser = MarkdownParser(chunk_size=100)
        paragraphs = [f"Paragraph {i} with some content." for i in range(20)]
        content = f"# Large Section\n\n" + "\n\n".join(paragraphs)
        
        units = parser.parse(content, "test.md")
        chunks = parser.chunk(units, "doc123")

        # Should split into multiple chunks
        assert len(chunks) > 1
        for chunk in chunks:
            assert chunk.metadata["is_partial"] is True

    def test_chunk_metadata(self):
        """Test that chunk metadata is properly set."""
        parser = MarkdownParser()
        content = '''# Main

## Sub

Content
'''
        units = parser.parse(content, "test.md")
        chunks = parser.chunk(units, "doc123")

        assert len(chunks) == 1
        metadata = chunks[0].metadata
        assert metadata["language"] == "markdown"
        assert metadata["chunk_type"] == "markdown"
        assert "Main" in metadata["sections"]
        assert "Sub" in metadata["sections"]
        assert metadata["section_hierarchy"] == "Main > Sub"

    def test_empty_file(self):
        """Test parsing an empty markdown file."""
        parser = MarkdownParser()
        content = ""
        
        units = parser.parse(content, "test.md")
        # Empty content creates an Introduction section with empty content
        assert len(units) == 1

    def test_parse_lists(self):
        """Test parsing markdown with lists."""
        parser = MarkdownParser()
        content = '''# Lists

Unordered list:
- Item 1
- Item 2
- Item 3

Ordered list:
1. First
2. Second
3. Third
'''
        units = parser.parse(content, "test.md")

        assert len(units) == 1
        assert "- Item 1" in units[0].content
        assert "1. First" in units[0].content

    def test_parse_links_and_images(self):
        """Test parsing markdown with links and images."""
        parser = MarkdownParser()
        content = '''# Media

Check out [this link](https://example.com).

![Alt text](image.png)
'''
        units = parser.parse(content, "test.md")

        assert len(units) == 1
        assert "[this link]" in units[0].content
        assert "![Alt text]" in units[0].content

    def test_parse_tables(self):
        """Test parsing markdown with tables."""
        parser = MarkdownParser()
        content = '''# Data

| Name | Age |
|------|-----|
| Alice| 30  |
| Bob  | 25  |
'''
        units = parser.parse(content, "test.md")

        assert len(units) == 1
        assert "| Name | Age |" in units[0].content

    def test_parse_blockquotes(self):
        """Test parsing markdown with blockquotes."""
        parser = MarkdownParser()
        content = '''# Quotes

> This is a quote.
> It spans multiple lines.

Regular text.
'''
        units = parser.parse(content, "test.md")

        assert len(units) == 1
        assert "> This is a quote" in units[0].content

    def test_parse_horizontal_rules(self):
        """Test parsing markdown with horizontal rules."""
        parser = MarkdownParser()
        content = '''# Section

Content above.

---

Content below.
'''
        units = parser.parse(content, "test.md")

        assert len(units) == 1
        assert "---" in units[0].content

    def test_word_count_metadata(self):
        """Test that word count is tracked in metadata."""
        parser = MarkdownParser()
        content = '''# Title

This is a sentence with exactly ten words in it.
'''
        units = parser.parse(content, "test.md")

        assert len(units) == 1
        assert "word_count" in units[0].metadata
        assert units[0].metadata["word_count"] > 0

    def test_parse_inline_code(self):
        """Test parsing markdown with inline code."""
        parser = MarkdownParser()
        content = '''# Code

Use the `print()` function to output text.
'''
        units = parser.parse(content, "test.md")

        assert len(units) == 1
        assert "`print()`" in units[0].content

    def test_parse_emphasis(self):
        """Test parsing markdown with emphasis."""
        parser = MarkdownParser()
        content = '''# Emphasis

This is *italic* and this is **bold**.

This is _also italic_ and this is __also bold__.
'''
        units = parser.parse(content, "test.md")

        assert len(units) == 1
        assert "*italic*" in units[0].content
        assert "**bold**" in units[0].content

    def test_parse_nested_lists(self):
        """Test parsing markdown with nested lists."""
        parser = MarkdownParser()
        content = '''# Nested

- Item 1
  - Subitem 1.1
  - Subitem 1.2
- Item 2
'''
        units = parser.parse(content, "test.md")

        assert len(units) == 1
        assert "Subitem 1.1" in units[0].content

    def test_parse_task_lists(self):
        """Test parsing markdown with task lists."""
        parser = MarkdownParser()
        content = '''# Tasks

- [x] Completed task
- [ ] Incomplete task
'''
        units = parser.parse(content, "test.md")

        assert len(units) == 1
        assert "- [x]" in units[0].content
        assert "- [ ]" in units[0].content

    def test_parse_footnotes(self):
        """Test parsing markdown with footnotes."""
        parser = MarkdownParser()
        content = '''# Content

This has a footnote[^1].

[^1]: This is the footnote.
'''
        units = parser.parse(content, "test.md")

        assert len(units) == 1
        assert "[^1]" in units[0].content

    def test_chunk_section_hierarchy(self):
        """Test that section hierarchy is preserved in chunks."""
        parser = MarkdownParser(chunk_size=1000)
        content = '''# Main

## Sub1

### Sub1.1

Content
'''
        units = parser.parse(content, "test.md")
        chunks = parser.chunk(units, "doc123")

        assert len(chunks) == 1
        hierarchy = chunks[0].metadata["section_hierarchy"]
        assert "Main" in hierarchy
        assert "Sub1" in hierarchy
        assert "Sub1.1" in hierarchy

    def test_chunk_header_levels(self):
        """Test that header levels are tracked in chunk metadata."""
        parser = MarkdownParser(chunk_size=1000)
        content = '''# Level 1

## Level 2

### Level 3
'''
        units = parser.parse(content, "test.md")
        chunks = parser.chunk(units, "doc123")

        assert len(chunks) == 1
        levels = chunks[0].metadata["header_levels"]
        assert 1 in levels
        assert 2 in levels
        assert 3 in levels

    def test_real_world_documentation(self):
        """Test parsing realistic documentation."""
        parser = MarkdownParser()
        content = '''# API Documentation

## Overview

This API provides access to user data.

## Authentication

All requests require an API key:

```bash
curl -H "Authorization: Bearer YOUR_KEY" https://api.example.com
```

## Endpoints

### GET /users

Returns a list of users.

**Parameters:**
- `limit` (optional): Maximum number of results
- `offset` (optional): Pagination offset

**Response:**

```json
{
  "users": [...],
  "total": 100
}
```

### POST /users

Creates a new user.

## Rate Limiting

Requests are limited to 1000 per hour.

## Support

Contact support@example.com for help.
'''
        units = parser.parse(content, "api-docs.md")

        # Should have multiple sections
        assert len(units) >= 5
        section_names = [u.name for u in units]
        assert "API Documentation" in section_names
        assert "Authentication" in section_names
        assert "Endpoints" in section_names

    def test_parse_mdx_content(self):
        """Test parsing MDX content (markdown with JSX)."""
        parser = MarkdownParser()
        content = '''# Component Demo

<MyComponent prop="value">
  Content here
</MyComponent>

Regular markdown continues.
'''
        units = parser.parse(content, "test.mdx")

        assert len(units) == 1
        assert "<MyComponent" in units[0].content

    def test_unit_type_by_header_level(self):
        """Test that unit types are assigned based on header level."""
        parser = MarkdownParser()
        content = '''# Level 1

## Level 2

### Level 3
'''
        units = parser.parse(content, "test.md")

        assert units[0].type == CodeUnitType.MODULE  # Level 1
        assert units[1].type == CodeUnitType.CLASS   # Level 2
        assert units[2].type == CodeUnitType.FUNCTION  # Level 3
