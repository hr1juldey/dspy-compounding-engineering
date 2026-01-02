"""
Todo creator module.

Single Responsibility: Create new todo files from findings.
"""

import os
from datetime import datetime
from typing import Optional

from utils.todo.file_utils import (
    get_next_issue_id,
    get_todos_dir,
    sanitize_description,
)


def create_finding_todo(
    finding: dict,
    todos_dir: Optional[str] = None,
    issue_id: Optional[int] = None,
) -> str:
    """
    Create pending todo file from review finding.

    Args:
        finding: Dict with keys: agent, review, severity (p1/p2/p3),
                 category, location, description, solution, effort
        todos_dir: Directory to store todos
        issue_id: Optional specific issue ID

    Returns:
        Path to created todo file
    """
    todos_dir = get_todos_dir(todos_dir)
    os.makedirs(todos_dir, exist_ok=True)

    if issue_id is None:
        issue_id = get_next_issue_id(todos_dir)

    # Extract finding details with defaults
    agent = finding.get("agent", "Unknown Agent")
    review_text = finding.get("review", "No details provided")
    severity = finding.get("severity", "p2")
    category = finding.get("category", "code-review")
    title = finding.get("title", f"Finding from {agent}")

    # Create filename
    desc_slug = sanitize_description(title)
    filename = f"{issue_id:03d}-pending-{severity}-{desc_slug}.md"
    filepath = os.path.join(todos_dir, filename)

    # Build tags list
    tags = ["code-review", category.lower().replace(" ", "-")]
    if severity == "p1":
        tags.append("critical")

    today = datetime.now().strftime("%Y-%m-%d")

    content = f"""---
status: pending
priority: {severity}
issue_id: "{issue_id:03d}"
tags: [{", ".join(tags)}]
dependencies: []
---

# {title}

## Problem Statement

Finding from **{agent}** during code review.

{review_text}

## Findings

- **Source:** {agent}
- **Category:** {category}
- **Severity:** {severity.upper()}

## Proposed Solutions

### Option 1: Address Finding

**Approach:** Review and implement the suggested fix from the code review.

**Pros:**
- Addresses the identified issue
- Improves code quality

**Cons:**
- Requires investigation time

**Effort:** {finding.get("effort", "Medium")}

**Risk:** Low

## Recommended Action

*To be filled during triage.*

## Acceptance Criteria

- [ ] Issue addressed
- [ ] Tests pass
- [ ] Code reviewed

## Work Log

### {today} - Created from Code Review

**By:** Review Agent ({agent})

**Actions:**
- Finding identified during automated code review
- Todo created for triage

**Learnings:**
- Pending triage decision

## Notes

Source: Automated code review
"""

    with open(filepath, "w") as f:
        f.write(content)

    return filepath
