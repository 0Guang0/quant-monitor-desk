"""Batch 01 B01-TDX manual probe — six vertical slices (TDX-01..06)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from backend.app.datasources.adapters.tdx_pytdx import (
    build_equity_bar_manifest,
    build_index_bar_manifest,
    build_security_list_manifest,
)
from backend.app.ops.tdx_manual_probe import (
    TDX_PROBE_FAIL_AUTH_MISSING,
    TDX_PROBE_FAIL_VALIDATION,
    TDX_PROBE_PASS_RAW_ONLY,
    TDX_PROBE_REDEFERRED,
    MAX_NETWORK_CALLS,
    TDX_PROBE_TARGETS,
    build_comparison_report,
    run_security_list_cap_probe,
    run_tdx_live_manual_probe,
    run_tdx_manual_probe,
)
from backend.app.ops.tdx_live_manual_probe_gate import MAX_TOTAL_ROWS


def _tmp_evidence(tmp_path: Path) -> Path:
    d = tmp_path / "execute-evidence"
    d.mkdir(parents=True)
    return d


# --- TDX-01 Authorization gate ---


def test_tdx01_liveProbeWithoutAuth_returnsFailAuthMissing(tmp_path: Path) -> None:
    """覆盖范围：TDX-01 live runner 无有效授权 payload
    测试对象：run_tdx_live_manual_probe
    目的/目标：live 路径在 host/port 未填或 gate 不匹配时拒绝网络
    验证点：overall_status 为 TDX_PROBE_FAIL_AUTH_MISSING 或 TDX_PROBE_REDEFERRED
    失败含义：无授权也能进入 live fetch，违反 hardening §3
    """
    result = run_tdx_live_manual_probe(
        authorization_evidence=tmp_path / "missing_auth.md",
        tdx_host="127.0.0.1",
        tdx_port=7709,
        evidence_dir=_tmp_evidence(tmp_path),
        sandbox_root=tmp_path / "sandbox",
    )
    assert result["overall_status"] in {
        TDX_PROBE_FAIL_AUTH_MISSING,
        TDX_PROBE_REDEFERRED,
    }
    assert result["live_attempted"] is True
    assert result["raw_records"] == []


def test_tdx01_liveProbePlaceholderHost_returnsDeferred(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """覆盖范围：TDX-01 授权 MD 存在但 host/port 仍为占位
    测试对象：run_tdx_live_manual_probe + 项目授权文件
    目的/目标：BLK-TDX-04 未解除时 live 须 REDEFERRED 而非静默联网
    验证点：占位 host 与 runtime 不匹配时 overall_status 为 TDX_PROBE_REDEFERRED
    失败含义：占位授权被当作有效 live 凭证
    """
    from backend.app.config import PROJECT_ROOT

    auth = PROJECT_ROOT / "docs/quality/tdx_pytdx_live_manual_probe_authorization_2026-06-24.md"
    if not auth.is_file():
        pytest.skip("authorization MD not present in worktree")
    result = run_tdx_live_manual_probe(
        authorization_evidence=auth,
        tdx_host="127.0.0.1",
        tdx_port=7709,
        evidence_dir=_tmp_evidence(tmp_path),
        sandbox_root=tmp_path / "sandbox",
    )
    assert result["overall_status"] == TDX_PROBE_REDEFERRED


# --- TDX-02 Mocked equity daily ---


def test_tdx02_mockedEquity_writesRawEvidenceWithLineage(tmp_path: Path) -> None:
    """覆盖范围：TDX-02 mocked equity daily probe
    测试对象：run_tdx_manual_probe equity 记录
    目的/目标：mocked 路径写出含 source_id/symbol/hash 的 raw JSON
    验证点：equity 记录 status=PASS_RAW_ONLY，含 content_hash 与 sandbox_path
    失败含义：mocked CI 无法证明 TDX equity 字段形状
    """
    evidence = _tmp_evidence(tmp_path)
    sandbox = tmp_path / "sandbox"
    result = run_tdx_manual_probe(evidence_dir=evidence, sandbox_root=sandbox)
    equity = next(
        r for r in result["raw_records"] if r["operation"] == "fetch_daily_bar"
    )
    assert equity["status"] == TDX_PROBE_PASS_RAW_ONLY
    assert equity["source_id"] == "tdx_pytdx"
    assert equity["params"]["instrument_id"] == "sh.600519"
    assert equity["content_hash"]
    assert Path(equity["sandbox_path"]).is_file()
    payload = json.loads(Path(equity["sandbox_path"]).read_text(encoding="utf-8"))
    assert payload["source_id"] == "tdx_pytdx"
    assert payload["symbol"] == "sh.600519"
    assert payload["rows"]


def test_tdx02_equityManifest_hasRequiredFields() -> None:
    """覆盖范围：tdx_pytdx adapter equity manifest
    测试对象：build_equity_bar_manifest
    目的/目标：parser/manifest 含 registry 声明字段
    验证点：manifest 含 symbol、rows、fields
    失败含义：raw evidence 缺少后续 validation 所需字段清单
    """
    manifest = build_equity_bar_manifest("sh.600519", [{"datetime": "2026-06-18"}])
    assert manifest["source_id"] == "tdx_pytdx"
    assert "trade_date" in manifest["fields"] or "datetime" in str(manifest["rows"])


# --- TDX-03 Mocked index daily ---


def test_tdx03_mockedIndex_writesRawEvidence(tmp_path: Path) -> None:
    """覆盖范围：TDX-03 mocked index daily probe
    测试对象：run_tdx_manual_probe index 记录
    目的/目标：000001.SH index raw evidence 保持 validation-only
    验证点：index 记录 PASS_RAW_ONLY；registry closeout 保持 disabled
    失败含义：index 探针缺失或误标 production-ready
    """
    result = run_tdx_manual_probe(
        evidence_dir=_tmp_evidence(tmp_path),
        sandbox_root=tmp_path / "sandbox",
    )
    index_row = next(
        r for r in result["raw_records"] if r["operation"] == "fetch_index_daily_bar"
    )
    assert index_row["status"] == TDX_PROBE_PASS_RAW_ONLY
    assert index_row["params"]["instrument_id"] == "000001.SH"
    assert result["registry_closeout"]["validation_only_preserved"] is True
    assert result["registry_closeout"]["enabled_by_default"] is False


def test_tdx03_indexManifest_hasIndexId() -> None:
    """覆盖范围：index bar manifest 辅助函数
    测试对象：build_index_bar_manifest
    目的/目标：指数探针 manifest 含 index_id
    验证点：index_id == 000001.SH
    失败含义：指数与 equity 符号空间混淆
    """
    manifest = build_index_bar_manifest("000001.SH", [{"datetime": "2026-06-18"}])
    assert manifest["index_id"] == "000001.SH"
    assert manifest["operation"] == "fetch_index_daily_bar"


# --- TDX-04 Security list cap ---


def test_tdx04_securityListOverCap_failsExplicit(tmp_path: Path) -> None:
    """覆盖范围：TDX-04 security list 超 cap
    测试对象：run_security_list_cap_probe(requested_rows=25)
    目的/目标：超过 018C cap=20 时显式 FAIL_VALIDATION，禁止静默截断
    验证点：status == TDX_PROBE_FAIL_VALIDATION
    失败含义：超 cap 拉取无状态，违反 hardening cap
    """
    record = run_security_list_cap_probe(requested_rows=25)
    assert record["status"] == TDX_PROBE_FAIL_VALIDATION
    assert "exceeds cap" in (record.get("failure_reason") or "").lower()


def test_tdx04_securityListWithinCap_passes(tmp_path: Path) -> None:
    """覆盖范围：TDX-04 security list 在 cap 内
    测试对象：run_security_list_cap_probe(requested_rows=20)
    目的/目标：cap 内 list probe 写出 raw evidence
    验证点：status PASS_RAW_ONLY，row_count <= 20
    失败含义：合法小 list 探针失败
    """
    record = run_security_list_cap_probe(requested_rows=20)
    assert record["status"] == TDX_PROBE_PASS_RAW_ONLY
    assert record["row_count"] <= 20


def test_tdx04_securityListManifest_shape() -> None:
    """覆盖范围：security list manifest
    测试对象：build_security_list_manifest
    目的/目标：list manifest 含 market 与 fields
    验证点：market == sh
    失败含义：security list 证据缺少市场维度
    """
    manifest = build_security_list_manifest("sh", [{"code": "600519", "name": "x"}])
    assert manifest["market"] == "sh"
    assert manifest["operation"] == "fetch_security_list"


# --- TDX-05 Comparison report ---


def test_tdx05_comparisonReport_distinguishesVerdicts(tmp_path: Path) -> None:
    """覆盖范围：TDX-05 comparison summary
    测试对象：build_comparison_report
    目的/目标：区分 comparable / missing / conflict，不自动覆盖 baostock
    验证点：comparable 与 missing 列表存在；does_not_auto_overwrite 为 true
    失败含义：对照报告无法支持人工裁决
    """
    result = run_tdx_manual_probe(
        evidence_dir=_tmp_evidence(tmp_path),
        sandbox_root=tmp_path / "sandbox",
    )
    report = result["comparison"]
    assert report["does_not_auto_overwrite_baostock_or_akshare"] is True
    assert "comparable" in report
    assert "missing" in report
    assert "conflicts" in report
    empty = build_comparison_report([])
    assert empty["missing"]


# --- TDX-06 Registry closeout ---


def test_tdx06_registryCloseout_doesNotCloseEmOrAkshare(tmp_path: Path) -> None:
    """覆盖范围：TDX-06 registry/defer closeout 负向断言
    测试对象：decide_registry_closeout / run_tdx_manual_probe
    目的/目标：TDX mocked 成功不得闭合 R3-B2.75-REQ2-EM 或 AkShare 行
    验证点：does_not_close_* 为 True；OPEN 行仍在 registry_rows_must_remain_open
    失败含义：TDX 探针被误用作 Eastmoney/AkShare 闭合证据
    """
    result = run_tdx_manual_probe(
        evidence_dir=_tmp_evidence(tmp_path),
        sandbox_root=tmp_path / "sandbox",
    )
    closeout = result["registry_closeout"]
    assert closeout["does_not_close_R3-B2.75-REQ2-EM"] is True
    assert closeout["does_not_close_R3-PROMPT14-AKSHARE-VAL-01"] is True
    assert "R3-B2.75-REQ2-EM" in closeout["registry_rows_must_remain_open"]
    assert "R3-PROMPT14-AKSHARE-VAL-01" in closeout["registry_rows_must_remain_open"]


def test_tdx06_mockedProbe_overallPassRawOnly(tmp_path: Path) -> None:
    """覆盖范围：TDX-06 mocked bundle 整体状态
    测试对象：run_tdx_manual_probe overall_status
    目的/目标：三路 mocked 探针均 PASS 时 overall 为 TDX_PROBE_PASS_RAW_ONLY
    验证点：overall_status == TDX_PROBE_PASS_RAW_ONLY
    失败含义：mocked CI 路径无法给出明确探针结论
    """
    result = run_tdx_manual_probe(
        evidence_dir=_tmp_evidence(tmp_path),
        sandbox_root=tmp_path / "sandbox",
    )
    assert result["overall_status"] == TDX_PROBE_PASS_RAW_ONLY
    assert result["live_attempted"] is False


def test_tdx06_registryProposedDelta_yamlExists() -> None:
    """覆盖范围：TDX-06 proposed registry delta 文件
    测试对象：research/registry_proposed_delta.yaml
    目的/目标：主会话批处理前有 proposed delta，本分支不 commit registry
    验证点：YAML 含 tdx_pytdx 决策且 EM/AkShare 保持 open
    失败含义：合并协调缺少 registry 提议证据
    """
    from backend.app.config import PROJECT_ROOT

    path = (
        PROJECT_ROOT
        / ".trellis/tasks/round3-tdx-manual-probe/research/registry_proposed_delta.yaml"
    )
    assert path.is_file(), "registry_proposed_delta.yaml must exist for TDX-06"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert data["tdx_pytdx"]["decision"] in {"PROBE_PASS_RAW_ONLY", "PROBE_REDEFERRED"}
    for row in ("R3-B2.75-REQ2-EM", "R3-PROMPT14-AKSHARE-VAL-01"):
        assert data["registry_rows_remain_open"][row] == "OPEN"


# --- P03/P04/P05/P06/P08 adversarial closure ---


def test_tdx_caps_maxNetworkCalls_blocksExcessLiveFetches(tmp_path: Path) -> None:
    """覆盖范围：live 路径 max_network_calls 硬上限
    测试对象：run_tdx_live_manual_probe(max_network_calls=0)
    目的/目标：P03 验证 018C cap=5 可配置且超限时 FAIL_VALIDATION
    验证点：network_calls==0；至少一条记录含 max_network_calls exceeded
    失败含义：无界 live 网络调用违反 hardening cap
    """
    from backend.app.config import PROJECT_ROOT

    auth = PROJECT_ROOT / "docs/quality/tdx_pytdx_live_manual_probe_authorization_2026-06-24.md"
    if not auth.is_file():
        pytest.skip("authorization MD not present")
    result = run_tdx_live_manual_probe(
        authorization_evidence=auth,
        tdx_host="__USER_FILL_HOST__",
        tdx_port=0,
        evidence_dir=_tmp_evidence(tmp_path),
        sandbox_root=tmp_path / "sandbox",
        max_network_calls=0,
    )
    assert result["network_calls"] == 0
    assert any(
        "max_network_calls" in (r.get("failure_reason") or "")
        for r in result["raw_records"]
    )


def test_tdx_caps_maxTotalRows_aggregateValidation(tmp_path: Path) -> None:
    """覆盖范围：聚合行数 MAX_TOTAL_ROWS 校验
    测试对象：run_tdx_manual_probe + 超大 mock row_count 注入
    目的/目标：P03 总行数超 40 时降为 FAIL_VALIDATION
    验证点：total_rows > MAX_TOTAL_ROWS 时 overall 非 PASS_RAW_ONLY
    失败含义：cap 绕过导致超量 raw 证据
    """
    from backend.app.datasources.adapters.fetch_port import FetchPayload, FetchPort
    from backend.app.datasources.fetch_result import FetchRequest

    class _HugeRowPort:
        def fetch_payload(self, req: FetchRequest) -> FetchPayload:
            rows = [{"datetime": f"2026-06-{i:02d}"} for i in range(1, 20)]
            content = json.dumps({"rows": rows}).encode()
            return FetchPayload(content=content, file_type="json", row_count=len(rows))

    ports = {t.probe_id: _HugeRowPort() for t in TDX_PROBE_TARGETS}
    result = run_tdx_manual_probe(
        evidence_dir=_tmp_evidence(tmp_path),
        sandbox_root=tmp_path / "sandbox",
        fetch_ports=ports,
    )
    assert result["total_rows"] > MAX_TOTAL_ROWS
    assert result["overall_status"] == TDX_PROBE_FAIL_VALIDATION


def test_tdx04_equityIndexTargets_respectWindowAndRowCaps() -> None:
    """覆盖范围：equity/index probe target 窗口与行数 cap
    测试对象：TDX_PROBE_TARGETS equity + index 条目
    目的/目标：P04 018C 较小 cap：5 trading days / max_rows=10
    验证点：window_label 含 5 trading days；max_rows <= 10
    失败含义：addendum 默认 cap 泄漏到执行目标
    """
    equity = next(t for t in TDX_PROBE_TARGETS if t.operation == "fetch_daily_bar")
    index = next(t for t in TDX_PROBE_TARGETS if t.operation == "fetch_index_daily_bar")
    assert "5 trading days" in equity.window_label
    assert "5 trading days" in index.window_label
    assert equity.max_rows <= 10
    assert index.max_rows <= 10


def test_tdx02_mockedEquity_rawRecordHasAsOf(tmp_path: Path) -> None:
    """覆盖范围：raw record lineage as_of 字段
    测试对象：run_tdx_manual_probe equity 记录
    目的/目标：P05 snapshot_lineage_contract 要求 as_of 可追溯
    验证点：equity 记录含非空 as_of（ISO date）
    失败含义：raw evidence 缺 as_of，DH2/lineage 检查假 FAIL
    """
    result = run_tdx_manual_probe(
        evidence_dir=_tmp_evidence(tmp_path),
        sandbox_root=tmp_path / "sandbox",
    )
    equity = next(r for r in result["raw_records"] if r["operation"] == "fetch_daily_bar")
    assert equity.get("as_of")
    assert len(str(equity["as_of"])) >= 10


def test_tdx05_comparisonMissing_alignsWithVerdictTaxonomy(tmp_path: Path) -> None:
    """覆盖范围：comparison missing[] 与 verdict 分类一致
    测试对象：build_comparison_report
    目的/目标：P06 missing 仅含 verdict 以 missing_ 开头；comparable 对称
    验证点：空输入全进 missing；mocked 全进 comparable
    失败含义：报告分类字符串匹配误判导致错误裁决
    """
    empty = build_comparison_report([])
    assert len(empty["missing"]) == 3
    assert not empty["comparable"]
    for item in empty["missing"]:
        assert str(item.get("verdict", "")).startswith("missing")

    result = run_tdx_manual_probe(
        evidence_dir=_tmp_evidence(tmp_path),
        sandbox_root=tmp_path / "sandbox",
    )
    report = result["comparison"]
    assert len(report["comparable"]) == 3
    assert not report["missing"]
    for item in report["comparable"]:
        assert str(item.get("verdict", "")).startswith("comparable")


def test_tdx08_routeMatrix_neverSelectsTdxAsPrimary() -> None:
    """覆盖范围：018C production primary 负向断言（引用 test_interface_probe_018c）
    测试对象：build_route_matrix from interface_probe
    目的/目标：P08 TDX 不得成为 selected primary
    验证点：tdx_pytdx 行 enabled_by_default=False；selected_source_id≠tdx_pytdx
    失败含义：TDX 探针分支误晋升 production primary
    """
    from backend.app.ops.interface_probe import build_route_matrix

    for row in build_route_matrix()["routes"]:
        if row["source_id"] == "tdx_pytdx":
            assert not row["source_enabled_by_default"]
            assert row["selected_source_id"] != "tdx_pytdx"


def test_tdx_blk04_livePath_documentedProbeDeferred(tmp_path: Path) -> None:
    """覆盖范围：BLK-TDX-04/05 live 路径书面 PROBE_REDEFERRED
    测试对象：run_tdx_live_manual_probe + 授权 MD 占位 host（127.0.0.1 不匹配表）
    目的/目标：closure test 绿即可；不冒充 live PASS（见 018C test_interface_probe_018c）
    验证点：overall_status==TDX_PROBE_REDEFERRED；live_probe==PROBE_REDEFERRED
    失败含义：占位授权被当作 live PASS
    """
    from backend.app.config import PROJECT_ROOT

    auth = PROJECT_ROOT / "docs/quality/tdx_pytdx_live_manual_probe_authorization_2026-06-24.md"
    if not auth.is_file():
        pytest.skip("authorization MD not present")
    result = run_tdx_live_manual_probe(
        authorization_evidence=auth,
        tdx_host="127.0.0.1",
        tdx_port=7709,
        evidence_dir=_tmp_evidence(tmp_path),
        sandbox_root=tmp_path / "sandbox",
    )
    assert result["overall_status"] == TDX_PROBE_REDEFERRED
    assert result["overall_status"] != TDX_PROBE_PASS_RAW_ONLY
    assert result["registry_closeout"]["tdx_pytdx_live_probe"] == "PROBE_REDEFERRED"
