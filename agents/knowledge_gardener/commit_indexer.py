"""
Commit Indexer Signature.

Single Responsibility: Index git commits as shared memory.
"""

import dspy


class CommitIndexerSignature(dspy.Signature):
    """
    Index git commits as shared memory.

    Tasks:
    - Extract commit metadata
    - Tag with affected files/entities
    - Create searchable summaries
    """

    recent_commits_json: str = dspy.InputField(desc="Git commits from GitService")

    shared_commit_memory_json: str = dspy.OutputField(desc="Indexed commits")
    indexing_summary: str = dspy.OutputField(desc="Commits indexed, files affected")
