"""Source route planner — auditable routing before adapter fetch (Round2.6 Phase C)."""

from __future__ import annotations

import os
import platform
from pathlib import Path
from typing import Any

import yaml
from backend.app.config import PROJECT_ROOT
from backend.app.datasources.capability_registry import SourceCapabilityRegistry
from backend.app.datasources.route_models import SourceRouteCandidate, SourceRoutePlan
from backend.app.datasources.source_registry import SourceRegistry


def _platform_key() -> str:
    plat = platform.system().lower()
    if plat == "windows":
        return "windows"
    if plat == "darwin":
        return "macos"
    return "linux"


class SourceRoutePlanner:
    DEFAULT_MATRIX: Path = PROJECT_ROOT / "specs/contracts/platform_source_matrix.yaml"

    def __init__(
        self,
        *,
        source_registry: SourceRegistry,
        capability_registry: SourceCapabilityRegistry,
        platform_matrix_path: Path | None = None,
    ) -> None:
        self._registry = source_registry
        self._capabilities = capability_registry
        matrix_path = platform_matrix_path or self.DEFAULT_MATRIX
        self._matrix: dict[str, Any] = yaml.safe_load(matrix_path.read_text(encoding="utf-8")) or {}

    def _source_enabled(self, source_id: str) -> tuple[bool, str | None]:
        try:
            rec = self._registry.get(source_id)
        except KeyError:
            return False, "source_not_in_registry"
        if not rec.is_enabled:
            return False, "source_disabled_by_default"
        return True, None

    def _platform_allows(self, source_id: str) -> tuple[bool, str | None]:
        key = _platform_key()
        entry = ((self._matrix.get("platforms") or {}).get(key) or {}).get(source_id) or {}
        if not entry:
            return False, f"platform_matrix_missing:{key}:{source_id}"
        if source_id == "qmt_xtdata" and not entry.get("available_if_user_configured", False):
            return False, "qmt_xtdata_not_available_on_this_platform"
        if source_id == "qmt_xqshare":
            for env_name in entry.get("requires_env") or []:
                if not os.environ.get(env_name):
                    return False, f"missing_env:{env_name}"
            if not entry.get("default_enabled", False):
                return False, "user_authorization_required"
        if not entry.get("default_enabled", False) and entry.get("requires_user_confirmation"):
            return False, "user_authorization_required"
        return bool(entry.get("available_if_user_configured", False)), None

    def _ordered_candidates(
        self,
        data_domain: str,
        *,
        use_fallback: bool,
        extra_candidates: list[tuple[str, str]] | None,
    ) -> list[tuple[str, str]]:
        try:
            binding = self._registry.get_domain_roles(data_domain)
        except KeyError:
            return list(extra_candidates or [])

        ordered: list[tuple[str, str]] = [(binding.primary_source_id, "Primary")]
        if binding.validation_source_id:
            ordered.append((binding.validation_source_id, "Validation"))
        if use_fallback:
            for fid in binding.fallback_source_ids:
                ordered.append((fid, "FallbackPolicy"))
        if extra_candidates:
            ordered.extend(extra_candidates)
        return ordered

    def plan(
        self,
        *,
        data_domain: str,
        operation: str,
        run_id: str,
        job_id: str,
        market_id: str | None = None,
        use_fallback: bool = False,
        extra_candidates: list[tuple[str, str]] | None = None,
    ) -> SourceRoutePlan:
        del market_id  # reserved for future market-scoped routing
        ordered = self._ordered_candidates(
            data_domain, use_fallback=use_fallback, extra_candidates=extra_candidates
        )
        candidates: list[SourceRouteCandidate] = []
        selected: str | None = None
        quality_flags: list[str] = []
        route_status = "NO_AVAILABLE_SOURCE"

        for source_id, role in ordered:
            cap_ok = self._capabilities.is_capability_declared(source_id, data_domain)
            plat_ok, plat_reason = self._platform_allows(source_id)
            reg_ok, reg_reason = self._source_enabled(source_id)
            disabled_reason: str | None = None

            if not cap_ok:
                disabled_reason = "capability_missing"
            elif not plat_ok:
                disabled_reason = plat_reason
            elif not reg_ok:
                disabled_reason = reg_reason

            skip_reason = disabled_reason
            schedulable = disabled_reason is None

            candidates.append(
                SourceRouteCandidate(
                    source_id=source_id,
                    role=role,
                    enabled=schedulable,
                    allowed_domain=data_domain,
                    capability_declared=cap_ok,
                    disabled_reason=disabled_reason,
                    skip_reason=skip_reason,
                )
            )
            if schedulable and selected is None:
                selected = source_id
                route_status = "READY"
                if role == "FallbackPolicy":
                    quality_flags.append("SOURCE_FALLBACK_USED")

        if route_status != "READY":
            selected = None
            if any(c.source_id == "qmt_xtdata" and c.skip_reason for c in candidates):
                route_status = "DISABLED_SOURCE"
            elif any(c.skip_reason == "capability_missing" for c in candidates):
                route_status = "CAPABILITY_MISSING"
            elif any(
                c.skip_reason
                and (
                    "user_authorization" in c.skip_reason
                    or (c.skip_reason or "").startswith("missing_env:")
                )
                for c in candidates
            ):
                route_status = "USER_AUTH_REQUIRED"

        return SourceRoutePlan(
            route_plan_id=SourceRoutePlan.new_id(),
            run_id=run_id,
            job_id=job_id,
            data_domain=data_domain,
            operation=operation,
            route_status=route_status,
            selected_source_id=selected,
            candidates=candidates,
            quality_flags=quality_flags,
        )
