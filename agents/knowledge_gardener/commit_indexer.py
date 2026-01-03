"""
Commit Indexer Signature.

Single Responsibility: Index git commits as shared memory.
"""

import dspy


class CommitIndexerSignature(dspy.Signature):
    """Index git commits as searchable shared memory for the knowledge base.

    INPUTS:
    - recent_commits_json: JSON string containing recent git commits from GitService.
      Format:
      [
        {
          "sha": "abc123...",
          "author": "John Doe",
          "timestamp": "2024-01-03T10:30:00",
          "message": "Fix authentication bug",
          "files_changed": ["auth/login.py", "auth/session.py"],
          "stats": {"additions": 15, "deletions": 8}
        },
        ...
      ]

    OUTPUT:
    You must return two fields:
    - shared_commit_memory_json: JSON string containing indexed commits with enriched
      metadata for searchability. Format:
      [
        {
          "commit_sha": "abc123...",
          "author": "John Doe",
          "timestamp": "2024-01-03T10:30:00",
          "summary": "Brief, searchable summary of changes",
          "affected_files": ["auth/login.py", "auth/session.py"],
          "affected_entities": ["login_user", "SessionManager", "validate_token"],
          "tags": ["authentication", "bugfix", "security"],
          "impact_scope": "Module|System-wide",
          "searchable_text": "Combined text for full-text search"
        },
        ...
      ]
    - indexing_summary: Summary of indexing results
      (e.g., "Indexed 25 commits affecting 42 files and 38 entities. Top tags:
      authentication (8), performance (5), refactoring (4)")

    TASK INSTRUCTIONS:
    - Extract and preserve commit metadata (sha, author, timestamp, message)
    - Identify affected files from the commit data
    - Infer affected entities (functions, classes) from file paths and commit messages
    - Generate semantic tags based on commit message and changes
    - Assess impact scope (single file, module, or system-wide)
    - Create searchable summary combining message, files, and inferred intent
    - Build searchable_text field for full-text search (combine all relevant info)
    - Focus on making commits discoverable and contextually rich
    """

    recent_commits_json: str = dspy.InputField(desc="Git commits from GitService")

    shared_commit_memory_json: str = dspy.OutputField(desc="Indexed commits")
    indexing_summary: str = dspy.OutputField(desc="Commits indexed, files affected")
