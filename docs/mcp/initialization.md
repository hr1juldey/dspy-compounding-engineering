# MCP Server Initialization Guide

## Quick Start

When using the Compounding Engineering MCP server on a repository, you must initialize it first:

```python
# Step 1: Initialize (one-time setup)
initialize_repo(repo_root="/path/to/your/repo")

# Step 2: Use any other tools
analyze_code(repo_root="/path/to/your/repo", entity="MyClass")
generate_plan(repo_root="/path/to/your/repo", feature_description="Add auth")
```

## Why Initialization is Required

The CE system needs to:
1. Create directory structure (`.ce/` or `.claude/`)
2. Set up path management singleton
3. Initialize vector database collections (per-repo isolation)
4. Detect repository environment (Python/Node/Rust/etc.)

## Multi-Repository Pattern

When working with multiple repositories, each gets isolated collections:

```python
# Repo A
initialize_repo(repo_root="/path/to/repo-a")
index_codebase(repo_root="/path/to/repo-a")

# Repo B (separate collections, no data collision)
initialize_repo(repo_root="/path/to/repo-b")
index_codebase(repo_root="/path/to/repo-b")
```

## Correct Initialization Pattern (For Advanced Users)

When using CE's knowledge base directly in code:

```python
from utils.paths import get_paths
from utils.knowledge.core import KnowledgeBase

# CORRECT: Set target repository path first
get_paths(target_repo_path)
kb = KnowledgeBase()

# INCORRECT: This uses CE repo path, not target repo
# kb = KnowledgeBase()  # Wrong - will use wrong hash!
```

## Where MCP Server Saves Results

All output files are saved within the compounding directory:

| File Type | Location | Example |
|-----------|----------|---------|
| Plans | `{repo_root}/{base_dir}/plans/` | `/path/to/repo/.ce/plans/feature-auth.md` |
| Todos | `{repo_root}/{base_dir}/todos/` | `/path/to/repo/.ce/todos/123-fix-bug.md` |
| Analysis | `{repo_root}/{base_dir}/analysis/` | `/path/to/repo/.ce/analysis/class-deps.json` |
| Cache | `{repo_root}/{base_dir}/cache/` | `/path/to/repo/.ce/cache/embeddings.pkl` |
| Memory | `{repo_root}/{base_dir}/memory/` | `/path/to/repo/.ce/memory/session.json` |
| Knowledge | `{repo_root}/{base_dir}/knowledge/` | `/path/to/repo/.ce/knowledge/AI.md` |

### Configuration

The base directory name (`{base_dir}`) is determined by:
1. `initialize_repo(dir_name=".claude")` parameter
2. `COMPOUNDING_DIR_NAME=.claude` in target repo's `.env` file
3. Default: `.ce`

### Legacy Directories

**Note**: Older versions saved files to `{cwd}/plans/` instead of `{repo_root}/.ce/plans/`. If you can't find results, check for legacy directories:
- `plans/`
- `todos/`
- `analysis/`

These should be migrated to the compounding directory.

## Tools Requiring Initialization

All tools that accept `repo_root` parameter require initialization:
- `analyze_code`
- `generate_plan`
- `index_codebase`
- `garden_knowledge`
- `codify_feedback`
- `compress_knowledge_base`
- `execute_work`
- `review_code`
- `triage_issues`
- `generate_command`

## Checking Initialization Status

Use `get_repo_status` to check if a repo is initialized:

```python
status = get_repo_status(repo_root="/path/to/repo")
print(status["initialized"])  # True/False
```
