"""Shared datasource exceptions (Batch A+)."""

from __future__ import annotations


class SourceMismatchError(ValueError):
    """Raised when FetchRequest source_id does not match adapter source_id."""
