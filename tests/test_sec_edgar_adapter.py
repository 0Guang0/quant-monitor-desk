"""R3H-01 SEC EDGAR 披露适配器测试（Batch 3H · step 9.4）。

覆盖范围：SEC EDGAR filings 与 Form 4 insider 交易的 fetch port、身份头门禁与 replay 证据。
测试对象：backend/app/datasources/fetch_ports/sec_edgar_port.py 与 normalizers/sec_edgar.py。
目的/目标：证明 sec_edgar 源可在 replay-first 路径下产出合规披露证据并满足 route 终态。
验证点：identity header gate、replay fixture、evidence 字段（9.4 起逐步补齐）。
失败含义：SEC 披露源无法在 Batch 3H 闭合为 READY_WITH_EVIDENCE 或 ADR。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from backend.app.config import PROJECT_ROOT

_FILINGS_REPLAY = PROJECT_ROOT / "tests/fixtures/replay/sec_edgar/filings_replay_bundle.json"
_FORM4_REPLAY = PROJECT_ROOT / "tests/fixtures/replay/sec_edgar/form4_replay_bundle.json"


def _filings_req(**overrides: object):
    from backend.app.datasources.fetch_result import FetchRequest

    base = {
        "run_id": "r3h01-sec-edgar-filings",
        "source_id": "sec_edgar",
        "data_domain": "us_filings",
        "instrument_id": "0000320193",
    }
    base.update(overrides)
    return FetchRequest(**base)


def _form4_req(**overrides: object):
    from backend.app.datasources.fetch_result import FetchRequest

    base = {
        "run_id": "r3h01-sec-edgar-form4",
        "source_id": "sec_edgar",
        "data_domain": "us_insider_form4",
        "instrument_id": "0000320193",
    }
    base.update(overrides)
    return FetchRequest(**base)


def test_secEdgar_port_mockFetch_emitsFilingsEvidence() -> None:
    """覆盖范围：mock SEC EDGAR port 公司披露抓取
    测试对象：create_sec_edgar_fetch_port + SecEdgarMockFetchPort.fetch_payload
    目的/目标：port 直接产出 sec_edgar_evidence_v1 filings 包
    验证点：schema_version、accession_number、cik、content_hash、source_fetch_id
    失败含义：L2 port 未交付 filings 证据形状，无法登记 READY_WITH_EVIDENCE
    """
    from backend.app.datasources.fetch_ports.sec_edgar_port import create_sec_edgar_fetch_port
    from backend.app.datasources.normalizers.sec_edgar import SEC_EDGAR_EVIDENCE_SCHEMA_VERSION

    port = create_sec_edgar_fetch_port(
        ciks=("0000320193",),
        max_filings=5,
        data_domain="us_filings",
        use_mock=True,
    )
    payload = port.fetch_payload(_filings_req())
    body = json.loads(payload.content.decode("utf-8"))
    assert body["schema_version"] == SEC_EDGAR_EVIDENCE_SCHEMA_VERSION
    assert body["data_domain"] == "us_filings"
    assert body.get("source_fetch_id")
    assert body.get("content_hash")
    filings = body.get("filings") or []
    assert filings
    row = filings[0]
    assert row.get("accession_number")
    assert row.get("cik")
    assert row.get("form_type")
    assert row.get("filing_date")


def test_secEdgar_port_mockFetch_emitsForm4Evidence() -> None:
    """覆盖范围：mock SEC EDGAR port Form 4 内部人交易抓取
    测试对象：create_sec_edgar_fetch_port（us_insider_form4 域）
    目的/目标：port 产出 Form 4 证据包，字段含 transaction_date/shares/price
    验证点：data_domain==us_insider_form4；观测行含 issuer_symbol 与 transaction_code
    失败含义：Form 4 域无 port 路径，sec_edgar 双域承诺未闭合
    """
    from backend.app.datasources.fetch_ports.sec_edgar_port import create_sec_edgar_fetch_port
    from backend.app.datasources.normalizers.sec_edgar import SEC_EDGAR_EVIDENCE_SCHEMA_VERSION

    port = create_sec_edgar_fetch_port(
        ciks=("0000320193",),
        max_filings=5,
        data_domain="us_insider_form4",
        use_mock=True,
    )
    payload = port.fetch_payload(_form4_req())
    body = json.loads(payload.content.decode("utf-8"))
    assert body["schema_version"] == SEC_EDGAR_EVIDENCE_SCHEMA_VERSION
    assert body["data_domain"] == "us_insider_form4"
    txs = body.get("transactions") or []
    assert txs
    row = txs[0]
    assert row.get("accession_number")
    assert row.get("issuer_symbol")
    assert row.get("transaction_date")
    assert row.get("transaction_code")


def test_secEdgar_port_identityHeader_missingBlocksLive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：未配置 SEC 身份头时 live fetch 拒绝
    测试对象：SecEdgarLiveFetchPort.fetch_payload
    目的/目标：缺 SEC_EDGAR_USER_AGENT 时不得联网
    验证点：PortError.status 为 USER_AUTH_REQUIRED 或 FAILED
    失败含义：无身份头仍可 live fetch，违反 SEC fair access policy
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.sec_edgar_port import create_sec_edgar_fetch_port

    monkeypatch.delenv("SEC_EDGAR_USER_AGENT", raising=False)
    port = create_sec_edgar_fetch_port(
        ciks=("0000320193",),
        max_filings=5,
        data_domain="us_filings",
        use_mock=False,
    )
    with pytest.raises(PortError) as exc_info:
        port.fetch_payload(_filings_req())
    assert exc_info.value.status in {"USER_AUTH_REQUIRED", "FAILED"}
    assert "user-agent" in exc_info.value.message.lower() or "identity" in exc_info.value.message.lower()


def test_secEdgar_port_cikCap_rejectsOverMaxCiks() -> None:
    """覆盖范围：port CIK 数量 cap 溢出
    测试对象：create_sec_edgar_fetch_port 构造 ciks 超上限
    目的/目标：§7 默认 5 CIK cap 在 factory 层硬拒绝
    验证点：len(ciks) > MAX_CIKS 时构造即 PortError
    失败含义：CIK cap 可被绕过
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.sec_edgar_port import (
        MAX_CIKS,
        create_sec_edgar_fetch_port,
    )

    too_many = tuple(f"{i:010d}" for i in range(MAX_CIKS + 1))
    with pytest.raises(PortError, match="CIK"):
        create_sec_edgar_fetch_port(
            ciks=too_many,
            max_filings=5,
            data_domain="us_filings",
            use_mock=True,
        )


