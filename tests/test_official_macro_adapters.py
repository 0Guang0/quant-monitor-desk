"""R3H-01 官方宏观/披露适配器测试（Batch 3H）。

覆盖范围：六源官方宏观与披露适配器（fred、us_treasury、sec_edgar、cftc_cot、bis、world_bank）
的 fetch port、证据契约、路由与 Layer smoke。
测试对象：backend/app/datasources/normalizers/official_macro.py 及兄弟 fetch port 模块。
目的/目标：证明六源可在 replay-first 路径下产出合规证据并满足 route/registry 终态。
验证点：各 step 子集（evidence_contract、fred_port、layer 等）按 EXECUTION_INDEX §1 通过。
失败含义：Batch 3H R3H-01 无法在 Round4 前闭合官方源生产入口决策。
"""

from __future__ import annotations

import json
from pathlib import Path

from backend.app.config import PROJECT_ROOT

_LIVE_FRED = (
    PROJECT_ROOT / "tests/fixtures/sandbox_clean_write/r3g01/live_wire/fred_live_fetch_evidence.json"
)
_PROMOTE_FRED = PROJECT_ROOT / "tests/fixtures/sandbox_clean_write/r3g01/fred/fred_evidence.json"


def test_bootSkeleton_testModuleLoads() -> None:
    """覆盖范围：Execute 9.0 测试模块骨架是否可加载
    测试对象：tests/test_official_macro_adapters.py 模块本身
    目的/目标：确认 R3H-01 专用测试文件已登记且 pytest 可收集
    验证点：本测试通过即表示骨架就绪，后续 9.1+ 可挂证据契约用例
    失败含义：Execute 无法在本模块追加六源适配器回归用例
    """
    assert True


def test_evidence_contract_livePayload_declaresOfficialMacroSchema(tmp_path: Path) -> None:
    """覆盖范围：FRED live 抓取证据经 normalizer 写出 promote 包
    测试对象：materialize_fred_evidence_from_live（official_macro normalizer）
    目的/目标：live 与 promote 共用 official_macro_evidence_v1，观测行用 observation_date
    验证点：schema_version==official_macro_evidence_v1；观测无 date 别名；无 DH sidecar
    失败含义：G10 未闭合，live 与 promote 字段仍靠 bridge 侧车与 date 别名硬凑
    """
    from backend.app.datasources.normalizers.official_macro import (
        OFFICIAL_MACRO_EVIDENCE_SCHEMA_VERSION,
        materialize_fred_evidence_from_live,
        read_fred_evidence_bundle,
    )

    out = tmp_path / "fred_promote"
    materialize_fred_evidence_from_live(_LIVE_FRED, out)
    bundle = read_fred_evidence_bundle(out)
    assert bundle["schema_version"] == OFFICIAL_MACRO_EVIDENCE_SCHEMA_VERSION
    assert len(bundle["observations"]) == 3
    for obs in bundle["observations"]:
        assert obs.get("observation_date")
        assert "date" not in obs
    assert not (out / "pilot_v2_closeout.json").is_file()
    assert not (out / "validation_report_summary.json").is_file()


def test_evidence_contract_writeReadRoundTrip_fixturePreservesFields(tmp_path: Path) -> None:
    """覆盖范围：既有 promote fixture 经 read/write 往返
    测试对象：write_fred_evidence_bundle + read_fred_evidence_bundle
    目的/目标：rehearsal_loader 与 bridge 读同一 canonical 形状，legacy date 升级 observation_date
    验证点：source_fetch_id、content_hash、as_of_timestamp、retrieved_at 保留；观测日期不丢
    失败含义：promote 链无法无损读写官方宏观证据，staging 行会缺日期或指纹
    """
    from backend.app.datasources.normalizers.official_macro import (
        read_fred_evidence_bundle,
        write_fred_evidence_bundle,
    )

    legacy = json.loads(_PROMOTE_FRED.read_text(encoding="utf-8"))
    out = tmp_path / "roundtrip"
    write_fred_evidence_bundle(out, legacy)
    bundle = read_fred_evidence_bundle(out)
    assert bundle["source_fetch_id"] == "fred-fetch-1"
    assert bundle["content_hash"] == "fred-hash-complete"
    assert bundle["as_of_timestamp"] == "2026-06-23T18:00:00Z"
    assert bundle["retrieved_at"] == "2026-06-23T18:00:00Z"
    assert bundle["observations"][0]["observation_date"] == "2024-01-02"


def test_evidence_contract_stagingRows_observationDateEndToEnd(tmp_path: Path) -> None:
    """覆盖范围：live → promote → rehearsal staging 行
    测试对象：materialize_fred_promote_evidence + staging_rows_from_bundle
    目的/目标：observation_date 从 live 经 normalizer 到 staging trade_date，无需字段重命名
    验证点：3 行 staging；DGS10×2 + VIXCLS×1；trade_date 来自 observation_date
    失败含义：FRED 官方宏观证据无法贯通 promote 预演链，G10/G14 仍开放
    """
    from backend.app.ops.sandbox_clean_write.live_evidence_bridge import (
        materialize_fred_promote_evidence,
    )
    from backend.app.ops.sandbox_clean_write.rehearsal_loader import (
        load_rehearsal_bundle,
        staging_rows_from_bundle,
    )
    from backend.app.ops.sandbox_clean_write.rehearsal_plan import RehearsalCandidate

    out = tmp_path / "fred"
    materialize_fred_promote_evidence(_LIVE_FRED, out)
    candidate = RehearsalCandidate(
        source_id="fred",
        domain="macro_series",
        operation="fetch_macro_series",
        symbols_or_series=("DGS10", "VIXCLS"),
        window_days=120,
    )
    bundle = load_rehearsal_bundle(candidate, evidence_dir=out, dry_run=False, cap_profile="r3g03")
    rows = staging_rows_from_bundle(
        bundle,
        batch_id="evidence-contract",
        max_rows=400,
        start_date="2026-01-01",
        end_date="2026-12-31",
    )
    assert len(rows) == 3
    dgs10 = [r for r in rows if r.instrument_id == "DGS10"]
    vix = [r for r in rows if r.instrument_id == "VIXCLS"]
    assert len(dgs10) == 2
    assert len(vix) == 1
    assert {r.trade_date for r in dgs10} == {"2026-06-25", "2026-06-24"}
    assert vix[0].trade_date == "2026-06-25"
