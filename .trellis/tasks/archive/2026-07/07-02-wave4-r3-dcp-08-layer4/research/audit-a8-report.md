# Audit A8 — 测试缺口（R3-DCP-08）

| 字段                  | 值                             |
| --------------------- | ------------------------------ |
| 维度                  | A8                             |
| 任务                  | `07-02-wave4-r3-dcp-08-layer4` |
| plan_protocol_version | 4.1                            |
| 模板                  | `agents/qa-expert.md`          |
| 日期                  | 2026-07-02                     |
| 审计员                | A8 subagent（test-gap only）   |

---

## 维度证据

### 1. 全量 pytest（AUDIT.plan §2 A8 · 独立复验）

| 项             | 结果               |
| -------------- | ------------------ |
| 命令           | `uv run pytest -q` |
| exit code      | **0**              |
| collected      | **2092**           |
| skipped        | **8**              |
| passed（推算） | **2084**           |
| failed         | **0**              |

Skip 明细（`-rs`）：

| 模块                                             | 原因                                              |
| ------------------------------------------------ | ------------------------------------------------- |
| `tests/test_batch25_production_data_gate.py:133` | target DB not present; local readiness gate only  |
| `tests/test_batch25_production_data_gate.py:158` | no staged raw evidence in data/raw                |
| `tests/test_batch275_live_pilot_gate.py:830`     | need `--run-network` for live vendor fetch        |
| `tests/test_fred_macro_incremental_e2e.py:85`    | live_smoke requires `FRED_API_KEY`                |
| `tests/test_fred_sandbox_pilot.py:303`           | `FRED_API_KEY` absent — live fetch opt-in skipped |
| `tests/test_ops_db_inspector.py:440`             | symlinks not supported on this platform           |
| `tests/test_prediction_market_adapters.py:526`   | `KALSHI_LIVE_SMOKE` not set                       |
| `tests/test_prediction_market_adapters.py:555`   | `POLYMARKET_LIVE_SMOKE` not set                   |

以上 8 条均为环境/平台 opt-in，**非 DCP-08 新增 skip**；仓库内 **无** `@pytest.mark.flaky`。

DCP-08 聚焦测（独立跑绿）：

```bash
uv run pytest tests/test_layer4_clean_read.py tests/test_layer4_us_equity_clean_e2e.py \
  tests/test_qmd_data_sync_tier_a_router.py -k mootdx -q  # exit 0
uv run pytest tests/test_docstring_quadruple_coverage.py -q  # exit 0
```

### 2. 切片 S08-BOOT..CLOSE 建议测试 vs 实际

| Slice                 | to-issues 建议测试 / 证据                                    | 实际                                                                                                             | 映射     |
| --------------------- | ------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------- | -------- |
| **S08-BOOT**          | `layer4_clean_e2e_support.py` + `test_catalog.yaml`          | `tests/layer4_clean_e2e_support.py`；`test_layer4_clean_read` / `test_layer4_us_equity_clean_e2e` 已登记 catalog | **是**   |
| **S08-READ**          | `test_layer4_clean_read.py`                                  | 4 用例（聚合 / 日历 / 空 bar fail-closed）                                                                       | **是**   |
| **S08-ADAPTER**       | adapter 单测                                                 | `test_usEquityCleanAdapter_loadBreadthAndCalendar`                                                               | **是**   |
| **S08-BUILD**         | `test_layer4_market_structure.py` 全绿 + `tier_a_clean` 入口 | 022 共 17 用例 **全绿**；**无** `source_mode=tier_a_clean` 专项断言                                              | **部分** |
| **S08-E2E**           | `test_layer4_us_equity_clean_e2e.py`                         | 1 用例（happy path）                                                                                             | **部分** |
| **S08-REG-MOOTDX**    | `test_qmd_data_sync_tier_a_router.py` mootdx dry-run         | `test_tierASyncRouter_dryRun_mootdx_selectedSourceId_aligned`                                                    | **是**   |
| **S08-REG-EM**        | `rg ACC-EASTMONEY specs/datasource_registry/`                | registry 两行含 `ACC-EASTMONEY-TAXONOMY-001`（DCP-05 Repair 遗留）；**无** DCP-08 taxonomy pytest                | **缺口** |
| **S08-L4-E2E-LEDGER** | `l4-e2e-live-evidence.md` + pytest                           | 证据 md [x] + e2e 绿                                                                                             | **是**   |
| **S08-CLOSE**         | `uv run pytest -q`                                           | exit 0                                                                                                           | **是**   |

