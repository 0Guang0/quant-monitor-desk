"""FastAPI application entry (placeholder shell)."""

from __future__ import annotations

from backend.app import __version__
from backend.app.config import get_resource_profile
from fastapi import FastAPI

app = FastAPI(
    title="Quant Monitor Desk",
    description="Local-first quantitative monitoring console",
    version=__version__,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "resource_profile": get_resource_profile(),
    }
