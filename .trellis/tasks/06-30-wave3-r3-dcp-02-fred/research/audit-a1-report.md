# Audit A1 — Spec / trellis-check / Trace Authority

> **维：** A1 (audit-spec)  
> **任务：** `.trellis/tasks/06-30-wave3-r3-dcp-02-fred`  
> **协议：** debt-lite Phase 8D（`task.json` · `meta.plan_protocol_version: "8d"`）  
> **Worktree：** `../quant-monitor-desk-wt-dcp02` · branch `feature/wave3-r3-dcp-02-fred`  
> **审计日期：** 2026-06-30  
> **模型：** composer-2.5

---

## 维度证据

### trellis-check 步骤 1–7

| 检查项 | 结果 | 证据 |
| ------ | ---- | ---- |
| **1 变更范围** | PARTIAL | `git status`（worktree）：modified 7 文件 + untracked 新测/ops/task 工件；`git diff master --name-only` 仅 7 已跟踪文件（新文件未 commit） |
| **2 任务工件** | PASS | 已 Read `prd.md` · `DEBT.plan.md` · `AUDIT.plan.md` · `research/reference-adoption-dcp02.md` · `research/execute-reference-read-evidence.md` |
| **3 包上下文** | PASS | `uv run python ./.trellis/scripts/get_context.py --mode packages` → `Spec layers: backend` |
| **4 Spec Quality** | SKIP | 变更限于 backend ops/cli/port；未触 UI/API 新层；未读独立 package spec index（单 repo backend 层） |
| **5 项目检查** | FAIL | 定向测：`uv run pytest tests/test_fred_macro_incremental_*.py -q` → **13 passed, 1 skipped**（live smoke skip）；全库：`uv run pytest -q` → **1 failed**（见下） |
| **6 跨层** | PASS | 数据流 Storage(DuckDB `axis_observation`) → Service(`DataSourceService`/`run_incremental`) → CLI(`sync_plan`)；无 UI；import 无环（静态读码） |
| **7 manifest** | FAIL | `check.jsonl` / `implement.jsonl` 仍含 `_example` 占位；`DEBT.plan.md` forbidden 含 `tests/test_catalog.yaml` 但 diff 已改 |

**定向 pytest（2026-06-30）：**

```text
uv run pytest tests/test_fred_macro_incremental_watermark.py \
  tests/test_fred_macro_incremental_port.py \
  tests/test_fred_macro_incremental_e2e.py \
  tests/test_fred_macro_incremental_cli.py -q
.........s....  [100%]
```

**全库 pytest：**

```text
FAILED tests/test_batch25_production_data_gate.py::test_current_target_db_has_no_clean_layer1_production_observations
AssertionError: _table_count(con, "fetch_log") == 0  → 实际 3
```

### diff vs DEBT.plan / AUDIT.plan 边界

| 类别 | 文件 | 判定 |
| ---- | ---- | ---- |
| **allowed · 新增** | `backend/app/ops/fred_incremental_watermark.py` · `fred_incremental_run.py` · `tests/test_fred_macro_incremental_*.py` · `tests/fred_macro_incremental_support.py` | PASS |
| **allowed · 修改** | `fred_port.py` · `data_commands.py` · `main.py` | PASS |
| **forbidden · 未触** | `baostock_port.py` · `sync/orchestrator.py` · `sync/runners.py` · `sync/watermark*.py`（源码） | PASS（`git diff master` 无输出） |
| **forbidden · 已触** | `tests/test_catalog.yaml` | **FAIL**（709 行量级 diff；DEBT §Boundary forbidden 明文禁止） |
| **scope 外 · 已触** | `docs/generated/*`（3 文件） | **NOTE**（不在 allowed 列表；典型 loop_maintain 副产物，宜 merge 协调） |
| **金路径 bypass** | `fred_incremental_run.py` L278–327 | PASS — 经 `orch.run_incremental(..., datasource_service=proxy)`；无旁路 fetch runner |
| **runtime patch** | `fred_incremental_run.py` L169–218 `_macro_incremental_validation_patch` | PASS（ponytail 注释 + 未改 `runners.py` 磁盘；协调手册禁 **写** 源码） |

