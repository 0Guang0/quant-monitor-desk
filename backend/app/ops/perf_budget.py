"""Production-equivalent smoke budget loader and threshold checks (R3F-HYG-06)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from backend.app import config as app_config

DEFAULT_BUDGET_RELATIVE = Path("specs/contracts/production_equivalent_smoke_budget.yaml")


def load_smoke_budget(path: Path | None = None) -> dict[str, Any]:
    """Load threshold contract YAML."""
    budget_path = path or (app_config.PROJECT_ROOT / DEFAULT_BUDGET_RELATIVE)
    raw = yaml.safe_load(budget_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"invalid smoke budget document: {budget_path}")
    thresholds = raw.get("thresholds")
    if not isinstance(thresholds, dict):
        raise ValueError(f"missing thresholds in smoke budget: {budget_path}")
    return raw


def build_smoke_artifact(
    metrics: dict[str, Any],
    *,
    budget: dict[str, Any] | None = None,
    use_service_path: bool,
) -> dict[str, Any]:
    """Return artifact payload with status PASS or FAIL (never raises)."""
    doc = budget if budget is not None else load_smoke_budget()
    thresholds = doc["thresholds"]
    violations: list[str] = []

    elapsed = float(metrics.get("elapsed_s", 0))
    if elapsed > float(thresholds["elapsed_s_max"]):
        violations.append(f"elapsed_s {elapsed} > {thresholds['elapsed_s_max']}")

    steps = int(metrics.get("pytest_steps", 0))
    if steps < int(thresholds["pytest_steps_min"]):
        violations.append(f"pytest_steps {steps} < {thresholds['pytest_steps_min']}")

    shard_count = int(metrics.get("shard_count_benchmark", 0))
    if shard_count < int(thresholds["shard_count_benchmark_min"]):
        violations.append(
            f"shard_count_benchmark {shard_count} < {thresholds['shard_count_benchmark_min']}"
        )

    if use_service_path:
        required_guard = str(thresholds.get("guard_status_required", ""))
        guard_status = str(metrics.get("guard_status", ""))
        if required_guard and guard_status != required_guard:
            violations.append(f"guard_status {guard_status!r} != {required_guard!r}")

    status = "PASS" if not violations else "FAIL"
    return {
        "owner": doc.get("owner", "b3f-hyg"),
        "phase": "3F.5",
        "status": status,
        "closure_test": doc.get("closure_command", ""),
        "thresholds_source": str(DEFAULT_BUDGET_RELATIVE).replace("\\", "/"),
        "metrics": metrics,
        "violations": violations,
        "does_not_authorize_live_sources": True,
    }


def evaluate_smoke_metrics(
    metrics: dict[str, Any],
    *,
    budget: dict[str, Any] | None = None,
    use_service_path: bool,
) -> dict[str, Any]:
    """Return PASS artifact payload; raises ValueError when a threshold is exceeded."""
    artifact = build_smoke_artifact(
        metrics,
        budget=budget,
        use_service_path=use_service_path,
    )
    if artifact["violations"]:
        raise ValueError("; ".join(artifact["violations"]))
    return artifact
