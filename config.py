"""DEPRECATED: Import from server.config instead.

This module is kept for backward compatibility during migration.
New code should import from server.config directly.
"""

import warnings

# Re-export everything from server.config for backward compatibility
from server.config import *  # noqa: F401, F403

warnings.warn(
    "Importing from root 'config' is deprecated. Use 'from server.config import ...' instead.",
    DeprecationWarning,
    stacklevel=2,
)
