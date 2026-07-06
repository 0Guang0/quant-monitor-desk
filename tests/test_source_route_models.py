from __future__ import annotations

from backend.app.datasources.route_models import SourceRoutePlan


def _plan(*, route_status: str, quality_flags: list[str] | None = None) -> SourceRoutePlan:
    return SourceRoutePlan(
        route_plan_id="route-1",
        run_id="run-1",
        job_id="job-1",
        data_domain="macro_series",
        operation="fetch_macro_series",
        route_status=route_status,
        selected_source_id="fred" if route_status == "READY" else None,
        quality_flags=list(quality_flags or []),
    )


def test_sourceRoutePlan_readyPrimary_payloadIncludesPrimaryRouteGrade() -> None:
    """覆盖范围：READY 主源路由的 route_grade
    测试对象：SourceRoutePlan.to_payload_dict
    目的/目标：正常主源路径必须在持久化 payload 中标记 primary，方便验收报告引用
    验证点：route_grade == primary；route_status == READY；selected_source_id 保留
    失败含义：RoutePlan 只有状态没有等级，下游无法区分主源级 clean 和降级 clean
    """
    payload = _plan(route_status="READY").to_payload_dict()

    assert payload["route_status"] == "READY"
    assert payload["route_grade"] == "primary"
    assert payload["selected_source_id"] == "fred"


def test_sourceRoutePlan_readyFallback_payloadIncludesDegradedRouteGrade() -> None:
    """覆盖范围：READY fallback 路由的 route_grade
    测试对象：SourceRoutePlan.to_payload_dict
    目的/目标：使用 fallback 或 validation 源时必须标记 degraded，不能伪装成主源级路径
    验证点：quality_flags 含 SOURCE_FALLBACK_USED 时 route_grade == degraded
    失败含义：降级路径进入验收报告后会被当成 primary-grade 成功
    """
    payload = _plan(route_status="READY", quality_flags=["SOURCE_FALLBACK_USED"]).to_payload_dict()

    assert payload["route_status"] == "READY"
    assert payload["route_grade"] == "degraded"
    assert "SOURCE_FALLBACK_USED" in payload["quality_flags"]


def test_sourceRoutePlan_blockedStatus_payloadIncludesBlockedRouteGrade() -> None:
    """覆盖范围：非 READY 路由的 route_grade
    测试对象：SourceRoutePlan.to_payload_dict
    目的/目标：授权缺失、禁用和资源阻断等路径必须统一标记 blocked，不能算验收成功
    验证点：USER_AUTH_REQUIRED 生成 route_grade == blocked；selected_source_id 为 None
    失败含义：被阻断路径可能被验收报告误判为可用数据路径
    """
    payload = _plan(route_status="USER_AUTH_REQUIRED").to_payload_dict()

    assert payload["route_status"] == "USER_AUTH_REQUIRED"
    assert payload["route_grade"] == "blocked"
    assert payload["selected_source_id"] is None
