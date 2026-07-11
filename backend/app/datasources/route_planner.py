"""Source route planner — auditable routing before adapter fetch (Round2.6 Phase C)."""

from __future__ import annotations

import json
import os
import platform
import sys
from pathlib import Path
from typing import Any

import yaml
from backend.app.config import PROJECT_ROOT
from backend.app.datasources.activation_overlay import ask_activation
from backend.app.datasources.capability_registry import SourceCapabilityRegistry
from backend.app.datasources.auth.license_gate import LicenseGateDecision, check_license_gate
from backend.app.datasources.route_models import SourceRouteCandidate, SourceRoutePlan
from backend.app.datasources.source_registry import (
    SourceRegistry,
    schema_check_enums_valid,
)


def _platform_key() -> str:
    plat = platform.system().lower()
    if plat == "windows":
        return "windows"
    if plat == "darwin":
        return "macos"
    return "linux"


_MATRIX_CACHE: dict[str, dict[str, Any]] = {}


def _load_platform_matrix(path: Path) -> dict[str, Any]:
    key = str(path.resolve())
    if key not in _MATRIX_CACHE:
        _MATRIX_CACHE[key] = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return _MATRIX_CACHE[key]


_LICENSE_GATED_SOURCES = frozenset({"qmt_xtdata", "ths_ifind", "qmt_xqshare"})


