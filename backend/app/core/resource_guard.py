"""ResourceGuard — system resource checks before heavy jobs."""

from __future__ import annotations

import os
import sys
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
    duckdb_temp_size_gb: float = 0.0
    cache_size_gb: float = 0.0
    system_memory_usage_pct: float = 0.0
    system_disk_usage_pct: float = 0.0

    def __post_init__(self) -> None:
        for name in (
            "available_memory_gb",
            "disk_free_gb",
            "process_rss_mb",
            "project_size_gb",
            "duckdb_temp_size_gb",
            "cache_size_gb",
            "system_memory_usage_pct",
            "system_disk_usage_pct",
        ):
            value = getattr(self, name)
            if value < 0:
                raise ValueError(f"{name} must be non-negative, got {value}")


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
        temp_max = float(profile_limits["duckdb_temp_max_gb"])
        signals.append(
            (
                _signal_decision(
                    snapshot.duckdb_temp_size_gb,
                    temp_max * 0.7,
                    temp_max * 0.85,
                    temp_max,
                    higher_is_worse=True,
                ),
                "duckdb temp directory above threshold",
            )
        )

    cache_t = proj_t
    signals.extend(
        [
            (
                _signal_decision(
                    snapshot.cache_size_gb,
                    cache_t["cache_warn_gb"],
                    cache_t["cache_pause_gb"],
                    cache_t["cache_hard_stop_gb"],
                    higher_is_worse=True,
                ),
                "cache directory above threshold",
            ),
            (
                _signal_decision(
                    snapshot.system_memory_usage_pct,
                    sys_t["system_memory_usage_warn_pct"],
                    sys_t["system_memory_usage_pause_pct"],
                    sys_t["system_memory_usage_hard_stop_pct"],
                    higher_is_worse=True,
                ),
                "system memory usage above threshold",
            ),
            (
                _signal_decision(
                    snapshot.system_disk_usage_pct,
                    sys_t["system_disk_usage_warn_pct"],
                    sys_t["system_disk_usage_pause_pct"],
                    sys_t["system_disk_usage_hard_stop_pct"],
                    higher_is_worse=True,
                ),
                "system disk usage above threshold",
            ),
        ]
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
    for root, _dirs, files in os.walk(path, followlinks=False):
        for name in files:
            fp = Path(root) / name
            if fp.is_symlink():
                continue
            total += fp.stat().st_size
    return total / (1024**3)


def format_pause_event(
    decision: Decision, reason: str, snap: ResourceSnapshot, profile: str
) -> str:
    """Build the RESOURCE_GUARD_PAUSED operator message (GLOBAL_RESOURCE_LIMITS §4)."""
    return (
        "RESOURCE_GUARD_PAUSED\n"
        f"decision={decision.value}\n"
        f"reason={reason}\n"
        f"available_memory_gb={snap.available_memory_gb:.2f}\n"
        f"disk_free_gb={snap.disk_free_gb:.2f}\n"
        f"project_size_gb={snap.project_size_gb:.2f}\n"
        f"process_rss_mb={snap.process_rss_mb:.1f}\n"
        f"profile={profile}\n"
        "suggestion=retry later or switch to normal/batch profile\n"
    )


class ResourceGuard:
    def __init__(self, profile: str | None = None, con=None) -> None:
        self.profile = profile or get_resource_profile()
        self.con = con
        self._thresholds = load_thresholds()

    def snapshot(self) -> ResourceSnapshot:
        mem = psutil.virtual_memory()
        data_root = DATA_ROOT if DATA_ROOT.exists() else PROJECT_ROOT / "data"
        disk_root = data_root.parent if data_root.exists() else PROJECT_ROOT
        disk = psutil.disk_usage(str(disk_root))
        rss = psutil.Process().memory_info().rss
        cache_dir = data_root / "cache"
        return ResourceSnapshot(
            available_memory_gb=mem.available / (1024**3),
            disk_free_gb=disk.free / (1024**3),
            process_rss_mb=rss / (1024**2),
            project_size_gb=_dir_size_gb(data_root),
            duckdb_temp_size_gb=_dir_size_gb(cache_dir / "duckdb_tmp"),
            cache_size_gb=_dir_size_gb(cache_dir),
            system_memory_usage_pct=float(mem.percent),
            system_disk_usage_pct=float(disk.percent),
        )

    def check(self) -> tuple[Decision, str]:
        snap = self.snapshot()
        profile_limits = self._thresholds["profiles"][self.profile]
        decision, reason = evaluate(snap, self._thresholds, profile_limits)
        if decision in (Decision.PAUSE, Decision.HARD_STOP):
            print(format_pause_event(decision, reason, snap, self.profile), file=sys.stderr, end="")
        if decision != Decision.OK and self.con is not None:
            try:
                self.con.execute("BEGIN")
                self.con.execute(
                    """
                    INSERT INTO resource_guard_log (
                        event_id, decision, reason, profile,
                        available_memory_gb, disk_free_gb, process_rss_mb,
                        project_size_gb, system_memory_usage_pct,
                        system_disk_usage_pct, cache_size_gb,
                        duckdb_temp_size_gb, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                        snap.system_memory_usage_pct,
                        snap.system_disk_usage_pct,
                        snap.cache_size_gb,
                        snap.duckdb_temp_size_gb,
                        datetime.now(UTC),
                    ],
                )
                self.con.execute("COMMIT")
            except Exception:
                self.con.execute("ROLLBACK")
                raise
        return decision, reason
