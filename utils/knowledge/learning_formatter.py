"""
Learning formatting for LLM context injection.

Transforms structured learning data into human/LLM-readable text.
Pure functions with no external dependencies.
"""

from typing import Any, Dict, List


class LearningFormatter:
    """
    Formats learnings for context injection into LLM prompts.

    Single Responsibility: Transform structured learning data into
    human/LLM-readable markdown text.
    """

    @staticmethod
    def format_context_string(learnings: List[Dict[str, Any]]) -> str:
        """
        Format learnings as context for embedding in prompts.

        Args:
            learnings: List of learning dictionaries

        Returns:
            Formatted markdown string for context injection
        """
        if not learnings:
            return "No relevant past learnings found."

        context = "## Relevant Past Learnings\n\n"
        for learning in learnings:
            context += f"### {learning.get('title', 'Untitled')}\n"
            context += f"- **Category**: {learning.get('category', 'General')}\n"
            context += f"- **Source**: {learning.get('source', 'Unknown')}\n"
            context += f"- **Date**: {learning.get('created_at', 'Unknown')}\n"

            content = learning.get("content", "")
            if isinstance(content, dict):
                context += f"\n{content.get('summary', '')}\n\n"
            else:
                context += f"\n{content}\n\n"

            # Add codified improvements if available
            if learning.get("codified_improvements"):
                context += "- **Improvements**:\n"
                for imp in learning["codified_improvements"]:
                    context += (
                        f"  - [{imp.get('type', 'item')}] {imp.get('title', '')}: "
                        f"{imp.get('description', '')}\n"
                    )
            context += "\n"

        return context

    @staticmethod
    def format_compounding_prompt(learnings: List[Dict[str, Any]], limit: int = 20) -> str:
        """
        Format learnings as system prompt for auto-injection.

        Equivalent to CLAUDE.md - ensures every LLM call benefits from
        past learnings.

        Args:
            learnings: List of all learning dictionaries
            limit: Max recent learnings to include (default: 20)

        Returns:
            Formatted prompt string ready for prepend/append
        """
        if not learnings:
            return ""

        # Sort by most recent
        sorted_learnings = sorted(learnings, key=lambda x: x.get("created_at", ""), reverse=True)[
            :limit
        ]

        prompt = "\n\n---\n\n## System Learnings (Auto-Injected)\n\n"
        prompt += (
            "The following patterns and learnings have been codified from past work. "
            "Apply these automatically to the current task:\n\n"
        )

        for learning in sorted_learnings:
            prompt += f"### {learning.get('title', 'Untitled')}\n"
            prompt += f"**Source:** {learning.get('source', 'unknown')}\n"

            # Add codified improvements
            if learning.get("codified_improvements"):
                for imp in learning["codified_improvements"]:
                    prompt += f"- {imp.get('description', '')}\n"

            prompt += "\n"

        return prompt
