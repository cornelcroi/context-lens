"""Python parser using AST for intelligent code chunking."""

import ast
import logging
import uuid
from typing import List, Optional

from ..models.data_models import DocumentChunk
from .base import CodeUnit, CodeUnitType, LanguageParser, ParsingError, SyntaxParsingError

logger = logging.getLogger(__name__)


class PythonParser(LanguageParser):
    """Parser for Python source code using AST.

    Uses Python's built-in ast module to parse code into logical units
    (functions, classes, methods) while preserving docstrings and decorators.
    """

    @classmethod
    def get_supported_extensions(cls) -> List[str]:
        """Get supported file extensions.

        Returns:
            List of Python file extensions
        """
        return [".py", ".pyw"]

    def parse(self, content: str, file_path: str) -> List[CodeUnit]:
        """Parse Python code using AST.

        Args:
            content: Python source code
            file_path: Path to the file (for error reporting)

        Returns:
            List of CodeUnit objects representing parsed structures

        Raises:
            SyntaxParsingError: If Python code has syntax errors
        """
        try:
            tree = ast.parse(content)
            code_units = []

            # Extract imports first
            imports = self._extract_imports(tree, content)
            if imports:
                code_units.extend(imports)

            # Extract top-level classes and functions
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.ClassDef):
                    unit = self._extract_class(node, content)
                    if unit:
                        code_units.append(unit)
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    unit = self._extract_function(node, content)
                    if unit:
                        code_units.append(unit)

            logger.debug(f"Parsed {len(code_units)} code units from {file_path}")
            return code_units

        except SyntaxError as e:
            logger.warning(f"Python syntax error in {file_path}: {e}")
            raise SyntaxParsingError(f"Syntax error in Python file: {e}") from e
        except Exception as e:
            logger.error(f"Failed to parse Python file {file_path}: {e}")
            raise ParsingError(f"Failed to parse Python file: {e}") from e

    def _extract_imports(self, tree: ast.AST, content: str) -> List[CodeUnit]:
        """Extract import statements.

        Args:
            tree: AST tree
            content: Source code content

        Returns:
            List of CodeUnit objects for imports
        """
        import_nodes = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                import_nodes.append(node)

        if not import_nodes:
            return []

        # Group all imports together
        source_lines = content.split("\n")
        first_import = import_nodes[0]
        last_import = import_nodes[-1]

        import_content = "\n".join(
            source_lines[first_import.lineno - 1 : last_import.end_lineno]
        )

        return [
            CodeUnit(
                type=CodeUnitType.IMPORT,
                name="imports",
                content=import_content,
                start_line=first_import.lineno,
                end_line=last_import.end_lineno,
            )
        ]

    def _extract_class(
        self, node: ast.ClassDef, content: str, parent: Optional[str] = None
    ) -> Optional[CodeUnit]:
        """Extract class definition as a code unit.

        Args:
            node: AST ClassDef node
            content: Source code content
            parent: Parent class name if this is a nested class

        Returns:
            CodeUnit for the class
        """
        source_lines = content.split("\n")

        # Get source code for this class
        class_content = "\n".join(source_lines[node.lineno - 1 : node.end_lineno])

        # Extract docstring
        docstring = ast.get_docstring(node)

        # Extract decorators
        decorators = []
        for dec in node.decorator_list:
            try:
                dec_str = ast.unparse(dec)
                # Ensure decorator starts with @
                if not dec_str.startswith("@"):
                    dec_str = f"@{dec_str}"
                decorators.append(dec_str)
            except Exception:
                # If unparsing fails, just use the decorator name
                if isinstance(dec, ast.Name):
                    decorators.append(f"@{dec.id}")

        return CodeUnit(
            type=CodeUnitType.CLASS,
            name=node.name,
            content=class_content,
            start_line=node.lineno,
            end_line=node.end_lineno,
            parent=parent,
            docstring=docstring,
            decorators=decorators,
            metadata={"base_classes": [base.id for base in node.bases if isinstance(base, ast.Name)]},
        )

    def _extract_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        content: str,
        parent: Optional[str] = None,
    ) -> Optional[CodeUnit]:
        """Extract function definition as a code unit.

        Args:
            node: AST FunctionDef or AsyncFunctionDef node
            content: Source code content
            parent: Parent class name if this is a method

        Returns:
            CodeUnit for the function
        """
        source_lines = content.split("\n")

        # Get source code for this function
        func_content = "\n".join(source_lines[node.lineno - 1 : node.end_lineno])

        # Extract docstring
        docstring = ast.get_docstring(node)

        # Extract decorators
        decorators = []
        for dec in node.decorator_list:
            try:
                dec_str = ast.unparse(dec)
                # Ensure decorator starts with @
                if not dec_str.startswith("@"):
                    dec_str = f"@{dec_str}"
                decorators.append(dec_str)
            except Exception:
                if isinstance(dec, ast.Name):
                    decorators.append(f"@{dec.id}")

        # Determine if it's a method or function
        unit_type = CodeUnitType.METHOD if parent else CodeUnitType.FUNCTION

        # Check if it's async
        is_async = isinstance(node, ast.AsyncFunctionDef)

        return CodeUnit(
            type=unit_type,
            name=node.name,
            content=func_content,
            start_line=node.lineno,
            end_line=node.end_lineno,
            parent=parent,
            docstring=docstring,
            decorators=decorators,
            metadata={"is_async": is_async},
        )

    def chunk(self, code_units: List[CodeUnit], document_id: str) -> List[DocumentChunk]:
        """Convert code units into document chunks.

        Args:
            code_units: List of parsed code units
            document_id: ID of the document

        Returns:
            List of DocumentChunk objects
        """
        chunks = []
        current_units = []
        current_size = 0

        for unit in code_units:
            unit_size = len(unit.content)

            # If this unit alone exceeds chunk size, split it
            if unit_size > self.chunk_size * 1.5:
                # Save current chunk if any
                if current_units:
                    chunks.extend(
                        self._create_chunks_from_units(current_units, document_id, len(chunks))
                    )
                    current_units = []
                    current_size = 0

                # Split large unit
                chunks.extend(self._split_large_unit(unit, document_id, len(chunks)))
                continue

            # If adding this unit would exceed chunk size, finalize current chunk
            if current_size + unit_size > self.chunk_size and current_units:
                chunks.extend(
                    self._create_chunks_from_units(current_units, document_id, len(chunks))
                )
                current_units = []
                current_size = 0

            # Add unit to current chunk
            current_units.append(unit)
            current_size += unit_size

        # Finalize remaining chunk
        if current_units:
            chunks.extend(self._create_chunks_from_units(current_units, document_id, len(chunks)))

        return chunks

    def _create_chunks_from_units(
        self, units: List[CodeUnit], document_id: str, start_index: int
    ) -> List[DocumentChunk]:
        """Create document chunks from code units.

        Args:
            units: List of code units to combine
            document_id: Document ID
            start_index: Starting chunk index

        Returns:
            List containing a single DocumentChunk
        """
        content = "\n\n".join(unit.content for unit in units)

        # Create metadata
        metadata = self._create_chunk_metadata(units, "python", "code")

        # Add Python-specific metadata
        metadata["has_docstrings"] = any(u.docstring for u in units)
        metadata["has_decorators"] = any(u.decorators for u in units)

        chunk = DocumentChunk(
            id=str(uuid.uuid4()),
            document_id=document_id,
            content=content,
            chunk_index=start_index,
            embedding=[],
            metadata=metadata,
        )

        return [chunk]

    def _split_large_unit(
        self, unit: CodeUnit, document_id: str, start_index: int
    ) -> List[DocumentChunk]:
        """Split a large code unit into multiple chunks.

        Args:
            unit: Large code unit to split
            document_id: Document ID
            start_index: Starting chunk index

        Returns:
            List of DocumentChunk objects
        """
        # For very large functions/classes, split by lines with overlap
        lines = unit.content.split("\n")
        chunks = []
        current_lines = []
        current_size = 0

        for line in lines:
            line_size = len(line) + 1  # +1 for newline

            if current_size + line_size > self.chunk_size and current_lines:
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
                            "language": "python",
                            "parent_structure": f"{unit.type.value} {unit.name}",
                            "is_partial": True,
                            "original_unit_type": unit.type.value,
                        },
                    )
                )

                # Start new chunk with overlap (last few lines)
                overlap_lines = current_lines[-3:] if len(current_lines) > 3 else current_lines
                current_lines = overlap_lines + [line]
                current_size = sum(len(l) + 1 for l in current_lines)
            else:
                current_lines.append(line)
                current_size += line_size

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
                        "language": "python",
                        "parent_structure": f"{unit.type.value} {unit.name}",
                        "is_partial": True,
                        "original_unit_type": unit.type.value,
                    },
                )
            )

        return chunks
