from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _run_acceptance_cli(
    *args: str,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / "qmd_ops.py"),
        "accept-source-route-db",
        *args,
    ]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
        cwd=PROJECT_ROOT,
        env=env,
    )


def test_qmdOps_acceptSourceRouteDb_delegatesToSpineAndWritesHonestReport(
    tmp_path: Path,
) -> None:
    """覆盖范围：qmd-ops FRED macro tracer 缺 live 授权时的输出
    测试对象：scripts/qmd_ops.py accept-source-route-db
    目的/目标：CLI 必须委托验收 Module，并把缺 live 授权的 FRED tracer 诚实写入报告
    验证点：returncode==1；stdout/report 均为 BLOCKED；报告包含 route_plan_id 和 fred route evidence
    失败含义：CLI 绕过 Module、绕过授权门禁，或把 blocked tracer 伪装成产品验收成功
    """
    data_root = tmp_path / ".audit-sandbox" / "source-route-db-acceptance"
    report_path = data_root / "reports" / "acceptance.json"

    result = _run_acceptance_cli(
        "--target",
        "macro_series:fred:fetch_macro_series",
        "--data-root",
        str(data_root),
        "--report",
        str(report_path),
    )

    assert result.returncode == 1, result.stderr
    stdout_payload = json.loads(result.stdout)
    file_payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert file_payload == stdout_payload
    assert stdout_payload["data_domain"] == "macro_series"
    assert stdout_payload["source_id"] == "fred"
    assert stdout_payload["operation"] == "fetch_macro_series"
    assert stdout_payload["implementation_mode"] == "not_implemented"
    assert stdout_payload["route_plan_id"]
    assert stdout_payload["route_grade"] == "primary"
    assert stdout_payload["source_used"] == "fred"
    assert stdout_payload["failure_class"] == "BLOCKED"
    assert stdout_payload["write_grade"] == "blocked"
    assert stdout_payload["status"] == "FAIL"


def test_qmdOps_acceptSourceRouteDb_persistsRouteEvidenceInAcceptanceDb(
    tmp_path: Path,
) -> None:
    """覆盖范围：qmd-ops FRED macro tracer 的 CLI 端到端路由证据
    测试对象：scripts/qmd_ops.py accept-source-route-db + 隔离 acceptance DuckDB
    目的/目标：CLI 报告里的 route_plan_id 必须能在 acceptance DB 里追溯，不只是进程内字段
    验证点：job_event_log.ROUTE_PLAN payload.route_plan_id 等于报告 route_plan_id
    失败含义：正式验收命令可能产出不可审计报告，无法复盘 SourceRoutePlan 选择
    """
    data_root = tmp_path / ".audit-sandbox" / "source-route-db-acceptance"
    report_path = data_root / "reports" / "acceptance.json"

    result = _run_acceptance_cli(
        "--target",
        "macro_series:fred:fetch_macro_series",
        "--data-root",
        str(data_root),
        "--report",
        str(report_path),
    )

    assert result.returncode == 1, result.stderr
    report_payload = json.loads(report_path.read_text(encoding="utf-8"))
    db_path = data_root / "duckdb" / "quant_monitor.duckdb"
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        route_payloads = con.execute(
            """
            SELECT payload_json
            FROM job_event_log
            WHERE event_type = 'ROUTE_PLAN'
            """
        ).fetchall()
    finally:
        con.close()

    assert len(route_payloads) == 1
    route_payload = json.loads(route_payloads[0][0])
    assert route_payload["route_plan_id"] == report_payload["route_plan_id"]
    assert route_payload["selected_source_id"] == "fred"


def test_qmdOps_acceptSourceRouteDb_rejectsCanonicalDataRoot(tmp_path: Path) -> None:
    """覆盖范围：生产等价验收入口的数据根隔离
    测试对象：scripts/qmd_ops.py accept-source-route-db --data-root
    目的/目标：验收命令不得把 canonical data/ 当作隔离 acceptance DB 根目录
    验证点：returncode==1；failure_class==CONTRACT_VIOLATION；错误包含 canonical main data root
    失败含义：真实验收可能污染主数据根，破坏生产等价验收隔离承诺
    """
    report_path = tmp_path / "reports" / "acceptance.json"

    result = _run_acceptance_cli(
        "--target",
        "macro_series:fred:fetch_macro_series",
        "--data-root",
        str(PROJECT_ROOT / "data"),
        "--report",
        str(report_path),
    )

    assert result.returncode == 2, result.stderr
    assert "canonical main DB" in result.stderr


