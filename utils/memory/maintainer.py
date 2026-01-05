"""
Agent Memory Maintainer.

Scheduled maintenance for mem0 agent memories:
1. Compress agent memories
2. Index git commits as shared memory
3. Prune stale entity caches (>7 days)
"""

import json
import time
from typing import cast

import dspy

from agents.knowledge_gardener.memory_compressor import MemoryCompressorSignature
from utils.git.service import GitService
from utils.io.logger import logger
from utils.memory.agent_memory import AgentMemory
from utils.paths import get_paths


class AgentMemoryMaintainer:
    """
    Maintains mem0 memories across all agents.

    Tasks:
    - Compress agent memories (deduplicate)
    - Index git commits as shared memory
    - Prune stale entity caches (>7 days old)
    """

    def __init__(self):
        self.git_service = GitService()
        self.memory_compressor = dspy.ChainOfThought(MemoryCompressorSignature)

    def compress_agent_memories(self, agent_name: str):
        """
        Compress agent memory using DSPy MemoryCompressor.

        Deduplicates and merges similar memories.

        Args:
            agent_name: Name of agent whose memories to compress

        Returns:
            Compression statistics
        """
        logger.info(f"Compressing memories for agent: {agent_name}")

        try:
            # Get agent memories
            agent_memory = AgentMemory(agent_name)
            memories = agent_memory.get_all(user_id=agent_name)  # type: ignore[attr-defined]

            if not memories:
                logger.debug(f"No memories found for {agent_name}")
                return {"removed": 0, "merged": 0, "kept": 0}

            # Convert memories to JSON for LLM processing
            memories_json = json.dumps(memories, indent=2)

            # Use DSPy to compress
            prediction = cast(
                dspy.Prediction, self.memory_compressor(agent_memories_json=memories_json)
            )

            # Parse compressed memories
            compressed_memories = json.loads(prediction.compressed_memories_json)
            stats = prediction.compression_stats

            # Clear old memories and add compressed ones
            agent_memory.delete_all(user_id=agent_name)  # type: ignore[attr-defined]

            for memory in compressed_memories:
                agent_memory.add_interaction(
                    query=memory.get("query", ""),
                    result=memory.get("result", {}),
                    user_id=agent_name,
                )

            logger.success(
                f"Compressed {agent_name} memories: "
                f"removed={stats['removed']}, merged={stats['merged']}, kept={stats['kept']}"
            )

            return stats

        except Exception as e:
            logger.error(f"Failed to compress memories for {agent_name}: {e}")
            return {"error": str(e)}

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
        Prune stale cache files using TTL.

        Removes cache files older than max_age_days based on modification time.

        Args:
            max_age_days: Maximum age in days for cache files

        Returns:
            Number of files pruned
        """
        logger.info(f"Pruning cache files older than {max_age_days} days")

        try:
            paths = get_paths()
            cache_dir = paths.cache_dir

            if not cache_dir.exists():
                logger.debug("Cache directory doesn't exist, nothing to prune")
                return 0

            # Calculate age threshold
            max_age_sec = max_age_days * 24 * 60 * 60
            now = time.time()

            pruned_count = 0
            pruned_size = 0

            # Iterate through cache files
            for cache_file in cache_dir.rglob("*"):
                if not cache_file.is_file():
                    continue

                try:
                    # Check file age based on modification time
                    file_age_sec = now - cache_file.stat().st_mtime

                    if file_age_sec > max_age_sec:
                        file_size = cache_file.stat().st_size
                        cache_file.unlink()

                        pruned_count += 1
                        pruned_size += file_size

                        logger.debug(f"Pruned stale cache file: {cache_file.name}")

                except Exception as e:
                    logger.warning(f"Failed to prune {cache_file}: {e}")
                    continue

            if pruned_count > 0:
                size_mb = pruned_size / (1024 * 1024)
                logger.success(f"Pruned {pruned_count} cache files ({size_mb:.2f} MB freed)")
            else:
                logger.debug("No stale cache files to prune")

            return pruned_count

        except Exception as e:
            logger.error(f"Failed to prune caches: {e}")
            return 0
