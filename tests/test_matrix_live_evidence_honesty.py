"""Matrix live evidence honesty — mock/replay must not back live PASS rows.

Checker 负例（subprocess 测 check_source_route_db_acceptance_matrix）已迁至
phase-scripts/check_source_route_matrix_checker_regression.py。
"""

from __future__ import annotations

import json
from pathlib import Path

from backend.app.ops.matrix_live_evidence_honesty import (
    collect_live_pass_row_evidence_violations,
    non_live_marker_reasons_from_identifier,
    validate_matrix_live_evidence_honesty,
)
from backend.app.ops.source_route_db_acceptance_matrix import iter_matrix_targets, matrix_target_key


def test_nonLiveMarkerReasons_detectsReplayAndMockFetchIds() -> None:
    """覆盖范围：source_fetch_id / fetch_id mock-replay 标记
    测试对象：non_live_marker_reasons_from_identifier
    目的/目标：ADR-016 honesty_rules 禁止 mock/replay 冒充 live PASS
    验证点：baostock-replay-*、av-mock-*、treasury-mock-* 均返回非空原因
    失败含义：final live checker 无法识别假 live 证据
    """
    assert non_live_marker_reasons_from_identifier("baostock-replay-600519")
    assert non_live_marker_reasons_from_identifier("av-mock-AAPL-abc")
    assert non_live_marker_reasons_from_identifier("cftc-mock-088691-deadbeef")
    assert non_live_marker_reasons_from_identifier("stooq-replay-global")
    assert not non_live_marker_reasons_from_identifier("baostock-live-sh600519-deadbeef")
    assert not non_live_marker_reasons_from_identifier("fred-live-DGS10-deadbeef")


def test_validateMatrixLiveEvidenceHonesty_rejectsReplayBackedLivePassRow(
    tmp_path: Path,
) -> None:
    """覆盖范围：live PASS 行 raw evidence 含 replay fetch_id
    测试对象：validate_matrix_live_evidence_honesty
    目的/目标：矩阵报告 status=PASS + implementation_mode=live 时须拒绝 replay 证据
    验证点：raw JSON 含 baostock-replay-* 时返回非空 violations
    失败含义：task-01 可被 replay fixture 假绿关账
    """
    data_root = tmp_path / "sandbox"
    raw_dir = data_root / "raw" / "baostock" / "cn_equity_daily_bar" / "2026-07-07"
    raw_dir.mkdir(parents=True)
    raw_dir.joinpath("evidence.json").write_text(
        json.dumps(
            {
                "source_id": "baostock",
                "source_fetch_id": "baostock-replay-600519",
                "bars": [{"instrument_id": "sh.600519", "trade_date": "2026-07-01"}],
            }
        ),
        encoding="utf-8",
    )
    baostock_target = next(t for t in iter_matrix_targets() if t.request.source_id == "baostock")
    payload = {
        "live_authorized": True,
        "closure_mode": "final_live_authorized",
        "data_root": str(data_root),
        "rows": [
            {
                "target": matrix_target_key(baostock_target),
                "source_id": "baostock",
                "status": "PASS",
                "implementation_mode": "live",
                "failure_class": "NONE",
            }
        ],
    }

    violations = validate_matrix_live_evidence_honesty(data_root, payload)

    assert violations
    assert any("baostock" in item for item in violations)


def test_collectLivePassRowEvidenceHonesty_skipsNonLivePassRows() -> None:
    """覆盖范围：仅 live PASS 行触发 raw 扫描
    测试对象：collect_live_pass_row_evidence_violations
    目的/目标：dry_run / FAIL / replay 模式行不应误报 honesty 违规
    验证点：implementation_mode=replay 或 status=FAIL 时返回空列表
    失败含义：checker 误杀合法 dry-run 或 honest FAIL 报告
    """
    data_root = Path("/nonexistent")
    assert collect_live_pass_row_evidence_violations(
        data_root,
        {"status": "FAIL", "implementation_mode": "live", "source_id": "baostock"},
        target_key="baostock",
    ) == []
    assert collect_live_pass_row_evidence_violations(
        data_root,
        {"status": "PASS", "implementation_mode": "dry_run", "source_id": "baostock"},
        target_key="baostock",
    ) == []
