# Audit A2 — Ponytail（R3-DCP-09 bounded backfill CI）

> **维：** A2 ponytail-review  
> **协议：** plan_protocol_version 4.1  
> **模板：** `agents/audit-a2-ponytail.md`  
> **日期：** 2026-07-02  
> **工作目录：** `quant-monitor-desk-wt-dcp09` · 分支 `feature/wave4-r3-dcp-09-backfill-ci`  
> **diff 基线：** `git diff HEAD`（已暂存+未暂存）+ untracked 实现文件

---

## 维度证据 §3.2

### Boot / diff 记录

| 项                               | 证据                                                                                                                                                                                                                                                                                                                                                                          |
| -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `git diff --stat`                | 16 files changed, **913 insertions(+), 603 deletions(−)**（net **+310**）                                                                                                                                                                                                                                                                                                     |
| 主要触及（INDEX §1 / to-issues） | `backend/app/cli/data_commands.py` (+185) · `backend/app/ops/baostock_incremental_run.py` (+57) · `backend/app/sync/jobs.py` (+44) · `scripts/wave3_isolated_production_acceptance.py` (重构) · `scripts/wave3_live_production_acceptance.py` (+58) · 新建 `specs/contracts/bounded_backfill_cap.yaml` · 7 个 pytest 模块 · `.github/workflows/nightly.yml`                   |
| DOUBT 搜索范围                   | `backend/app/cli/data_commands.py` · `backend/app/ops/baostock_incremental_run.py` · `backend/app/sync/jobs.py` · `scripts/wave3_*_production_acceptance.py` · `tests/test_*backfill*` · `tests/test_*nightly*` · `tests/test_wave3_*` · 对照 `sync_baostock_incremental` / `baostock_incremental_run.run_baostock_bar_incremental` / `tests/incremental_baostock_support.py` |
| A2 checklist                     | `git diff --stat` 已记录 · 候选均附 file:line + 梯级 · A4 交叉见下 · 阻塞/建议见 findings P 级                                                                                                                                                                                                                                                                                |

### 候选删改（file:line · ponytail 梯级）

| 候选删改                                                         | ponytail 梯级                | 备注                                                                       |
| ---------------------------------------------------------------- | ---------------------------- | -------------------------------------------------------------------------- |
| `jobs.py:50-52` 模块常量 vs `bounded_backfill_cap.yaml` 双写     | 梯级 1（YAGNI 双 SSOT）      | ADR-030 声明 YAML 为 SSOT；runtime 未读 YAML；见 A2-P2-001                 |
| `jobs.py:62-64` `load_bounded_backfill_cap()` 仅测试调用         | 梯级 1                       | 与上同源；runtime cap 仍靠硬编码常量                                       |
| `data_commands.py:505-687` `backfill_plan` 全文 (~183 LOC)       | 梯级 2（复用 sync 路径）     | ~70 LOC 与 `sync_baostock_incremental` gate/execute 尾段同形；见 A2-P2-002 |
| `data_commands.py:620-687` vs `457-502` sandbox→orch 执行尾      | 梯级 2 + **A4 重叠**         | 重复 `assert_sandbox_db_allowed` / `CliFailure` / service 构建             |
| `baostock_incremental_run.py:133` 二次 `plan_backfill_shards`    | 梯级 2                       | 仅取 `len(shards)`；CLI 已 cap；见 A2-P3-001                               |
| `baostock_incremental_run.py:94-100` `BaostockBackfillRunResult` | 梯级 1（单消费者 dataclass） | 仅 `backfill_plan` 消费；见 A2-P3-002                                      |
| `test_bounded_backfill_cli_e2e.py:19-69` replay helper           | 梯级 2                       | 未复用 `incremental_baostock_support`；见 A2-P3-003                        |
| `test_wave3_*_acceptance_*.py:12-17` `_load_module` 双份         | 梯级 2                       | 各 ~6 LOC；可 conftest；见 A2-P3-004                                       |
| `plan_backfill_shards` max_shards 扩展 (`jobs.py:148-188`)       | —（不计 bloat）              | S00 / ADR-030 / to-issues explicit AC                                      |
| `wave3_isolated` `_build_steps` 抽取                             | —（PASS · 减重复）           | `--quick` 所需；比内联 steps 列表更 ponytail                               |
| `nightly.yml` + `nightly_ci.md`                                  | —（PASS）                    | S04 最小可执行清单；无 wrapper 层                                          |
| `wave3_live` severity gate (~40 LOC)                             | —（PASS）                    | S05 AC 直接映射；无多余抽象                                                |

### A4 交叉引用

- `backfill_plan` 与 `sync_baostock_incremental` 共享同一套 sandbox gate、`ResourceGuard`/`route_preview` 检查、`CliFailure` 映射（`data_commands.py:620-685` ↔ `436-500`）→ 与 A4 错误模型重复维护面重叠，Repair 时宜与 A2-P2-002 一并抽取。

### DOUBT

≥1 处 ≥20 行可简化：**是**。`backfill_plan` 净增 ~183 行，其中 gate + live 执行尾 ~70 行可与既有 `sync_baostock_incremental` 合并；`load_bounded_backfill_cap` + 模块常量构成 ADR 声明的 YAML SSOT 与 runtime 脱节。

