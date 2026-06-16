"""ResourceGuard — system resource checks before heavy jobs."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

import psutil
import yaml
from backend.app.config import CONFIGS_ROOT, DATA_ROOT, PROJECT_ROOT, get_resource_profile


class Decision(StrEnum):
    OK = "OK"
    WARN = "WARN"
    PAUSE = "PAUSE"
    HARD_STOP = "HARD_STOP"


@dataclass(frozen=True)
class ResourceSnapshot:
    available_memory_gb: float
    disk_free_gb: float
    process_rss_mb: float
    project_size_gb: float


_SEVERITY = {
    Decision.OK: 0,
    Decision.WARN: 1,
    Decision.PAUSE: 2,
    Decision.HARD_STOP: 3,
}


def _signal_decision(
    value: float, warn: float, pause: float, hard: float, higher_is_worse: bool
) -> Decision:
    if higher_is_worse:
        if value > hard:
            return Decision.HARD_STOP
        if value > pause:
            return Decision.PAUSE
        if value > warn:
            return Decision.WARN
        return Decision.OK
    if value < hard:
        return Decision.HARD_STOP
    if value < pause:
        return Decision.PAUSE
    if value < warn:
        return Decision.WARN
    return Decision.OK


def evaluate(
    snapshot: ResourceSnapshot,
    thresholds: dict,
    profile_limits: dict | None = None,
) -> tuple[Decision, str]:
    """Pure function: return (decision, reason). Most severe signal wins."""
    sys_t = thresholds["system_thresholds"]
    proj_t = thresholds["project_size_thresholds"]

    signals: list[tuple[Decision, str]] = [
        (
            _signal_decision(
                snapshot.available_memory_gb,
                sys_t["available_memory_warn_gb"],
                sys_t["available_memory_pause_gb"],
                sys_t["available_memory_hard_stop_gb"],
                higher_is_worse=False,
            ),
            "available memory below threshold",
        ),
        (
            _signal_decision(
                snapshot.disk_free_gb,
                sys_t["disk_free_warn_gb"],
                sys_t["disk_free_pause_gb"],
                sys_t["disk_free_hard_stop_gb"],
                higher_is_worse=False,
            ),
            "disk free space below threshold",
        ),
        (
            _signal_decision(
                snapshot.project_size_gb,
                proj_t["project_warn_gb"],
                proj_t["project_pause_gb"],
                proj_t["project_hard_stop_gb"],
                higher_is_worse=True,
            ),
            "project size above threshold",
        ),
    ]

    if profile_limits is not None:
        signals.append(
            (
                _signal_decision(
                    snapshot.process_rss_mb,
                    profile_limits["process_rss_warn_mb"],
                    profile_limits["process_rss_pause_mb"],
                    profile_limits["process_rss_hard_stop_mb"],
                    higher_is_worse=True,
                ),
                "process rss above threshold",
            )
        )

    worst = Decision.OK
    reasons: list[str] = []
    for decision, reason in signals:
        if _SEVERITY[decision] > _SEVERITY[worst]:
            worst = decision
            reasons = [reason]
        elif decision == worst and decision != Decision.OK:
            reasons.append(reason)

    if worst == Decision.OK:
        return Decision.OK, ""
    return worst, "; ".join(reasons)


def load_thresholds() -> dict:
    """Load profile and threshold config from configs + contract."""
    config_path = CONFIGS_ROOT / "resource_limits.yaml"
    contract_path = PROJECT_ROOT / "specs/contracts/resource_limits.yaml"
    with config_path.open(encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    with contract_path.open(encoding="utf-8") as f:
        contract = yaml.safe_load(f)
    cfg["system_thresholds"] = contract["system_thresholds"]
    cfg["project_size_thresholds"] = contract["project_size_thresholds"]
    return cfg


def _dir_size_gb(path: Path) -> float:
    total = 0
    if not path.exists():
        return 0.0
    for item in path.rglob("*", follow_symlinks=False):
        if item.is_file():
            total += item.stat().st_size
    return total / (1024**3)


class ResourceGuard:
    def __init__(self, profile: str | None = None, con=None) -> None:
        self.profile = profile or get_resource_profile()
        self.con = con
        self._thresholds = load_thresholds()

    def snapshot(self) -> ResourceSnapshot:
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage(str(DATA_ROOT.parent if DATA_ROOT.exists() else PROJECT_ROOT))
        rss = psutil.Process().memory_info().rss
        project_size = _dir_size_gb(DATA_ROOT)
        return ResourceSnapshot(
            available_memory_gb=mem.available / (1024**3),
            disk_free_gb=disk.free / (1024**3),
            process_rss_mb=rss / (1024**2),
            project_size_gb=project_size,
        )

    def check(self) -> tuple[Decision, str]:
        snap = self.snapshot()
        profile_limits = self._thresholds["profiles"][self.profile]
        decision, reason = evaluate(snap, self._thresholds, profile_limits)
        if decision != Decision.OK and self.con is not None:
            self.con.execute("BEGIN")
            self.con.execute(
                """
                INSERT INTO resource_guard_log (
                    event_id, decision, reason, profile,
                    available_memory_gb, disk_free_gb, process_rss_mb,
                    project_size_gb, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    str(uuid.uuid4()),
                    decision.value,
                    reason,
                    self.profile,
                    snap.available_memory_gb,
                    snap.disk_free_gb,
                    snap.process_rss_mb,
                    snap.project_size_gb,
                    datetime.now(UTC),
                ],
            )
            self.con.execute("COMMIT")
        return decision, reason
