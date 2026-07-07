from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from backend.app.ops.source_route_db_acceptance import SourceRouteDbAcceptanceSpine
from backend.app.ops.source_route_db_acceptance_matrix import (
    DOCUMENTED_SOURCE_MATRIX,
    evaluate_matrix_row_closure,
    find_matrix_target,
    iter_matrix_targets,
    matrix_target_key,
    validate_matrix_against_registry,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _matrix_data_root(tmp_path: Path) -> Path:
    root = tmp_path / ".audit-sandbox" / "source-route-db-test"
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_acceptanceHelperConsumers_strictMode_hasZeroProductRuntimeConsumers() -> None:
    """覆盖范围：旧 helper/smoke 严格门禁（SSOT）
    测试对象：scripts/check_acceptance_helper_consumers.py --strict 与 --strict-seam-inventory
    目的/目标：产品/runtime 零 consumer；seam inventory 关账
    验证点：strict 退出码 0；product_runtime_count/consumer_count 为 0；seam_inventory PASS
    失败含义：旧 helper 仍被产品路径调用，验收 PASS 语义会继续分裂
    """
    for extra in ([], ["--strict-seam-inventory"]):
        proc = subprocess.run(
            [
                sys.executable,
                "scripts/check_acceptance_helper_consumers.py",
                "--strict",
                *extra,
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
        if extra:
            assert payload["seam_inventory_status"] == "PASS"


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
    monkeypatch,
) -> None:
    """覆盖范围：validation 定位源的 execute 诚实性
    测试对象：SourceRouteDbAcceptanceSpine.execute for akshare validation target
    目的/目标：validation-only 源 live 授权后应产出合格非 primary clean 验收，而非 BLOCKED 失败
    验证点：status=PASS；write_grade=blocked；downstream=VALIDATION_ONLY；fake port raw 证据落盘
    失败含义：validation 源被误判为 BLOCKED 失败或静默写入 primary clean，矩阵 closure 不可通过
    """
    import json
    import uuid
    from dataclasses import dataclass

    from backend.app.datasources.adapters.fetch_port import FetchPayload
    from backend.app.datasources.fetch_result import FetchRequest

    @dataclass(frozen=True)
    class _AkshareValidationPort:
        def fetch_payload(self, req: FetchRequest) -> FetchPayload:
            bundle = {
                "schema_version": "cn_market_evidence_v1",
                "source_id": "akshare",
                "data_domain": req.data_domain,
                "bars": [
                    {
                        "instrument_id": "sh.600519",
                        "trade_date": "2026-06-15",
                        "open": 1400.0,
                        "high": 1410.0,
                        "low": 1395.0,
                        "close": 1405.0,
                        "volume": 1000.0,
                        "source_used": "akshare",
                    }
                ],
                "source_fetch_id": f"akshare-validation-{uuid.uuid4().hex[:8]}",
                "content_hash": f"validation-{uuid.uuid4().hex[:12]}",
            }
            return FetchPayload(
                content=json.dumps(bundle).encode("utf-8"),
                file_type="json",
                row_count=1,
            )

    def _fake_create_product_live_fetch_port(**_kwargs):
        return _AkshareValidationPort()

    target = find_matrix_target(
        next(t.request for t in iter_matrix_targets() if t.request.source_id == "akshare")
    )
    assert target is not None

    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setattr(
        "backend.app.ops.matrix_live_runners.create_product_live_fetch_port",
        _fake_create_product_live_fetch_port,
    )

    data_root = _matrix_data_root(tmp_path)
    report = SourceRouteDbAcceptanceSpine().execute(
        target.request,
        data_root=data_root,
        live_authorized=True,
    ).to_dict()

    assert report["status"] == "PASS"
    assert report["failure_class"] == "NONE"
    assert report["write_grade"] == "blocked"
    assert report["downstream_layer_read_status"] == "VALIDATION_ONLY"
    assert report["route_plan_id"] is not None
    assert report["implementation_mode"] == "live"
    assert list((data_root / "raw").rglob("*.json"))


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
        data_root=_matrix_data_root(tmp_path),
        live_authorized=False,
    )

    assert payload["matrix_count"] == 22
    assert payload["closure_status"] == "PASS"
    assert payload["closure_mode"] == "dry_run"
    assert payload["live_authorized"] is False
    assert all(row["closure_outcome"] == "PASS" for row in payload["rows"])


def test_sourceRouteDbAcceptanceMatrix_dryRunMatrix_skipsBulkRouteEvidencePersist(
    tmp_path: Path,
) -> None:
    """覆盖范围：dry-run 全矩阵 bulk 执行时的 DB 写入量
    测试对象：execute_documented_matrix(live_authorized=False)
    目的/目标：CI dry-run 须复用单次 bootstrap 且跳过 22 次 ROUTE_PLAN 写入，避免无意义的 writer 锁竞争
    验证点：closure 仍 PASS；job_event_log 无 ROUTE_PLAN 行
    失败含义：production_gate 每次 PR 做 22× migration + 22× route persist，CI 矩阵 gate 过慢
    """
    import duckdb

    from backend.app.ops.source_route_db_acceptance import ACCEPTANCE_DUCKDB_NAME
    from backend.app.ops.source_route_db_acceptance_matrix import execute_documented_matrix

    payload = execute_documented_matrix(
        SourceRouteDbAcceptanceSpine(),
        data_root=_matrix_data_root(tmp_path),
        live_authorized=False,
    )
    assert payload["closure_status"] == "PASS"
    db_path = _matrix_data_root(tmp_path) / "duckdb" / ACCEPTANCE_DUCKDB_NAME
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        route_count = con.execute(
            "SELECT COUNT(*) FROM job_event_log WHERE event_type = 'ROUTE_PLAN'"
        ).fetchone()[0]
    finally:
        con.close()
    assert route_count == 0


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
        data_root=_matrix_data_root(tmp_path),
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


def test_sourceRouteDbAcceptanceMatrix_checkerRejectsForgedClosureOutcomes(
    tmp_path: Path,
) -> None:
    """覆盖范围：checker 防篡改 closure_outcome 假绿
    测试对象：check_source_route_db_acceptance_matrix.py --strict --live-authorized
    目的/目标：即使 JSON 缓存 closure_outcome=PASS，也必须按 status/failure_class 重算
    验证点：全行 FAIL_EXTERNAL 但 closure_outcome=PASS 时 strict exit 1 且报 mismatch/violation
    失败含义：release gate 可被手工编辑报告绕过，CI 假绿
    """
    report_path = tmp_path / "forged-matrix.json"
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
    assert any("mismatch" in item for item in payload["closure_violations"])


def test_sourceRouteDbAcceptanceMatrix_liveClosure_allowsSecFailExternalClosurePass() -> None:
    """覆盖范围：SEC FAIL_EXTERNAL 的 external_deferred closure 语义
    测试对象：evaluate_matrix_row_closure(final_live_authorized)
    目的/目标：ADR-016 要求 SEC 矩阵行诚实 FAIL_EXTERNAL，但登记 external_deferred 时 closure PASS 不阻断 Slice 10
    验证点：sec_edgar 行 failure_class=FAIL_EXTERNAL → closure_outcome=PASS；status 仍为 FAIL
    失败含义：SEC 环境失败被 closure 误阻断关账，或矩阵行被 mock 成 PASS 假绿
    """
    sec_target = next(t for t in iter_matrix_targets() if t.request.source_id == "sec_edgar")
    row = {
        "status": "FAIL",
        "failure_class": "FAIL_EXTERNAL",
        "write_grade": "not_written",
        "errors": ["SSL EOF to data.sec.gov"],
    }
    outcome = evaluate_matrix_row_closure(
        sec_target,
        row,
        closure_mode="final_live_authorized",
    )
    assert outcome == "PASS"
    assert row["failure_class"] == "FAIL_EXTERNAL"


def test_sourceRouteDbAcceptanceMatrix_liveClosure_allowsDeferredValidationFailExternal(
) -> None:
    """覆盖范围：validation 源 external_deferred FAIL_EXTERNAL closure 语义
    测试对象：evaluate_matrix_row_closure(final_live_authorized)
    目的/目标：stooq geo block 等 validation 行须诚实 FAIL，但登记 external_deferred 时不阻断关账
    验证点：stooq validation 行 failure_class=FAIL_EXTERNAL → closure_outcome=PASS；status 仍为 FAIL
    失败含义：validation 源 replay 假绿或 geo 失败误阻断 Slice 10
    """
    stooq_target = next(t for t in iter_matrix_targets() if t.request.source_id == "stooq")
    row = {
        "status": "FAIL",
        "failure_class": "FAIL_EXTERNAL",
        "write_grade": "blocked",
        "errors": ["Stooq returned HTML instead of CSV (bot/geo block)"],
    }
    outcome = evaluate_matrix_row_closure(
        stooq_target,
        row,
        closure_mode="final_live_authorized",
    )
    assert outcome == "PASS"
    assert row["status"] == "FAIL"


def test_sourceRouteDbAcceptanceMatrix_liveClosure_blocksNonDeferredFailExternal() -> None:
    """覆盖范围：未登记 external_deferred 的 FAIL_EXTERNAL 仍阻断 closure
    测试对象：evaluate_matrix_row_closure(final_live_authorized)
    目的/目标：仅 sec_edgar 等登记源可 FAIL_EXTERNAL + closure PASS；其它源仍 FAIL_EXTERNAL 阻断
    验证点：fred 行 failure_class=FAIL_EXTERNAL → closure_outcome=FAIL_EXTERNAL
    失败含义：任意外部失败都可 closure PASS，Slice 10 假关账
    """
    fred_target = next(t for t in iter_matrix_targets() if t.request.source_id == "fred")
    row = {
        "status": "FAIL",
        "failure_class": "FAIL_EXTERNAL",
        "write_grade": "not_written",
        "errors": ["upstream timeout"],
    }
    outcome = evaluate_matrix_row_closure(
        fred_target,
        row,
        closure_mode="final_live_authorized",
    )
    assert outcome == "FAIL_EXTERNAL"


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
                "errors": ["gate:QMT_XTDATA_AUTHORIZED:missing for qmt_xtdata"],
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
                "errors": ["gate:THS_IFIND_LICENSE_ARTIFACT:missing for ths_ifind"],
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
                "errors": ["gate:QMT_XTDATA_AUTHORIZED:missing for qmt_xtdata"],
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
                "errors": ["gate:THS_IFIND_LICENSE_ARTIFACT:missing for ths_ifind"],
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
    验证点：cninfo=sh.600519；alpha_vantage=AAPL；kalshi=KXFED-27APR-T4.25
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
    验证点：status=PASS；failure_class=NONE；write_grade=not_written；raw 证据含 stub 诚实标记
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
        "backend.app.ops.matrix_live_runners.create_product_live_fetch_port",
        _fake_create_product_live_fetch_port,
    )
    target = next(t for t in iter_matrix_targets() if t.request.source_id == "coingecko")
    data_root = _matrix_data_root(tmp_path)
    report = SourceRouteDbAcceptanceSpine().execute(
        target.request,
        data_root=data_root,
        live_authorized=True,
    ).to_dict()

    assert report["status"] == "PASS"
    assert report["failure_class"] == "NONE"
    assert report["write_grade"] == "not_written"
    assert report["implementation_mode"] == "live"
    cg_raw = list((data_root / "raw" / "coingecko").rglob("*.json"))
    assert cg_raw
    raw_text = cg_raw[0].read_text(encoding="utf-8")
    assert "stub-" in raw_text
    assert '"content_hash": "stub"' in raw_text


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


