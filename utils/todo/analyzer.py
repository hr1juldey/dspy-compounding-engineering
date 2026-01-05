"""
Todo dependency analyzer.

Single Responsibility: Analyze dependencies between todos.
"""

from typing import List


def analyze_dependencies(todos: List[dict]) -> dict:  # noqa: C901
    """
    Analyze dependencies between todos and create execution plan.

    Args:
        todos: List of todo dicts with 'id' and 'frontmatter'

    Returns:
        Dict with execution_order (batches) and mermaid_diagram
    """
    if not todos:
        return {"execution_order": [], "mermaid_diagram": ""}

    # Build dependency graph (Prerequisite -> Dependent)
    forward_graph = {t["id"]: set() for t in todos}
    id_to_todo = {t["id"]: t for t in todos}
    in_degree = {t["id"]: 0 for t in todos}

    for todo in todos:
        deps = todo["frontmatter"].get("dependencies", [])
        for dep in deps:
            dep_id = str(dep)
            if dep_id in id_to_todo:
                forward_graph[dep_id].add(todo["id"])
                in_degree[todo["id"]] += 1

    # Topological sort with batching
    queue = [t["id"] for t in todos if in_degree[t["id"]] == 0]
    batches = []
    processed_count = 0

    while queue:
        current_batch = sorted(queue)
        batches.append(
            {
                "batch": len(batches) + 1,
                "todos": current_batch,
                "can_parallel": True,
            }
        )
        processed_count += len(current_batch)

        next_queue = []
        for t_id in current_batch:
            for dependent in forward_graph[t_id]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    next_queue.append(dependent)
        queue = next_queue

    # Handle cycles or missing dependencies
    if processed_count < len(todos):
        remaining = [t["id"] for t in todos if in_degree[t["id"]] > 0]
        batches.append(
            {
                "batch": len(batches) + 1,
                "todos": remaining,
                "can_parallel": False,
                "warning": "Cycle detected or missing dependencies",
            }
        )

    # Generate Mermaid diagram
    mermaid = ["flowchart TD"]
    for t_id in forward_graph:
        mermaid.append(f"  T{t_id}[Todo {t_id}]")
        for dep in forward_graph[t_id]:
            mermaid.append(f"  T{t_id} --> T{dep}")

    return {
        "execution_order": batches,
        "mermaid_diagram": "\n".join(mermaid),
    }
