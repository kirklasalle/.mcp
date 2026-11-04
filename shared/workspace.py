"""Workspace path resolution shared by standalone MCP servers."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


def resolve_workspace_root(default: Optional[Path] = None) -> Path:
    """Return an existing workspace directory, honoring an explicit client root."""
    configured = os.environ.get("MCP_WORKSPACE_ROOT")
    root = Path(configured).expanduser() if configured else (default or Path.cwd())
    try:
        resolved = root.resolve(strict=True)
    except OSError as exc:
        raise ValueError(f"MCP workspace root does not exist: {root}") from exc
    if not resolved.is_dir():
        raise ValueError(f"MCP workspace root is not a directory: {resolved}")
    return resolved
