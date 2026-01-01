"""
Agent memory wrapper using mem0 + Qdrant.

Provides per-agent persistent memory for:
- Conversation history
- Learned reasoning patterns
- Entity relationship cache (up to 3rd degree)
"""

from mem0 import Memory

from utils.io.logger import logger
from utils.memory.config import get_mem0_config


class AgentMemory:
    """
    Per-agent memory using mem0.

    Storage:
    - Conversation history (query → result)
    - Learned patterns (reasoning chains)
    - Entity relationship cache (3-hop limit, 7-day TTL)
    """

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        config = get_mem0_config(agent_name)

        try:
            self.memory = Memory.from_config(config)
            logger.debug(f"Initialized mem0 for agent: {agent_name}")
        except Exception as e:
            logger.error(f"Failed to init mem0 for {agent_name}: {e}")
            self.memory = None

    def add_interaction(self, query: str, result: dict, user_id: str = "system"):
        """Store agent interaction in memory."""
        if not self.memory:
            return

        try:
            messages = [
                {"role": "user", "content": query},
                {"role": "assistant", "content": str(result)},
            ]
            self.memory.add(messages, user_id=user_id)
            logger.debug(f"Stored interaction for {self.agent_name}")
        except Exception as e:
            logger.error(f"Failed to store interaction: {e}")

    def get_context(self, query: str, user_id: str = "system", limit: int = 5) -> str:
        """Retrieve relevant past interactions."""
        if not self.memory:
            return ""

        try:
            memories = self.memory.search(query, user_id=user_id, limit=limit)

            if not memories:
                return ""

            context_parts = ["## Past Agent Interactions\n"]
            for mem in memories:
                context_parts.append(f"- {mem['memory']}\n")

            return "\n".join(context_parts)
        except Exception as e:
            logger.error(f"Failed to retrieve context: {e}")
            return ""

    def update_entity_cache(self, entity_id: str, relationships: dict):
        """Cache entity relationships (up to 3rd degree)."""
        if not self.memory:
            return

        try:
            cache_entry = [
                {
                    "role": "system",
                    "content": f"Entity {entity_id} relationships: {relationships}",
                }
            ]
            self.memory.add(cache_entry, user_id="entity_cache")
        except Exception as e:
            logger.error(f"Failed to cache entity: {e}")
