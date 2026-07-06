from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _run_acceptance_cli(*args: str) -> subprocess.CompletedProcess[str]:
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / "qmd_ops.py"),
        "accept-source-route-db",
        *args,
    ]
    return subprocess.run(cmd, capture_output=True, text=True, check=False, cwd=PROJECT_ROOT)


def test_qmdOps_acceptSourceRouteDb_delegatesToSpineAndWritesHonestReport(
    tmp_path: Path,
) -> None:
    """覆盖范围：qmd-ops FRED macro tracer 缺 live 授权时的输出
    测试对象：scripts/qmd_ops.py accept-source-route-db
    目的/目标：CLI 必须委托验收 Module，并把缺 live 授权的 FRED tracer 诚实写入报告
    验证点：returncode==1；stdout/report 均为 BLOCKED；报告包含 route_plan_id 和 fred route evidence
    失败含义：CLI 绕过 Module、绕过授权门禁，或把 blocked tracer 伪装成产品验收成功
    """
    data_root = tmp_path / "source-route-db-acceptance"
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

    assert result.returncode == 1, result.stderr
    payload = json.loads(result.stdout)
    assert payload["failure_class"] == "CONTRACT_VIOLATION"
    assert payload["route_grade"] == "blocked"
    assert payload["write_grade"] == "blocked"
    assert "canonical main data root" in payload["errors"][0]


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
        str(tmp_path / "source-route-db-acceptance"),
        "--report",
        str(report_path),
    )

    assert result.returncode == 2
    assert "data_domain:source_id:operation" in result.stderr
    assert not report_path.exists()
