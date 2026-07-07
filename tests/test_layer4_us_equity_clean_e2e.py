"""US_EQ Layer4 Tier A clean e2e (Execute S08-E2E)."""

from __future__ import annotations

from backend.app.layer4_markets.market_structure import (
    MarketStructureBuilder,
    _CLEAN_RULE_VERSION,
)
from tests.layer4_clean_e2e_support import (
    AS_OF,
    TRADE_DATE,
    bootstrap_layer4_clean_db,
    seed_us_breadth_fixture,
)


def test_layer4UsEquity_cleanRead_breadthSnapshot_e2e(tmp_path) -> None:
    """覆盖范围：US_EQ 从 replay clean bar + US 日历贯通 Layer4 breadth 快照
    测试对象：MarketStructureBuilder.build(source_mode=tier_a_clean)
    目的/目标：证明 US_EQ clean e2e 绿；source 不含 staged_fixture；breadth 可断言
    验证点：advancers==2；decliners==1；lineage 含 security_bar_1d；source 无 staged_fixture
    失败含义：Wave 4 G4 US_EQ Layer4 竖切未闭合，ACC-LAYER-E2E-LIVE-001 L4 无法关账
    """
    cm = bootstrap_layer4_clean_db(tmp_path)
    with cm.writer() as con:
        expected_adv, expected_dec, _ = seed_us_breadth_fixture(con)
        result = MarketStructureBuilder().build(
            market_id="US_EQ",
            trade_date=TRADE_DATE,
            as_of=AS_OF,
            source_mode="tier_a_clean",
            clean_con=con,
        )

    assert result.breadth_row.market_id == "US_EQ"
    assert result.breadth_row.trade_date == TRADE_DATE
    assert result.breadth_row.advancers == expected_adv
    assert result.breadth_row.decliners == expected_dec
    assert len(result.calendar_rows) == 1
    cal = result.calendar_rows[0]
    assert cal.is_trading_day is True
    assert cal.session_type == "regular"
    assert cal.timezone == "America/New_York"
    assert "staged_fixture" not in result.breadth_row.source
    assert "staged_fixture" not in result.calendar_rows[0].source
    assert "security_bar_1d" in "".join(result.lineage_envelope.source_dataset_ids)
    assert len(result.lineage_envelope.source_content_hashes) == 3
    assert any("batch-AAPL" in fid for fid in result.lineage_envelope.source_fetch_ids)
    assert result.lineage_envelope.rule_version == _CLEAN_RULE_VERSION
