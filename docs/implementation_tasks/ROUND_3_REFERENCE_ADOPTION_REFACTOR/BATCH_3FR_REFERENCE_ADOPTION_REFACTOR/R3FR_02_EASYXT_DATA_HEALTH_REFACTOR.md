# R3FR-02 — EasyXT-Style Data Health Refactor

> **Batch:** Batch 3F-R — Mature Reference Adoption Refactor  
> **Module movement:** Data health engine must move from minimal read-only checks to a complete supported-profile read-only engine for Round 3G admission.  
> **Execution posture:** read-only validation/reporting only; no live fetch; no clean write.

---

## 1. Purpose

Replace the thin self-built `check_daily_bars` path with QMD-owned data-health profiles adapted from mature EasyXT data-integrity logic. This is not a one-rule micro-slice. This task must deliver the complete supported-profile engine needed by Round 3G.

Supported profile closure for this batch:

```text
market_bar_1d / market_bar_p0
```

The first implementation batch for this module already exists historically as minimal data health. Therefore this next batch must complete the main promised read-only health scope for supported profiles, not add one more isolated metric.

---

## 2. Reference source files

Read and adapt from:

```text
参考项目/EasyXT/data_manager/data_integrity_checker.py
参考项目/EasyXT/data_manager/smart_data_detector.py
```

Do not import these files at runtime.

---

## 3. What can be adapted directly into QMD-owned code

From `data_integrity_checker.py`:

- report object shape: errors/warnings/info summary;
- orchestration order: missing dates → null fields → price relations → outliers → volume anomalies;
- empty data failure;
- required OHLCV null checks;
- non-positive price checks;
- OHLC relation checks;
- extreme return warnings;
- volume anomaly warnings;
- compact report summary with capped detail rows.

From `smart_data_detector.py`:

- expected vs existing trading-day shape;
- missing trading-day list;
- continuous missing-date segment grouping;
- completeness ratio;
- first/last data date summary.

---

## 4. What must be rewritten

- Remove EasyXT DB path assumptions.
- Remove hardcoded table names such as `stock_daily`.
- Remove SQL string interpolation.
- Remove `sys.path.insert` and local project import assumptions.
- Replace EasyXT calendar examples with QMD calendar source/fixture/contract; if official calendar evidence is unavailable, return explicit WARN status rather than pretending authority.
- Replace EasyXT report classes with QMD data-health result types.
- Make rules profile-driven through `specs/contracts/data_quality_rules.yaml`.

---

## 5. Target QMD files

Create/update:

```text
backend/app/ops/data_health_profiles/__init__.py
backend/app/ops/data_health_profiles/ohlcv_rules.py
backend/app/ops/data_health_profiles/calendar_gap_rules.py
backend/app/ops/data_health_profiles/report_builder.py
backend/app/ops/data_health.py
specs/contracts/data_quality_rules.yaml
docs/ops/data_health_cli.md
tests/test_data_health_easyxt_profiles.py
tests/test_ops_data_health.py
```

If final file names differ, the PR must document the mapping.

---

## 6. Required rule coverage

The `market_bar_p0` profile must include all of these rule IDs or documented equivalent names in `data_quality_rules.yaml`:

```text
MISSING_TRADING_DAY
MISSING_REQUIRED_OHLCV_FIELD
NON_POSITIVE_PRICE
INVALID_OHLC
EXTREME_RETURN
VOLUME_OUTLIER
DUPLICATE_PRIMARY_KEY
INSUFFICIENT_HISTORY
MISSING_SOURCE_USED
```

Do not close this task by adding one or two metrics only.

---

## 7. Required API shape

Expose a QMD-owned profile runner that can be called by CLI and by Round 3G rehearsal code:

```python
run_data_health_profile(
    *,
    profile_id: str,
    domain: str,
    evidence_path: Path | None,
    db_path: Path | None,
    start_date: str | None,
    end_date: str | None,
    max_rows: int,
) -> DataHealthReport
```

The implementation may choose different names, but it must provide a single profile-runner boundary rather than scattered helpers.

---

## 8. Forbidden scope

- No production DB write.
- No live source fetch.
- No full-market scan.
- No full-history scan.
- No minute-bar expansion.
- No runtime import from `参考项目/**`.
- No hardcoded EasyXT DB/table assumptions.

---

## 9. Tests / gates

Required verification:

```bash
uv run pytest tests/test_data_health_easyxt_profiles.py tests/test_ops_data_health.py -q
uv run pytest tests/test_reference_adoption_guardrails.py -q
```

Test cases must include:

- empty dataset failure;
- duplicate primary key failure;
- missing required OHLCV field failure;
- non-positive price failure;
- invalid OHLC relation failure;
- extreme return warning;
- volume outlier warning;
- missing trading-day warning/failure according to calendar authority;
- capped report details;
- no runtime import from `参考项目/**`.

---

## 10. Done criteria

R3FR-02 is done only when the complete supported `market_bar_p0` profile is implemented and can be consumed by R3FR-06 CLI without another task. Partial one-rule extensions are not acceptable.
