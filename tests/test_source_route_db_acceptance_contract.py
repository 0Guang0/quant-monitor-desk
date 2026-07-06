from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest
import yaml
from backend.app.ops.source_route_db_acceptance import (
    REQUIRED_ACCEPTANCE_REPORT_FIELDS,
    AcceptanceReport,
    AcceptanceRequest,
    SourceRouteDbAcceptanceSpine,
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


def test_sourceRouteDbAcceptance_spinePreview_reportsNotImplementedHonestly(tmp_path: Path) -> None:
    """覆盖范围：新验收 Module 未接真实流程时的诚实状态
    测试对象：SourceRouteDbAcceptanceSpine.preview / execute
    目的/目标：尚未实现真实 route/fetch/write 时必须明确失败，不能伪装成 PASS
    验证点：preview 与 execute 均为 FAIL；implementation_mode 为 not_implemented
    失败含义：未完成路径被当成产品验收成功，后续执行者会误判任务完成
    """
    request = AcceptanceRequest.from_target("macro_series:fred:fetch_macro_series")
    spine = SourceRouteDbAcceptanceSpine()

    preview = spine.preview(request).to_dict()
    report = spine.execute(request, data_root=tmp_path, live_authorized=False).to_dict()

    assert preview["status"] == "FAIL"
    assert preview["implementation_mode"] == "not_implemented"
    assert report["status"] == "FAIL"
    assert report["implementation_mode"] == "not_implemented"
    assert report["failure_class"] == "NOT_IMPLEMENTED"
