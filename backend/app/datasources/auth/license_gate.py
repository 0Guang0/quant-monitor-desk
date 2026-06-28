"""License gate for authorization-gated CN sources (R3H-03)."""

from __future__ import annotations

import os
from enum import Enum


class LicenseGateDecision(str, Enum):
    AUTHORIZED = "AUTHORIZED"
    DISABLED_NO_ARTIFACT = "DISABLED_NO_ARTIFACT"
    DISABLED_ENV_MISSING = "DISABLED_ENV_MISSING"


# ponytail: env-only gate; upgrade path = signed artifact file validation per source ADR
_SOURCE_ENV_REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "ths_ifind": ("THS_IFIND_LICENSE_ARTIFACT",),
    "qmt_xtdata": ("QMT_XTDATA_AUTHORIZED",),
    "qmt_xqshare": ("XQSHARE_REMOTE_HOST", "XQSHARE_REMOTE_PORT", "QMT_XQSHARE_AUTHORIZED"),
}


def check_license_gate(source_id: str) -> LicenseGateDecision:
    """Return authorization decision for auth-gated sources."""
    required = _SOURCE_ENV_REQUIREMENTS.get(source_id)
    if not required:
        return LicenseGateDecision.AUTHORIZED
    missing = [name for name in required if not os.environ.get(name)]
    if not missing:
        return LicenseGateDecision.AUTHORIZED
    if source_id == "ths_ifind" and not os.environ.get("THS_IFIND_LICENSE_ARTIFACT"):
        return LicenseGateDecision.DISABLED_NO_ARTIFACT
    return LicenseGateDecision.DISABLED_ENV_MISSING


def require_license_gate(source_id: str) -> None:
    """Raise PortError-compatible message when gate blocks fetch."""
    from backend.app.datasources.adapters.fetch_port import PortError

    decision = check_license_gate(source_id)
    if decision == LicenseGateDecision.AUTHORIZED:
        return
    if decision == LicenseGateDecision.DISABLED_NO_ARTIFACT:
        raise PortError("USER_AUTH_REQUIRED", f"{source_id} blocked: license artifact missing")
    raise PortError("USER_AUTH_REQUIRED", f"{source_id} blocked: authorization env missing")
