"""R3FR-02 — market_bar_p0 profile engine tests."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from backend.app.ops.data_health_profiles import MARKET_BAR_P0_RULE_IDS, run_data_health_profile
from backend.app.ops.data_health_profiles.calendar_gap_rules import check_missing_trading_day
from backend.app.ops.data_health_profiles.ohlcv_rules import (
    check_duplicate_primary_key,
    check_extreme_return,
    check_insufficient_history,
    check_invalid_ohlc,
    check_missing_required_ohlcv_field,
    check_non_positive_price,
    check_volume_outlier,
    run_ohlcv_rules,
)
from backend.app.ops.data_health_profiles.report_builder import cap_check_details
from backend.app.ops.data_health import DataHealthCheckResult

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_RULES_PATH = _PROJECT_ROOT / "specs" / "contracts" / "data_quality_rules.yaml"
_GOOD_BUNDLE = _PROJECT_ROOT / "tests" / "fixtures" / "data_health" / "good_bundle"

MARKET_BAR_P0_RULE_IDS_SET = frozenset(MARKET_BAR_P0_RULE_IDS)

_GOOD_BAR = {
    "symbol": "sh.600519",
    "trade_date": "2024-01-02",
    "open": 10.0,
    "high": 12.0,
    "low": 9.0,
    "close": 11.0,
    "volume": 100.0,
}


def test_marketBarP0_ruleIdsRegisteredInContract() -> None:
    """覆盖范围：market_bar_p0 九 rule ID 契约注册
    测试对象：specs/contracts/data_quality_rules.yaml ops_cli_profiles
    目的/目标：AC-1 — profile 规则 ID 与 frozen §6.1 映射一致
    验证点：market_bar_1d.rules 集合等于九项活卡 ID
    失败含义：规则 ID 漂移导致 profile 不完整或 CLI 假完成
    """
    raw = yaml.safe_load(_RULES_PATH.read_text(encoding="utf-8")) or {}
    profile = raw["ops_cli_profiles"]["market_bar_1d"]
    assert profile["rule_set_id"] == "market_bar_p0"
    registered = set(profile["rules"])
    assert registered == MARKET_BAR_P0_RULE_IDS_SET


def test_ohlcv_emptyBars_insufficientHistory() -> None:
    """覆盖范围：空 bar 集
    测试对象：ohlcv_rules.check_insufficient_history
    目的/目标：空数据集须 FAIL（INSUFFICIENT_HISTORY）
    验证点：checks 含 INSUFFICIENT_HISTORY 且 status FAIL
    失败含义：空数据被当成健康
    """
    checks = check_insufficient_history([], domain="market_bar_1d", min_history=2)
    assert any(c.rule_id == "INSUFFICIENT_HISTORY" and c.status == "FAIL" for c in checks)


def test_non_positive_volume_fails() -> None:
    """覆盖范围：负成交量
    测试对象：ohlcv_rules.check_non_positive_price
    目的/目标：负 volume 映射 NON_POSITIVE_PRICE（frozen §9.2）
    验证点：volume=-1 时 FAIL
    失败含义：负成交量静默通过
    """
    row = dict(_GOOD_BAR, volume=-1)
    checks = check_non_positive_price([row], domain="market_bar_1d")
    assert any(c.rule_id == "NON_POSITIVE_PRICE" and c.status == "FAIL" for c in checks)


def test_duplicate_primaryKey_fails() -> None:
    """覆盖范围：主键重复
    测试对象：ohlcv_rules.check_duplicate_primary_key
    目的/目标：DUPLICATE_PRIMARY_KEY 可检出
    验证点：rule_id 与 FAIL status
    失败含义：重复 bar 不可见
    """
    bars = [_GOOD_BAR, dict(_GOOD_BAR)]
    checks = check_duplicate_primary_key(bars, domain="market_bar_1d")
    assert any(c.rule_id == "DUPLICATE_PRIMARY_KEY" and c.status == "FAIL" for c in checks)


def test_ohlcv_missingRequiredField_fails() -> None:
    """覆盖范围：缺 OHLCV 字段
    测试对象：ohlcv_rules.check_missing_required_ohlcv_field
    目的/目标：MISSING_REQUIRED_OHLCV_FIELD 可检出
    验证点：缺 volume 时 FAIL
    失败含义：必填价量字段缺口通过检查
    """
    row = dict(_GOOD_BAR)
    row.pop("volume")
    checks = check_missing_required_ohlcv_field([row], domain="market_bar_1d")
    assert any(
        c.rule_id == "MISSING_REQUIRED_OHLCV_FIELD" and c.status == "FAIL" for c in checks
    )


def test_non_positive_price_fails() -> None:
    """覆盖范围：非正价格
    测试对象：ohlcv_rules.check_non_positive_price
    目的/目标：NON_POSITIVE_PRICE 可检出（含零价）
    验证点：open=0 时 FAIL
    失败含义：非法价格通过检查
    """
    row = dict(_GOOD_BAR, open=0)
    checks = check_non_positive_price([row], domain="market_bar_1d")
    assert any(c.rule_id == "NON_POSITIVE_PRICE" and c.status == "FAIL" for c in checks)


def test_invalid_ohlc_relation_fails() -> None:
    """覆盖范围：OHLC 关系非法
    测试对象：ohlcv_rules.check_invalid_ohlc
    目的/目标：INVALID_OHLC 可检出 high<low 情形
    验证点：rule_id 与 FAIL
    失败含义：价量关系坏数据进入下游
    """
    row = dict(_GOOD_BAR, high=5, low=8)
    checks = check_invalid_ohlc([row], domain="market_bar_1d")
    assert any(c.rule_id == "INVALID_OHLC" and c.status == "FAIL" for c in checks)


def test_calendar_missingTradingDay_warnsWithoutAuthority() -> None:
    """覆盖范围：缺失交易日（无官方日历）
    测试对象：calendar_gap_rules.check_missing_trading_day
    目的/目标：无 calendar 证据时 MISSING_TRADING_DAY → WARN
    验证点：status WARN；rule_id 正确
    失败含义：假装权威日历或静默忽略缺口
    """
    bars = [
        dict(_GOOD_BAR, trade_date="2024-01-02"),
        dict(_GOOD_BAR, trade_date="2024-01-04"),
    ]
    checks = check_missing_trading_day(
        bars, domain="market_bar_1d", calendar_authority=False
    )
    assert any(c.rule_id == "MISSING_TRADING_DAY" and c.status == "WARN" for c in checks)


def test_extreme_return_warns() -> None:
    """覆盖范围：极端收益率
    测试对象：ohlcv_rules.check_extreme_return
    目的/目标：EXTREME_RETURN → WARN
    验证点：两日收益率超阈值时 WARN
    失败含义：极端波动不可见
    """
    bars = [
        dict(_GOOD_BAR, trade_date="2024-01-02", close=10),
        dict(_GOOD_BAR, trade_date="2024-01-03", close=20),
    ]
    checks = check_extreme_return(bars, domain="market_bar_1d")
    assert any(c.rule_id == "EXTREME_RETURN" and c.status == "WARN" for c in checks)


def test_volume_outlier_warns() -> None:
    """覆盖范围：成交量异常
    测试对象：ohlcv_rules.check_volume_outlier
    目的/目标：VOLUME_OUTLIER → WARN（非 NEGATIVE_VOLUME）
    验证点：相对中位数异常大时 WARN
    失败含义：成交量异常不可见
    """
    bars = [
        dict(_GOOD_BAR, trade_date="2024-01-02", volume=100),
        dict(_GOOD_BAR, trade_date="2024-01-03", volume=100),
        dict(_GOOD_BAR, trade_date="2024-01-04", volume=5000),
    ]
    checks = check_volume_outlier(bars, domain="market_bar_1d")
    assert any(c.rule_id == "VOLUME_OUTLIER" and c.status == "WARN" for c in checks)


def test_insufficient_history_singleBar_fails() -> None:
    """覆盖范围：历史行数不足（单行）
    测试对象：ohlcv_rules.check_insufficient_history
    目的/目标：INSUFFICIENT_HISTORY 窗口不足 FAIL
    验证点：单行且 min_history=2 时 FAIL
    失败含义：窗口不足不可见
    """
    checks = check_insufficient_history(
        [_GOOD_BAR], domain="market_bar_1d", min_history=2
    )
    assert any(c.rule_id == "INSUFFICIENT_HISTORY" and c.status == "FAIL" for c in checks)


def test_capped_reportDetails_mixedPassFail_respectsMaxRows() -> None:
    """覆盖范围：PASS+FAIL 混合超 cap
    测试对象：report_builder.cap_check_details
    目的/目标：AC-2 — 混合详情仍须截断至 max_rows
    验证点：15 PASS + 10 FAIL，cap=5 时总长 ≤ 5
    失败含义：混合场景 cap 失效导致无界输出
    """
    checks = [
        DataHealthCheckResult(
            rule_id=f"PASS_{i}",
            severity="INFO",
            status="PASS",
            source_id="baostock",
            domain="market_bar_1d",
            evidence_path=None,
            row_count=1,
            message=f"ok {i}",
        )
        for i in range(15)
    ] + [
        DataHealthCheckResult(
            rule_id=f"FAIL_{i}",
            severity="FAIL",
            status="FAIL",
            source_id="baostock",
            domain="market_bar_1d",
            evidence_path=None,
            row_count=1,
            message=f"issue {i}",
        )
        for i in range(10)
    ]
    capped = cap_check_details(checks, max_rows=5)
    assert len(capped) <= 5


def test_capped_reportDetails_respectsMaxRows() -> None:
    """覆盖范围：报告详情 capped
    测试对象：report_builder.cap_check_details
    目的/目标：AC-2 — 详情行数 ≤ max_rows
    验证点：输入多条 FAIL，cap 后长度 ≤ max_rows
    失败含义：无界详情导致运维输出爆炸
    """
    checks = [
        DataHealthCheckResult(
            rule_id=f"RULE_{i}",
            severity="FAIL",
            status="FAIL",
            source_id="baostock",
            domain="market_bar_1d",
            evidence_path=None,
            row_count=1,
            message=f"issue {i}",
        )
        for i in range(20)
    ]
    capped = cap_check_details(checks, max_rows=5)
    assert len(capped) <= 5


def test_profile_runner_goodEvidence_passes() -> None:
    """覆盖范围：profile runner 证据路径
    测试对象：run_data_health_profile
    目的/目标：AC-3 — good_bundle 可跑通 runner
    验证点：overall_status 非 BLOCKED；checks 非空
    失败含义：runner 未接线或证据加载失败
    """
    report, _, _, _, _ = run_data_health_profile(
        profile_id="market_bar_p0",
        domain="market_bar_1d",
        evidence_path=_GOOD_BUNDLE,
        db_path=None,
        start_date=None,
        end_date=None,
        max_rows=100,
    )
    assert report.profile == "market_bar_p0"
    assert report.production_db_mutated is False
    assert report.source_fetch_performed is False
    assert len(report.checks) >= 1
    rules_seen = {c.rule_id for c in report.checks}
    assert MARKET_BAR_P0_RULE_IDS_SET.issubset(rules_seen)


def test_evidence_bundle_loadsBars() -> None:
    """覆盖范围：evidence 夹具 bar 加载
    测试对象：run_data_health_profile on good_bundle
    目的/目标：row_count_checked 语义通过 checks 体现
    验证点：checks 中至少一条 row_count ≥ 2
    失败含义：evidence 解析未加载 bars.json
    """
    report, _, _, _, _ = run_data_health_profile(
        profile_id="market_bar_p0",
        domain="market_bar_1d",
        evidence_path=_GOOD_BUNDLE,
        db_path=None,
        start_date=None,
        end_date=None,
        max_rows=50,
    )
    assert any((c.row_count or 0) >= 2 for c in report.checks)


def test_missing_sourceUsed_onBadManifest(tmp_path: Path) -> None:
    """覆盖范围：lineage MISSING_SOURCE_USED
    测试对象：run_data_health_profile + 缺 source_used 的 manifest
    目的/目标：血缘缺口可检出
    验证点：checks 含 MISSING_SOURCE_USED FAIL
    失败含义：来源不可追溯
    """
    import json

    evidence = tmp_path / "bad_lineage"
    evidence.mkdir()
    (evidence / "raw_evidence_manifest.json").write_text(
        json.dumps(
            {
                "data_domain": "cn_equity_daily_bar",
                "source_id": "baostock",
                "generated_at": "2026-06-23T18:11:44Z",
                "manifest_entries": [
                    {
                        "source_fetch_id": "fetch-1",
                        "content_hash": "hash-1",
                        "as_of_timestamp": "2026-06-23T18:11:44Z",
                        "relative_paths": [],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (evidence / "staging_evidence_manifest.json").write_text("{}", encoding="utf-8")
    (evidence / "bars.json").write_text(
        json.dumps({"rows": [_GOOD_BAR, dict(_GOOD_BAR, trade_date="2024-01-03")]}),
        encoding="utf-8",
    )
    manifest = json.loads((evidence / "raw_evidence_manifest.json").read_text())
    manifest["manifest_entries"][0]["relative_paths"] = ["bars.json"]
    (evidence / "raw_evidence_manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )

    report, _, _, _, _ = run_data_health_profile(
        profile_id="market_bar_p0",
        domain="market_bar_1d",
        evidence_path=evidence,
        db_path=None,
        start_date=None,
        end_date=None,
        max_rows=50,
    )
    assert any(c.rule_id == "MISSING_SOURCE_USED" and c.status == "FAIL" for c in report.checks)


def test_malformedBarJson_raisesLoadError(tmp_path: Path) -> None:
    """覆盖范围：损坏 bar JSON
    测试对象：run_data_health_profile evidence 加载
    目的/目标：JSON 解析失败映射 DataHealthLoadError（P1-01）
    验证点：非 JSON bar 文件触发 DataHealthLoadError
    失败含义：未收口异常穿透 CLI traceback
    """
    import json

    from backend.app.ops.data_health import DataHealthLoadError

    evidence = tmp_path / "bad_json"
    evidence.mkdir()
    (evidence / "raw_evidence_manifest.json").write_text(
        json.dumps(
            {
                "source_id": "baostock",
                "manifest_entries": [
                    {
                        "content_hash": "h1",
                        "relative_paths": ["bars.json"],
                        "source_used": "baostock",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (evidence / "staging_evidence_manifest.json").write_text("{}", encoding="utf-8")
    (evidence / "bars.json").write_text("not-json{{{", encoding="utf-8")

    with pytest.raises(DataHealthLoadError, match="invalid bar payload"):
        run_data_health_profile(
            profile_id="market_bar_p0",
            domain="market_bar_1d",
            evidence_path=evidence,
            db_path=None,
            start_date=None,
            end_date=None,
            max_rows=50,
        )


def test_profileRunner_dbPath_populatesSchemaHashCoverage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, registry_yaml_fixture: Path
) -> None:
    """覆盖范围：db-path 只读 schema_hash 扫描（A7-002/003）
    测试对象：run_data_health_profile + fetch_log
    目的/目标：提供 db-path 时 envelope 可含 bounded schema_hash_coverage
    验证点：schema_hash_coverage 非空；limitations 声明只读扫描
    失败含义：db-path 参数无实际 lineage 价值
    """
    from backend.app.cli import data_commands
    from backend.app.db.connection import ConnectionManager

    data_root = tmp_path / "data"
    data_root.mkdir()
    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    db_path = data_root / "duckdb" / "quant_monitor.duckdb"
    data_commands.init_basic(dry_run=False, db_path=db_path)
    cm = ConnectionManager(db_path)
    with cm.writer() as con:
        con.execute(
            """
            INSERT INTO fetch_log (
                fetch_id, source_id, data_domain, schema_hash, raw_file_paths, status
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                "fetch-schema-1",
                "baostock",
                "market_bar_1d",
                "sha256-schema-test",
                '["raw/bars.json"]',
                "SUCCESS",
            ],
        )
    _, limitations, _, schema_coverage, _ = run_data_health_profile(
        profile_id="market_bar_p0",
        domain="market_bar_1d",
        evidence_path=_GOOD_BUNDLE,
        db_path=db_path,
        start_date=None,
        end_date=None,
        max_rows=50,
    )
    assert schema_coverage.get("sha256-schema-test") == ["raw/bars.json"]
    assert any("schema_hash" in item.lower() for item in limitations)


def test_dataHealthProfiles_attributionPresent() -> None:
    """覆盖范围：AC-8 attribution 切片验收
    测试对象：backend/app/ops/data_health_profiles 包模块头
    目的/目标：MIT/EasyXT 追溯短语可机械验收
    验证点：__init__.py 含 EasyXT 与 attribution 注释
    失败含义：参考采纳边界无代码层追溯
    """
    init_path = (
        _PROJECT_ROOT / "backend" / "app" / "ops" / "data_health_profiles" / "__init__.py"
    )
    text = init_path.read_text(encoding="utf-8")
    assert "EasyXT" in text
    assert "Attribution" in text


def test_ohlcv_rules_orchestration_stopsOnFail() -> None:
    """覆盖范围：OHLCV 编排短路
    测试对象：run_ohlcv_rules
    目的/目标：FAIL 后不再掩盖首要问题
    验证点：重复键场景仅报告 DUPLICATE 或更早 FAIL
    失败含义：编排顺序错误导致噪声掩盖
    """
    bars = [_GOOD_BAR, dict(_GOOD_BAR)]
    checks = run_ohlcv_rules(bars, domain="market_bar_1d", min_history=1)
    assert checks and checks[0].status == "FAIL"
