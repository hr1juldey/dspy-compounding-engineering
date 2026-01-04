"""
FastMCP prompts for structured LLM interactions.

Prompts are reusable message templates that help LLMs generate structured responses.
"""

from fastmcp import FastMCP

# Prompts don't need background tasks - use separate server
prompts_server = FastMCP("Prompts")


@prompts_server.prompt(name="feature_development", tags={"development"})
def feature_development_prompt(
    feature_description: str,
    constraints: str = "",
    target_files: str = "",
) -> str:
    """Generate a structured prompt for implementing a new feature."""
    return f"""Implement this feature: {feature_description}

Constraints: {constraints or "None specified"}
Target files: {target_files or "Auto-detect from codebase"}

Requirements:
- Follow SOLID principles
- Adhere to project conventions in CLAUDE.md
- Write clean, maintainable code
- Include appropriate error handling
- Add tests if applicable"""


@prompts_server.prompt(name="debugging_request", tags={"debugging"})
def debugging_request_prompt(
    error_message: str,
    stack_trace: str = "",
    context: str = "",
) -> str:
    """Generate a structured prompt for debugging an issue."""
    return f"""Debug this issue: {error_message}

Stack trace:
{stack_trace or "Not provided"}

Context: {context or "None"}

Please:
1. Identify the root cause
2. Explain why the error occurs
3. Suggest specific fixes with code examples
4. Recommend prevention strategies"""


@prompts_server.prompt(name="code_review", tags={"review"})
def code_review_prompt(
    code_changes: str,
    review_focus: str = "general",
) -> str:
    """Generate a structured prompt for code review."""
    return f"""Review the following code changes with focus on: {review_focus}

Code changes:
{code_changes}

Please evaluate:
1. Code correctness and logic
2. SOLID principles adherence
3. Security vulnerabilities
4. Performance implications
5. Maintainability and readability
6. Test coverage needs"""


@prompts_server.prompt(name="architecture_analysis", tags={"architecture"})
def architecture_analysis_prompt(
    component_description: str,
    analysis_type: str = "design",
) -> str:
    """Generate a structured prompt for architectural analysis."""
    return f"""Analyze the architecture for: {component_description}

Analysis type: {analysis_type}

Please provide:
1. Component responsibilities and boundaries
2. Dependencies and coupling analysis
3. Scalability considerations
4. Potential improvements
5. Trade-offs of current design"""


__all__ = [
    "prompts_server",
    "feature_development_prompt",
    "debugging_request_prompt",
    "code_review_prompt",
    "architecture_analysis_prompt",
]
