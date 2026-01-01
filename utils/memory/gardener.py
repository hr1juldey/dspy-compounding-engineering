"""
Memory gardener for maintaining mem0 memories.

Scheduled tasks for:
1. Compressing agent memories
2. Indexing git commits as shared memory
3. Pruning stale entity caches
"""

from utils.git.service import GitService
from utils.io.logger import logger
from utils.memory.agent_memory import AgentMemory


class MemoryGardener:
    """
    Maintains mem0 memories across all agents.

    Tasks:
    - Compress agent memories (deduplicate)
    - Index git commits as shared memory
    - Prune stale entity caches (>7 days old)
    """

    def __init__(self):
        self.git_service = GitService()

    def compress_agent_memories(self, agent_name: str):
        """
        Compress agent memory.

        Uses KnowledgeGardener signature to compress and deduplicate.
        TODO: Implement compression logic with KnowledgeGardener.
        """
        logger.info(f"Compressing memories for agent: {agent_name}")
        # TODO: Implement with AgentMemory(agent_name) and KnowledgeGardener

    def index_git_commits(self, branch: str = "HEAD", remote: str = "origin", limit: int = 100):
        """Index recent git commits as shared memory."""
        logger.info("Indexing git commits as shared memory")

        try:
            commits = self.git_service.get_pushed_commits(branch=branch, remote=remote, limit=limit)

            if not commits:
                logger.debug("No pushed commits to index")
                return

            shared_memory = AgentMemory("shared_git_commits")

            for commit in commits:
                # Get commit details
                metadata = self.git_service.get_commit_metadata(commit)
                changed_files = self.git_service.get_changed_files_in_commit(commit)

                summary = f"Commit {commit[:8]}: {metadata.get('message', '')}"
                result_data = {
                    "sha": commit,
                    "author": metadata.get("author"),
                    "date": metadata.get("date"),
                    "files": changed_files,
                }

                shared_memory.add_interaction(
                    query=summary, result=result_data, user_id="git_history"
                )

            logger.success(f"Indexed {len(commits)} commits")
        except Exception as e:
            logger.error(f"Failed to index commits: {e}")

    def prune_stale_caches(self, max_age_days: int = 7):
        """
        Prune stale entity caches.

        TODO: Implement TTL-based pruning.
        """
        logger.info(f"Pruning entity caches older than {max_age_days} days")
        # TODO: Implement cache pruning with TTL
