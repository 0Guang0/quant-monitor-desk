# Audit A1 Report — R3-DCP-06 Spec / Trace Authority / ENTRY / ADR-029

> **维：** A1 · **任务：** `wave4-r3-dcp-06-five-axis-clean` · **plan_protocol_version:** 4.1  
> **分支：** `feature/wave4-r3-dcp-06-five-axis-clean` vs `master`（`1c683397`..`90336721`）  
> **日期：** 2026-07-02 · **审计员：** trellis-check A1（readonly）

---

## 维度证据 §3.1

### Boot 与变更范围

| 检查项                            | 结果 | 证据                                                                                                                                                                                                                                   |
| --------------------------------- | ---- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `task.json` plan_protocol_version | PASS | `task.json` L16 `plan_protocol_version: "4.1"`                                                                                                                                                                                         |
| AUDIT.plan §0.1 Trace Authority   | PASS | 活卡 / ADR-029 / ENTRY / integration-audit / EXTERNAL-INDEX 均在 `audit.jsonl` 或 §5 可追溯                                                                                                                                            |
| git diff 范围                     | PASS | `git diff master..HEAD --name-only` → 71 文件；核心：`clean_observation_reader.py`、5× `test_layer1_*_clean_e2e.py`、`layer1_source_whitelist.yaml`、ADR-029、台账三件套                                                               |
| 独立 pytest（DCP-06 子集）        | PASS | `uv run pytest tests/test_layer1_clean_reader.py tests/test_layer1_*_clean_e2e.py tests/test_layer1_five_axis_panel_clean_smoke.py tests/test_model_input_whitelist.py::test_layer1_p0_dcp06_cleanReplayProven -q` → 17 passed, exit 0 |
| 全量 pytest                       | PASS | `research/execute-evidence/s07-green.txt` 声明全绿；A1 子集复跑 exit 0                                                                                                                                                                 |

### GitNexus

| 检查项             | 结果             | 证据                                                                                                                                                                                                                                                                                                                                            |
| ------------------ | ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| query / context ≥1 | PASS（索引陈旧） | `context({name:"read_macro_clean_observations", repo:"quant-monitor-desk"})` → **Symbol not found**；`query({search_query:"clean_observation_reader...", repo:"quant-monitor-desk"})` → 无 clean reader 流程，返回 axis_loader/ingestion 邻域。`gitnexus-audit-summary.md` 已注明 index stale；grep 确认 7 个测试模块 + reader 模块为唯一调用方 |

### ADR-029 ↔ 实现

| P0 锚点                      | ADR-029                               | 代码                                                                                                                            | 结果 |
| ---------------------------- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- | ---- |
| ENV-E1-DGS10                 | fred / axis_observation / DGS10       | `P0_MACRO_DB_KEYS` L19–20；`test_layer1_environment_clean_e2e.py`                                                               | PASS |
| CRD.CS1.BAA10Y               | fred / BAA10Y                         | L21；`test_layer1_credit_stress_clean_e2e.py`                                                                                   | PASS |
| RA.R1.VIXCLS_30D_IMPLIED_VOL | fred / VIXCLS                         | L22；`test_layer1_risk_appetite_clean_e2e.py`                                                                                   | PASS |
| LIQ.B-I1.AMIHUD_ILLIQ        | alpha_vantage / security_bar_1d / SPY | `P0_BAR_BINDING` L26–28；`amihud_observations_from_bars`；`test_layer1_liquidity_clean_e2e.py`                                  | PASS |
| SEN-S1-COT_LF_NET            | cftc_cot / 088691                     | L23；`test_layer1_sentiment_clean_e2e.py`                                                                                       | PASS |
| No fallback                  | fail-closed                           | `CleanObservationReadError` / `CleanObservationFallbackForbiddenError` L70–76, L96–98；`FORBIDDEN_FALLBACK_SOURCE_PREFIXES` L16 | PASS |
| No migration                 | ADR §4                                | diff 无 DDL；`bootstrap_layer1_clean_db` tmp_path                                                                               | PASS |
| staged 桥保留                | ADR consequences                      | `backend/` 无 import `clean_observation_reader`；`ingestion.py` 未改                                                            | PASS |
| Liquidity ponytail           | ADR §3                                | 代码 L30–31 `ponytail:` 注释；whitelist `L1-LIQ-AMIHUD-SPY` notes                                                               | PASS |

### 主线切片追溯（S00–S07）

