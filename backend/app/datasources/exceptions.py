"""Shared datasource exceptions (Batch A+)."""

from __future__ import annotations


class SourceMismatchError(ValueError):
    """Raised when FetchRequest source_id does not match adapter source_id."""


class AdapterConfigurationError(RuntimeError):
    """Raised when adapter factory wiring is incomplete for production use."""


class AdapterNotSupportedError(KeyError):
    """Raised when source_id has no registered adapter implementation."""

    def __init__(self, source_id: str, known: tuple[str, ...]) -> None:
        self.source_id = source_id
        self.known = known
        super().__init__(
            f"no adapter for source_id={source_id!r}; "
            f"known adapters: {', '.join(sorted(known))}; "
            "hint: source_registry may list a source without an implemented adapter"
        )
