"""
Todo updater module.

Single Responsibility: Update and complete existing todos.
"""

import os
from datetime import datetime

from utils.todo.parser import parse_todo, serialize_todo


def add_work_log_entry(content: str, action: str) -> str:
    """
    Add work log entry to todo content.

    Args:
        content: Existing markdown content
        action: Description of action taken

    Returns:
        Updated content with new work log entry
    """
    today = datetime.now().strftime("%Y-%m-%d")
    log_entry = f"""
### {today} - {action}

**By:** AI Agent

**Actions:**
- {action}
"""
    # Find Work Log section
    if "## Work Log" in content:
        parts = content.split("## Work Log")
        return f"{parts[0]}## Work Log\n{log_entry}{parts[1]}"
    else:
        return f"{content}\n\n## Work Log\n{log_entry}"


def complete_todo(
    file_path: str,
    resolution_summary: str,
    action_msg: str = "Task Completed",
    new_status: str = "completed",
    rename_to_complete: bool = True,
) -> str:
    """
    Mark todo as complete, update content, optionally rename.

    Args:
        file_path: Path to todo file
        resolution_summary: Summary of what was done
        action_msg: Short action message for log
        new_status: New status string
        rename_to_complete: Rename file to *-complete-*

    Returns:
        Path to (possibly new) todo file
    """
    if not os.path.exists(file_path):
        return file_path

    parsed = parse_todo(file_path)
    fm = parsed["frontmatter"]
    body = parsed["body"]

    # Update status
    fm["status"] = new_status

    # Update checkboxes
    body = body.replace("- [ ] Issue addressed", "- [x] Issue addressed")
    body = body.replace("- [ ] Tests pass", "- [x] Tests pass")
    body = body.replace("- [ ] Code reviewed", "- [x] Code reviewed")

    # Add Resolution Summary
    if "## Resolution" not in body and "## Resolution Summary" not in body:
        body += f"\n\n## Resolution\n\n{resolution_summary}\n"

    # Add Work Log
    body = add_work_log_entry(body, action_msg)

    new_content = serialize_todo(fm, body)

    # Determine new path
    new_path = file_path
    if rename_to_complete:
        dir_name = os.path.dirname(file_path)
        base_name = os.path.basename(file_path)
        new_base = base_name.replace("-ready-", "-complete-").replace("-pending-", "-complete-")
        if new_base != base_name:
            new_path = os.path.join(dir_name, new_base)

    # Write new file
    with open(new_path, "w") as f:
        f.write(new_content)

    # Remove old file if renamed
    if new_path != file_path:
        os.remove(file_path)

    return new_path
