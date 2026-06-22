"""Append-only failed write audit evidence when DB txn may roll back (ADV-A1-005)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SIDECAR_NAME = "failed_write_audit.ndjson"


def append_failed_write_audit(entry: dict[str, Any], *, data_root: Path) -> Path:
    """Persist one FAILED write audit line outside the caller transaction."""
    log_dir = Path(data_root) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / SIDECAR_NAME
    payload = {
        **entry,
        "recorded_at": datetime.now(UTC).isoformat(),
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, default=str, sort_keys=True))
        handle.write("\n")
    return path
