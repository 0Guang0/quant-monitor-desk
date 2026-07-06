from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import duckdb
import pytest
import yaml
from backend.app.ops.source_route_db_acceptance import (
    ACCEPTANCE_DUCKDB_NAME,
    REQUIRED_ACCEPTANCE_REPORT_FIELDS,
    AcceptanceReport,
    AcceptanceRequest,
    SourceRouteDbAcceptanceSpine,
    write_acceptance_report,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = PROJECT_ROOT / "specs/contracts/source_route_db_acceptance_contract.yaml"


def _contract() -> dict:
    return yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_sourceRouteDbAcceptance_contractFields_matchReportEnvelope() -> None:
    """覆盖范围：生产等价验收报告契约字段
    测试对象：source_route_db_acceptance_contract.yaml 与 AcceptanceReport.to_dict
    目的/目标：报告必须携带业务和审计共同需要的完整字段，不能漏掉降级证据
    验证点：契约 required_report_fields 与 Python REQUIRED 常量一致；to_dict 包含所有字段
    失败含义：验收报告缺字段时，下游无法判断 mock、降级、路由或写入状态
    """
    required = tuple(_contract()["required_report_fields"])
    request = AcceptanceRequest.from_target("macro_series:fred:fetch_macro_series")
    payload = AcceptanceReport.not_implemented(request).to_dict()

    assert required == REQUIRED_ACCEPTANCE_REPORT_FIELDS
    assert set(required) <= set(payload)
    assert payload["implementation_mode"] == "not_implemented"
    assert payload["failure_class"] == "NOT_IMPLEMENTED"
    assert payload["status"] == "FAIL"


def test_sourceRouteDbAcceptance_targetParser_requiresDomainSourceOperation() -> None:
    """覆盖范围：CLI target 字符串解析
    测试对象：AcceptanceRequest.from_target
    目的/目标：target 必须明确 domain、source 和 operation，避免验收请求语义含糊
    验证点：合法 target 解析为三个字段；缺段或空段抛 ValueError
    失败含义：错误 target 被接受后，验收可能跑错数据源或跑错业务域
    """
    request = AcceptanceRequest.from_target("macro_series:fred:fetch_macro_series")

    assert request.data_domain == "macro_series"
    assert request.source_id == "fred"
    assert request.operation == "fetch_macro_series"
    with pytest.raises(ValueError, match="data_domain:source_id:operation"):
        AcceptanceRequest.from_target("macro_series:fred")
    with pytest.raises(ValueError, match="data_domain:source_id:operation"):
        AcceptanceRequest.from_target("macro_series::fetch_macro_series")


def test_sourceRouteDbAcceptance_request_isFrozenContractInput() -> None:
    """覆盖范围：验收请求不可变性
    测试对象：AcceptanceRequest frozen dataclass
    目的/目标：请求创建后不应被执行流程中途篡改，保证报告能追溯原始意图
    验证点：修改 source_id 抛 FrozenInstanceError
    失败含义：执行过程中可变请求会让报告和实际验收目标不一致
    """
    request = AcceptanceRequest.from_target("macro_series:fred:fetch_macro_series")

    with pytest.raises(FrozenInstanceError):
        request.source_id = "akshare"  # type: ignore[misc]


def test_sourceRouteDbAcceptance_writeReport_persistsContractJson(tmp_path: Path) -> None:
    """覆盖范围：验收报告 JSON artifact 写入
    测试对象：write_acceptance_report + AcceptanceReport.to_dict
    目的/目标：报告文件格式必须由验收 Module 统一生成，CLI 不应自己拼 JSON 契约
    验证点：返回 JSON 与文件内容一致；JSON 包含 required report 字段和失败分类
    失败含义：不同入口可能写出不同报告格式，审计和自动验收无法稳定读取
    """
    request = AcceptanceRequest.from_target("macro_series:fred:fetch_macro_series")
    report = AcceptanceReport.not_implemented(request)
    report_path = tmp_path / "reports" / "acceptance.json"

    output = write_acceptance_report(report, report_path)

    payload = json.loads(output)
    assert report_path.read_text(encoding="utf-8") == output
    assert set(REQUIRED_ACCEPTANCE_REPORT_FIELDS) <= set(payload)
    assert payload["failure_class"] == "NOT_IMPLEMENTED"
    assert payload["status"] == "FAIL"


def test_sourceRouteDbAcceptance_spinePreview_reportsNotImplementedHonestly(tmp_path: Path) -> None:
    """覆盖范围：新验收 Module 未接真实流程时的诚实状态
    测试对象：SourceRouteDbAcceptanceSpine.preview / execute
    目的/目标：尚未实现真实 route/fetch/write 时必须明确失败，不能伪装成 PASS
    验证点：preview 与 execute 均为 FAIL；implementation_mode 为 not_implemented
    失败含义：未完成路径被当成产品验收成功，后续执行者会误判任务完成
    """
    request = AcceptanceRequest.from_target("cn_equity_daily_bar:qmt:fetch_daily_bar")
    spine = SourceRouteDbAcceptanceSpine()

    preview = spine.preview(request).to_dict()
    report = spine.execute(request, data_root=tmp_path, live_authorized=False).to_dict()

    assert preview["status"] == "FAIL"
    assert preview["implementation_mode"] == "not_implemented"
    assert report["status"] == "FAIL"
    assert report["implementation_mode"] == "not_implemented"
    assert report["failure_class"] == "NOT_IMPLEMENTED"


def test_sourceRouteDbAcceptance_fredMacroTracer_withoutLiveAuthorizationBlocks(
    tmp_path: Path,
) -> None:
    """覆盖范围：macro_series/fred/fetch_macro_series 验收 tracer bullet
    测试对象：SourceRouteDbAcceptanceSpine.execute FRED route preview + live 授权门禁
    目的/目标：FRED macro 目标必须先产生路由证据，缺 live 授权时诚实 BLOCKED
    验证点：route_grade=primary；source_used=fred；failure_class=BLOCKED；status=FAIL
    失败含义：acceptance spine 可能绕过授权触网，或无法说明 FRED 目标被阻断在哪一层
    """
    request = AcceptanceRequest.from_target("macro_series:fred:fetch_macro_series")

    report = SourceRouteDbAcceptanceSpine().execute(
        request,
        data_root=tmp_path / "acceptance-root",
        live_authorized=False,
    ).to_dict()

    assert report["route_plan_id"]
    assert report["route_grade"] == "primary"
    assert report["source_used"] == "fred"
    assert report["source_role"] == "primary"
    assert report["failure_class"] == "BLOCKED"
    assert report["write_grade"] == "blocked"
    assert report["status"] == "FAIL"
    assert "live authorization missing" in report["errors"][0]


def test_sourceRouteDbAcceptance_fredMacroTracer_persistsRouteEvidence(
    tmp_path: Path,
) -> None:
    """覆盖范围：FRED macro tracer 的 RoutePlan 持久化证据
    测试对象：SourceRouteDbAcceptanceSpine.execute 写入 job_event_log ROUTE_PLAN
    目的/目标：验收报告里的 route_plan_id 必须能在隔离 acceptance DB 里追溯到持久化路由事件
    验证点：job_event_log 存在 ROUTE_PLAN；payload.route_plan_id 等于报告 route_plan_id
    失败含义：验收报告只有内存证据，审计者无法在 acceptance DB 复盘路由选择
    """
    request = AcceptanceRequest.from_target("macro_series:fred:fetch_macro_series")
    data_root = tmp_path / "acceptance-root"

    report = SourceRouteDbAcceptanceSpine().execute(
        request,
        data_root=data_root,
        live_authorized=False,
    ).to_dict()

    db_path = data_root / "duckdb" / ACCEPTANCE_DUCKDB_NAME
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
    payload = json.loads(route_payloads[0][0])
    assert payload["route_plan_id"] == report["route_plan_id"]
    assert payload["route_grade"] == "primary"
    assert payload["selected_source_id"] == "fred"


def test_sourceRouteDbAcceptance_fredMacroTracer_liveAuthorizedWithoutFredKeyBlocks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：FRED macro tracer 有 live 授权但缺凭证
    测试对象：SourceRouteDbAcceptanceSpine.execute FRED_API_KEY 门禁
    目的/目标：即使操作员允许 live fetch，缺 FRED 凭证也必须诚实阻断而不是进入未实现或假成功
    验证点：failure_class=BLOCKED；route evidence 保留；错误说明包含 FRED_API_KEY
    失败含义：验收可能在无真实凭证时继续推进，导致外部授权问题被误判为实现完成或普通缺口
    """
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    request = AcceptanceRequest.from_target("macro_series:fred:fetch_macro_series")

    report = SourceRouteDbAcceptanceSpine().execute(
        request,
        data_root=tmp_path / "acceptance-root",
        live_authorized=True,
    ).to_dict()

    assert report["route_plan_id"]
    assert report["route_grade"] == "primary"
    assert report["source_used"] == "fred"
    assert report["failure_class"] == "BLOCKED"
    assert report["write_grade"] == "blocked"
    assert report["status"] == "FAIL"
    assert "FRED_API_KEY" in report["errors"][0]


def test_sourceRouteDbAcceptance_execute_bootstrapsIsolatedAcceptanceDb(tmp_path: Path) -> None:
    """覆盖范围：production-equivalent acceptance DB 初始化
    测试对象：SourceRouteDbAcceptanceSpine.execute DB bootstrap 路径
    目的/目标：验收执行必须先在隔离 data_root 建立迁移后的 DuckDB，不触碰主库
    验证点：duckdb/quant_monitor.duckdb 创建；schema_version 有迁移记录；报告仍为 NOT_IMPLEMENTED
    失败含义：验收 spine 没有真实 DB 语义，后续 route/fetch/write 接入会落到非生产等价环境
    """
    request = AcceptanceRequest.from_target("cn_equity_daily_bar:qmt:fetch_daily_bar")
    data_root = tmp_path / "acceptance-root"

    report = SourceRouteDbAcceptanceSpine().execute(
        request,
        data_root=data_root,
        live_authorized=False,
    )

    db_path = data_root / "duckdb" / ACCEPTANCE_DUCKDB_NAME
    assert db_path.is_file()
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        migration_count = con.execute("SELECT COUNT(*) FROM schema_version").fetchone()[0]
    finally:
        con.close()
    assert migration_count > 0
    assert report.failure_class == "NOT_IMPLEMENTED"
    assert report.status == "FAIL"


def test_sourceRouteDbAcceptance_routePayload_primaryEvidenceFillsReportFields() -> None:
    """覆盖范围：READY primary RoutePlan payload 转验收报告字段
    测试对象：AcceptanceReport.from_route_payload
    目的/目标：job_event_log 的 ROUTE_PLAN 证据应能直接进入验收报告
    验证点：route_plan_id/route_grade/source_used/source_role/source_switched 均被规范化
    失败含义：验收报告无法引用已持久化路由证据，SourceRoutePlan 追溯断档
    """
    request = AcceptanceRequest.from_target("macro_series:fred:fetch_macro_series")
    report = AcceptanceReport.from_route_payload(
        request,
        {
            "route_plan_id": "route-1",
            "route_status": "READY",
            "route_grade": "primary",
            "selected_source_id": "fred",
            "quality_flags": [],
            "candidates": [{"source_id": "fred", "role": "Primary"}],
        },
    ).to_dict()

    assert report["route_plan_id"] == "route-1"
    assert report["route_grade"] == "primary"
    assert report["source_used"] == "fred"
    assert report["source_role"] == "primary"
    assert report["source_switched"] is False
    assert report["failure_class"] == "NOT_IMPLEMENTED"


def test_sourceRouteDbAcceptance_routePayload_degradedEvidenceMarksSwitched() -> None:
    """覆盖范围：fallback RoutePlan payload 转验收报告字段
    测试对象：AcceptanceReport.from_route_payload
    目的/目标：降级路由证据进入报告时必须保留 degraded 和 source_switched
    验证点：route_grade=degraded；source_role=fallback；source_switched=True；质量标记保留
    失败含义：fallback 路径会在验收报告里伪装成正常主源路径
    """
    request = AcceptanceRequest.from_target("macro_series:fred:fetch_macro_series")
    report = AcceptanceReport.from_route_payload(
        request,
        {
            "route_plan_id": "route-2",
            "route_status": "READY",
            "route_grade": "degraded",
            "selected_source_id": "qmt_xtdata",
            "requested_source_id": "fred",
            "quality_flags": ["SOURCE_FALLBACK_USED"],
            "candidates": [{"source_id": "qmt_xtdata", "role": "FallbackPolicy"}],
        },
    ).to_dict()

    assert report["route_grade"] == "degraded"
    assert report["source_used"] == "qmt_xtdata"
    assert report["source_role"] == "fallback"
    assert report["source_switched"] is True
    assert report["quality_flags"] == ["SOURCE_FALLBACK_USED"]


def test_sourceRouteDbAcceptance_routePayload_blockedEvidenceKeepsBlockedFailure() -> None:
    """覆盖范围：blocked RoutePlan payload 转验收报告字段
    测试对象：AcceptanceReport.from_route_payload
    目的/目标：授权缺失或禁用路由必须在验收报告里显示 blocked，而不是 not_implemented
    验证点：route_grade=blocked；write_grade=blocked；failure_class=BLOCKED；source_used=None
    失败含义：外部授权或路由阻断会被误归类为实现未完成，排障方向错误
    """
    request = AcceptanceRequest.from_target("macro_series:fred:fetch_macro_series")
    report = AcceptanceReport.from_route_payload(
        request,
        {
            "route_plan_id": "route-3",
            "route_status": "USER_AUTH_REQUIRED",
            "selected_source_id": None,
            "quality_flags": [],
        },
    ).to_dict()

    assert report["route_grade"] == "blocked"
    assert report["write_grade"] == "blocked"
    assert report["failure_class"] == "BLOCKED"
    assert report["source_used"] is None