def test_secEdgar_port_filingCap_blocksOverMaxFilings() -> None:
    """覆盖范围：port filings 行数 cap 溢出
    测试对象：SecEdgarMockFetchPort 构造 max_filings 超上限
    目的/目标：ResourceGuard/任务卡 cap（50 filings）在 port 层硬拒绝
    验证点：max_filings 超 MAX_FILINGS 时 fetch 前 PortError
    失败含义：cap 可被 port 参数绕过导致无界 filing pull
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.sec_edgar_port import (
        MAX_FILINGS,
        create_sec_edgar_fetch_port,
    )

    port = create_sec_edgar_fetch_port(
        ciks=("0000320193",),
        max_filings=MAX_FILINGS + 1,
        data_domain="us_filings",
        use_mock=True,
    )
    with pytest.raises(PortError, match="cap"):
        port.fetch_payload(_filings_req())


def test_secEdgar_port_replayFixture_filingsCanonical() -> None:
    """覆盖范围：filings replay fixture 与 normalizer 读路径
    测试对象：tests/fixtures/replay/sec_edgar/filings_replay_bundle.json
    目的/目标：replay 使用 canonical filings 字段 + schema_version
    验证点：read_filings_evidence_bundle 往返；含 accession_number 与 content_hash
    失败含义：replay 路径缺失，9.6 registry 无法登记
    """
    from backend.app.datasources.normalizers.sec_edgar import (
        SEC_EDGAR_EVIDENCE_SCHEMA_VERSION,
        read_filings_evidence_bundle,
    )

    bundle = read_filings_evidence_bundle(_FILINGS_REPLAY)
    assert bundle["schema_version"] == SEC_EDGAR_EVIDENCE_SCHEMA_VERSION
    assert bundle["data_domain"] == "us_filings"
    for row in bundle["filings"]:
        assert row.get("accession_number")
        assert row.get("cik")
        assert row.get("filing_date")


def test_secEdgar_port_replayFixture_form4Canonical() -> None:
    """覆盖范围：Form 4 replay fixture 与 normalizer 读路径
    测试对象：tests/fixtures/replay/sec_edgar/form4_replay_bundle.json
    目的/目标：replay 使用 canonical transaction 字段
    验证点：read_form4_evidence_bundle 往返
    失败含义：Form 4 replay 路径缺失
    """
    from backend.app.datasources.normalizers.sec_edgar import (
        SEC_EDGAR_EVIDENCE_SCHEMA_VERSION,
        read_form4_evidence_bundle,
    )

    bundle = read_form4_evidence_bundle(_FORM4_REPLAY)
    assert bundle["schema_version"] == SEC_EDGAR_EVIDENCE_SCHEMA_VERSION
    assert bundle["data_domain"] == "us_insider_form4"
    for row in bundle["transactions"]:
        assert row.get("transaction_date")
        assert row.get("issuer_symbol")


def test_secEdgar_port_route_disabledByDefault_unauthorized() -> None:
    """覆盖范围：us_filings 路由默认禁用
    测试对象：SourceRoutePlanner + source_registry sec_edgar
    目的/目标：enabled_by_default=false 时 route 为 DISABLED，非 READY
    验证点：route_status=DISABLED_SOURCE；sec_edgar candidate enabled=False
    失败含义：未配置 SEC 仍被 route 选为 production primary
    """
    from backend.app.datasources.capability_registry import SourceCapabilityRegistry
    from backend.app.datasources.route_planner import SourceRoutePlanner
    from backend.app.datasources.source_registry import SourceRegistry

    registry = SourceRegistry()
    registry.load()
    capabilities = SourceCapabilityRegistry()
    capabilities.load()
    planner = SourceRoutePlanner(source_registry=registry, capability_registry=capabilities)
    plan = planner.plan(
        data_domain="us_filings",
        operation="fetch_company_filings",
        run_id="r3h01-sec-route",
        job_id="sec-route-negative",
    )
    assert plan.route_status == "DISABLED_SOURCE"
    assert plan.selected_source_id is None
    sec = next((c for c in plan.candidates if c.source_id == "sec_edgar"), None)
    assert sec is not None
    assert sec.enabled is False


def test_secEdgar_port_route_readyWhenSourceEnabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """覆盖范围：显式启用 sec_edgar 后 route READY
    测试对象：SourceRoutePlanner（内存 registry 覆盖 enabled）
    目的/目标：授权配置后 us_filings 可选 sec_edgar primary
    验证点：route_status=READY；selected_source_id=sec_edgar
    失败含义：即使源已启用也无法 route 到官方 SEC port
    """
    from backend.app.datasources.capability_registry import SourceCapabilityRegistry
    from backend.app.datasources.route_planner import SourceRoutePlanner
    from backend.app.datasources.source_registry import SourceRegistry

    registry = SourceRegistry()
    registry.load()
    rec = registry.get("sec_edgar")
    object.__setattr__(rec, "is_enabled", True)
    orig_domain_roles = registry.get_domain_roles

    def _filings_domain_enabled(data_domain: str):
        binding = orig_domain_roles(data_domain)
        if data_domain != "us_filings":
            return binding
        from backend.app.datasources.source_registry import DomainRoleBinding

        return DomainRoleBinding(
            primary_source_id=binding.primary_source_id,
            validation_source_id=binding.validation_source_id,
            fallback_policy=binding.fallback_policy,
            domain_enabled_by_default=True,
            fallback_source_ids=binding.fallback_source_ids,
        )

    monkeypatch.setattr(registry, "get_domain_roles", _filings_domain_enabled)
    capabilities = SourceCapabilityRegistry()
    capabilities.load()
    planner = SourceRoutePlanner(source_registry=registry, capability_registry=capabilities)
    monkeypatch.setattr(planner, "_platform_allows", lambda _sid: (True, None))
    plan = planner.plan(
        data_domain="us_filings",
        operation="fetch_company_filings",
        run_id="r3h01-sec-route-ready",
        job_id="sec-route-positive",
        extra_candidates=[("sec_edgar", "Primary")],
    )
    sec = next((c for c in plan.candidates if c.source_id == "sec_edgar"), None)
    assert sec is not None
    assert sec.enabled is True
    assert plan.route_status == "READY"
    assert plan.selected_source_id == "sec_edgar"
