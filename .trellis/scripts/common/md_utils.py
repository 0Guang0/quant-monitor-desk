"""Shared markdown section extraction for Trellis validators."""

from __future__ import annotations


def extract_md_section(text: str, header_prefix: str) -> str:
    """Return body under ``## {header_prefix}`` until the next ``## `` heading."""
    lines = text.splitlines()
    start: int | None = None
    end = len(lines)
    prefix = f"## {header_prefix}"
    for i, line in enumerate(lines):
        stripped = line.strip()
        if start is None and stripped.startswith(prefix):
            start = i
            continue
        if start is not None and stripped.startswith("## ") and not stripped.startswith(prefix):
            end = i
            break
    if start is None:
        return ""
    return "\n".join(lines[start:end])