class SourceRoutePlanner:
    DEFAULT_MATRIX: Path = PROJECT_ROOT / "specs/contracts/platform_source_matrix.yaml"

    def __init__(
        self,
        *,
        source_registry: SourceRegistry,
        capability_registry: SourceCapabilityRegistry,
        platform_matrix_path: Path | None = None,
        activation_con: Any | None = None,
    ) -> None:
        self._registry = source_registry
        self._capabilities = capability_registry
        matrix_path = platform_matrix_path or self.DEFAULT_MATRIX
        self._matrix: dict[str, Any] = _load_platform_matrix(matrix_path)
        # 测试/隔离根可注入；plan(con=…) 优先覆盖
        self._activation_con = activation_con

    def _source_enabled(self, source_id: str) -> tuple[bool, str | None]:
        try:
            rec = self._registry.get(source_id)
        except KeyError:
            return False, "source_not_in_registry"
        if not rec.is_enabled:
            return False, "source_disabled_by_default"
        return True, None

    def _activation_allows(
        self,
        source_id: str,
        *,
        data_domain: str,
        operation: str,
        con: Any | None,
    ) -> tuple[bool, str | None, str]:
        """开关本优先；无 con 时回落 YAML 内存 is_enabled。"""
        # ponytail: 无 con 不读 overlay；产品 fetch 必须传 con。升级：所有正式入口传 con 后删此回落。
        if con is None:
            ok, reason = self._source_enabled(source_id)
            return ok, reason, ""
        try:
            self._registry.get(source_id)
        except KeyError:
            return False, "source_not_in_registry", ""
        decision = ask_activation(
            con,
            source_id=source_id,
            data_domain=data_domain,
            operation=operation,
        )
        if decision.is_allowed:
            return True, None, decision.overlay_revision
        return False, "source_disabled_by_default", decision.overlay_revision

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
        if source_id in _LICENSE_GATED_SOURCES:
            if check_license_gate(source_id) != LicenseGateDecision.AUTHORIZED:
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
        con: Any | None = None,
    ) -> SourceRoutePlan:
        del market_id  # reserved for future market-scoped routing
        if con is None:
            con = self._activation_con
        domain_disabled = False
        try:
            binding = self._registry.get_domain_roles(data_domain)
            domain_disabled = not binding.domain_enabled_by_default
        except KeyError:
            binding = None

        ordered = self._ordered_candidates(
            data_domain, use_fallback=use_fallback, extra_candidates=extra_candidates
        )
        candidates: list[SourceRouteCandidate] = []
        selected: str | None = None
        selected_role: str | None = None
        quality_flags: list[str] = []
        route_status = "NO_AVAILABLE_SOURCE"
        validation_only_primary_blocked = False
        revisions: dict[str, str] = {}

        for source_id, role in ordered:
            # ADR-018：先问开关，再安检（capability / platform / license）
            reg_ok, reg_reason, ovr_rev = self._activation_allows(
                source_id,
                data_domain=data_domain,
                operation=operation,
                con=con,
            )
            if ovr_rev:
                revisions[source_id] = ovr_rev
            cap_ok = self._capabilities.is_capability_declared(source_id, data_domain)
            plat_ok, plat_reason = self._platform_allows(source_id)
            disabled_reason: str | None = None

            if not reg_ok:
                disabled_reason = reg_reason
            elif not cap_ok:
                disabled_reason = "capability_missing"
            elif not plat_ok:
                disabled_reason = plat_reason
            else:
                try:
                    rec = self._registry.get(source_id)
                    if not schema_check_enums_valid(
                        source_type=rec.source_type, license_type=rec.license_type
                    ):
                        disabled_reason = "invalid_schema_source_or_license_type"
                except KeyError:
                    pass
            if disabled_reason is None and role == "Primary":
                try:
                    if self._registry.get(source_id).validation_only:
                        disabled_reason = "validation_only_cannot_be_primary"
                        validation_only_primary_blocked = True
                except KeyError:
                    pass

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
                selected_role = role
                route_status = "READY"
                if role == "FallbackPolicy":
                    quality_flags.append("SOURCE_FALLBACK_USED")

        if route_status != "READY":
            selected = None
            if domain_disabled:
                route_status = "DISABLED_SOURCE"
                quality_flags.append("DOMAIN_DISABLED_BY_DEFAULT")
            elif validation_only_primary_blocked and not any(c.enabled for c in candidates):
                route_status = "VALIDATION_ONLY_BLOCKED"
                quality_flags.append("VALIDATION_ONLY_PRIMARY_BLOCKED")
            elif any(c.skip_reason == "capability_missing" for c in candidates):
                route_status = "CAPABILITY_MISSING"
            elif any(c.source_id in ("qmt_xtdata", "tdx_pytdx") and c.skip_reason for c in candidates):
                route_status = "DISABLED_SOURCE"
            elif any(
                c.role == "Primary" and c.skip_reason == "source_disabled_by_default"
                for c in candidates
            ):
                route_status = "DISABLED_SOURCE"
            elif any(
                c.skip_reason
                and (
                    "user_authorization" in c.skip_reason
                    or (c.skip_reason or "").startswith("missing_env:")
                )
                for c in candidates
            ):
                route_status = "USER_AUTH_REQUIRED"
        elif domain_disabled:
            selected = None
            route_status = "DISABLED_SOURCE"
            quality_flags.append("DOMAIN_DISABLED_BY_DEFAULT")
        elif selected_role == "Validation":
            quality_flags.append("VALIDATION_SOURCE_USED")

        if selected and selected in revisions:
            overlay_revision = revisions[selected]
        elif ordered and ordered[0][0] in revisions:
            overlay_revision = revisions[ordered[0][0]]
        else:
            overlay_revision = ""

        plan = SourceRoutePlan(
            route_plan_id=SourceRoutePlan.new_id(),
            run_id=run_id,
            job_id=job_id,
            data_domain=data_domain,
            operation=operation,
            route_status=route_status,
            selected_source_id=selected,
            candidates=candidates,
            quality_flags=quality_flags,
            overlay_revision=overlay_revision,
        )
        _emit_source_policy_event(plan)
        return plan


def _emit_source_policy_event(plan: SourceRoutePlan) -> None:
    """最小 3-OBS：结构化 stderr；无新遥测依赖（对齐 write_telemetry 模式）。"""
    if os.environ.get("QMD_SOURCE_POLICY_TELEMETRY", "1") == "0":
        return
    reason = ""
    if plan.route_status != "READY":
        reason = next((c.skip_reason for c in plan.candidates if c.skip_reason), "") or plan.route_status
    payload = {
        "event": (
            "source_policy_resolved"
            if plan.route_status == "READY"
            else "source_policy_denied"
        ),
        "run_id": plan.run_id,
        "job_id": plan.job_id,
        "correlation_id": plan.run_id,
        "data_domain": plan.data_domain,
        "operation": plan.operation,
        "route_status": plan.route_status,
        "selected_source_id": plan.selected_source_id,
        "reason_code": reason,
        "overlay_revision": plan.overlay_revision,
    }
    print(
        json.dumps({k: v for k, v in payload.items() if v is not None}, ensure_ascii=False),
        file=sys.stderr,
    )
