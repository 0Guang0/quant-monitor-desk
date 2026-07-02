# 执行索引 — M-DATA-03 Tier A live acceptance（Plan v4.1）

> Execute 首读：`research/00-EXECUTION-ENTRY.md`

## 0. 冻结元数据

| 字段          | 值                                                                         |
| ------------- | -------------------------------------------------------------------------- |
| slug          | `m-data-03-tier-a-live`                                                    |
| protocol      | `4.1`                                                                      |
| execute_entry | `research/00-EXECUTION-ENTRY.md`                                           |
| source_card   | `docs/implementation_tasks/M_DATA_03_TIER_A_LIVE/M_DATA_03_TIER_A_LIVE.md` |
| frozen_card   | `frozen/M_DATA_03_TIER_A_LIVE.md`                                          |
| ADR           | `docs/decisions/ADR-034-m-data-03-tier-a-live-acceptance.md`               |

## 1. 步骤与证据（Execute · v4.1 code-first）

| Step     | 切片             | RED / GREEN 证据                                                              |
| -------- | ---------------- | ----------------------------------------------------------------------------- |
| 9.0      | S00-ELIGIBILITY  | `research/tier-a-live-eligibility.md` [x]                                     |
| 9.1      | S00-INFRA        | `tests/test_tier_a_live_harness.py` · `scripts/tier_a_live_acceptance.py` [x] |
| 9.2      | S-LIVE-FRED      | `tests/test_fred_macro_incremental_e2e.py` `-m network` RED→GREEN [x]         |
| 9.3      | S-LIVE-BAOSTOCK  | `tests/test_baostock_incremental_e2e.py` `-m network` RED→GREEN [x]           |
| 9.4–9.12 | S-LIVE-\* (9 源) | 见 §2 十一源 e2e · `-m network` RED→GREEN [x]                                 |
| 9.13     | S-MERGE          | `loop_maintain` · registry tests GREEN [x]                                    |
| 9.14     | S-ACCEPT         | `scripts/tier_a_live_acceptance.py` exit 0 GREEN [x]                          |

切片 AC SSOT：`research/to-issues-slices.md`

## 2. AC ↔ 测试

| AC             | 验证                                                                    |
| -------------- | ----------------------------------------------------------------------- |
| AC-LIVE-11     | 11/11 各源 e2e `-m network`（默认 `pytest -q` skip）                    |
| AC-HARNESS     | `tests/test_tier_a_live_harness.py` 负向 3 项                           |
| AC-DISPATCH    | `tests/test_tier_a_live_dispatch.py`                                    |
| AC-CLI         | `scripts/tier_a_live_acceptance.py` exit 0/1/2                          |
| AC-E2-INSPECT  | S-ACCEPT · `DbInspector.inspect()` PASS/WARN（见 `plan-spec.md` F0/E2） |
| AC-FULL-PYTEST | `uv run pytest -q`                                                      |

十一源 e2e：`tests/test_fred_macro_incremental_e2e.py` · `tests/test_baostock_incremental_e2e.py` · `tests/test_us_treasury_incremental_e2e.py` · `tests/test_bis_incremental_e2e.py` · `tests/test_world_bank_incremental_e2e.py` · `tests/test_cftc_incremental_e2e.py` · `tests/test_sec_edgar_incremental_e2e.py` · `tests/test_alpha_vantage_incremental_e2e.py` · `tests/test_deribit_incremental_e2e.py` · `tests/test_cninfo_incremental_e2e.py` · `tests/test_mootdx_incremental_e2e.py`

### 2.1 Tier 复验（Repair / Audit 关账）

| Tier                   | 命令                                                                                                                               | 用途                                                         |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| harness                | `uv run pytest tests/test_tier_a_live_harness.py tests/test_tier_a_live_dispatch.py -q`                                            | S00-INFRA + dispatch 集成                                    |
| 全量                   | `uv run pytest -q`                                                                                                                 | PASS 门槛                                                    |
| loop                   | `uv run python scripts/loop_maintain.py`                                                                                           | S-MERGE registry 三件套                                      |
| handoff                | `python .trellis/scripts/task.py validate-execute-handoff .trellis/tasks/m-data-03-tier-a-live`                                    | Trellis v4.1 关账                                            |
| live 11/11 post-Repair | `QMD_ALLOW_LIVE_FETCH=1 uv run python scripts/tier_a_live_acceptance.py --data-root .audit-sandbox/m-data-03/doubt-final-20260703` | **exit 0** · 11/11 pass（R-FINAL-CLOSE · D-01 · 2026-07-03） |

## 3. 必须读原文（manifest · 索引完整）

| path                                                                            | manifest  | audience | for      |
| ------------------------------------------------------------------------------- | --------- | -------- | -------- |
| `docs/decisions/ADR-034-m-data-03-tier-a-live-acceptance.md`                    | must-read | both     | S00+     |
| `docs/decisions/ADR-027-product-live-fetch-gate.md`                             | must-read | both     | S00+     |
| `docs/decisions/ADR-028-dcp05-tier-a-clean-domain-extension.md`                 | must-read | both     | live     |
| `docs/implementation_tasks/M_DATA_03_TIER_A_LIVE/M_DATA_03_TIER_A_LIVE.md`      | must-read | both     | BOOT     |
| `.trellis/tasks/m-data-03-tier-a-live/research/plan-spec.md`                    | must-read | both     | S00+     |
| `.trellis/tasks/m-data-03-tier-a-live/research/reference-adoption-m-data-03.md` | must-read | both     | BOOT     |
| `backend/app/ops/tier_a_live_acceptance.py`                                     | must-read | both     | S00+     |
| `backend/app/ops/tier_a_live_incremental_dispatch.py`                           | must-read | both     | S-ACCEPT |
| `scripts/tier_a_live_acceptance.py`                                             | must-read | both     | S00+     |
| `tests/test_tier_a_live_dispatch.py`                                            | must-read | both     | S-ACCEPT |

## 4. 已并入冻结任务卡

v4.1 薄指针 — 规格在 Execution Bundle。

## 5. Audit 追溯集

| 类别   | 文件                              |
| ------ | --------------------------------- |
| frozen | `frozen/M_DATA_03_TIER_A_LIVE.md` |
| entry  | `research/00-EXECUTION-ENTRY.md`  |
| index  | 本文件                            |
| slices | `research/to-issues-slices.md`    |
| audit  | `AUDIT.plan.md`                   |