def test_resolveMatrixEvidenceInstrumentId_usesSourceLiveDefaults() -> None:
    """覆盖范围：矩阵 validation fetch 默认 instrument SSOT
    测试对象：resolve_matrix_evidence_instrument_id
    目的/目标：未显式传 instrument_id 时必须从 SOURCE_LIVE_DEFAULTS 解析 bounded probe 符号
    验证点：mootdx → sh.600519；显式入参不被覆盖
    失败含义：validation 探针 missing instrument_id 导致矩阵 FAIL_EXTERNAL
    """
    from backend.app.ops.matrix_live_runners import resolve_matrix_evidence_instrument_id

    assert resolve_matrix_evidence_instrument_id("mootdx") == "sh.600519"
    assert resolve_matrix_evidence_instrument_id("mootdx", "sz.000001") == "sz.000001"


def test_normalizeIncrementalJobStatus_liveEmptyFetchMapsToEmptyResponse() -> None:
    """覆盖范围：live fetch 追平空窗时的 orchestrator 状态归一
    测试对象：macro_incremental_common._normalize_incremental_job_status
    目的/目标：FRED/World Bank live 空响应须映射 EMPTY_RESPONSE 而非 FAILED_FINAL
    验证点：FRED no usable rows、WB no rows for、deribit watermark window → EMPTY_RESPONSE
    失败含义：矩阵复跑已有 sandbox 时 honest 追平被误判 FAIL_EXTERNAL
    """
    from types import SimpleNamespace

    from backend.app.ops.macro_incremental_common import _normalize_incremental_job_status

    cases = (
        "FRED returned no usable rows for DGS10",
        "World Bank returned no rows for US/NY.GDP.MKTP.CD",
        "no instruments after deribit watermark window",
    )
    for message in cases:
        result = SimpleNamespace(status="FAILED_FINAL", message=message)
        assert _normalize_incremental_job_status(result) == "EMPTY_RESPONSE"


