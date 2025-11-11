"""YAML parser for structure-aware chunking."""

import uuid
from typing import Any, Dict, List

import yaml

from ..models.data_models import DocumentChunk
from .base import CodeUnit, CodeUnitType, LanguageParser, ParsingError

import logging

logger = logging.getLogger(__name__)


class YAMLParser(LanguageParser):
    """Parser for YAML files with structure-aware chunking."""

    @classmethod
    def get_supported_extensions(cls) -> List[str]:
        """Get supported file extensions."""
        return [".yaml", ".yml"]

    def parse(self, content: str, file_path: str) -> List[CodeUnit]:
        """Parse YAML into logical units."""
        try:
            data = yaml.safe_load(content)
            code_units = []

            if isinstance(data, dict):
                for key, value in data.items():
                    unit = self._create_yaml_unit(key, value)
                    if unit:
                        code_units.append(unit)
            elif isinstance(data, list):
                code_units = self._chunk_yaml_list(data, "list")
            else:
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

        except yaml.YAMLError as e:
            logger.warning(f"YAML parsing failed for {file_path}: {e}")
            raise ParsingError(f"Invalid YAML: {e}")

    def _create_yaml_unit(self, key: str, value: Any) -> CodeUnit:
        """Create a code unit for a YAML key-value pair."""
        unit_data = {key: value}
        unit_content = yaml.dump(unit_data, default_flow_style=False, sort_keys=False)

        if isinstance(value, dict):
            unit_type = CodeUnitType.CLASS
        elif isinstance(value, list):
            unit_type = CodeUnitType.MODULE
        else:
            unit_type = CodeUnitType.TEXT

        return CodeUnit(
            type=unit_type,
            name=key,
            content=unit_content,
            start_line=1,
            end_line=unit_content.count("\n") + 1,
            metadata={
                "yaml_type": type(value).__name__,
                "is_list": isinstance(value, list),
                "is_mapping": isinstance(value, dict),
            },
        )

    def _chunk_yaml_list(self, yaml_list: List[Any], name: str) -> List[CodeUnit]:
        """Chunk a top-level YAML list."""
        if len(yaml_list) <= 10:
            return [
                CodeUnit(
                    type=CodeUnitType.MODULE,
                    name=name,
                    content=yaml.dump(yaml_list, default_flow_style=False),
                    start_line=1,
                    end_line=yaml.dump(yaml_list, default_flow_style=False).count("\n") + 1,
                )
            ]

        code_units = []
        chunk_size = 20
        for i in range(0, len(yaml_list), chunk_size):
            chunk_items = yaml_list[i : i + chunk_size]
            unit_content = yaml.dump(chunk_items, default_flow_style=False)

            code_units.append(
                CodeUnit(
                    type=CodeUnitType.MODULE,
                    name=f"{name}_items_{i}_{i+len(chunk_items)}",
                    content=unit_content,
                    start_line=1,
                    end_line=unit_content.count("\n") + 1,
                    metadata={"is_list_chunk": True, "chunk_start": i, "chunk_end": i + len(chunk_items)},
                )
            )

        return code_units

    def chunk(self, code_units: List[CodeUnit], document_id: str) -> List[DocumentChunk]:
        """Convert YAML code units into chunks."""
        if not code_units:
            return []

        chunks = []
        current_units = []
        current_size = 0

        for unit in code_units:
            unit_size = len(unit.content)

            if unit_size > self.chunk_size * 1.5:
                if current_units:
                    chunks.append(self._create_yaml_chunk(current_units, document_id, len(chunks)))
                    current_units = []
                    current_size = 0
                chunks.extend(self._split_large_yaml_unit(unit, document_id, len(chunks)))
                continue

            if current_size + unit_size > self.chunk_size and current_units:
                chunks.append(self._create_yaml_chunk(current_units, document_id, len(chunks)))
                current_units = []
                current_size = 0

            current_units.append(unit)
            current_size += unit_size

        if current_units:
            chunks.append(self._create_yaml_chunk(current_units, document_id, len(chunks)))

        return chunks

    def _create_yaml_chunk(
        self, units: List[CodeUnit], document_id: str, index: int
    ) -> DocumentChunk:
        """Create a chunk from YAML units."""
        combined_data = {}
        for unit in units:
            try:
                unit_data = yaml.safe_load(unit.content)
                if isinstance(unit_data, dict):
                    combined_data.update(unit_data)
            except yaml.YAMLError:
                pass

        content = (
            yaml.dump(combined_data, default_flow_style=False, sort_keys=False)
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
                "chunk_type": "yaml",
                "language": "yaml",
                "keys": [u.name for u in units],
                "start_line": units[0].start_line,
                "end_line": units[-1].end_line,
            },
        )

    def _split_large_yaml_unit(
        self, unit: CodeUnit, document_id: str, start_index: int
    ) -> List[DocumentChunk]:
        """Split a large YAML unit."""
        try:
            data = yaml.safe_load(unit.content)
            chunks = []

            if isinstance(data, dict):
                items = list(data.items())
                chunk_data = {}

                for key, value in items:
                    chunk_data[key] = value
                    if len(yaml.dump(chunk_data)) > self.chunk_size:
                        chunks.append(
                            DocumentChunk(
                                id=str(uuid.uuid4()),
                                document_id=document_id,
                                content=yaml.dump(chunk_data, default_flow_style=False),
                                chunk_index=start_index + len(chunks),
                                embedding=[],
                                metadata={"chunk_type": "yaml_split", "language": "yaml", "is_partial": True},
                            )
                        )
                        chunk_data = {}

                if chunk_data:
                    chunks.append(
                        DocumentChunk(
                            id=str(uuid.uuid4()),
                            document_id=document_id,
                            content=yaml.dump(chunk_data, default_flow_style=False),
                            chunk_index=start_index + len(chunks),
                            embedding=[],
                            metadata={"chunk_type": "yaml_split", "language": "yaml", "is_partial": True},
                        )
                    )

            return chunks

        except yaml.YAMLError:
            return []