def test_qmdOps_acceptSourceRouteDb_rejectsNonSandboxDataRoot(tmp_path: Path) -> None:
    """覆盖范围：CLI 数据根须位于 .audit-sandbox/source-route-db*
    测试对象：scripts/qmd_ops.py accept-source-route-db --data-root
    目的/目标：验收命令不得对任意 tmp 路径 bootstrap DuckDB，须对齐 ADR-015 隔离 segment
    验证点：returncode==2；stderr 含 .audit-sandbox/source-route-db
    失败含义：运维误用非沙箱路径跑 live 矩阵，污染或混淆数据根
    """
    report_path = tmp_path / "reports" / "acceptance.json"

    result = _run_acceptance_cli(
        "--target",
        "macro_series:fred:fetch_macro_series",
        "--data-root",
        str(tmp_path / "outside-sandbox"),
        "--report",
        str(report_path),
    )

    assert result.returncode == 2, result.stderr
    assert ".audit-sandbox/source-route-db" in result.stderr


def test_qmdOps_acceptSourceRouteDb_allowLiveWithoutFredKeyBlocks(tmp_path: Path) -> None:
    """覆盖范围：qmd-ops FRED macro tracer live 授权后的凭证门禁
    测试对象：scripts/qmd_ops.py accept-source-route-db --allow-live-fetch
    目的/目标：CLI 允许 live fetch 后仍必须要求真实 FRED_API_KEY，不能把缺凭证当成普通未实现
    验证点：returncode==1；failure_class=BLOCKED；route evidence 保留；错误包含 FRED_API_KEY
    失败含义：运维误以为已授权即可完成 live 验收，实际无凭证时可能产生假完成报告
    """
    data_root = tmp_path / ".audit-sandbox" / "source-route-db-acceptance"
    report_path = data_root / "reports" / "acceptance.json"
    env = os.environ.copy()
    env["FRED_API_KEY"] = ""

    result = _run_acceptance_cli(
        "--target",
        "macro_series:fred:fetch_macro_series",
        "--data-root",
        str(data_root),
        "--report",
        str(report_path),
        "--allow-live-fetch",
        env=env,
    )

    assert result.returncode == 1, result.stderr
    payload = json.loads(result.stdout)
    assert payload["route_plan_id"]
    assert payload["source_used"] == "fred"
    assert payload["failure_class"] == "BLOCKED"
    assert payload["write_grade"] == "blocked"
    assert "FRED_API_KEY" in payload["errors"][0]


def test_qmdOps_acceptSourceRouteDb_invalidTargetFailsBeforeReport(tmp_path: Path) -> None:
    """覆盖范围：生产等价验收 CLI target 参数校验
    测试对象：scripts/qmd_ops.py accept-source-route-db --target
    目的/目标：缺少 source 或 operation 的请求必须在执行前失败，不能生成误导报告
    验证点：returncode==2；stderr 说明 target 形状；report 文件不存在
    失败含义：错误 target 进入验收流程后，报告会指向错误的数据域或来源
    """
    report_path = tmp_path / "reports" / "acceptance.json"

    result = _run_acceptance_cli(
        "--target",
        "macro_series:fred",
        "--data-root",
        str(tmp_path / ".audit-sandbox" / "source-route-db-acceptance"),
        "--report",
        str(report_path),
    )

    assert result.returncode == 2
    assert "data_domain:source_id:operation" in result.stderr
    assert not report_path.exists()


def test_qmdOps_acceptSourceRouteDb_allDocumentedSources_writesMatrixReport(
    tmp_path: Path,
) -> None:
    """覆盖范围：全矩阵验收 CLI
    测试对象：scripts/qmd_ops.py accept-source-route-db --all-documented-sources
    目的/目标：Slice 10 矩阵 runner 必须写出 22 行聚合结果，并以 closure 语义判定成功
    验证点：无 live 授权时 returncode==0；matrix_count==22；closure_status==PASS
    失败含义：全源 closure 仍要求不可能的全 status PASS，或无法产出可审计矩阵报告
    """
    data_root = tmp_path / ".audit-sandbox" / "source-route-db-matrix"
    report_path = data_root / "reports" / "matrix.json"

    result = _run_acceptance_cli(
        "--all-documented-sources",
        "--data-root",
        str(data_root),
        "--report",
        str(report_path),
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["matrix_count"] == 22
    assert payload["live_authorized"] is False
    assert payload["closure_status"] == "PASS"
    assert len(payload["rows"]) == 22
    for row in payload["rows"]:
        assert row["target"]
        assert row["closure_outcome"] == "PASS"
        assert row["failure_class"]
