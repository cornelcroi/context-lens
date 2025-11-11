"""JavaScript/TypeScript parser using regex patterns."""

import re
import uuid
from typing import List, Optional

from ..models.data_models import DocumentChunk
from .base import CodeUnit, CodeUnitType, LanguageParser, ParsingError

import logging

logger = logging.getLogger(__name__)


class JavaScriptParser(LanguageParser):
    """Parser for JavaScript and TypeScript source code.

    Uses regex patterns to identify functions, classes, and other structures
    in JavaScript/TypeScript code.
    """

    @classmethod
    def get_supported_extensions(cls) -> List[str]:
        """Get supported file extensions."""
        return [".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"]

    def parse(self, content: str, file_path: str) -> List[CodeUnit]:
        """Parse JavaScript/TypeScript code into code units."""
        code_units = []

        # Extract imports/requires
        imports = self._extract_imports(content)
        if imports:
            code_units.extend(imports)

        # Extract classes
        classes = self._extract_classes(content)
        code_units.extend(classes)

        # Extract functions (regular and arrow)
        functions = self._extract_functions(content)
        code_units.extend(functions)

        # Sort by start line
        code_units.sort(key=lambda u: u.start_line)

        return code_units

    def _extract_imports(self, content: str) -> List[CodeUnit]:
        """Extract import and require statements."""
        units = []

        # Pattern for ES6 imports and CommonJS requires
        import_patterns = [
            r"^import\s+.+?from\s+['\"].+?['\"];?",
            r"^import\s+['\"].+?['\"];?",
            r"^const\s+.+?=\s+require\(['\"].+?['\"]\);?",
            r"^var\s+.+?=\s+require\(['\"].+?['\"]\);?",
            r"^let\s+.+?=\s+require\(['\"].+?['\"]\);?",
        ]

        all_imports = []
        for pattern in import_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            all_imports.extend(matches)

        if all_imports:
            # Sort by position
            all_imports.sort(key=lambda m: m.start())
            first = all_imports[0]
            last = all_imports[-1]

            start_line = content[:first.start()].count("\n") + 1
            end_line = content[:last.end()].count("\n") + 1

            import_content = content[first.start():last.end()]

            units.append(
                CodeUnit(
                    type=CodeUnitType.IMPORT,
                    name="imports",
                    content=import_content,
                    start_line=start_line,
                    end_line=end_line,
                )
            )

        return units

    def _extract_classes(self, content: str) -> List[CodeUnit]:
        """Extract class definitions."""
        units = []

        # Pattern for class declarations
        class_pattern = r"(?:export\s+)?(?:default\s+)?class\s+(\w+)(?:\s+extends\s+\w+)?\s*\{"

        for match in re.finditer(class_pattern, content):
            class_name = match.group(1)
            start_pos = match.start()

            # Find matching closing brace
            end_pos = self._find_matching_brace(content, match.end() - 1)
            if end_pos == -1:
                continue

            class_content = content[start_pos:end_pos + 1]
            start_line = content[:start_pos].count("\n") + 1
            end_line = content[:end_pos].count("\n") + 1

            # Extract JSDoc
            jsdoc = self._extract_jsdoc(content, start_pos)

            units.append(
                CodeUnit(
                    type=CodeUnitType.CLASS,
                    name=class_name,
                    content=class_content,
                    start_line=start_line,
                    end_line=end_line,
                    docstring=jsdoc,
                )
            )

        return units

    def _extract_functions(self, content: str) -> List[CodeUnit]:
        """Extract function declarations, expressions, and arrow functions."""
        units = []

        # Pattern for function declarations
        func_decl_pattern = r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\([^)]*\)\s*\{"

        # Pattern for arrow functions assigned to variables
        arrow_pattern = r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>\s*\{"

        # Pattern for function expressions
        func_expr_pattern = r"(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?function\s*\([^)]*\)\s*\{"

        patterns = [
            (func_decl_pattern, "function"),
            (arrow_pattern, "arrow_function"),
            (func_expr_pattern, "function_expression"),
        ]

        for pattern, func_type in patterns:
            for match in re.finditer(pattern, content):
                func_name = match.group(1)
                start_pos = match.start()

                # Find matching closing brace
                brace_pos = content.find("{", match.end() - 10)
                if brace_pos == -1:
                    continue

                end_pos = self._find_matching_brace(content, brace_pos)
                if end_pos == -1:
                    continue

                func_content = content[start_pos:end_pos + 1]
                start_line = content[:start_pos].count("\n") + 1
                end_line = content[:end_pos].count("\n") + 1

                # Extract JSDoc
                jsdoc = self._extract_jsdoc(content, start_pos)

                units.append(
                    CodeUnit(
                        type=CodeUnitType.FUNCTION,
                        name=func_name,
                        content=func_content,
                        start_line=start_line,
                        end_line=end_line,
                        docstring=jsdoc,
                        metadata={"function_type": func_type},
                    )
                )

        return units

    def _extract_jsdoc(self, content: str, item_start: int) -> Optional[str]:
        """Extract JSDoc comment before function/class."""
        before_item = content[:item_start].rstrip()

        # Look for JSDoc comment (/** ... */)
        jsdoc_pattern = r"/\*\*[\s\S]*?\*/"
        matches = list(re.finditer(jsdoc_pattern, before_item))

        if matches:
            last_match = matches[-1]
            # Check if it's immediately before the item
            between = before_item[last_match.end():].strip()
            if not between or between.startswith("export") or between.startswith("async"):
                return last_match.group(0)

        return None

    def chunk(self, code_units: List[CodeUnit], document_id: str) -> List[DocumentChunk]:
        """Convert code units into document chunks."""
        if not code_units:
            return []

        chunks = []
        current_units = []
        current_size = 0

        for unit in code_units:
            unit_size = len(unit.content)

            # If this unit is too large, split it
            if unit_size > self.chunk_size * 1.5:
                # Save current chunk
                if current_units:
                    chunks.append(
                        self._create_chunk_from_units(current_units, document_id, len(chunks))
                    )
                    current_units = []
                    current_size = 0

                # Split large unit
                chunks.extend(self._split_large_unit(unit, document_id, len(chunks)))
                continue

            # If adding this would exceed size, finalize current chunk
            if current_size + unit_size > self.chunk_size and current_units:
                chunks.append(
                    self._create_chunk_from_units(current_units, document_id, len(chunks))
                )
                current_units = []
                current_size = 0

            current_units.append(unit)
            current_size += unit_size

        # Finalize remaining
        if current_units:
            chunks.append(self._create_chunk_from_units(current_units, document_id, len(chunks)))

        return chunks

    def _create_chunk_from_units(
        self, units: List[CodeUnit], document_id: str, index: int
    ) -> DocumentChunk:
        """Create a document chunk from code units."""
        content = "\n\n".join(unit.content for unit in units)
        metadata = self._create_chunk_metadata(units, "javascript", "code")

        return DocumentChunk(
            id=str(uuid.uuid4()),
            document_id=document_id,
            content=content,
            chunk_index=index,
            embedding=[],
            metadata=metadata,
        )

    def _split_large_unit(
        self, unit: CodeUnit, document_id: str, start_index: int
    ) -> List[DocumentChunk]:
        """Split a large code unit into multiple chunks."""
        lines = unit.content.split("\n")
        chunks = []
        current_lines = []
        current_size = 0

        for line in lines:
            if current_size + len(line) > self.chunk_size and current_lines:
                # Create chunk
                chunk_content = "\n".join(current_lines)
                chunks.append(
                    DocumentChunk(
                        id=str(uuid.uuid4()),
                        document_id=document_id,
                        content=chunk_content,
                        chunk_index=start_index + len(chunks),
                        embedding=[],
                        metadata={
                            "chunk_type": "code_split",
                            "language": "javascript",
                            "parent_structure": f"{unit.type.value} {unit.name}",
                            "is_partial": True,
                        },
                    )
                )

                # Start new chunk with overlap
                overlap_lines = current_lines[-3:] if len(current_lines) > 3 else current_lines
                current_lines = overlap_lines + [line]
                current_size = sum(len(l) for l in current_lines)
            else:
                current_lines.append(line)
                current_size += len(line)

        # Add final chunk
        if current_lines:
            chunk_content = "\n".join(current_lines)
            chunks.append(
                DocumentChunk(
                    id=str(uuid.uuid4()),
                    document_id=document_id,
                    content=chunk_content,
                    chunk_index=start_index + len(chunks),
                    embedding=[],
                    metadata={
                        "chunk_type": "code_split",
                        "language": "javascript",
                        "parent_structure": f"{unit.type.value} {unit.name}",
                        "is_partial": True,
                    },
                )
            )

        return chunks
