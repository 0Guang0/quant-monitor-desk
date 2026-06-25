#!/usr/bin/env python3
"""Regenerate B3F-SH execute-evidence *-green.txt and playbook artifacts (Repair)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
TASK = ROOT / ".trellis/tasks/round3-source-health-and-quality-runners"
EVIDENCE = TASK / "execute-evidence"
RESEARCH_EVIDENCE = TASK / "research/execute-evidence"

STEPS: list[tuple[str, str]] = [
    ("9.0-green.txt", "uv run pytest tests/test_sync_orchestrator.py -q"),
    (
        "9.1-green.txt",
        "uv run pytest tests/test_source_health_snapshot.py::test_sourceHealthSnapshot_writer_insertsRow -q",
    ),
    (
        "9.2-green.txt",
        "uv run pytest tests/test_b3f_quality_runners.py::test_b3fQualityRunners_revisionAudit_notDeferred -q",
    ),
    (
        "9.3-green.txt",
        "uv run pytest tests/test_b3f_quality_runners.py::test_b3fQualityRunners_dataQuality_notDeferred -q",
    ),
    (
        "9.4-green.txt",
        "uv run pytest tests/test_source_health_snapshot.py::test_sourceHealthSnapshot_rollupPersist_fields -q",
    ),
    (
        "9.5-green.txt",
        "uv run pytest tests/test_ops_data_health.py::test_opsDataHealth_dh2Path_noSnapshotDdl -q",
    ),
    (
        "9.6-green.txt",
        "uv run pytest tests/test_fred_live_primary_closeout.py::test_fredLivePrimary_requiresAuthorizationYaml -q",
    ),
    (
        "9.7-green.txt",
        "uv run pytest tests/test_b3f_sh_hard_constraints.py::test_b3fShHardConstraints_akshareNotClosedBySidecar -q",
    ),
]

TIER_A = (
    "uv run pytest tests/test_source_health_snapshot.py tests/test_b3f_quality_runners.py "
    "tests/test_ops_data_health.py tests/test_data_health_v2.py -q"
)

DH_PYTEST = "uv run pytest tests/test_ops_data_health.py tests/test_data_health_v2.py -q"

RUFF_BRANCH = (
    "uv run ruff check "
    "backend/app/ops/source_health_writer.py "
    "backend/app/ops/fred_live_primary.py "
    "backend/app/ops/b3f_sh_registry_guard.py "
    "backend/app/ops/data_health.py "
    "backend/app/sync/orchestrator.py "
    "backend/app/sync/runners.py "
    "backend/app/sync/contract.py "
    "backend/app/sync/jobs.py "
    "tests/test_source_health_snapshot.py "
    "tests/test_b3f_quality_runners.py "
    "tests/test_fred_live_primary_closeout.py "
    "tests/test_b3f_sh_hard_constraints.py"
)

RUFF_PLAYBOOK = "uv run ruff check backend/app/ops backend/app/sync"


def run(cmd: str) -> tuple[int, str]:
    proc = subprocess.run(
        cmd,
        shell=True,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, out.strip()


def write_evidence(name: str, cmd: str, code: int, out: str) -> None:
    body = f"# Command: {cmd}\n# exit_code: {code}\n\n{out}\n\nEXIT:{code}\n"
    for dest in (EVIDENCE / name, RESEARCH_EVIDENCE / name):
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(body, encoding="utf-8")


def main() -> int:
    failed = False
    for name, cmd in STEPS:
        code, out = run(cmd)
        write_evidence(name, cmd, code, out)
        print(f"{name}: exit {code}")
        failed = failed or code != 0

    code, out = run(TIER_A)
    write_evidence("playbook-8.4-tier-a.txt", TIER_A, code, out)
    print(f"playbook-8.4-tier-a.txt: exit {code}")
    failed = failed or code != 0

    code_dh, out_dh = run(DH_PYTEST)
    write_evidence("playbook-8.4-dh.txt", DH_PYTEST, code_dh, out_dh)
    failed = failed or code_dh != 0

    code_ruff_branch, out_ruff_branch = run(RUFF_BRANCH)
    write_evidence("playbook-8.4-ruff.txt", RUFF_BRANCH, code_ruff_branch, out_ruff_branch)
    print(f"playbook-8.4-ruff.txt: exit {code_ruff_branch}")
    failed = failed or code_ruff_branch != 0

    code_ruff_full, out_ruff_full = run(RUFF_PLAYBOOK)
    write_evidence("playbook-8.4-ruff-full.txt", RUFF_PLAYBOOK, code_ruff_full, out_ruff_full)

    code_full_py, _out_full_py = run("uv run pytest -q")
    code_full_ruff, _out_full_ruff = run("uv run ruff check .")
    green_body = "\n".join(
        [
            "=== Playbook §8.4 B3F-SH (repair closure) ===",
            "",
            DH_PYTEST,
            out_dh,
            "",
            RUFF_BRANCH,
            out_ruff_branch,
            "",
            "# Playbook line 528 full ops+sync ruff — repo baseline debt:",
            f"{RUFF_PLAYBOOK}",
            f"exit_code={code_ruff_full} (see playbook-8.4-ruff-full.txt; Tier C branch slice green above)",
            "",
            "# Playbook line 529 full pytest+ruff — repo baseline debt (MASTER §6 Tier B waiver):",
            "uv run pytest -q && uv run ruff check .",
            f"pytest exit_code={code_full_py}; ruff exit_code={code_full_ruff}",
            "Tier A evidence: execute-evidence/playbook-8.4-tier-a.txt",
            "",
            f"EXIT:{0 if not failed else 1}",
            "",
        ]
    )
    for dest in (EVIDENCE / "playbook-8.4-green.txt", RESEARCH_EVIDENCE / "playbook-8.4-green.txt"):
        dest.write_text(green_body, encoding="utf-8")

    # A2 dedupe — research YAML is pointer; canonical in execute-evidence/
    research_yaml = RESEARCH_EVIDENCE / "fred_live_authorization_2026-06-25.yaml"
    research_yaml.write_text(
        "# Canonical copy: ../fred_live_authorization_2026-06-25.yaml\n",
        encoding="utf-8",
    )

    handoff_code, handoff_out = run(
        "uv run python .trellis/scripts/task.py validate-execute-handoff "
        ".trellis/tasks/round3-source-health-and-quality-runners"
    )
    print(handoff_out)
    return 1 if failed or handoff_code != 0 else 0


if __name__ == "__main__":
    sys.exit(main())
