"""
Temporal Extractor (Dimension 5).

Extracts git history evolution of code entities.
"""

from agents.graphrag.schema import CodeChange, GitHistory
from utils.git.service import GitService


class TemporalExtractor:
    """Extracts git history for code entities."""

    def __init__(self):
        self.git_service = GitService()

    def extract_history(self, entity_name: str, file_path: str) -> GitHistory | None:
        """
        Extract git history for an entity.

        Returns:
            GitHistory or None if no history available
        """
        try:
            # Get file history from git
            commits = self.git_service.get_file_history(file_path, max_count=10)

            if not commits:
                return None

            # Parse commits into CodeChange objects
            changes = []
            for commit in commits:
                commit_sha = commit.get("sha", "")
                metadata = self.git_service.get_commit_metadata(commit_sha)
                author = metadata.get("author") or commit.get("author") or "unknown"
                date = metadata.get("date") or commit.get("date") or "unknown"
                message = metadata.get("message") or commit.get("message") or ""
                changes.append(
                    CodeChange(
                        commit_sha=commit_sha,
                        author=str(author),
                        date=str(date),
                        message=str(message),
                        change_type="modified",
                        lines_added=0,
                        lines_removed=0,
                    )
                )

            if not changes:
                return None

            # Analyze change frequency
            total_commits = len(changes)
            if total_commits >= 5:
                frequency = "high"
            elif total_commits >= 2:
                frequency = "medium"
            else:
                frequency = "low"

            # Analyze stability
            if total_commits <= 2:
                stability = "stable"
            elif total_commits <= 5:
                stability = "evolving"
            else:
                stability = "volatile"

            return GitHistory(
                entity_name=entity_name,
                file_path=file_path,
                first_seen=changes[-1],
                last_modified=changes[0],
                total_commits=total_commits,
                recent_changes=changes[:5],
                change_frequency=frequency,
                stability=stability,
            )

        except Exception:
            return None
