"""Load Layer 1 five-axis specs into registry/profile/guardrail models."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

import yaml
from backend.app.config import CONFIGS_ROOT, PROJECT_ROOT
from backend.app.layer1_axes.guardrails import AxisEngineeringGuardrailValidator
from backend.app.layer1_axes.models import (
    AxisDefinition,
    AxisEngineeringGuardrail,
    AxisIndicatorDefinition,
    AxisIndicatorProfile,
    AxisLoadResult,
)

AXIS_FOLDER_BY_KEY = {
    "environment": "environment_axis",
    "credit_stress": "credit_stress_axis",
    "risk_appetite": "risk_appetite_axis",
    "liquidity": "liquidity_axis",
    "sentiment": "sentiment_axis",
}

DEFAULT_QUALITY_RULES = (
    "MISSING_VALUE",
    "STALE_DATA",
    "INSUFFICIENT_HISTORY",
    "SOURCE_SWITCHED",
)

DEFAULT_STALE_RULES = ("max_staleness_days",)

CONTRACT_REQUIRED_INDICATOR_FIELDS = (
    "indicator_id",
    "axis_id",
    "display_name_cn",
    "plain_language_summary",
    "layer",
    "module",
    "frequency",
    "unit",
    "primary_source",
    "validation_source",
    "fallback_policy",
    "allow_score",
    "diagnostic_only",
)

MODULE_SUPERSET_FIELDS = ("quality_rules", "stale_rules", "forbidden_substitutes")


class AxisSpecLoadError(ValueError):
    """Axis spec failed validation."""


class AxisSpecLoader:
    """Parse five-axis YAML specs into loader outputs (module doc §5)."""

    def load(
        self,
        *,
        spec_root: Path | None = None,
        enabled_axes: list[str] | None = None,
        config_path: Path | None = None,
    ) -> AxisLoadResult:
        cfg_path = config_path or CONFIGS_ROOT / "layer1_axes.yml"
        cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
        root = (spec_root or (PROJECT_ROOT / str(cfg["spec_root"]))).resolve()
        _assert_spec_root_allowed(root)
        axes_to_load = enabled_axes or list(cfg["enabled_axes"])

        axes: list[AxisDefinition] = []
        indicators: list[AxisIndicatorDefinition] = []
        profiles: list[AxisIndicatorProfile] = []
        guardrails: list[AxisEngineeringGuardrail] = []

        for axis_key in axes_to_load:
            folder = AXIS_FOLDER_BY_KEY.get(axis_key)
            if folder is None:
                raise AxisSpecLoadError(f"unknown enabled axis key: {axis_key!r}")
            axis_dir = root / folder
            spec_file = axis_dir / f"{axis_key}_axis_indicator_spec.yaml"
            if not spec_file.is_file():
                alt = next(axis_dir.glob("*_indicator_spec.yaml"), None)
                spec_file = alt if alt else spec_file
            if not spec_file.is_file():
                raise AxisSpecLoadError(f"missing indicator spec for axis {axis_key!r}")

            spec = yaml.safe_load(spec_file.read_text(encoding="utf-8"))
            axis_id = str(spec["axis_id"])
            eng_path = axis_dir / f"{axis_key}_axis_engineering_rules.md"
            rel_spec = (
                str(spec_file.relative_to(PROJECT_ROOT))
                if spec_file.is_relative_to(PROJECT_ROOT)
                else str(spec_file)
            )
            axes.append(
                AxisDefinition(
                    axis_id=axis_id,
                    axis_name=axis_key,
                    axis_name_cn=str(spec.get("axis_name_cn", axis_id)),
                    description=str(spec.get("plain_language_summary", "")),
                    spec_path=rel_spec,
                )
            )

            axis_forbidden = tuple(str(x) for x in (spec.get("forbidden") or []))
            rel_eng = (
                str(eng_path.relative_to(PROJECT_ROOT))
                if eng_path.is_relative_to(PROJECT_ROOT)
                else str(eng_path)
            )
            if eng_path.is_file():
                _validate_engineering_rules_file(axis_id=axis_id, eng_path=eng_path)
            guardrails.append(
                AxisEngineeringGuardrail(
                    axis_id=axis_id,
                    forbidden_labels=axis_forbidden,
                    forbidden_substitutes=axis_forbidden,
                    engineering_rules_path=rel_eng if eng_path.is_file() else "",
                )
            )

            for module_name, raw_ind, group_kind in _iter_indicators(spec):
                ind = dict(raw_ind)
                ind.setdefault("axis_id", axis_id)
                ind["module"] = module_name
                profile, definition = _build_indicator_records(
                    ind,
                    axis_id=axis_id,
                    group_kind=group_kind,
                    spec_path=rel_spec,
                    axis_forbidden=axis_forbidden,
                )
                indicators.append(definition)
                profiles.append(profile)

        return AxisLoadResult(
            axes=tuple(axes),
            indicators=tuple(indicators),
            profiles=tuple(profiles),
            guardrails=tuple(guardrails),
        )

    def load_from_config(self) -> AxisLoadResult:
        return self.load()


def _iter_indicators(spec: dict[str, Any]):
    modules = spec.get("modules") or {}
    if isinstance(modules, dict):
        for mod_name, mod_body in modules.items():
            if not isinstance(mod_body, dict):
                continue
            for ind in mod_body.get("indicators") or []:
                if isinstance(ind, dict):
                    yield mod_name, ind, "module"

    for special in (
        "shadow_diagnostics",
        "blindspots",
        "layer2_background",
        "layer2_overlay_blindspot",
    ):
        body = spec.get(special)
        if isinstance(body, dict):
            for ind in body.get("indicators") or []:
                if isinstance(ind, dict):
                    yield special, ind, special


def _classify_indicator(ind: dict[str, Any], group_kind: str) -> tuple[bool, bool, bool]:
    layer = str(ind.get("layer", ""))
    dest_tag = str(ind.get("dest_tag", ""))
    status = str(ind.get("status", ""))

    is_forbidden = (
        status == "forbidden"
        or layer == "Forbidden"
        or dest_tag == "FORBIDDEN"
        or "FORBIDDEN" in str(ind.get("indicator_id", ""))
    )
    is_blindspot = group_kind == "blindspots" or layer == "BlindSpot"
    is_shadow = (
        group_kind == "shadow_diagnostics"
        or layer == "Shadow"
        or dest_tag == "SHADOW"
        or ".SHADOW." in str(ind.get("indicator_id", ""))
    )
    return is_forbidden, is_blindspot, is_shadow


def _is_observable(
    ind: dict[str, Any],
    *,
    is_forbidden: bool,
    is_blindspot: bool,
    is_shadow: bool,
) -> bool:
    if is_forbidden or is_blindspot or is_shadow:
        return False
    layer = str(ind.get("layer", ""))
    if "Layer2" in layer:
        return False
    return True


def _coerce_rules(
    ind: dict[str, Any], field_name: str, default: tuple[str, ...]
) -> tuple[str, ...]:
    raw = ind.get(field_name)
    if raw is None:
        return default
    if isinstance(raw, list):
        if field_name in MODULE_SUPERSET_FIELDS and len(raw) == 0:
            raise AxisSpecLoadError(
                f"indicator {ind.get('indicator_id')!r}: "
                f"{field_name} must be non-empty when present"
            )
        return tuple(str(x) for x in raw)
    return (str(raw),)


def _build_indicator_records(
    ind: dict[str, Any],
    *,
    axis_id: str,
    group_kind: str,
    spec_path: str,
    axis_forbidden: tuple[str, ...],
) -> tuple[AxisIndicatorProfile, AxisIndicatorDefinition]:
    indicator_id = ind.get("indicator_id")
    if not indicator_id:
        raise AxisSpecLoadError(f"indicator missing indicator_id in axis {axis_id}")

    is_forbidden, is_blindspot, is_shadow = _classify_indicator(ind, group_kind)
    observable = _is_observable(
        ind, is_forbidden=is_forbidden, is_blindspot=is_blindspot, is_shadow=is_shadow
    )

    layer_tag = str(ind.get("layer", ""))
    display_name_cn = str(ind.get("display_name_cn", indicator_id))
    plain_summary = str(ind.get("plain_language_summary", display_name_cn))

    if observable:
        for req in CONTRACT_REQUIRED_INDICATOR_FIELDS:
            if req in ("axis_id", "module"):
                continue
            if req == "allow_score":
                continue
            if req == "diagnostic_only":
                continue
            if req == "unit" and not ind.get("unit"):
                ind.setdefault("unit", "unitless")
                continue
            if req == "frequency" and not ind.get("frequency"):
                ind.setdefault("frequency", "daily")
                continue
            if req == "validation_source" and not ind.get("validation_source"):
                ind.setdefault("validation_source", "none")
                continue
            if req == "fallback_policy" and not ind.get("fallback_policy"):
                ind.setdefault("fallback_policy", "last_good_cache + stale_reason")
                continue
            if req == "primary_source" and not ind.get("primary_source"):
                if is_shadow or is_blindspot or is_forbidden:
                    ind.setdefault("primary_source", "none")
                    continue
                raise AxisSpecLoadError(f"indicator {indicator_id!r} missing primary_source")

    quality_rules = _coerce_rules(ind, "quality_rules", DEFAULT_QUALITY_RULES)
    stale_rules = _coerce_rules(ind, "stale_rules", DEFAULT_STALE_RULES)
    forbidden_substitutes = _coerce_rules(
        ind,
        "forbidden_substitutes",
        axis_forbidden,
    )

    if observable and ind.get("quality_rules") is not None and ind.get("quality_rules") == []:
        raise AxisSpecLoadError(f"indicator {indicator_id!r}: quality_rules must be non-empty")

    diagnostic_only = bool(ind.get("diagnostic_only"))
    if is_shadow and group_kind == "shadow_diagnostics":
        diagnostic_only = True
    if is_blindspot:
        diagnostic_only = True
    allow_score = bool(
        ind.get("allow_score", ind.get("gate_scoring", not diagnostic_only and not is_forbidden))
    )

    formula = str(ind.get("formula", ""))
    if not formula and ind.get("raw_inputs"):
        formula = "raw_inputs:" + ",".join(str(x) for x in ind["raw_inputs"])

    definition = AxisIndicatorDefinition(
        indicator_id=str(indicator_id),
        axis_id=axis_id,
        indicator_name=str(ind.get("indicator_name", indicator_id)),
        display_name_cn=display_name_cn,
        dest_tag=str(ind.get("dest_tag", "")),
        layer_tag=layer_tag,
        exec_tier=str(ind.get("exec_tier", "")),
        frequency=str(ind.get("frequency", "daily")),
        unit=str(ind.get("unit", "unitless")),
        directionality=str(ind.get("directionality", "")),
        primary_source=str(ind.get("primary_source", "none")),
        validation_source=str(ind.get("validation_source", "none")),
        fallback_policy=str(ind.get("fallback_policy", "last_good_cache + stale_reason")),
        formula=formula,
        allow_score=allow_score,
        diagnostic_only=diagnostic_only,
        is_blindspot=is_blindspot,
        is_forbidden=is_forbidden,
        is_shadow=is_shadow,
        is_observable=observable,
        module=str(ind.get("module", group_kind)),
        quality_rules=quality_rules,
        stale_rules=stale_rules,
        forbidden_substitutes=forbidden_substitutes,
        spec_path=spec_path,
        role_notes=str(ind.get("role", "")),
        is_enabled=str(ind.get("status", "")) != "disabled_unless_consensus_source_auditable",
    )

    boundary = str(ind.get("boundary", ""))
    profile = AxisIndicatorProfile(
        indicator_id=str(indicator_id),
        axis_id=axis_id,
        display_name_cn=display_name_cn,
        plain_language_name=display_name_cn,
        plain_language_summary=plain_summary,
        physical_meaning_static=plain_summary,
        financial_meaning_static=plain_summary,
        coverage_scope_static=boundary,
        penetration_power_static="",
        boundary_static=boundary,
        blind_spot_static=str(ind.get("reason", "")) if is_blindspot else "",
        update_frequency=str(ind.get("frequency", "daily")),
        primary_source=definition.primary_source,
        validation_source=definition.validation_source,
        fallback_policy=definition.fallback_policy,
        display_template="",
        interpretation_guardrails="no_action_semantics",
        no_action_semantics=True,
        spec_path=spec_path,
    )
    return profile, definition


def _assert_spec_root_allowed(root: Path) -> None:
    """Reject spec roots outside project tree (A3); allow OS temp dirs for pytest copies."""
    project = PROJECT_ROOT.resolve()
    if root.is_relative_to(project):
        return
    for env_key in ("TEMP", "TMP", "TMPDIR"):
        raw = os.environ.get(env_key)
        if raw:
            try:
                if root.is_relative_to(Path(raw).resolve()):
                    return
            except (OSError, ValueError):
                continue
    try:
        if root.is_relative_to(Path(tempfile.gettempdir()).resolve()):
            return
    except (OSError, ValueError):
        pass
    raise AxisSpecLoadError(
        f"spec_root {root!s} must be under project root {project!s} or system temp"
    )


def _validate_engineering_rules_file(*, axis_id: str, eng_path: Path) -> None:
    """AC-017-5: engineering_rules.md must document混频投影 metadata for ENV axis."""
    text = eng_path.read_text(encoding="utf-8")
    if axis_id == "ENVIRONMENT":
        if "projection_method" not in text or "source_frequency_map" not in text:
            raise AxisSpecLoadError(
                f"engineering rules for {axis_id!r} must document "
                "projection_method and source_frequency_map"
            )


def build_guardrail_validator(result: AxisLoadResult) -> AxisEngineeringGuardrailValidator:
    return AxisEngineeringGuardrailValidator(result.guardrails)