**DCP-08 新增/扩展测试模块（test_catalog 已登记）：**  
`test_layer4_clean_read.py` · `test_layer4_us_equity_clean_e2e.py` · `test_qmd_data_sync_tier_a_router.py`（+1 mootdx selected_source_id 用例）。

### 3. 五字段 docstring 抽检（DCP-08 新增）

| 模块                                                   | 用例数 | 五字段 | 门禁                                          |
| ------------------------------------------------------ | ------ | ------ | --------------------------------------------- |
| `test_layer4_clean_read.py`                            | 4      | 全覆盖 | `test_docstring_quadruple_coverage.py` **绿** |
| `test_layer4_us_equity_clean_e2e.py`                   | 1      | 全覆盖 | 同上                                          |
| `test_qmd_data_sync_tier_a_router.py`（mootdx 新用例） | 1      | 全覆盖 | 同上                                          |

### 4. Red Flag / 活卡 AC 追溯

| Red Flag / AC                                | 测试或 defer     | 证据                                                |
| -------------------------------------------- | ---------------- | --------------------------------------------------- |
| 禁止 staged 冒充 PASS（活卡 §3）             | 测试             | e2e `staged_fixture not in source`                  |
| P0 `US_EQ` clean e2e（活卡 §5）              | 测试             | `test_layer4UsEquity_cleanRead_breadthSnapshot_e2e` |
| `ACC-MOOTDX-DRYRUN-ROUTE-001`                | 测试             | `selected_source_id==mootdx`                        |
| `ACC-EASTMONEY-TAXONOMY-001`（不关 REQ2-EM） | **仅 rg / 文档** | 无 pytest 锁 taxonomy 内容                          |
| `ACC-LAYER-E2E-LIVE-001` L4                  | 测试 + 证据 md   | e2e + `l4-e2e-live-evidence.md`                     |
| 022 staged 无回归（INDEX §2）                | 测试             | `test_layer4_market_structure.py` 17 用例绿         |
| plan-doubt-review Cycle 1–4                  | Plan reconcile   | 无单独 pytest 表项（非测试 Red Flag）               |

### 5. 对抗性扫描（A8 最低动作）

| 扫描项                                                     | 结论                                                                 |
| ---------------------------------------------------------- | -------------------------------------------------------------------- |
| `tier_a_clean` Builder 负向（`clean_con=None` / 非 US_EQ） | **无** pytest                                                        |
| `tier_a_clean` 未来观测拒绝                                | staged 有 `test_marketSnapshotRejectsFutureInput`；clean 路径 **无** |
| `build_calendar_row` 非交易日                              | 仅测交易日 `TRADE_DATE`                                              |
| `collect_clean_lineage_provenance`                         | 仅 e2e 间接断言 `security_bar_1d` 字符串                             |
| mootdx dry-run 无 monkeypatch                              | `_patch_mootdx_registry_validation_only` 仍依赖测试补丁              |
| flaky 标记                                                 | **0**                                                                |
| purpose drift                                              | DCP-08 新增用例未发现                                                |

已对抗搜索：`tests/test_layer4_*.py` · `tests/layer4_clean_e2e_support.py` · `tests/test_qmd_data_sync_tier_a_router.py` · `backend/app/layer4_markets/{clean_read,market_structure}.py` · `to-issues-slices.md` S08-* · `plan-doubt-review.md` · 全库 `@pytest.mark.flaky` · `specs/datasource_registry/*eastmoney\*`。

---

## §维度裁决

**FAIL**

（§计划内问题 3 条 + §计划外发现 2 条非占位 finding）

---

## 计划内问题