---

## §维度裁决

**FAIL**

（§计划内 2 条 + §计划外 3 条非占位 finding）

---

## 计划内问题

| ID        | P   | 标题                                 | 锚点                                                                                                                                                | 根因                                                                                                                                                                                             | 修复方案                                                                                                                                          | 验证                                                                                                                                                          |
| --------- | --- | ------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A2-P2-001 | P2  | cap YAML SSOT 未接入 runtime         | `backend/app/sync/jobs.py:50-64` · `specs/contracts/bounded_backfill_cap.yaml` · `docs/decisions/ADR-030-bounded-backfill-cap-and-ci-nightly.md:28` | ADR-030 / 活卡声明 `bounded_backfill_cap.yaml` 为 SSOT；实现用模块级常量 `DEFAULT_MAX_BACKFILL_SHARDS` 等，`load_bounded_backfill_cap()` 仅 `test_bounded_backfill_cap.py` 调用，YAML 改值不生效 | 启动时或模块 init 从 YAML 加载三 cap 写入模块常量（或删除常量、统一 `load_bounded_backfill_cap()["caps"]`）；`backfill_plan` / CLI 校验读同一来源 | `uv run pytest tests/test_bounded_backfill_cap.py tests/test_qmd_data_backfill_cli.py -q`；临时改 YAML 中 `default_max_backfill_shards` 断言 planner 行为跟随 |
| A2-P2-002 | P2  | `backfill_plan` 大量复制 sync 金路径 | `backend/app/cli/data_commands.py:505-687`（尤其 `620-687` ↔ `sync_baostock_incremental` `436-502`）                                                | 新 CLI 未抽取与 incremental 共用的 sandbox gate + orchestrator 执行尾；~70 LOC 同形（`assert_sandbox_db_allowed`、`build_baostock_incremental_service`、`ConnectionManager` 等）                 | 抽取 `_baostock_bar_execute_after_gates(...)` 或让 `backfill_plan` 在 shard 规划后调用共享 helper；保留 backfill 特有 shard JSON 字段             | `uv run pytest tests/test_qmd_data_backfill_cli.py tests/test_bounded_backfill_cli_e2e.py tests/test_baostock_incremental_e2e.py -q`                          |

---

## 计划外发现

| ID        | P   | 标题                                | 锚点                                                  | 根因                                                                                                                                                           | 修复方案                                                                                                                               | 验证                                                                                             |
| --------- | --- | ----------------------------------- | ----------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| A2-P3-001 | P3  | runner 内冗余 shard 规划            | `backend/app/ops/baostock_incremental_run.py:133-144` | `run_baostock_bar_backfill` 再调 `plan_backfill_shards(date_start, date_end)` 无 `max_shards`，只为 `shard_count=len(shards)`；CLI 已用 capped `effective_end` | `shard_count=len(results)`；删除 L133 `shards = plan_backfill_shards(...)`                                                             | `uv run pytest tests/test_bounded_backfill_cli_e2e.py -q`                                        |
| A2-P3-002 | P3  | 单消费者 backfill 结果 dataclass    | `backend/app/ops/baostock_incremental_run.py:94-100`  | `BaostockBackfillRunResult` 仅 `backfill_plan` 一处 import；字段可用 `BaostockIncrementalRunResult` 扩展或具名 tuple                                           | 与 incremental 对齐：返回 `(job_id, statuses)` 或复用单一 `RunResult`；删除专用 dataclass                                              | `uv run pytest tests/test_bounded_backfill_cli_e2e.py tests/test_qmd_data_backfill_cli.py -q`    |
| A2-P3-003 | P3  | e2e replay patch 未复用测试 support | `tests/test_bounded_backfill_cli_e2e.py:19-69`        | `_write_two_shard_replay` / `_patch_baostock_replay` 与 `incremental_baostock_support` + `test_baostock_incremental_e2e` 同型 mock 注入                        | 将 replay fixture 写入与 `build_baostock_incremental_service` monkeypatch 移入 `incremental_baostock_support.py`（参数化 replay path） | `uv run pytest tests/test_bounded_backfill_cli_e2e.py tests/test_baostock_incremental_e2e.py -q` |

已对抗搜索：`backend/app/cli/data_commands.py` 全文；`backend/app/ops/baostock_incremental_run.py`；`backend/app/sync/jobs.py` cap 段；`scripts/wave3_*`；新建 `tests/test_*dcp09*` / `*backfill*` / `*nightly*` / `*quick_profile*` / `*findings_gate*`；对照 `research/to-issues-slices.md` S00–S06 范围外无额外 ≥20 行新抽象模块。

### 做得好的地方

- **`plan_backfill_shards` max_shards 扩展**（`jobs.py:148-188`）直接服务 S00 AC，逻辑紧凑，无额外 factory。
- **`wave3_isolated_production_acceptance._build_steps`** 抽取反而减少重复，符合 ponytail。
- **`nightly.yml` / `nightly_ci.md`** 逐步对应活卡两步，无第三层 manifest 代码。
- **`baostock_incremental_run.run_baostock_bar_backfill`** 整体 ~45 LOC，沿 incremental 薄编排模式，未引入新 runner 类。
