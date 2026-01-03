"""
Indexed file metadata tracking.

Tracks which files have been indexed, their mtimes, and chunk counts
to enable incremental indexing without re-processing unchanged files.
"""

import os
from typing import Dict, Set


class IndexerMetadata:
    """
    Manages metadata for indexed files.

    Single Responsibility: Track what's been indexed and enable
    incremental indexing by comparing file mtimes.
    """

    def __init__(self, client, collection_name: str):
        """
        Initialize metadata manager.

        Args:
            client: Qdrant client
            collection_name: Collection to track metadata in
        """
        self.client = client
        self.collection_name = collection_name

    def get_indexed_files_metadata(self) -> Dict[str, float]:
        """
        Get metadata for all indexed files (path -> mtime mapping).

        Returns:
            Dictionary: {filepath: last_modified_timestamp}
        """
        indexed_files = {}
        offset = None

        try:
            while True:
                # Scroll through collection to get all indexed files
                scroll_result = self.client.scroll(
                    collection_name=self.collection_name,
                    limit=10000,
                    with_payload=True,
                    with_vectors=False,
                    offset=offset,
                )

                points, offset = scroll_result

                for point in points:
                    if point.payload and "path" in point.payload:
                        filepath = point.payload["path"]
                        mtime = point.payload.get("last_modified", 0.0)
                        # Keep most recent mtime for each file
                        if filepath not in indexed_files or mtime > indexed_files[filepath]:
                            indexed_files[filepath] = mtime

                if offset is None:
                    break

        except Exception:
            # Collection may not exist yet - return empty
            return {}

        return indexed_files

    def needs_update(
        self,
        filepath: str,
        current_mtime: float,
        indexed_files: Dict[str, float],
    ) -> bool:
        """
        Check if file needs re-indexing (mtime changed).

        Args:
            filepath: Path to check
            current_mtime: Current file modification time
            indexed_files: Indexed files metadata dict

        Returns:
            True if file should be re-indexed, False if unchanged
        """
        if filepath not in indexed_files:
            return True  # New file

        return current_mtime > indexed_files[filepath]

    def filter_files(
        self,
        files: list[str],
        ignore_exts: Set[str],
        ignore_dirs: Set[str],
        root_dir: str,
    ) -> list[tuple[str, float]]:
        """
        Filter files by extensions and directories, get mtimes.

        Args:
            files: List of file paths from git ls-files
            ignore_exts: File extensions to skip
            ignore_dirs: Directories to skip
            root_dir: Root directory for full paths

        Returns:
            List of (filepath, mtime) for valid files
        """
        valid_files = []

        for filepath in files:
            # Skip ignored extensions
            _, ext = os.path.splitext(filepath)
            if ext.lower() in ignore_exts:
                continue

            # Skip ignored directories
            if any(filepath.startswith(d) for d in ignore_dirs):
                continue

            full_path = os.path.join(root_dir, filepath)
            if not os.path.exists(full_path):
                continue

            # Get file mtime
            mtime = os.path.getmtime(full_path)
            valid_files.append((filepath, mtime))

        return valid_files
