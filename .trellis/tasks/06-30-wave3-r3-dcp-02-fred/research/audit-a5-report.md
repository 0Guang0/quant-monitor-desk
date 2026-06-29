# Audit A5 — Verification / Completion

> **维：** A5 (audit-completion)  
> **任务：** `wave3-r3-dcp-02-fred` · debt-lite Phase 8D  
> **活卡：** `R3_DCP_02_FRED_INCREMENTAL.md` §5  
> **切片 SSOT：** `DEBT.plan.md` S02-01..05  
> **Worktree：** `../quant-monitor-desk-wt-dcp02` · branch `feature/wave3-r3-dcp-02-fred`  
> **审计日期：** 2026-06-30  
> **GitNexus：** `query` ×2 · `context(run_incremental)` ×1（新符号 `run_fred_macro_incremental` 未索引）

---

## 3.1 A5 Checklist

| 项 | 结果 | 证据 |
| --- | --- | --- |
| 每条 AC → 代码/测试追溯 + 1–5 分 | 见 §3.2 | 14/14 `test_*` 五字段齐全；活卡 §5 除 registry/pytest 全绿外均有测 |
| 独立复跑与实现一致 | PASS | §3.4 最弱 2 行 exit 0 |
| diff 无 silent 扩大 scope | PASS | §3.3 未触 forbidden 文件 |
| 定向 pytest | PASS | §3.5 exit 0（1 skip live_smoke） |
| 全库 `uv run pytest -q` | **FAIL** | §3.5 exit 1（3 failures） |

---

## 3.2 AC ↔ 测试追溯（五字段 + 评分）

### 活卡 §5 / DEBT 切片

| AC / 切片 | 测试（模块::函数） | 五字段 | 分 |
| --- | --- | --- | --- |
| **S02-01** watermark 空表 | `test_fred_macro_incremental_watermark::test_fredWatermark_emptyTable_returnsCappedColdStart` | 覆盖/对象/目的/验证点/失败含义 ✓ | 5 |
| **S02-01** 有观测 | `…::test_fredWatermark_existingObservation_returnsNextDay` | ✓ | 5 |
| **S02-01** 多 series | `…::test_fredWatermark_multiSeries_independentWatermarks` | ✓ | 5 |
| **S02-02** start_time → observation_start | `test_fred_macro_incremental_port::test_fredPort_startTime_mapsToObservationStart` | ✓ | 5 |
| **S02-02** 冷启动 cap | `…::test_fredPort_coldStart_usesCappedWindow` | ✓ | 5 |
| **S02-02** mock 过滤窗 | `…::test_fredPort_mock_filtersObservationsBeforeStart` | ✓ | 5 |
| **S02-02** 无 key 负例 | `…::test_fredPort_live_rejectsWithoutApiKey` | ✓ | 5 |
| **S02-03** replay 金路径 | `test_fred_macro_incremental_e2e::test_fredIncremental_e2e_replay_writesAxisObservation` | ✓ | 5 |
| **S02-04** 幂等 | `…::test_fredIncremental_idempotent_secondRun_rowCountStable` | ✓ | 5 |
| **S02-04** env-gated live smoke | `…::test_fredIncremental_live_smoke_envGated` | ✓（见 finding A5-P2-01） | 4 |
| **S02-05** CLI dry-run | `test_fred_macro_incremental_cli::test_fredIncrementalCli_dryRun_includesSourceId` | ✓ | 5 |
| **S02-05** CLI live gate | `…::test_fredIncrementalCli_execute_rejectsWithoutLiveEnv` | ✓ | 5 |
| **S02-05** CLI mock 真跑 | `…::test_fredIncrementalCli_execute_mockInTest` | ✓ | 5 |
| **S02-05** CLI help | `…::test_fredIncrementalCli_help_showsSourceIdFlag` | ✓ | 5 |
| **活卡 §5** `reference-adoption-dcp02.md` L1/L2/L3 | 文档 `research/reference-adoption-dcp02.md` + `execute-reference-read-evidence.md` | 无自动化测；调研 SSOT 已落盘 | 3 |
| **活卡 §5** `uv run pytest -q` exit 0 | 全库复跑 | **FAIL**（§3.5） | 1 |
| **活卡 §5** Audit + Repair 关账 | 本维进行中 | — | — |

**五字段抽检：** 14 个 `test_*` 均含「覆盖范围、测试对象、目的/目标、验证点、失败含义」五行。

**金路径代码链（GitNexus + Read）：**

- `context(run_incremental)` → `backend/app/sync/orchestrator.py:126-163`（L1 金路径，未改源码）
- `fred_incremental_run.py:320` 调用 `orch.run_incremental(...)`，`clean_table="axis_observation"`，`primary_keys=("observation_id",)`
- GitNexus 未索引新符号 `run_fred_macro_incremental` / `read_observation_date_watermark`（worktree 未 commit + analyze 滞后）