| 切片                  | 规格锚点                                      | 实现 / 证据                                                                                                                                                 | 追溯                                                                                                 |
| --------------------- | --------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| **S00** CORE-READER   | `to-issues-slices.md` S00 · FR-1..3 · ADR-029 | `backend/app/layer1_axes/clean_observation_reader.py`（257 行）；`tests/test_layer1_clean_reader.py` 6 tests；`execute-reference-read-evidence-s00-core.md` | **FAIL** — `execute-evidence/s00-{red,green}.txt` **缺失**（INDEX §1 / to-issues §2 要求 RED→GREEN） |
| **S01** ENVIRONMENT   | ADR-029 ENV-E1-DGS10                          | `tests/test_layer1_environment_clean_e2e.py`；`s01-red.txt` / `s01-green.txt`                                                                               | PASS                                                                                                 |
| **S02** CREDIT_STRESS | CRD.CS1.BAA10Y                                | `tests/test_layer1_credit_stress_clean_e2e.py`；`s02-*`                                                                                                     | PASS                                                                                                 |
| **S03** RISK_APPETITE | RA.R1.VIXCLS                                  | `tests/test_layer1_risk_appetite_clean_e2e.py`；`s03-*`                                                                                                     | PASS                                                                                                 |
| **S04** LIQUIDITY     | LIQ ponytail                                  | `tests/test_layer1_liquidity_clean_e2e.py`；`s04-*`                                                                                                         | PASS                                                                                                 |
| **S05** SENTIMENT     | SEN-S1-COT_LF_NET                             | `tests/test_layer1_sentiment_clean_e2e.py`；`s05-*`                                                                                                         | PASS                                                                                                 |
| **S06** INTEGRATION   | FR-4/5/6 · §3.5.1                             | `tests/test_layer1_five_axis_panel_clean_smoke.py`；`s06-*`                                                                                                 | PASS                                                                                                 |
| **S07** REPAIR        | doubt/audit gaps                              | `P0_ROW_CAPS`/`P0_WINDOW_CAPS`；`audit-repair-ledger-s07.md`；`s07-*`；`execute-reference-read-evidence-s07-repair.md`                                      | **FAIL** — 未登记于 `to-issues-slices.md` / `EXECUTION_INDEX.md` §1 / `00-EXECUTION-ENTRY.md` §1·§6  |

### 子任务追溯

| 子任务        | 范围                                                                                       | 结果 | 证据                                                                                                                                                                                                                                           |
| ------------- | ------------------------------------------------------------------------------------------ | ---- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **K2 / FR-4** | S01–S05 每轴 clean→feature→interpretation；S06/S07 panel 解读链                            | PASS | 五轴 e2e 均断言 `AxisInterpretationEngine` + `boundary_reminder`；S07 修复 LIQ `liq_interp`（`test_layer1FiveAxisPanel_cleanSmoke` L126–129）                                                                                                  |
| **K1 / FR-6** | `clean_replay_proven` + matrix + tests                                                     | PASS | `layer1_source_whitelist.yaml` L15/52/162/181/200 `readiness: clean_replay_proven`；`docs/quality/model_input_readiness_matrix.md` legend + 5 行；`test_layer1_p0_dcp06_cleanReplayProven`                                                     |
| **A4 / FR-5** | P0_ROW_CAPS · ResourceGuard · window/row cap                                               | PASS | `clean_observation_reader.py` L31–45 caps；`test_layer1CleanReader_macroRespectsWhitelistRowCap`；`test_layer1FiveAxisPanel_resourceGuardOnMigratedDb` 真 `ResourceGuard(con).check()`；`test_layer1FiveAxisPanel_windowLenWithinWhitelistCap` |
| **L1 子集**   | 待修复清单 · ROADMAP §3.5.1/§3.5.2 · R3_DCP_TO_ISSUES_INDEX §6.2 · audit-repair-ledger-s07 | PASS | `待修复清单.md` L92 ACC-LAYER L1✅ L3–L5 open；ROADMAP §3.5.1 全 [x]、§3.5.2 L327 DCP-06 行；`R3_DCP_TO_ISSUES_INDEX.md` §6.2 L159–161；ledger 13 项已关账                                                                                     |

### Trace Authority 核对

| 条目                      | 结果     | 证据                                                                                  |
| ------------------------- | -------- | ------------------------------------------------------------------------------------- |
| 原始任务卡 scope/AC       | PASS     | 活卡 §5 AC [x] 与代码一致；`frozen/R3_DCP_06_LAYER1_FIVE_AXIS_CLEAN.md` → ENTRY       |
| ENTRY §2 约束             | PASS     | ADR-029/028、no fallback、replay 隔离、无 migration — diff 符合                       |
| to-issues 切片 AC         | **FAIL** | S07 repair 未入切片总表；S00 缺 RED/GREEN 证据文件                                    |
| EXECUTION_INDEX §1 步骤   | **FAIL** | 仅列 S00–S06 + Audit；无 S07；无 `[x]` 勾选                                           |
| EXECUTION_INDEX §2.1 Tier | **FAIL** | `audit-boot-v4.1.md` L11 要求 §2.1；INDEX **无 §2.1 节**                              |
| integration-audit 闭环    | **FAIL** | L19 仍写「六组 clean e2e **待 Execute**」；L51「PASS_WITH_GAPS」与 Execute 完成态矛盾 |
| omission / 活卡 Red Flags | PASS     | B2.5-O-05 未假关；L3–L5 阶段外置已登记；tiingo ponytail 文档化                        |
| test_catalog 登记         | PASS     | `tests/test_catalog.yaml` L671–790 含全部 clean 模块                                  |