| ID        | P   | 标题                                           | 锚点                                                                                                                                                       | 根因                                                                                                            | 修复方案                                                                                                                                                                                         | 验证                                                                                               |
| --------- | --- | ---------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------- |
| A8-P2-001 | P2  | S08-BUILD `tier_a_clean` Builder 负向未测      | `to-issues-slices.md` S08-BUILD · `market_structure.py` L275–280 · `test_layer4_market_structure.py`（无 `tier_a_clean`）                                  | Execute 仅在 e2e/clean_read 覆盖 happy path；`clean_con=None` 与 `CN_A`+`tier_a_clean` fail-closed 无回归       | 在 `test_layer4_clean_read.py` 或新建 Builder 小节补 2 测：`tier_a_clean`+`clean_con=None` → `Layer4MarketError`；`CN_A`+`tier_a_clean` → `only supports US_EQ`                                  | `uv run pytest tests/test_layer4_clean_read.py -q` exit 0                                          |
| A8-P2-002 | P2  | S08-E2E 仅 happy path，缺 clean 未来观测闸     | `to-issues-slices.md` S08-E2E · 对比 `test_marketSnapshotRejectsFutureInput`（staged）· `market_structure.py` `_build_tier_a_clean` L292–303               | staged 022 有 future 拒绝；`tier_a_clean` 共用 `_reject_future_observation` 但无对称 pytest                     | 在 `test_layer4_us_equity_clean_e2e.py` 或 `test_layer4_clean_read.py`：seed bar `as_of` 晚于 build `as_of` → `Layer4MarketError` 含 `future`                                                    | `uv run pytest tests/test_layer4_us_equity_clean_e2e.py tests/test_layer4_clean_read.py -q` exit 0 |
| A8-P2-003 | P2  | S08-REG-EM 无 pytest 锁 ACC-EASTMONEY taxonomy | `to-issues-slices.md` S08-REG-EM · `source_registry.yaml` L319 · `source_capabilities.yaml` L1261 · `docs/ops/data_sync_quick_reference.md` §ACC-EASTMONEY | 切片 AC 写 `rg` 验 registry；A8 要求契约面 pytest 或 explicit defer——当前 **无** pytest 防 DCP-08 taxonomy 回退 | 增 `test_sourceRegistry_eastmoney_accTaxonomy_notesPresent`（或扩 `test_source_registry.py`）：断言 eastmoney `notes` 含 `ACC-EASTMONEY-TAXONOMY-001`、bar via baostock/mootdx、**不关** REQ2-EM | `uv run pytest tests/test_source_registry.py -k eastmoney -q` exit 0                               |

---

## 计划外发现

| ID        | P   | 标题                                       | 锚点                                                                                                                                                  | 根因                                                                                               | 修复方案                                                                                                       | 验证                                                                                                |
| --------- | --- | ------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| A8-P3-001 | P3  | mootdx dry-run 测依赖 registry monkeypatch | `test_qmd_data_sync_tier_a_router.py` L76–88 `_patch_mootdx_registry_validation_only` · `test_tierASyncRouter_dryRun_mootdx_selectedSourceId_aligned` | 注释写「until registry reconcile」；测绿依赖 `validation_only=False` 补丁，非 live registry 默认态 | coordinator merge `registry_proposed_delta.yaml` 后删除 patch；或增无 patch 对照测（registry 已 reconcile 时） | merge 后 `uv run pytest tests/test_qmd_data_sync_tier_a_router.py -k mootdx -q` 无 monkeypatch 仍绿 |
| A8-P3-002 | P3  | clean e2e 未断言 lineage `rule_version`    | `market_structure.py` `_CLEAN_RULE_VERSION` · `test_layer4UsEquity_cleanRead_breadthSnapshot_e2e`                                                     | e2e 断言 `security_bar_1d` 与 breadth 计数，未锁 `layer4_market_tier_a_clean_v1` rule_version      | e2e 增 `assert result.lineage_envelope.rule_version == "layer4_market_tier_a_clean_v1"`                        | `uv run pytest tests/test_layer4_us_equity_clean_e2e.py -q` exit 0                                  |

已对抗搜索：plan-doubt-review · to-issues S08-\* · layer4 clean 全模块 · tier_a router mootdx · eastmoney registry · flaky/skip · 五字段门禁 · staged 022 对称边界。

---

## 摘要

| 项                 | 值                                                                        |
| ------------------ | ------------------------------------------------------------------------- |
| §维度裁决          | **FAIL**                                                                  |
| findings（非占位） | **5**（计划内 3 · 计划外 2）                                              |
| pytest             | exit **0** · collected **2092** · skipped **8**                           |
| 报告路径           | `.trellis/tasks/07-02-wave4-r3-dcp-08-layer4/research/audit-a8-report.md` |