---

## 3.3 Git diff 范围（working tree vs HEAD）

**Branch HEAD：** `71e47e74`（与 `master` 同 commit；实现均为 **uncommitted**）

| 类别 | 路径 |
| --- | --- |
| 修改 | `backend/app/cli/data_commands.py`, `main.py`, `fetch_ports/fred_port.py` |
| 新增 | `backend/app/ops/fred_incremental_run.py`, `fred_incremental_watermark.py` |
| 新增测 | `tests/test_fred_macro_incremental_{watermark,port,e2e,cli}.py`, `fred_macro_incremental_support.py` |

**Forbidden 抽检：** 无 `baostock_port` · `orchestrator.py` · `runners.py` · `sync/watermark*` 写操作 · `test_catalog.yaml` 改动。

---

## 3.4 INDEX §2.1 等价 — 最弱 2 行独立复跑

| 原行（DEBT/AUDIT 矩阵） | 独立命令 | exit | 与代码一致 |
| --- | --- | --- | --- |
| S02-04 幂等（Tier B 行为） | `uv run pytest tests/test_fred_macro_incremental_e2e.py -q -k idempotent` | 0 | ✓ |
| S02-05 CLI mock 真跑（Tier B 隔离库） | `uv run pytest tests/test_fred_macro_incremental_cli.py -q -k mockInTest` | 0 | ✓ |

`live_smoke` 需 `FRED_API_KEY`，本环境 skip（`s`），符合 env-gate 设计。

---

## 3.5 Pytest 复验

### 定向（AUDIT.plan A5）

```text
uv run pytest tests/test_fred_macro_incremental_watermark.py \
  tests/test_fred_macro_incremental_port.py \
  tests/test_fred_macro_incremental_e2e.py \
  tests/test_fred_macro_incremental_cli.py -q
```

**结果：** 14 passed, 1 skipped (`live_smoke`), **exit 0**

> PowerShell 下 `tests/test_fred_macro_incremental*.py` glob 不展开 → 须显式列文件。

### 全库（活卡 §5 · AUDIT.plan A5）

```text
uv run pytest -q
```

**结果：** **exit 1** — 3 failures

| 失败用例 | 根因归类 |
| --- | --- |
| `test_batch25_production_data_gate::test_current_target_db_has_no_clean_layer1_production_observations` | **已知环境：** canonical `data/duckdb/quant_monitor.duckdb` 中 `fetch_log` count=3（非本轨写入） |
| `test_loop_engineering_flow::test_loopMaintain_check_passesWhenRepoFresh` | **本轨缺口：** 4 个新测模块未登记 `tests/test_catalog.yaml` |
| `test_loop_engineering_flow::test_testCatalog_coversEveryDiscoveredTestModule` | 同上 catalog 缺口 |

---

## §维度裁决

**FAIL**

---

## 计划内问题

| ID | P | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | --- | --- | --- | --- | --- |
| A5-P1-01 | P1 | 活卡 §5 全库 pytest 未绿 — test_catalog 未登记 | `tests/test_fred_macro_incremental_*.py` ×4 · `DEBT.plan.md` Merge gate | Execute 未跑 `loop_maintain.py --fix`；`DEBT.plan` forbidden 禁止本轨改 catalog，但 merge gate 仍要求登记 | 主会话 merge coordinator：`uv run python scripts/loop_maintain.py --fix` 登记 4 模块 + 刷新 project map | `uv run pytest tests/test_loop_engineering_flow.py -q -k "loopMaintain or testCatalog"` exit 0 |
| A5-P1-02 | P1 | 活卡 §5 `uv run pytest -q` AC 未满足 | `R3_DCP_02_FRED_INCREMENTAL.md` §5 末行 | A5-P1-01 + 环境 canonical DB 污染 | 先 A5-P1-01；fetch_log 环境清理或 skip 策略由主会话裁定 | `uv run pytest -q` exit 0 |
| A5-P2-01 | P2 | live_smoke 五字段验证点与断言不一致 | `test_fred_macro_incremental_e2e.py:150-180` | docstring 写 `EMPTY_RESPONSE`；断言接受 `FAILED_FINAL` | 对齐验证点与断言（或改 status 语义文档） | `uv run pytest tests/test_fred_macro_incremental_e2e.py -q -k live_smoke`（有 key 时） |
| A5-P2-02 | P2 | 实现未 commit，branch 与 master 同 SHA | `git log -1` · `git status` | Execute 切片代码均在 working tree | commit + push 至 `feature/wave3-r3-dcp-02-fred` | `git diff master...HEAD --stat` 含 fred 增量文件 |

---

## 计划外发现

| — | — | 无 | — | — | — | — |

已对抗搜索：GitNexus `query(fred macro incremental)` · `context(run_incremental)` · forbidden 路径 grep · canonical DB `fetch_log` 行来源（环境遗留，非本 diff 引入）。

---