def test_matrixIncrementalLiveReportBuilder_emptyResponseWithExistingCleanRows_passes() -> None:
    """覆盖范围：矩阵 incremental live 报告 builder 在追平复跑时的 PASS 语义
    测试对象：source_route_db_acceptance._matrix_incremental_live_report（纯 report builder，无 DB）
    目的/目标：sync_status=EMPTY_RESPONSE 且 rows_written>0 时须 PASS（非 FAIL_EXTERNAL）
    验证点：status=PASS、failure_class=NONE；job_id=None 时不触达 cm
    失败含义：Slice 10 在复用 acceptance DB 时 fred/world_bank/deribit 假红
    """
    from backend.app.ops.source_route_db_acceptance import (
        AcceptanceRequest,
        _matrix_incremental_live_report,
    )

    target = next(t for t in iter_matrix_targets() if t.request.source_id == "world_bank")
    request = AcceptanceRequest(
        data_domain=target.request.data_domain,
        source_id=target.request.source_id,
        operation=target.request.operation,
    )
    report = _matrix_incremental_live_report(
        request,
        {"route_plan_id": "plan-1", "selected_source_id": "world_bank", "route_grade": "primary"},
        cm=object(),  # type: ignore[arg-type]
        matrix_target=target,
        sync_status="EMPTY_RESPONSE",
        rows_written=12,
        job_id=None,
    )
    assert report.status == "PASS"
    assert report.failure_class == "NONE"