**变更文件清单（相对 master + worktree unstaged）：**

```text
backend/app/cli/data_commands.py
backend/app/cli/main.py
backend/app/datasources/fetch_ports/fred_port.py
backend/app/ops/fred_incremental_run.py          (untracked)
backend/app/ops/fred_incremental_watermark.py    (untracked)
tests/test_fred_macro_incremental_*.py           (untracked ×4)
tests/fred_macro_incremental_support.py          (untracked)
tests/test_catalog.yaml                          (modified — forbidden)
docs/generated/*                                 (modified — scope 外)
```

### Trace Authority（debt-lite 映射）

> v4.1 `§0.1` 不适用；以 `DEBT.plan.md` + 活卡 + `prd.md` + `research/*` 为 Trace SSOT。

| 条目 | 核对问题 | 结果 | 证据 |
| ---- | -------- | ---- | ---- |
| **活卡 §5 AC** | watermark / replay / live / 幂等 / pytest 全绿 | PARTIAL | 定向测绿；活卡 §5 末项 `uv run pytest -q` **未绿**（见上） |
| **活卡 §3 约束** | 金路径 · env gate · 隔离库 · 禁 baostock | PASS | e2e/cli 测 `QMD_DATA_ROOT` 隔离；`assert_product_live_allowed`；无 baostock diff |
| **活卡 §4 CLI** | `--source fred` | DEFER | 活卡 §4 写 `--source fred`；**prd/DEBT S02-05 SSOT** 为 `--source-id fred`（`main.py` L25 · CLI 测 L19–33）— 活卡待主会话同步 |
| **DEBT 边界** | allowed/forbidden 无泄漏 | FAIL | `test_catalog.yaml` forbidden 泄漏 |
| **reference-adoption L1/L2/L3** | Plan 产物 + Execute cite | PARTIAL | `research/reference-adoption-dcp02.md` + `execute-reference-read-evidence.md` 完整；**port/CLI 新切片 cite 不足**（见计划内 finding） |
| **AUDIT §2.1 cite 抽检** | port/CLI 改动含等级 + 锚点 | FAIL | `_sync_fred_macro_incremental` 仅任务 ID 注释；无 L2/L3 源码锚点 |
| **implement/check manifest** | debt-lite jsonl 登记 | FAIL | `_example` 占位未删 |
| **7.pre gitnexus-audit-summary** | AUDIT.plan §4 DoD | FAIL | `research/gitnexus-audit-summary.md` **不存在**（仅有 Execute 版 `gitnexus-execute-summary.md`） |

### DOUBT 对抗搜索

| 疑点 | 搜索范围 | 结论 |
| ---- | -------- | ---- |
| baostock 域泄漏 | `git diff master` · `rg baostock fred_incremental*` | 无命中 |
| orchestrator/runners 源码改写 | `git diff master -- orchestrator runners watermark` | 无 diff |
| adapter bypass | Read `fred_incremental_run.py` · e2e 测 docstring | 金路径经 `DataSourceService` + `run_incremental` |
| EasyXT silent 回退 | `test_fred_macro_incremental_port.py` L94–109 | 负例测 `USER_AUTH_REQUIRED` |
| 活卡 Red Flags | 活卡 §3 · AUDIT §5 | canonical 写：`fetch_log==3` 暗示默认 `data/duckdb` 可能被非隔离 CLI 触达（与 AUDIT §5 硬门槛相关） |

### GitNexus

| 动作 | 结果 |
| ---- | ---- |
| `query("fred macro incremental run_incremental DataSourceService")` | 返回 live_pilot / DataSourceService.fetch 流；**未索引** 新符号 `run_fred_macro_incremental` |
| `context("run_fred_macro_incremental")` | Symbol not found（索引 stale / 未 analyze） |
| Execute 摘要 | `research/gitnexus-execute-summary.md` 已记录 query + impact 尝试 |

**索引说明：** worktree 新文件未入 GitNexus 图；A1 以源码 + pytest 为准，不依赖自述 PASS。

---

## §维度裁决

**FAIL**

---

## 计划内问题

