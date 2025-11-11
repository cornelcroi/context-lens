"""Rust parser using regex patterns."""

import re
import uuid
from typing import List, Optional

from ..models.data_models import DocumentChunk
from .base import CodeUnit, CodeUnitType, LanguageParser

import logging

logger = logging.getLogger(__name__)


class RustParser(LanguageParser):
    """Parser for Rust source code.

    Uses regex patterns to identify structs, enums, traits, functions,
    and impl blocks in Rust code.
    """

    @classmethod
    def get_supported_extensions(cls) -> List[str]:
        """Get supported file extensions."""
        return [".rs"]

    def parse(self, content: str, file_path: str) -> List[CodeUnit]:
        """Parse Rust code into code units."""
        code_units = []

        # Extract use statements
        uses = self._extract_uses(content)
        if uses:
            code_units.append(uses)

        # Extract structs
        structs = self._extract_structs(content)
        code_units.extend(structs)

        # Extract enums
        enums = self._extract_enums(content)
        code_units.extend(enums)

        # Extract traits
        traits = self._extract_traits(content)
        code_units.extend(traits)

        # Extract impl blocks
        impls = self._extract_impl_blocks(content)
        code_units.extend(impls)

        # Extract standalone functions
        functions = self._extract_functions(content)
        code_units.extend(functions)

        # Sort by start line
        code_units.sort(key=lambda u: u.start_line)

        return code_units

    def _extract_uses(self, content: str) -> Optional[CodeUnit]:
        """Extract use statements."""
        use_pattern = r'^use\s+[\w::{},\s*]+;'
        matches = list(re.finditer(use_pattern, content, re.MULTILINE))

        if matches:
            first_match = matches[0]
            last_match = matches[-1]
            start_line = content[:first_match.start()].count("\n") + 1
            end_line = content[:last_match.end()].count("\n") + 1
            use_content = content[first_match.start() : last_match.end()]

            return CodeUnit(
                type=CodeUnitType.IMPORT,
                name="uses",
                content=use_content,
                start_line=start_line,
                end_line=end_line,
            )
        return None

    def _extract_structs(self, content: str) -> List[CodeUnit]:
        """Extract struct declarations."""
        units = []
        # Pattern for struct: (pub) struct Name (generics) {
        struct_pattern = r"(?:pub\s+)?struct\s+(\w+)(?:<[^>]+>)?\s*\{"

        for match in re.finditer(struct_pattern, content):
            struct_name = match.group(1)
            start_pos = match.start()

            # Find matching closing brace
            end_pos = self._find_matching_brace(content, match.end() - 1)
            if end_pos == -1:
                continue

            struct_content = content[start_pos : end_pos + 1]
            doc_comment = self._extract_rust_doc_comment(content, start_pos)

            units.append(
                CodeUnit(
                    type=CodeUnitType.CLASS,
                    name=struct_name,
                    content=struct_content,
                    start_line=content[:start_pos].count("\n") + 1,
                    end_line=content[:end_pos].count("\n") + 1,
                    docstring=doc_comment,
                    metadata={"rust_type": "struct"},
                )
            )

        return units

    def _extract_enums(self, content: str) -> List[CodeUnit]:
        """Extract enum declarations."""
        units = []
        # Pattern for enum: (pub) enum Name (generics) {
        enum_pattern = r"(?:pub\s+)?enum\s+(\w+)(?:<[^>]+>)?\s*\{"

        for match in re.finditer(enum_pattern, content):
            enum_name = match.group(1)
            start_pos = match.start()

            # Find matching closing brace
            end_pos = self._find_matching_brace(content, match.end() - 1)
            if end_pos == -1:
                continue

            enum_content = content[start_pos : end_pos + 1]
            doc_comment = self._extract_rust_doc_comment(content, start_pos)

            units.append(
                CodeUnit(
                    type=CodeUnitType.CLASS,
                    name=enum_name,
                    content=enum_content,
                    start_line=content[:start_pos].count("\n") + 1,
                    end_line=content[:end_pos].count("\n") + 1,
                    docstring=doc_comment,
                    metadata={"rust_type": "enum"},
                )
            )

        return units

    def _extract_traits(self, content: str) -> List[CodeUnit]:
        """Extract trait declarations."""
        units = []
        # Pattern for trait: (pub) trait Name (generics) {
        trait_pattern = r"(?:pub\s+)?trait\s+(\w+)(?:<[^>]+>)?\s*\{"

        for match in re.finditer(trait_pattern, content):
            trait_name = match.group(1)
            start_pos = match.start()

            # Find matching closing brace
            end_pos = self._find_matching_brace(content, match.end() - 1)
            if end_pos == -1:
                continue

            trait_content = content[start_pos : end_pos + 1]
            doc_comment = self._extract_rust_doc_comment(content, start_pos)

            units.append(
                CodeUnit(
                    type=CodeUnitType.CLASS,
                    name=trait_name,
                    content=trait_content,
                    start_line=content[:start_pos].count("\n") + 1,
                    end_line=content[:end_pos].count("\n") + 1,
                    docstring=doc_comment,
                    metadata={"rust_type": "trait"},
                )
            )

        return units

    def _extract_impl_blocks(self, content: str) -> List[CodeUnit]:
        """Extract impl blocks."""
        units = []
        # Pattern for impl: impl (generics) (Trait for) Type (generics) {
        impl_pattern = r"impl(?:<[^>]+>)?\s+(?:(\w+)(?:<[^>]+>)?\s+for\s+)?(\w+)(?:<[^>]+>)?\s*\{"

        for match in re.finditer(impl_pattern, content):
            trait_name = match.group(1)
            type_name = match.group(2)
            start_pos = match.start()

            # Find matching closing brace
            end_pos = self._find_matching_brace(content, match.end() - 1)
            if end_pos == -1:
                continue

            impl_content = content[start_pos : end_pos + 1]
            doc_comment = self._extract_rust_doc_comment(content, start_pos)

            # Create descriptive name
            if trait_name:
                impl_name = f"{trait_name} for {type_name}"
            else:
                impl_name = type_name

            units.append(
                CodeUnit(
                    type=CodeUnitType.CLASS,
                    name=impl_name,
                    content=impl_content,
                    start_line=content[:start_pos].count("\n") + 1,
                    end_line=content[:end_pos].count("\n") + 1,
                    docstring=doc_comment,
                    metadata={"rust_type": "impl", "trait": trait_name, "type": type_name},
                )
            )

        return units

    def _extract_functions(self, content: str) -> List[CodeUnit]:
        """Extract standalone function declarations (not in impl blocks)."""
        units = []
        # Pattern for function: (pub) (async) (unsafe) (extern) fn name (generics) (params) (-> return) (where clause) {
        fn_pattern = r"(?:pub\s+)?(?:async\s+)?(?:unsafe\s+)?(?:extern\s+\"[^\"]+\"\s+)?fn\s+(\w+)(?:<[^>]+>)?\s*\([^)]*\)(?:\s*->\s*[^{]+)?(?:\s+where\s+[^{]+)?\s*\{"

        for match in re.finditer(fn_pattern, content):
            fn_name = match.group(1)
            start_pos = match.start()

            # Skip if this function is inside an impl block
            if self._is_inside_impl_block(content, start_pos):
                continue

            # Find matching closing brace
            end_pos = self._find_matching_brace(content, match.end() - 1)
            if end_pos == -1:
                continue

            fn_content = content[start_pos : end_pos + 1]
            doc_comment = self._extract_rust_doc_comment(content, start_pos)

            # Check for async
            is_async = "async" in content[start_pos : match.end()]

            units.append(
                CodeUnit(
                    type=CodeUnitType.FUNCTION,
                    name=fn_name,
                    content=fn_content,
                    start_line=content[:start_pos].count("\n") + 1,
                    end_line=content[:end_pos].count("\n") + 1,
                    docstring=doc_comment,
                    metadata={"is_async": is_async},
                )
            )

        return units

    def _is_inside_impl_block(self, content: str, pos: int) -> bool:
        """Check if position is inside an impl or trait block."""
        # Look backwards for impl or trait keyword
        before = content[:pos]
        
        # Check for impl blocks
        impl_pattern = r"impl(?:<[^>]+>)?\s+(?:\w+(?:<[^>]+>)?\s+for\s+)?\w+(?:<[^>]+>)?\s*\{"
        for match in re.finditer(impl_pattern, before):
            impl_start = match.end() - 1
            impl_end = self._find_matching_brace(content, impl_start)
            if impl_end != -1 and impl_start < pos < impl_end:
                return True
        
        # Check for trait blocks
        trait_pattern = r"(?:pub\s+)?trait\s+\w+(?:<[^>]+>)?\s*\{"
        for match in re.finditer(trait_pattern, before):
            trait_start = match.end() - 1
            trait_end = self._find_matching_brace(content, trait_start)
            if trait_end != -1 and trait_start < pos < trait_end:
                return True

        return False

    def _extract_rust_doc_comment(self, content: str, start_pos: int) -> Optional[str]:
        """Extract Rust doc comment (/// or //!) before item."""
        before_code = content[:start_pos].rstrip()
        lines = before_code.split("\n")
        doc_lines = []

        for line in reversed(lines):
            stripped = line.strip()
            if stripped.startswith("///"):
                doc_lines.insert(0, stripped[3:].strip())
            elif stripped.startswith("//!"):
                doc_lines.insert(0, stripped[3:].strip())
            elif stripped.startswith("#["):  # Attribute
                continue
            elif stripped:
                break

        return "\n".join(doc_lines) if doc_lines else None

    def chunk(self, code_units: List[CodeUnit], document_id: str) -> List[DocumentChunk]:
        """Convert Rust code units into chunks."""
        if not code_units:
            return []

        chunks = []
        current_units = []
        current_size = 0

        for unit in code_units:
            unit_size = len(unit.content)

            # If unit is too large, split it
            if unit_size > self.chunk_size * 1.5:
                # Save current chunk if any
                if current_units:
                    chunks.append(self._create_rust_chunk(current_units, document_id, len(chunks)))
                    current_units = []
                    current_size = 0

                # Split large unit
                chunks.extend(self._split_large_unit(unit, document_id, len(chunks)))
                continue

            # If adding this unit exceeds chunk size, save current chunk
            if current_size + unit_size > self.chunk_size and current_units:
                chunks.append(self._create_rust_chunk(current_units, document_id, len(chunks)))
                current_units = []
                current_size = 0

            current_units.append(unit)
            current_size += unit_size

        # Save remaining units
        if current_units:
            chunks.append(self._create_rust_chunk(current_units, document_id, len(chunks)))

        return chunks

    def _create_rust_chunk(
        self, units: List[CodeUnit], document_id: str, index: int
    ) -> DocumentChunk:
        """Create a chunk from Rust code units."""
        content = "\n\n".join(unit.content for unit in units)

        # Collect metadata
        has_docstrings = any(u.docstring for u in units)
        rust_types = [u.metadata.get("rust_type") for u in units if "rust_type" in u.metadata]
        parent_structure = " > ".join(u.name for u in units)

        return DocumentChunk(
            id=str(uuid.uuid4()),
            document_id=document_id,
            content=content,
            chunk_index=index,
            embedding=[],
            metadata={
                "chunk_type": "code",
                "language": "rust",
                "parent_structure": parent_structure,
                "start_line": units[0].start_line,
                "end_line": units[-1].end_line,
                "has_docstrings": has_docstrings,
                "rust_types": rust_types,
            },
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
            line_size = len(line) + 1  # +1 for newline

            if current_size + line_size > self.chunk_size and current_lines:
                # Save current chunk
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
                            "language": "rust",
                            "parent_structure": unit.name,
                            "is_partial": True,
                            "rust_type": unit.metadata.get("rust_type"),
                        },
                    )
                )

                # Start new chunk with overlap
                overlap_lines = max(1, self.chunk_overlap // 50)  # Approximate lines for overlap
                current_lines = current_lines[-overlap_lines:] + [line]
                current_size = sum(len(l) + 1 for l in current_lines)
            else:
                current_lines.append(line)
                current_size += line_size

        # Save remaining lines
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
                        "language": "rust",
                        "parent_structure": unit.name,
                        "is_partial": True,
                        "rust_type": unit.metadata.get("rust_type"),
                    },
                )
            )

        return chunks
