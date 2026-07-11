#!/usr/bin/env python3
"""矩阵 checker 负例回归（阶段性 · 非业务 pytest）

功能：
  用伪造 / dry-run / mock-replay 报告驱动
  scripts/check_source_route_db_acceptance_matrix.py --strict，断言 exit≠0。
  对应原 tests/test_source_route_db_acceptance_matrix.py 与
  tests/test_matrix_live_evidence_honesty.py 中「subprocess 测 checker 自身」的 meta 用例：
  - checkerRejectsLiveReportWithContractFailures
  - liveAuthorizedChecker_rejectsDryRunReport
  - checkerRejectsForgedClosureOutcomes
  - liveAuthorizedChecker_rejectsMockReplayEvidence

业务价值：
  防止 release/CI 矩阵门禁被伪造 closure_outcome、dry-run 冒充 live、
  或 mock/replay 证据假绿绕过。这是 tooling 自检，不是产品业务 outcome。

退役 / 清理时间（满足任一即可删本文件）：
  1. checker 负例已并入正式 scripts/check_* 的 --self-test 且 production_gate 调用；或
  2. 矩阵 gate 被替换且本脚本无调用方。

运行：
  uv run python phase-scripts/check_source_route_matrix_checker_regression.py
  uv run python phase-scripts/check_source_route_matrix_checker_regression.py --strict
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.ops.source_route_db_acceptance import SourceRouteDbAcceptanceSpine
from backend.app.ops.source_route_db_acceptance_matrix import (
    execute_documented_matrix,
    iter_matrix_targets,
    matrix_target_key,
)

CHECKER = PROJECT_ROOT / "scripts" / "check_source_route_db_acceptance_matrix.py"


def _run_checker(*extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), "--strict", "--format", "json", *extra],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def _check_rejects_not_implemented(tmp: Path, errors: list[str]) -> None:
    report_path = tmp / "not-impl.json"
    target = next(t for t in iter_matrix_targets() if t.request.source_id == "kalshi")
    report_path.write_text(
        json.dumps(
            {
                "matrix_count": 22,
                "rows": [
                    {
                        "target": matrix_target_key(target),
                        "status": "FAIL",
                        "failure_class": "NOT_IMPLEMENTED",
                        "write_grade": "not_written",
                        "errors": ["live execute handler not wired for kalshi"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    proc = _run_checker("--live-authorized", "--report", str(report_path))
    if proc.returncode != 1:
        errors.append(f"NOT_IMPLEMENTED live report expected exit 1, got {proc.returncode}")
        return
    payload = json.loads(proc.stdout)
    if payload.get("status") != "FAIL" or not payload.get("closure_violations"):
        errors.append("NOT_IMPLEMENTED live report missing closure_violations")


def _check_rejects_dry_run_as_live(tmp: Path, errors: list[str]) -> None:
    data_root = tmp / ".audit-sandbox" / "source-route-db-checker-dry"
    data_root.mkdir(parents=True)
    report_path = tmp / "dry-run-matrix.json"
    payload = execute_documented_matrix(
        SourceRouteDbAcceptanceSpine(),
        data_root=data_root,
        live_authorized=False,
    )
    report_path.write_text(json.dumps(payload), encoding="utf-8")
    proc = _run_checker("--live-authorized", "--report", str(report_path))
    if proc.returncode != 1:
        errors.append(f"dry-run as live expected exit 1, got {proc.returncode}")
        return
    checker_payload = json.loads(proc.stdout)
    if not (
        checker_payload.get("report_metadata_violations")
        or checker_payload.get("closure_violations")
    ):
        errors.append("dry-run as live missing metadata/closure violations")


def _check_rejects_forged_closure(tmp: Path, errors: list[str]) -> None:
    report_path = tmp / "forged-matrix.json"
    rows: list[dict[str, object]] = []
    for target in iter_matrix_targets():
        rows.append(
            {
                "target": matrix_target_key(target),
                "status": "FAIL",
                "failure_class": "FAIL_EXTERNAL",
                "write_grade": "not_written",
                "closure_outcome": "PASS",
                "errors": ["forged row"],
            }
        )
    report_path.write_text(
        json.dumps(
            {
                "matrix_count": 22,
                "live_authorized": True,
                "closure_mode": "final_live_authorized",
                "closure_status": "PASS",
                "rows": rows,
            }
        ),
        encoding="utf-8",
    )
    proc = _run_checker("--live-authorized", "--report", str(report_path))
    if proc.returncode != 1:
        errors.append(f"forged closure expected exit 1, got {proc.returncode}")
        return
    payload = json.loads(proc.stdout)
    violations = payload.get("closure_violations") or []
    if payload.get("status") != "FAIL" or not violations:
        errors.append("forged closure missing closure_violations")
    elif not any("mismatch" in item for item in violations):
        errors.append("forged closure missing mismatch in closure_violations")


def _check_rejects_mock_replay_evidence(tmp: Path, errors: list[str]) -> None:
    data_root = tmp / "live-sandbox"
    raw_dir = data_root / "raw" / "alpha_vantage" / "us_equity_daily_bar" / "2026-07-07"
    raw_dir.mkdir(parents=True)
    raw_dir.joinpath("evidence.json").write_text(
        json.dumps(
            {
                "source_id": "alpha_vantage",
                "source_fetch_id": "av-mock-AAPL-deadbeef",
                "bars": [],
            }
        ),
        encoding="utf-8",
    )
    av_target = next(t for t in iter_matrix_targets() if t.request.source_id == "alpha_vantage")
    report_path = data_root / "reports" / "source-matrix-acceptance.json"
    report_path.parent.mkdir(parents=True)
    report_path.write_text(
        json.dumps(
            {
                "matrix_count": 22,
                "live_authorized": True,
                "closure_mode": "final_live_authorized",
                "closure_status": "PASS",
                "data_root": str(data_root),
                "rows": [
                    {
                        "target": matrix_target_key(av_target),
                        "source_id": "alpha_vantage",
                        "status": "PASS",
                        "implementation_mode": "live",
                        "failure_class": "NONE",
                        "closure_outcome": "PASS",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    proc = _run_checker(
        "--live-authorized",
        "--report",
        str(report_path),
        "--data-root",
        str(data_root),
    )
    if proc.returncode != 1:
        errors.append(f"mock/replay evidence expected exit 1, got {proc.returncode}")
        return
    payload = json.loads(proc.stdout)
    if payload.get("status") != "FAIL" or not payload.get("evidence_honesty_violations"):
        errors.append("mock/replay evidence missing evidence_honesty_violations")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)

    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="qmd-matrix-checker-") as raw:
        tmp = Path(raw)
        _check_rejects_not_implemented(tmp, errors)
        _check_rejects_dry_run_as_live(tmp, errors)
        _check_rejects_forged_closure(tmp, errors)
        _check_rejects_mock_replay_evidence(tmp, errors)

    for item in errors:
        print(f"CHECKER_REGRESSION: {item}")
    if not errors:
        print("check_source_route_matrix_checker_regression: PASS")
    return 1 if args.strict and errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
