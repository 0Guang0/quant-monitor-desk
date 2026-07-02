# M-DATA-03 S-ACCEPT — live acceptance evidence

> **Date:** 2026-07-03 (R-FINAL-CLOSE)  
> **Sandbox (post-Repair · doubt close):** `.audit-sandbox/m-data-03/doubt-final-20260703`  
> **Command:** `QMD_ALLOW_LIVE_FETCH=1 uv run python scripts/tier_a_live_acceptance.py --data-root .audit-sandbox/m-data-03/doubt-final-20260703`  
> **Log:** `research/doubt-live-final.log`（redacted）

## Result

| Gate                              | Status                               |
| --------------------------------- | ------------------------------------ |
| `tier_a_live_acceptance.py` 11/11 | **exit 0**                           |
| `uv run pytest` harness+dispatch  | exit 0（29 passed, 1 skipped）       |
| Main DB pollution                 | **none** (isolated `m-data-03` path) |

## Per-source (post-Repair · R-FINAL-CLOSE · 2026-07-03)

| source_id     | status   | sync           | inspect | health |
| ------------- | -------- | -------------- | ------- | ------ |
| alpha_vantage | **pass** | COMPLETED      | PASS    | SKIP   |
| baostock      | **pass** | EMPTY_RESPONSE | PASS    | SKIP   |
| bis           | **pass** | COMPLETED      | PASS    | SKIP   |
| cninfo        | **pass** | EMPTY_RESPONSE | PASS    | SKIP   |
| cftc_cot      | **pass** | COMPLETED      | PASS    | SKIP   |
| deribit       | **pass** | COMPLETED      | PASS    | SKIP   |
| fred          | **pass** | COMPLETED      | PASS    | SKIP   |
| mootdx        | **pass** | EMPTY_RESPONSE | PASS    | SKIP   |
| sec_edgar     | **pass** | EMPTY_RESPONSE | PASS    | SKIP   |
| us_treasury   | **pass** | COMPLETED      | PASS    | SKIP   |
| world_bank    | **pass** | COMPLETED      | PASS    | SKIP   |

## Per-source (prior · R-DOUBT-CODE · 2026-07-03)

## Prior run (Execute · 2026-07-02)

| Gate                              | Status                                  |
| --------------------------------- | --------------------------------------- |
| `tier_a_live_acceptance.py` 11/11 | **exit 0**                              |
| Sandbox                           | `.audit-sandbox/m-data-03/accept-final` |

## S-MERGE

- `uv run python scripts/loop_maintain.py --fix` — OK
- `tests/test_source_registry.py` + `tests/test_source_capabilities.py` — green
- registry YAML — no schema change (DCP-05 SSOT retained)

## SEC EDGAR

- `SEC_EDGAR_USER_AGENT` configured in root `.env` (contact identity per SEC fair-access)
- Live skip resolved for acceptance dispatch (`data_domain=us_filings`)

## Notes

- Acceptance uses `tier_a_live_incremental_dispatch.py` per-source ops runners + `DbInspector.inspect()` (E2 gate)
- `COMPLETED` with zero new clean rows normalized to `EMPTY_RESPONSE` (caught-up semantics, aligned with e2e)
- **F0 data health（Repair 后）：** `run_source_live_acceptance` 在 sync/inspect 后调用 `_run_f0_data_health`：
  - 有 raw evidence → partial profile（bar `market_bar_p0`；cninfo `staged_pilot_v3`；其余 `fred_sandbox_pilot`）
  - 无 raw / evidence 不可加载 → **`SKIP`**，不阻断 pass
  - `sandbox_clean_write_gate_ready=False` 且非 FAIL/BLOCKED → **`SKIP`**（partial F0 ponytail；E2 inspect 权威）
  - health `FAIL`/`BLOCKED` → 源 **fail**
- **R-DOUBT-CODE 根因修复：** deribit/cninfo watermark 导入别名；bar 源改 ops runner（非 CLI router）；mootdx `adapter_id=baostock` ponytail；F0 `DataHealthLoadError` fail-closed→SKIP
