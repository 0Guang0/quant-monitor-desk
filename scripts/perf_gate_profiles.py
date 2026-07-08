"""Wall-clock pytest profile runners for P5 perf gate (Slice B)."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

QUICK_BUDGET_SEC = 180.0
FULL_BUDGET_SEC = 300.0
CI_PARALLEL_BUDGET_SEC = 240.0


@dataclass(frozen=True, slots=True)
class PerfGateProfile:
    name: str
    extra_args: tuple[str, ...]
    marker_expr: str
    budget_sec: float


PROFILES: dict[str, PerfGateProfile] = {
    "quick": PerfGateProfile(
        "quick",
        (),
        "not slow and not network and not perf_gate",
        QUICK_BUDGET_SEC,
    ),
    "full": PerfGateProfile(
        "full",
        (),
        "not perf_gate",
        FULL_BUDGET_SEC,
    ),
    "ci-parallel": PerfGateProfile(
        "ci-parallel",
        ("-n", "auto"),
        "not perf_gate",
        CI_PARALLEL_BUDGET_SEC,
    ),
}


def _subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("QMD_PERF_GATE", None)
    env["QMD_PERF_GATE_SUBPROCESS"] = "1"
    return env


def run_profile(profile_name: str, *, verbose: bool = True) -> float:
    """Run one pytest profile subprocess; raise AssertionError on fail or budget breach."""
    profile = PROFILES[profile_name]
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        *profile.extra_args,
        "-m",
        profile.marker_expr,
    ]
    if verbose:
        print(
            f"perf_gate: starting {profile.name} "
            f"(budget {profile.budget_sec:.0f}s)...",
            flush=True,
        )
    started = time.perf_counter()
    proc = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        check=False,
        env=_subprocess_env(),
    )
    elapsed = time.perf_counter() - started
    if proc.returncode != 0:
        raise AssertionError(f"{profile.name} pytest exit={proc.returncode} elapsed={elapsed:.1f}s")
    if elapsed >= profile.budget_sec:
        raise AssertionError(
            f"{profile.name} elapsed={elapsed:.1f}s exceeds budget={profile.budget_sec:.0f}s"
        )
    if verbose:
        print(f"perf_gate: {profile.name} PASS {elapsed:.1f}s", flush=True)
    return elapsed


def run_profiles(profile_names: tuple[str, ...]) -> int:
    """Run profiles sequentially; return 0 on all PASS else 1."""
    exit_code = 0
    for name in profile_names:
        try:
            run_profile(name)
        except AssertionError as exc:
            print(f"perf_gate: FAIL {exc}", flush=True)
            exit_code = 1
    return exit_code