### trellis-check 步骤摘要

1. 变更范围：`git diff master..HEAD` 71 文件 ✓
2. 任务工件：prd / frozen / ENTRY / to-issues / plan-spec 已读 ✓
3. Spec：ADR-029 P0 表与 `P0_MACRO_DB_KEYS`/`P0_BAR_BINDING` 一致 ✓
4. manifest vs diff：`check.jsonl` 点名 frozen + INDEX；diff 覆盖 ✓
5. 跨层：reader 仅测试路径引用；ingestion 未破坏 ✓

---

## §维度裁决

**FAIL**

（计划内 4 项 P2 追溯缺口；功能/ADR 对齐与台账子集关账已满足，但 Trace Authority 未闭合。）

**Finding count：** 4（计划内）+ 1（计划外）= **5**

---

## 计划内问题

| ID       | P   | 标题                                                | 锚点                                                                             | 根因                                                                                            | 修复方案                                                                                                                                        | 验证                                            |
| -------- | --- | --------------------------------------------------- | -------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| A1-P2-01 | P2  | S00 缺 execute-evidence RED/GREEN                   | `EXECUTION_INDEX.md` §1 L19 · `to-issues-slices.md` L11                          | S00 实现与 `test_layer1_clean_reader.py` 已绿，但未按切片规则落盘 `s00-red.txt`/`s00-green.txt` | 补写 `research/execute-evidence/s00-red.txt`（RED 前失败摘要）与 `s00-green.txt`（`uv run pytest tests/test_layer1_clean_reader.py -q` exit 0） | `test -f .../s00-green.txt` 且 green 含 exit 0  |
| A1-P2-02 | P2  | S07 repair 切片未入 Bundle 追溯集                   | `to-issues-slices.md` · `EXECUTION_INDEX.md` §1 · `00-EXECUTION-ENTRY.md` §1 L15 | S07 在 audit repair 中新增（ledger/evidence 存在），但 Plan 冻结 Bundle 未增补切片行            | 在 `to-issues-slices.md` 增 **S07-REPAIR** 行（K1/A4/L1 关账）；同步 `EXECUTION_INDEX.md` §1 Step 3.5 与 ENTRY §1 完成条件含 S07                | grep 三文件均含 `S07`                           |
| A1-P2-03 | P2  | integration-audit.md Plan GAP 与 Execute 完成态矛盾 | `research/integration-audit.md` L19–23 · L51                                     | Plan 5d 文档未在 Execute/S07 后 reconcile                                                       | 更新 integration-audit：测试类→PASS；doc-gap 表勾选已交付项；结论改为 PASS 或注明 S07 已闭合                                                    | Read 文件无「待 Execute」clean e2e 表述         |
| A1-P2-04 | P2  | EXECUTION_INDEX 缺 §2.1 Tier 表                     | `agents/audit-boot-v4.1.md` L11 · `EXECUTION_INDEX.md`                           | v4.1 Boot 要求 INDEX §2.1 记录 Tier/复验命令；INDEX 仅 §2 AC 表                                 | 在 `EXECUTION_INDEX.md` 增 §2.1：`uv run pytest -q` + DCP-06 定向模块列表 + 步末证据路径                                                        | `EXECUTION_INDEX.md` 含 `## 2.1` 与 pytest 命令 |

---

## 计划外发现

| ID       | P   | 标题                                  | 锚点                                                       | 根因                                                                           | 修复方案                                                                                                          | 验证                                            |
| -------- | --- | ------------------------------------- | ---------------------------------------------------------- | ------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| A1-P3-01 | P3  | GitNexus 索引未收录 clean reader 符号 | `gitnexus-audit-summary.md` L30–32 · MCP `context`/`query` | 新文件 `clean_observation_reader.py` 未 re-analyze；symbol-level impact 不可用 | Repair 或主会话跑 `node .gitnexus/run.cjs analyze`；复验 `context({name:"read_macro_clean_observations"})` 有结果 | GitNexus context 返回 callers/defs 非 not found |

已对抗搜索：`backend/` 生产路径是否 import clean reader（设计为 parallel test-proven path，ADR-029 允许）· `resource_limits.yaml` 是否含 per-indicator row cap（无；caps 来自 K1 whitelist mirror，ponytail 已注释）· 活卡 `reference-adoption-dcp06.md` 是否存在（PASS）· staged ingestion 默认是否被替换（PASS，未改 `ingestion.py`）· §3.5.1 ResourceGuard 声称 vs 实现（真 `ResourceGuard(con).check()` + cap 测试已覆盖，roadmap 措辞略宽但可接受）。

---
