"""CLI-boundary run correlation ids for sync jobs and write audit."""

from __future__ import annotations

import re
import uuid


def _slug_command(command: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", command.lower().strip())
    return slug.strip("-")[:32] or "run"


def new_cli_run_id(command: str, *, prefix: str = "cli") -> str:
    """Issue a correlation id at the CLI boundary (one id per operator invocation)."""
    safe_prefix = re.sub(r"[^a-z0-9]+", "-", prefix.lower().strip()).strip("-") or "cli"
    return f"{safe_prefix}-{_slug_command(command)}-{uuid.uuid4().hex[:12]}"


def cli_requested_by(command: str) -> str:
    """Stable write_audit_log.requested_by label for a qmd-data subcommand."""
    label = command.strip() or "unknown"
    return f"qmd-data:{label}"
