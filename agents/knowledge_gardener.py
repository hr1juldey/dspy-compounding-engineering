import dspy


class KnowledgeGardener(dspy.Signature):
    """
    EXTENDED: Knowledge Gardener now maintains both KB learnings AND mem0 agent memories.

    Your role is to maintain the health and utility of the AI Knowledge Base and agent memories.
    You take collections of raw, potentially duplicate, or obsolete content and compress them
    into high-quality, consolidated insights.

    ## Gardening Protocol

    1. **Consolidate Duplicates**: Merge similar learnings into single, robust entries.
    2. **Remove Noise**: Discard one-off, trivial, or highly context-specific items that don't
       generalize.
    3. **Refine Clarity**: Rewrite entries to be concise, actionable, and clear.
    4. **Categorize**: Ensure every entry is correctly categorized.
    5. **Identify Patterns**: Look for underlying themes across multiple entries.

    ## Memory Gardening (NEW)

    6. **Deduplicate Agent Memories**: Remove redundant conversation entries
    7. **Compress Reasoning Chains**: Consolidate similar reasoning patterns
    8. **Prune Stale Entities**: Remove outdated entity relationship caches (>7 days)
    9. **Merge Common Patterns**: Extract patterns shared across agents

    ## Git Commit Memory (NEW)

    When commits are pushed:
    1. Extract commit message + diff summary
    2. Store as shared memory accessible to all agents
    3. Tag with affected files/entities

    ## Input
    - current_knowledge_json: KB learnings
    - agent_memories_json: Per-agent mem0 memories (NEW)
    - recent_commits_json: Pushed commits (NEW)

    ## Output
    - compressed_knowledge_json: Cleaned KB
    - compressed_memories_json: Cleaned agent memories (NEW)
    - shared_commit_memory_json: Common memory from commits (NEW)
    """

    current_knowledge_json = dspy.InputField(
        desc="The current state of the knowledge base (list of JSON objects)."
    )
    agent_memories_json = dspy.InputField(
        desc="Agent-specific memories to compress (per-agent conversation history).",
        default="{}",
    )
    recent_commits_json = dspy.InputField(
        desc="Recent git commits to index as shared memory.", default="[]"
    )

    compressed_knowledge_json = dspy.OutputField(
        desc="The refined, compressed list of knowledge items in JSON format."
    )
    compressed_memories_json = dspy.OutputField(
        desc="Compressed agent memories (deduplicated, patterns extracted)."
    )
    shared_commit_memory_json = dspy.OutputField(
        desc="Shared memory from git commits (accessible to all agents)."
    )
