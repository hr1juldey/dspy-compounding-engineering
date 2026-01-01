"""
JSON structure extractor for semantic chunking.

Extracts top-level keys and nested structures from JSON files.
"""

import json
from dataclasses import dataclass
from typing import Any


@dataclass
class JSONStructure:
    """JSON document structure"""

    top_level_keys: list[str]
    is_array: bool
    total_items: int
    estimated_size: int
    file_path: str


class JSONExtractor:
    """Extracts structure from JSON files"""

    def extract(self, content: str, filepath: str = "") -> JSONStructure:
        """Parse JSON and extract structure"""
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return JSONStructure([], False, 0, len(content), filepath)

        is_array = isinstance(data, list)
        top_level_keys = [] if is_array else list(data.keys()) if isinstance(data, dict) else []
        total_items = len(data) if is_array else len(top_level_keys)

        return JSONStructure(
            top_level_keys=top_level_keys,
            is_array=is_array,
            total_items=total_items,
            estimated_size=len(content),
            file_path=filepath,
        )

    def chunk_by_keys(
        self, content: str, structure: JSONStructure, target_size: int = 2000
    ) -> list[str]:
        """
        Chunk JSON by top-level keys or array items.

        Strategy:
        - For objects: Group by top-level keys
        - For arrays: Split into sub-arrays
        - Keep objects/arrays intact (don't split mid-structure)
        - Maintain valid JSON in each chunk
        """
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return [content]

        chunks = []

        if structure.is_array:
            # Split array into chunks
            chunks = self._chunk_array(data, target_size)
        elif structure.top_level_keys:
            # Group by top-level keys
            chunks = self._chunk_object(data, structure.top_level_keys, target_size)
        else:
            # Simple value or unknown structure
            return [content]

        # Convert back to JSON strings
        return [json.dumps(chunk, indent=2) for chunk in chunks]

    def _chunk_array(self, data: list, target_size: int) -> list[Any]:
        """Split array into smaller arrays"""
        chunks = []
        current_chunk = []
        current_size = 0

        for item in data:
            item_str = json.dumps(item, indent=2)
            item_size = len(item_str)

            if current_size + item_size <= target_size:
                current_chunk.append(item)
                current_size += item_size
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = [item]
                current_size = item_size

        if current_chunk:
            chunks.append(current_chunk)

        return chunks if chunks else [data]

    def _chunk_object(self, data: dict, keys: list[str], target_size: int) -> list[dict]:
        """Group object by top-level keys"""
        chunks = []
        current_chunk = {}
        current_size = 0

        for key in keys:
            if key not in data:
                continue

            value_str = json.dumps({key: data[key]}, indent=2)
            value_size = len(value_str)

            if current_size + value_size <= target_size:
                current_chunk[key] = data[key]
                current_size += value_size
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = {key: data[key]}
                current_size = value_size

        if current_chunk:
            chunks.append(current_chunk)

        return chunks if chunks else [data]