| ID | P | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| A1-P1-001 | P1 | 修改 forbidden `test_catalog.yaml` | `DEBT.plan.md` L39 · `git diff master -- tests/test_catalog.yaml` | Execute 在轨 B 直接改 registry；与 DEBT forbidden 及「Registry 主会话排队」冲突 | Revert 本轨对 `tests/test_catalog.yaml` 的改动；merge 时由主会话跑 `uv run python scripts/loop_maintain.py --fix` 登记四支 incremental 测模块 | `git diff master -- tests/test_catalog.yaml` 为空；`loop_maintain.py` check exit 0 |
| A1-P1-002 | P1 | port/CLI 新切片缺 reference-adoption cite | `AUDIT.plan.md` §2.1 · `data_commands.py` L143–238 · `fred_incremental_run.py` L1–5 | Execute 仅在 docstring 写 R3-DCP-02 ID，未按 §2.1 标注 L1/L2/L3 + 源码锚点（对比 `fred_port.py` L1–6 OpenBB architecture_only cite） | 在 `_sync_fred_macro_incremental` · `run_fred_macro_incremental` · `_macro_incremental_validation_patch` 顶部补 cite 行（指向 `reference-adoption-dcp02.md` §2 行 + `execute-reference-read-evidence.md` R1–R3） | A1 复验：grep 新改函数区块含 `L1`/`L2`/`architecture_only`/`forbidden` 至少各一锚点 |
| A1-P1-003 | P1 | 活卡 merge gate `uv run pytest -q` 未绿 | 活卡 §5 · `prd.md` AC#6 · `DEBT.plan.md` Merge gate | canonical `data/duckdb/quant_monitor.duckdb` 中 `fetch_log` 已有 3 行；`_sync_fred_macro_incremental` 默认 `QMD_DATA_ROOT` 回落 `PROJECT_ROOT/data`（`data_commands.py` L195–196），开发/手动 CLI 可能写 canonical | 确认污染来源；清理或隔离 canonical DB（仅 sandbox）；CLI 文档/默认路径 fail-closed 或 Execute 增加「无 QMD_DATA_ROOT 且非 dry-run 则拒绝」ponytail guard；Repair 后全绿 | `uv run pytest -q` exit 0 |
| A1-P2-001 | P2 | check/implement manifest 仍为占位 | `check.jsonl` L1 · `implement.jsonl` L1 | debt-lite Execute 未登记 spec/research manifest | 删除 `_example` 行；按 `get_context.py` 补 `reference-adoption-dcp02.md` · `architecture-dcp02.md` · 活卡路径等 | `task.py validate-audit-handoff` 或人工 grep jsonl 无 `_example` |

---

## 计划外发现

| ID | P | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| A1-P2-002 | P2 | 缺 7.pre `gitnexus-audit-summary.md` | `AUDIT.plan.md` §4 DoD L77 | 主会话未在派发 A1–A8 前产出 Audit 版 GitNexus 摘要 | 主会话补写 `research/gitnexus-audit-summary.md`（含 `impact`/`query` 于 fred incremental 符号） | 文件存在且非 Execute 摘要拷贝 |
| A1-P3-001 | P3 | 活卡 §4 CLI 旗标与 prd 漂移 | 活卡 §4 L39 `--source fred` · `prd.md` L52 `--source-id` | 活卡未随 F4/audit 契约更新 | 主会话更新 `R3_DCP_02_FRED_INCREMENTAL.md` §4 为 `--source-id fred` | 活卡 §4 与 `main.py` L25 一致 |

已对抗搜索：`backend/app/sync/**` 写权限 · `baostock*` · `orchestrator`/`runners` 磁盘 diff · `rg FRED bypass` · canonical DB 表计数 · GitNexus 新符号索引 · forbidden EasyXT import — 除上表项外未发现额外 scope 泄漏或金路径 bypass。

---

## A1 checklist 关账

- [x] trellis-check 1–7 有证据（上表）
- [ ] diff vs audit/check manifest — **FAIL**（test_catalog forbidden；jsonl 占位）
- [x] Trace Authority 大部分继承；活卡 CLI 语法 **explicit defer**（prd 为准）
- [ ] 无 Plan omission — **FAIL**（cite · manifest · 7.pre · pytest 全绿）
- [x] GitNexus 已 query；说明索引未覆盖新符号