def test_deribitLiveFetchPort_acceptsLiveResolvedInstrument(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：Deribit live 矩阵 instrument 白名单
    测试对象：DeribitLiveFetchPort.fetch_payload
    目的/目标：live 解析出的当前期权名不得被静态 replay whitelist 拒绝
    验证点：mock _live_instruments/_book_summary 后 live 期权名可 fetch
    失败含义：resolve_matrix_deribit_live_instrument 与 fetch 白名单冲突 → rows_written=0
    """
    import json

    from backend.app.datasources.fetch_ports.deribit_port import DeribitLiveFetchPort
    from backend.app.datasources.fetch_result import FetchRequest

    active = "BTC-8JUL26-55000-C"
    port = DeribitLiveFetchPort(instruments=(active,), max_surface_rows=3)
    req = FetchRequest(
        run_id="deribit-live-test",
        source_id="deribit",
        data_domain="crypto_options_surface",
        instrument_id=active,
    )
    monkeypatch.setattr(
        DeribitLiveFetchPort,
        "_live_instruments",
        lambda self: [{"instrument_name": active, "mark_iv": 0.5, "source_used": "deribit"}],
    )
    monkeypatch.setattr(DeribitLiveFetchPort, "_book_summary_mark_iv", lambda self, _name: 0.5)
    payload = port.fetch_payload(req)
    bundle = json.loads(payload.content.decode("utf-8"))
    assert bundle["instruments"][0]["instrument_name"] == active


def test_secEdgar_fetchSubmissions_usesHttpx2Client(monkeypatch) -> None:
    """覆盖范围：SEC submissions live HTTP 客户端
    测试对象：_fetch_sec_submissions_json
    目的/目标：live fetch 应走 httpx2 Client（非 urllib），并带 fair-access User-Agent
    验证点：client.get 被调用；返回 JSON dict
    失败含义：urllib SSL/EOF 导致矩阵 NETWORK_ERROR 无法恢复
    """
    from backend.app.datasources.fetch_ports import sec_edgar_port
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

    class _Client:
        def get(self, url: str, **kwargs):
            captured["url"] = url
            captured["headers"] = kwargs.get("headers")
            return _Response()

    monkeypatch.setattr(sec_edgar_port, "_sec_http_client", lambda: _Client())
    payload = _fetch_sec_submissions_json("0000320193", user_agent="desk contact@example.com")

    assert payload["name"] == "Apple Inc."
    assert "data.sec.gov" in str(captured["url"])
    assert captured["headers"]["User-Agent"] == "desk contact@example.com"
    assert "@" in str(captured["headers"]["User-Agent"])


def test_sourceRouteDbAcceptanceMatrix_qualificationPlaceholder_blocksLiveExecute(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """覆盖范围：qualification_deferred 源占位 env 不得 auto PASS
    测试对象：execute for ths_ifind with placeholder license artifact
    目的/目标：THS_IFIND_LICENSE_ARTIFACT=1 须 BLOCKED，不得走 qualified_non_primary PASS
    验证点：failure_class=BLOCKED；errors 含 placeholder
    失败含义：占位 env 绕过 license 探针，矩阵假绿
    """
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setenv("THS_IFIND_LICENSE_ARTIFACT", "1")
    target = next(t for t in iter_matrix_targets() if t.request.source_id == "ths_ifind")
    report = SourceRouteDbAcceptanceSpine().execute(
        target.request,
        data_root=_matrix_data_root(tmp_path),
        live_authorized=True,
    ).to_dict()

    assert report["failure_class"] == "BLOCKED"
    assert report["status"] == "FAIL"
    assert any("placeholder" in err.lower() for err in report["errors"])


@pytest.mark.network
def test_sourceRouteDbAcceptanceMatrix_baostockSampleExecute_networkSubset(
    tmp_path: Path,
) -> None:
    """覆盖范围：矩阵 primary 源 live 子集（TD-05）
    测试对象：SourceRouteDbAcceptanceSpine.execute for baostock（无 API key）
    目的/目标：@pytest.mark.network 子集证明 matrix live handler 可真网 fetch
    验证点：live_authorized + QMD_ALLOW_LIVE_FETCH 时 status/failure_class 诚实（PASS 或 FAIL_EXTERNAL）
    失败含义：矩阵 live 路径在真网环境完全未覆盖，回归 silent
    """
    import os

    if os.environ.get("QMD_ALLOW_LIVE_FETCH") != "1":
        pytest.skip("QMD_ALLOW_LIVE_FETCH required for matrix network subset")

    target = next(t for t in iter_matrix_targets() if t.request.source_id == "baostock")
    report = SourceRouteDbAcceptanceSpine().execute(
        target.request,
        data_root=_matrix_data_root(tmp_path),
        live_authorized=True,
    ).to_dict()

    assert report["implementation_mode"] == "live"
    assert report["failure_class"] in {"NONE", "FAIL_EXTERNAL", "BLOCKED"}
    assert report["status"] in {"PASS", "FAIL"}


def test_sourceRouteDbAcceptanceSpine_execute_rejectsNonSandboxDataRoot(
    tmp_path: Path,
) -> None:
    """覆盖范围：spine 隔离 segment 负例（CR-03 / TD-02）
    测试对象：SourceRouteDbAcceptanceSpine.execute with /tmp 非沙箱路径
    目的/目标：非 .audit-sandbox/source-route-db 路径须 CONTRACT_VIOLATION，不得 bootstrap DB
    验证点：failure_class=CONTRACT_VIOLATION；errors 非空
    失败含义：任意路径可跑矩阵，ADR-015 隔离边界失效
    """
    target = next(t for t in iter_matrix_targets() if t.request.source_id == "baostock")
    bad_root = tmp_path / "not-audit-sandbox"
    bad_root.mkdir(parents=True, exist_ok=True)

    report = SourceRouteDbAcceptanceSpine().execute(
        target.request,
        data_root=bad_root,
        live_authorized=False,
    ).to_dict()

    assert report["failure_class"] == "CONTRACT_VIOLATION"
    assert report["status"] == "FAIL"
    assert report["errors"]


def test_sourceRouteDbAcceptanceMatrix_qmtPlaceholderEnv_blocksAutoPass(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """覆盖范围：qualification_deferred 源占位 env 不得 auto PASS（CR-05）
    测试对象：execute for qmt_xtdata with QMT_XTDATA_AUTHORIZED=1
    目的/目标：占位 env 须 BLOCKED，不得进入 evidence fetch 假 PASS
    验证点：failure_class=BLOCKED；errors 含 placeholder
    失败含义：QMT 占位 env 绕过终端资格探针
    """
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setenv("QMT_XTDATA_AUTHORIZED", "1")
    target = next(t for t in iter_matrix_targets() if t.request.source_id == "qmt_xtdata")
    report = SourceRouteDbAcceptanceSpine().execute(
        target.request,
        data_root=_matrix_data_root(tmp_path),
        live_authorized=True,
    ).to_dict()

    assert report["failure_class"] == "BLOCKED"
    assert report["status"] == "FAIL"
    assert any("placeholder" in err.lower() for err in report["errors"])
