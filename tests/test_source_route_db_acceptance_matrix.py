from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from backend.app.ops.source_route_db_acceptance import SourceRouteDbAcceptanceSpine
from backend.app.ops.source_route_db_acceptance_matrix import (
    DOCUMENTED_SOURCE_MATRIX,
    find_matrix_target,
    iter_matrix_targets,
    matrix_target_key,
    validate_matrix_against_registry,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_acceptanceHelperConsumers_strictMode_hasZeroProductRuntimeConsumers() -> None:
    """覆盖范围：旧 helper/smoke 严格门禁
    测试对象：scripts/check_acceptance_helper_consumers.py --strict
    目的/目标：产品/runtime 代码不得再直接依赖旧 acceptance seam
    验证点：strict 退出码为 0；product_runtime_count 为 0
    失败含义：旧 helper 仍被产品路径调用，验收 PASS 语义会继续分裂
    """
    proc = subprocess.run(
        [
            sys.executable,
            "scripts/check_acceptance_helper_consumers.py",
            "--strict",
            "--format",
            "json",
        ],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    payload = json.loads(proc.stdout)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert payload["strict_status"] == "PASS"
    assert payload["product_runtime_count"] == 0
    assert payload["consumer_count"] == 0


def test_sourceRouteDbAcceptanceMatrix_hasTwentyTwoDocumentedSources() -> None:
    """覆盖范围：文档 5.9.1 源矩阵规模
    测试对象：DOCUMENTED_SOURCE_MATRIX
    目的/目标：验收矩阵必须覆盖全部 22 个设计级数据源
    验证点：矩阵长度为 22；每个 target key 唯一
    失败含义：多源扩展遗漏数据源，最终 closure 无法声称全覆盖
    """
    keys = [matrix_target_key(target) for target in iter_matrix_targets()]

    assert len(DOCUMENTED_SOURCE_MATRIX) == 22
    assert len(keys) == len(set(keys))


def test_sourceRouteDbAcceptanceMatrix_registryAlignment_passesStrictInventory() -> None:
    """覆盖范围：矩阵与 registry/capabilities 对齐
    测试对象：validate_matrix_against_registry
    目的/目标：矩阵行必须能在机器可读 registry/capabilities 中找到对应 domain/operation
    验证点：violations 为空
    失败含义：文档源与实现枚举漂移，preview/execute 会对不存在的 capability 给出假状态
    """
    assert validate_matrix_against_registry() == []


def test_sourceRouteDbAcceptanceMatrix_previewCoversBaostockTarget() -> None:
    """覆盖范围：矩阵 target 的 preview 路由证据
    测试对象：SourceRouteDbAcceptanceSpine.preview
    目的/目标：每个矩阵 target 在 preview 阶段必须返回 route evidence，而不是 generic stub
    验证点：baostock target preview 为 live + route_grade primary/blocked 之一
    失败含义：矩阵 preview 未接通，调用方无法在进入 execute 前判断路由可用性
    """
    target = find_matrix_target(
        next(t.request for t in iter_matrix_targets() if t.request.source_id == "baostock")
    )
    assert target is not None

    preview = SourceRouteDbAcceptanceSpine().preview(target.request).to_dict()

    assert preview["implementation_mode"] == "live"
    assert preview["route_grade"] in {"primary", "degraded", "blocked"}


def test_sourceRouteDbAcceptanceMatrix_validationSourceExecute_blocksPrimaryClean(
    tmp_path: Path,
) -> None:
    """覆盖范围：validation 定位源的 execute 诚实性
    测试对象：SourceRouteDbAcceptanceSpine.execute for akshare validation target
    目的/目标：validation-only 源 live 授权后应产出合格非 primary clean 验收，而非 BLOCKED 失败
    验证点：status=PASS；failure_class=NONE；write_grade=blocked；downstream=VALIDATION_ONLY
    失败含义：validation 源被误判为 BLOCKED 失败或静默写入 primary clean，矩阵 closure 不可通过
    """
    target = find_matrix_target(
        next(t.request for t in iter_matrix_targets() if t.request.source_id == "akshare")
    )
    assert target is not None

    report = SourceRouteDbAcceptanceSpine().execute(
        target.request,
        data_root=tmp_path,
        live_authorized=True,
    ).to_dict()

    assert report["status"] == "PASS"
    assert report["failure_class"] == "NONE"
    assert report["write_grade"] == "blocked"
    assert report["downstream_layer_read_status"] == "VALIDATION_ONLY"
    assert report["route_plan_id"] is not None
    assert report["implementation_mode"] == "live"


def test_sourceRouteDbAcceptanceMatrix_qmtPreview_exposesMissingLocalTerminalGate(
    monkeypatch,
) -> None:
    """覆盖范围：local-terminal 源的 preview 前置条件
    测试对象：SourceRouteDbAcceptanceSpine.preview for qmt_xtdata
    目的/目标：preview 必须在缺 QMT_XTDATA_AUTHORIZED 时暴露 missing_prerequisites，不能假 PASS
    验证点：status=FAIL；live_ready=False；missing_prerequisites 含 QMT_XTDATA_AUTHORIZED
    失败含义：运维误以为 QMT 已可 live 验收，实际缺本地终端授权
    """
    monkeypatch.delenv("QMT_XTDATA_AUTHORIZED", raising=False)
    target = find_matrix_target(
        next(t.request for t in iter_matrix_targets() if t.request.source_id == "qmt_xtdata")
    )
    assert target is not None

    preview = SourceRouteDbAcceptanceSpine().preview(target.request).to_dict()

    assert preview["status"] == "FAIL"
    assert preview["live_ready"] is False
    assert any("QMT_XTDATA_AUTHORIZED" in item for item in preview["missing_prerequisites"])


def test_sourceRouteDbAcceptanceMatrix_dryRunClosure_passesWithoutLiveAuthorization(
    tmp_path: Path,
) -> None:
    """覆盖范围：无 live 授权时的矩阵 closure 语义
    测试对象：execute_documented_matrix + summarize_matrix_closure
    目的/目标：dry-run 矩阵应因诚实 BLOCKED 而 closure PASS，而非要求 22 行 status PASS
    验证点：closure_status=PASS；matrix_count=22；每行 closure_outcome=PASS
    失败含义：最终验收 gate 仍要求不可能的全 PASS，task-01 无法 honest close
    """
    from backend.app.ops.source_route_db_acceptance_matrix import execute_documented_matrix

    payload = execute_documented_matrix(
        SourceRouteDbAcceptanceSpine(),
        data_root=tmp_path,
        live_authorized=False,
    )

    assert payload["matrix_count"] == 22
    assert payload["closure_status"] == "PASS"
    assert payload["closure_mode"] == "dry_run"
    assert payload["live_authorized"] is False
    assert all(row["closure_outcome"] == "PASS" for row in payload["rows"])


def test_sourceRouteDbAcceptanceMatrix_checkerRejectsLiveReportWithContractFailures(
    tmp_path: Path,
) -> None:
    """覆盖范围：矩阵 checker 的业务 closure 校验
    测试对象：scripts/check_source_route_db_acceptance_matrix.py --strict --report
    目的/目标：checker 必须在 live 报告含 NOT_IMPLEMENTED/contract 失败时 FAIL，不能只看行存在
    验证点：伪造 live 报告含 NOT_IMPLEMENTED 行时 strict 退出码为 1
    失败含义：22 行 FAIL/BLOCKED 矩阵仍 PASS checker，无法作为最终 gate
    """
    report_path = tmp_path / "matrix.json"
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

    proc = subprocess.run(
        [
            sys.executable,
            "scripts/check_source_route_db_acceptance_matrix.py",
            "--strict",
            "--live-authorized",
            "--report",
            str(report_path),
            "--format",
            "json",
        ],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    payload = json.loads(proc.stdout)

    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert payload["status"] == "FAIL"
    assert payload["closure_violations"]


def test_sourceRouteDbAcceptanceMatrix_liveAuthorizedChecker_rejectsDryRunReport(
    tmp_path: Path,
) -> None:
    """覆盖范围：--live-authorized checker 防 dry-run 冒充
    测试对象：check_source_route_db_acceptance_matrix.py --strict --live-authorized --report
    目的/目标：dry-run 矩阵报告不得通过最终 live closure gate
    验证点：strict 退出码为 1；report_metadata_violations 或 closure_violations 非空
    失败含义：Slice 10 最终验收可被未授权 dry-run 报告绕过
    """
    from backend.app.ops.source_route_db_acceptance_matrix import execute_documented_matrix

    report_path = tmp_path / "dry-run-matrix.json"
    payload = execute_documented_matrix(
        SourceRouteDbAcceptanceSpine(),
        data_root=tmp_path / "data",
        live_authorized=False,
    )
    report_path.write_text(json.dumps(payload), encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable,
            "scripts/check_source_route_db_acceptance_matrix.py",
            "--strict",
            "--live-authorized",
            "--report",
            str(report_path),
            "--format",
            "json",
        ],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    checker_payload = json.loads(proc.stdout)

    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert checker_payload["status"] == "FAIL"
    assert checker_payload["report_metadata_violations"]
    assert checker_payload["closure_violations"]


def test_sourceRouteDbAcceptanceMatrix_liveClosure_rejectsMissingLiveAuthorizationRows() -> None:
    """覆盖范围：live closure 对 BLOCKED 行的严格语义
    测试对象：evaluate_matrix_row_closure(..., live_authorized=True)
    目的/目标：最终 live gate 不得把缺 live 授权的 BLOCKED 行当成 PASS
    验证点：含 live authorization missing 的 BLOCKED 行 closure_outcome=FAIL
    失败含义：用户授权全部源后仍可通过含 dry-run BLOCKED 行的报告
    """
    from backend.app.ops.source_route_db_acceptance_matrix import evaluate_matrix_row_closure

    target = next(t for t in iter_matrix_targets() if t.request.source_id == "fred")
    row = {
        "status": "FAIL",
        "failure_class": "BLOCKED",
        "write_grade": "blocked",
        "errors": ["live authorization missing for macro_series:fred:fetch_macro_series"],
    }

    assert (
        evaluate_matrix_row_closure(target, row, live_authorized=True) == "FAIL"
    )


def test_sourceRouteDbAcceptanceMatrix_dryRunClosure_allowsDeferredQualificationBlocked() -> None:
    """覆盖范围：dry_run closure 对无资格源的诚实 BLOCKED
    测试对象：evaluate_matrix_row_closure(..., closure_mode=dry_run)
    目的/目标：中间态 dry-run 可把 QMT/iFinD 缺终端/牌照记为 closure PASS
    验证点：qmt_xtdata 与 ths_ifind gate BLOCKED → closure_outcome PASS（仅 dry_run）
    失败含义：开发期矩阵无法诚实暴露长期无资格而不阻断 dry-run 关账
    """
    from backend.app.ops.source_route_db_acceptance_matrix import evaluate_matrix_row_closure

    qmt = next(t for t in iter_matrix_targets() if t.request.source_id == "qmt_xtdata")
    ifind = next(t for t in iter_matrix_targets() if t.request.source_id == "ths_ifind")
    assert (
        evaluate_matrix_row_closure(
            qmt,
            {
                "status": "FAIL",
                "failure_class": "BLOCKED",
                "errors": ["QMT_XTDATA_AUTHORIZED missing for qmt_xtdata"],
            },
            closure_mode="dry_run",
        )
        == "PASS"
    )
    assert (
        evaluate_matrix_row_closure(
            ifind,
            {
                "status": "FAIL",
                "failure_class": "BLOCKED",
                "errors": ["THS_IFIND_LICENSE_ARTIFACT missing for licensed source"],
            },
            closure_mode="dry_run",
        )
        == "PASS"
    )


def test_sourceRouteDbAcceptanceMatrix_finalLiveAuthorizedClosure_allowsDeferredQualificationBlocked() -> None:
    """覆盖范围：final_live_authorized closure 对无资格源的诚实 BLOCKED
    测试对象：evaluate_matrix_row_closure(..., closure_mode=final_live_authorized)
    目的/目标：用户已 live 授权时，QMT/iFinD 缺终端/牌照仍为预期缺口，closure 可 PASS
    验证点：qmt_xtdata 与 ths_ifind gate BLOCKED → closure_outcome PASS
    失败含义：预期无资格被误算进 closure FAIL，与 ADR-016 冲突
    """
    from backend.app.ops.source_route_db_acceptance_matrix import evaluate_matrix_row_closure

    qmt = next(t for t in iter_matrix_targets() if t.request.source_id == "qmt_xtdata")
    ifind = next(t for t in iter_matrix_targets() if t.request.source_id == "ths_ifind")
    assert (
        evaluate_matrix_row_closure(
            qmt,
            {
                "status": "FAIL",
                "failure_class": "BLOCKED",
                "errors": ["QMT_XTDATA_AUTHORIZED missing for qmt_xtdata"],
            },
            closure_mode="final_live_authorized",
        )
        == "PASS"
    )
    assert (
        evaluate_matrix_row_closure(
            ifind,
            {
                "status": "FAIL",
                "failure_class": "BLOCKED",
                "errors": ["THS_IFIND_LICENSE_ARTIFACT missing for licensed source"],
            },
            closure_mode="final_live_authorized",
        )
        == "PASS"
    )


def test_sourceRouteDbAcceptanceMatrix_finalLiveAuthorizedClosure_rejectsUnexpectedBlocked() -> None:
    """覆盖范围：final_live_authorized 对非资格延期源的 BLOCKED
    测试对象：evaluate_matrix_row_closure(..., closure_mode=final_live_authorized)
    目的/目标：除 qualification_deferred 外，缺 key/授权类 BLOCKED 仍阻断 closure
    验证点：alpha_vantage 缺 ALPHA_VANTAGE_API_KEY → closure FAIL
    失败含义：可配置凭证缺口被误当成预期无资格
    """
    from backend.app.ops.source_route_db_acceptance_matrix import evaluate_matrix_row_closure

    target = next(t for t in iter_matrix_targets() if t.request.source_id == "alpha_vantage")
    row = {
        "status": "FAIL",
        "failure_class": "BLOCKED",
        "errors": ["ALPHA_VANTAGE_API_KEY missing for alpha_vantage"],
    }
    assert evaluate_matrix_row_closure(target, row, closure_mode="final_live_authorized") == "FAIL"


def test_sourceRouteDbAcceptanceMatrix_liveClosure_rejectsMissingApiKeyBlocked() -> None:
    """覆盖范围：live closure 对可配置 API key 源的严格语义
    测试对象：evaluate_matrix_row_closure(..., live_authorized=True)
    目的/目标：用户应提供的 API key 缺失时不得因 qualification_deferred 豁免而 PASS
    验证点：alpha_vantage 缺 ALPHA_VANTAGE_API_KEY → closure FAIL
    失败含义：可配置凭证缺口被误当成长期无资格
    """
    from backend.app.ops.source_route_db_acceptance_matrix import evaluate_matrix_row_closure

    target = next(t for t in iter_matrix_targets() if t.request.source_id == "alpha_vantage")
    row = {
        "status": "FAIL",
        "failure_class": "BLOCKED",
        "errors": ["ALPHA_VANTAGE_API_KEY missing for alpha_vantage"],
    }
    assert evaluate_matrix_row_closure(target, row, live_authorized=True) == "FAIL"


def test_sourceRouteDbAcceptanceMatrix_symbolSsot_alignsWithPortWhitelists() -> None:
    """覆盖范围：矩阵 live 探针符号 SSOT
    测试对象：matrix_cninfo_symbols / matrix_alpha_vantage_symbol / matrix_kalshi_market_ticker
    目的/目标：CNINFO/AV/Kalshi 矩阵符号必须与 port/registry 白名单一致，避免裸 600519/IBM 触发 FAIL_EXTERNAL
    验证点：cninfo=sh.600519；alpha_vantage=SPY；kalshi=KXFED-27APR-T4.25
    失败含义：live 矩阵仍用非白名单符号，外部 fetch 失败被误判为源不可用
    """
    from backend.app.datasources.fetch_ports.alpha_vantage_port import SYMBOL_WHITELIST as AV_WL
    from backend.app.datasources.fetch_ports.cninfo_port import SYMBOL_WHITELIST as CNINFO_WL
    from backend.app.datasources.fetch_ports.kalshi_port import MARKET_WHITELIST as KALSHI_WL
    from backend.app.ops.source_route_db_acceptance_matrix import (
        matrix_alpha_vantage_symbol,
        matrix_cninfo_symbols,
        matrix_coingecko_asset_id,
        matrix_kalshi_market_ticker,
    )
    from backend.app.datasources.fetch_ports.coingecko_port import ASSET_WHITELIST as CG_WL

    cninfo_symbols = matrix_cninfo_symbols()
    assert cninfo_symbols
    assert all(symbol in CNINFO_WL for symbol in cninfo_symbols)
    assert matrix_alpha_vantage_symbol() in AV_WL
    assert matrix_kalshi_market_ticker() in KALSHI_WL
    assert matrix_coingecko_asset_id() in CG_WL


def test_sourceRouteDbAcceptanceMatrix_coingeckoEvidenceFetch_liveMock_passesWithoutAdapter(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """覆盖范围：Coingecko 矩阵 evidence_fetch live 路径
    测试对象：SourceRouteDbAcceptanceSpine.execute for coingecko matrix target
    目的/目标：绕过 DISABLED_SOURCE 与缺失 adapter，以 product live port + raw 证据完成验收
    验证点：status=PASS；failure_class=NONE；write_grade=not_written；raw 目录有文件
    失败含义：Coingecko 仍走 DataSourceService adapter 路径，矩阵 live 永远 FAIL_CONTRACT/FAIL_EXTERNAL
    """
    import json
    import uuid
    from dataclasses import dataclass

    from backend.app.datasources.adapters.fetch_port import FetchPayload
    from backend.app.datasources.fetch_result import FetchRequest
    from backend.app.ops.source_route_db_acceptance_matrix import matrix_coingecko_asset_id

    @dataclass(frozen=True)
    class _StubPort:
        def fetch_payload(self, req: FetchRequest) -> FetchPayload:
            asset_id = matrix_coingecko_asset_id()
            bundle = {
                "schema_version": 1,
                "source_id": "coingecko",
                "data_domain": req.data_domain,
                "instruments": [{"asset_id": asset_id, "symbol": "btc", "source_used": "coingecko"}],
                "source_fetch_id": f"stub-{uuid.uuid4().hex[:8]}",
                "content_hash": "stub",
                "as_of_timestamp": "2026-01-01T00:00:00+00:00",
                "retrieved_at": "2026-01-01T00:00:00+00:00",
                "schema_hash": "stub",
            }
            return FetchPayload(
                content=json.dumps(bundle).encode("utf-8"),
                file_type="json",
                row_count=1,
            )

    def _fake_create_product_live_fetch_port(**_kwargs):
        return _StubPort()

    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setattr(
        "backend.app.datasources.product_live_ports.create_product_live_fetch_port",
        _fake_create_product_live_fetch_port,
    )
    target = next(t for t in iter_matrix_targets() if t.request.source_id == "coingecko")
    report = SourceRouteDbAcceptanceSpine().execute(
        target.request,
        data_root=tmp_path,
        live_authorized=True,
    ).to_dict()

    assert report["status"] == "PASS"
    assert report["failure_class"] == "NONE"
    assert report["write_grade"] == "not_written"
    assert list((tmp_path / "raw").rglob("*"))


def test_resolveDeribitLiveOptionInstrument_readsBundleInstrumentName() -> None:
    """覆盖范围：Deribit live 探针合约解析
    测试对象：resolve_deribit_live_option_instrument
    目的/目标：live fetch 返回的 bundle instrument 必须成为增量 sync 的 instrument_id
    验证点：解析结果为 bundle 内 instrument_name，而非过期 seed
    失败含义：矩阵仍用过期 BTC-28JUN24，staging 过滤后 rows_written=0
    """
    import json
    from dataclasses import dataclass

    from backend.app.datasources.fetch_ports.deribit_port import resolve_deribit_live_option_instrument
    from backend.app.datasources.fetch_result import FetchRequest
    from backend.app.datasources.adapters.fetch_port import FetchPayload

    active = "BTC-8JUL26-55000-C"

    @dataclass(frozen=True)
    class _StubPort:
        instruments: tuple[str, ...] = ("BTC-28JUN24-65000-C",)

        def fetch_payload(self, req: FetchRequest) -> FetchPayload:
            bundle = {
                "instruments": [{"instrument_name": active, "mark_iv": 0.5, "source_used": "deribit"}],
            }
            return FetchPayload(
                content=json.dumps(bundle).encode("utf-8"),
                file_type="json",
                row_count=1,
            )

    assert resolve_deribit_live_option_instrument(_StubPort()) == active


def test_deribitStaging_rowsEmpty_whenInstrumentMismatch() -> None:
    """覆盖范围：Deribit staging 行过滤
    测试对象：deribit_staging_rows_from_bundle
    目的/目标：req instrument 与 bundle 不一致时必须返回空行（复现矩阵 FAIL 根因）
    验证点：过期 seed + live bundle → []
    失败含义：误把 instrument 不匹配当作可接受 live 成功
    """
    from backend.app.ops.deribit_incremental_run import deribit_staging_rows_from_bundle

    bundle = {
        "instruments": [{"instrument_name": "BTC-8JUL26-55000-C", "mark_iv": 0.5}],
        "content_hash": "h",
        "schema_hash": "s",
        "source_fetch_id": "f",
        "as_of_timestamp": "2026-07-07T00:00:00+00:00",
    }
    rows = deribit_staging_rows_from_bundle(
        bundle,
        instrument_name="BTC-28JUN24-65000-C",
    )
    assert rows == []


def test_secEdgar_fetchSubmissions_usesHttpx2Client(monkeypatch) -> None:
    """覆盖范围：SEC submissions live HTTP 客户端
    测试对象：_fetch_sec_submissions_json
    目的/目标：live fetch 应走 httpx2（非 urllib），并带 fair-access User-Agent
    验证点：httpx.get 被调用；返回 JSON dict
    失败含义：urllib SSL/EOF 导致矩阵 NETWORK_ERROR 无法恢复
    """
    from backend.app.datasources.fetch_ports.sec_edgar_port import _fetch_sec_submissions_json

    captured: dict[str, object] = {}

    class _Response:
        status_code = 200

        @staticmethod
        def json() -> dict:
            return {"name": "Apple Inc.", "filings": {"recent": {"accessionNumber": []}}}

        @staticmethod
        def raise_for_status() -> None:
            return None

    def _fake_get(url: str, **kwargs):
        captured["url"] = url
        captured["headers"] = kwargs.get("headers")
        return _Response()

    monkeypatch.setattr("backend.app.datasources.fetch_ports.sec_edgar_port.httpx.get", _fake_get)
    payload = _fetch_sec_submissions_json("0000320193", user_agent="desk contact@example.com")

    assert payload["name"] == "Apple Inc."
    assert "data.sec.gov" in str(captured["url"])
    assert captured["headers"]["User-Agent"] == "desk contact@example.com"
