"""Operator-approval gate for tools that mutate state or run external programs."""

import os
from typing import Any, Dict, Mapping, Optional

ALLOW_MUTATIONS_ENV = "MCP_ALLOW_MUTATIONS"

# Schema fragment for the per-call approval flag on gated tools.
APPROVED_PROPERTY: Dict[str, Any] = {
    "type": "boolean",
    "description": "Explicit operator approval for this network or execution action.",
}


def mutation_denial(
    tool_name: str, arguments: Optional[Mapping[str, Any]]
) -> Optional[Dict[str, Any]]:
    """Return an error payload unless the operator opted in and this call is approved.

    Both conditions are required: MCP_ALLOW_MUTATIONS=1 in the server environment
    and a literal boolean ``approved: true`` in the call arguments.
    """
    approved = (arguments or {}).get("approved") is True
    if os.getenv(ALLOW_MUTATIONS_ENV) == "1" and approved:
        return None
    return {
        "error": "explicit_approval_required",
        "tool": tool_name,
        "message": f"Set {ALLOW_MUTATIONS_ENV}=1 and pass approved=true for this call.",
    }
