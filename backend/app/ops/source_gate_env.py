"""Source gate env constants for source-route-db acceptance matrix."""

from __future__ import annotations

SOURCE_API_KEY_ENV: dict[str, str] = {
    "fred": "FRED_API_KEY",
    "alpha_vantage": "ALPHA_VANTAGE_API_KEY",
    "sec_edgar": "SEC_EDGAR_USER_AGENT",
}


def validate_sec_edgar_user_agent(raw: str | None) -> str | None:
    """SEC fair-access identity — same rules as sec_edgar_port._sec_user_agent."""
    if not raw or not str(raw).strip():
        return None
    agent = str(raw).strip()
    if "@" not in agent and "contact" not in agent.lower():
        return None
    return agent


__all__ = [
    "SOURCE_API_KEY_ENV",
    "validate_sec_edgar_user_agent",
]
