"""JSON parser for structure-aware chunking."""

import json
import uuid
from typing import Any, Dict, List

from ..models.data_models import DocumentChunk
from .base import CodeUnit, CodeUnitType, LanguageParser, ParsingError

import logging

logger = logging.getLogger(__name__)


class JSONParser(LanguageParser):
    """Parser for JSON files with structure-aware chunking.

    Chunks JSON by top-level keys for objects or by groups for arrays.
    """

    @classmethod
    def get_supported_extensions(cls) -> List[str]:
        """Get supported file extensions."""
        return [".json", ".jsonc"]

    def parse(self, content: str, file_path: str) -> List[CodeUnit]:
        """Parse JSON into logical units."""
        try:
            data = json.loads(content)
            code_units = []

            if isinstance(data, dict):
                # Chunk by top-level keys
                for key, value in data.items():
                    unit = self._create_json_unit(key, value)
                    if unit:
                        code_units.append(unit)
            elif isinstance(data, list):
                # For top-level arrays, chunk by groups
                code_units = self._chunk_array(data, "array")
            else:
                # Simple value
                code_units = [
                    CodeUnit(
                        type=CodeUnitType.TEXT,
                        name="root",
                        content=content,
                        start_line=1,
                        end_line=content.count("\n") + 1,
                    )
                ]

            return code_units

        except json.JSONDecodeError as e:
            logger.warning(f"JSON parsing failed for {file_path}: {e}")
            raise ParsingError(f"Invalid JSON: {e}")

    def _create_json_unit(self, key: str, value: Any) -> CodeUnit:
        """Create a code unit for a JSON key-value pair."""
        unit_data = {key: value}
        unit_content = json.dumps(unit_data, indent=2)

        # Determine type based on value
        if isinstance(value, dict):
            unit_type = CodeUnitType.CLASS  # Object
        elif isinstance(value, list):
            unit_type = CodeUnitType.MODULE  # Array
        else:
            unit_type = CodeUnitType.TEXT  # Primitive

        return CodeUnit(
            type=unit_type,
            name=key,
            content=unit_content,
            start_line=1,
            end_line=unit_content.count("\n") + 1,
            metadata={
                "json_type": type(value).__name__,
                "is_array": isinstance(value, list),
                "is_object": isinstance(value, dict),
                "array_length": len(value) if isinstance(value, (list, dict)) else None,
            },
        )

    def _chunk_array(self, array: List[Any], name: str) -> List[CodeUnit]:
        """Chunk a top-level array intelligently."""
        code_units = []

        # If array is small, keep it together
        if len(array) <= 10:
            return [
                CodeUnit(
                    type=CodeUnitType.MODULE,
                    name=name,
                    content=json.dumps(array, indent=2),
                    start_line=1,
                    end_line=json.dumps(array, indent=2).count("\n") + 1,
                )
            ]

        # For large arrays, chunk by groups
        chunk_size = 50  # items per chunk
        for i in range(0, len(array), chunk_size):
            chunk_items = array[i : i + chunk_size]
            unit_content = json.dumps(chunk_items, indent=2)

            code_units.append(
                CodeUnit(
                    type=CodeUnitType.MODULE,
                    name=f"{name}_items_{i}_{i+len(chunk_items)}",
                    content=unit_content,
                    start_line=1,
                    end_line=unit_content.count("\n") + 1,
                    metadata={
                        "is_array_chunk": True,
                        "chunk_start": i,
                        "chunk_end": i + len(chunk_items),
                    },
                )
            )

        return code_units

    def chunk(self, code_units: List[CodeUnit], document_id: str) -> List[DocumentChunk]:
        """Convert JSON code units into chunks."""
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
                        self._create_json_chunk(current_units, document_id, len(chunks))
                    )
                    current_units = []
                    current_size = 0

                # Split large unit
                chunks.extend(self._split_large_json_unit(unit, document_id, len(chunks)))
                continue

            # If adding this would exceed size, finalize current chunk
            if current_size + unit_size > self.chunk_size and current_units:
                chunks.append(self._create_json_chunk(current_units, document_id, len(chunks)))
                current_units = []
                current_size = 0

            current_units.append(unit)
            current_size += unit_size

        # Finalize remaining
        if current_units:
            chunks.append(self._create_json_chunk(current_units, document_id, len(chunks)))

        return chunks

    def _create_json_chunk(
        self, units: List[CodeUnit], document_id: str, index: int
    ) -> DocumentChunk:
        """Create a chunk from JSON units."""
        # Combine units into a single JSON object
        combined_data = {}
        for unit in units:
            try:
                unit_data = json.loads(unit.content)
                if isinstance(unit_data, dict):
                    combined_data.update(unit_data)
            except json.JSONDecodeError:
                pass

        content = (
            json.dumps(combined_data, indent=2)
            if combined_data
            else "\n".join(u.content for u in units)
        )

        return DocumentChunk(
            id=str(uuid.uuid4()),
            document_id=document_id,
            content=content,
            chunk_index=index,
            embedding=[],
            metadata={
                "chunk_type": "json",
                "language": "json",
                "keys": [u.name for u in units],
                "start_line": units[0].start_line,
                "end_line": units[-1].end_line,
            },
        )

    def _split_large_json_unit(
        self, unit: CodeUnit, document_id: str, start_index: int
    ) -> List[DocumentChunk]:
        """Split a large JSON unit."""
        try:
            data = json.loads(unit.content)
            chunks = []

            if isinstance(data, dict):
                # Split object by keys
                items = list(data.items())
                chunk_data = {}

                for key, value in items:
                    chunk_data[key] = value

                    if len(json.dumps(chunk_data)) > self.chunk_size:
                        chunks.append(
                            DocumentChunk(
                                id=str(uuid.uuid4()),
                                document_id=document_id,
                                content=json.dumps(chunk_data, indent=2),
                                chunk_index=start_index + len(chunks),
                                embedding=[],
                                metadata={
                                    "chunk_type": "json_split",
                                    "language": "json",
                                    "parent_key": unit.name,
                                    "is_partial": True,
                                },
                            )
                        )
                        chunk_data = {}

                if chunk_data:
                    chunks.append(
                        DocumentChunk(
                            id=str(uuid.uuid4()),
                            document_id=document_id,
                            content=json.dumps(chunk_data, indent=2),
                            chunk_index=start_index + len(chunks),
                            embedding=[],
                            metadata={
                                "chunk_type": "json_split",
                                "language": "json",
                                "parent_key": unit.name,
                                "is_partial": True,
                            },
                        )
                    )

            elif isinstance(data, list):
                # Split array into smaller arrays
                chunk_size = 20
                for i in range(0, len(data), chunk_size):
                    chunk_items = data[i : i + chunk_size]
                    chunks.append(
                        DocumentChunk(
                            id=str(uuid.uuid4()),
                            document_id=document_id,
                            content=json.dumps(chunk_items, indent=2),
                            chunk_index=start_index + len(chunks),
                            embedding=[],
                            metadata={
                                "chunk_type": "json_array_split",
                                "language": "json",
                                "parent_key": unit.name,
                                "array_range": f"{i}-{i+len(chunk_items)}",
                                "is_partial": True,
                            },
                        )
                    )

            return chunks

        except json.JSONDecodeError:
            # Fall back to line-based splitting
            return self._split_by_lines(unit, document_id, start_index)

    def _split_by_lines(
        self, unit: CodeUnit, document_id: str, start_index: int
    ) -> List[DocumentChunk]:
        """Fall back to line-based splitting."""
        lines = unit.content.split("\n")
        chunks = []
        current_lines = []
        current_size = 0

        for line in lines:
            if current_size + len(line) > self.chunk_size and current_lines:
                chunks.append(
                    DocumentChunk(
                        id=str(uuid.uuid4()),
                        document_id=document_id,
                        content="\n".join(current_lines),
                        chunk_index=start_index + len(chunks),
                        embedding=[],
                        metadata={
                            "chunk_type": "json_split",
                            "language": "json",
                            "is_partial": True,
                        },
                    )
                )
                current_lines = [line]
                current_size = len(line)
            else:
                current_lines.append(line)
                current_size += len(line)

        if current_lines:
            chunks.append(
                DocumentChunk(
                    id=str(uuid.uuid4()),
                    document_id=document_id,
                    content="\n".join(current_lines),
                    chunk_index=start_index + len(chunks),
                    embedding=[],
                    metadata={
                        "chunk_type": "json_split",
                        "language": "json",
                        "is_partial": True,
                    },
                )
            )

        return chunks
