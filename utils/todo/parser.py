"""
Todo file parser.

Single Responsibility: Parse and serialize todo markdown files.
"""

from typing import Callable

import frontmatter
from filelock import FileLock


def parse_todo(file_path: str) -> dict:
    """
    Parse a todo file into frontmatter and body.

    Returns:
        Dict with 'frontmatter' and 'body' keys
    """
    with open(file_path, encoding="utf-8") as f:
        post = frontmatter.load(f)
        return {"frontmatter": post.metadata, "body": post.content}


def serialize_todo(frontmatter_dict: dict, body: str) -> str:
    """
    Serialize frontmatter and body into markdown format.

    Args:
        frontmatter_dict: Frontmatter metadata
        body: Todo body content

    Returns:
        Complete markdown content with frontmatter
    """
    post = frontmatter.Post(body, **frontmatter_dict)
    return frontmatter.dumps(post)


def atomic_update_todo(file_path: str, update_fn: Callable[[dict, str], tuple[dict, str]]) -> bool:
    """
    Atomically update a todo file using file locking.

    Args:
        file_path: Path to todo file
        update_fn: Function(frontmatter, body) -> (new_frontmatter, new_body)

    Returns:
        True if update successful
    """
    lock_path = f"{file_path}.lock"

    try:
        with FileLock(lock_path, timeout=10):
            parsed = parse_todo(file_path)
            fm = parsed["frontmatter"]
            body = parsed["body"]

            new_fm, new_body = update_fn(fm, body)

            content = serialize_todo(new_fm, new_body)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

        return True

    except Exception:
        return False
