# Audit A2 Report — ponytail / YAGNI / bloat

> **维：** A2 (audit-ponytail)  
> **任务：** `.trellis/tasks/m-data-03-tier-a-live` · `plan_protocol_version: 4.1`  
> **模板：** `agents/audit-a2-ponytail.md`  
> **日期：** 2026-07-03  
> **分支：** 工作区未提交变更 vs `master`（含 untracked `tier_a_live_*`）

---

## 维度证据

### Boot checklist

- [x] `agents/audit-adversarial-authority.md` · `audit-boot-v4.1.md` · `audit-finding-schema.md` · `AUDIT.plan.md` · `00-EXECUTION-ENTRY.md` · `to-issues-slices.md` · `gitnexus-audit-summary.md` 已读
- [x] `git diff --stat` 已记录
- [x] `EXECUTION_INDEX` / `to-issues-slices` 切片范围已对照
- [x] DOUBT：≥1 处 ≥20 行可简化（见 findings）
- [x] 与 A4 交叉：`_extract_sync_status` 多形态脆弱解析见 A2-P2-004，语义/错误模型归 A4

### `git diff --stat`

| 范围                                                                                        | 文件数                   | 净增                                                                                                                                       |
| ------------------------------------------------------------------------------------------- | ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------ |
| **全任务工作区**                                                                            | 27                       | **+2018 / -621**                                                                                                                           |
| **A2 审计范围**（`tier_a_live_*`·`incremental_support`·live e2e·`deribit_port`·`conftest`） | 21 tracked + 5 untracked | tracked **+1385 / -8**；untracked 生产 **~794 行**（`tier_a_live_acceptance.py` 277 + `tier_a_live_incremental_dispatch.py` 471 + CLI 46） |

### §3.2 候选删改追溯

| 候选删改（file:line）                                                        | ponytail 梯级                                  | 备注                                           |
| ---------------------------------------------------------------------------- | ---------------------------------------------- | ---------------------------------------------- |
| `tier_a_live_incremental_dispatch.py:111-418` `_run_live_sync` 11 路 if/elif | **2**（复用 DCP-05 / `data_commands`）         | ~307 行；fred 已走 CLI，其余重抄 ops/bootstrap |
| `tier_a_live_acceptance.py:157-165` `_sync_result_passed`                    | **6**（删死代码）                              | 定义后零调用                                   |
| `tier_a_live_incremental_dispatch.py:454-459` 重复 `COMPLETED`+空 clean 分支 | **6**（删不可达）                              | 454-457 已 normalize，458-459 永假             |
| `tier_a_live_acceptance.py:27` + `dispatch.py:19` 双份 `_PASS_*_STATUSES`    | **2**（复用 `macro_incremental_common`）       | 与 `_SERIES_SUCCESS_STATUSES` 重叠             |
| `test_tier_a_live_harness.py:111-140` 两个相同 gate 负向测                   | **2**（合并 parametrize）                      | 同 code path 测两次                            |
| `tests/*_incremental_support.py` 5× `bootstrap_*_live_e2e_ctx`               | **2**（泛化如 `bootstrap_macro_live_e2e_ctx`） | macro 已收敛，port 源未收敛                    |
| `tier_a_live_incremental_dispatch.py:240` 未用 import                        | **6**                                          | `create_world_bank_fetch_port` 未引用          |
| `deribit_port.py:112-138` `_book_summary_mark_iv`                            | —                                              | **非 bloat**；live `mark_iv` 必要补齐          |

### 对抗搜索声明

已读：`backend/app/ops/tier_a_live_*.py`、`scripts/tier_a_live_acceptance.py`、`tests/test_tier_a_live_*.py`、`tests/*incremental_support.py`、11 源 `test_*_incremental_e2e.py` live 段、`tests/conftest.py` `isolated_live_data_root`、`deribit_port.py` diff；对照 `plan-doubt-review.md` Cycle 1、`data_commands.py` sync 入口、`macro_incremental_support.py` 收敛模式。

---

## §维度裁决

**FAIL**

（findings 表 ≥1 行非占位）

---

## 计划内问题

| ID        | P   | 标题                                       | 锚点                                                                          | 根因                                                                                                                                                                                                                                                                                                                                            | 修复方案                                                                                                                                                                                                                                                                      | 验证                                                                                                                                                                                                                           |
| --------- | --- | ------------------------------------------ | ----------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| A2-P1-001 | P1  | dispatch `_run_live_sync` 三重重复 DCP-05  | `backend/app/ops/tier_a_live_incremental_dispatch.py:111-418`                 | plan-doubt-review Cycle 1 约定「复用 DCP-05；只接 use*mock=False + harness」，但除 fred（120 行调 `data_commands._sync_fred_macro_incremental`）外，baostock/mootdx/5 macro/sec/av/deribit/cninfo 各写 ~25-50 行 orchestration，与 `data_commands.sync*_\_incremental`、`tests/\_\_incremental_support.bootstrap_\*\_live_e2e_ctx` 逻辑平行维护 | 缩为 **source_id → 既有 runner/CLI** 表（仿 fred）：baostock/mootdx 调 `sync_baostock_incremental`/`sync_mootdx_incremental(dry_run=False)`；macro 族扩展现有 `_run_macro_live` 或 registry；port 源抽单一 `_run_port_live` 参数化 builder。目标 `_run_live_sync` **<120 行** | `uv run pytest tests/test_tier_a_live_dispatch.py tests/test_tier_a_live_harness.py -q`；`QMD_ALLOW_LIVE_FETCH=1 uv run python scripts/tier_a_live_acceptance.py --quick --data-root .audit-sandbox/m-data-03/audit-a2` exit 0 |
| A2-P1-002 | P1  | acceptance 与 dispatch 双份 sandbox 初始化 | `tier_a_live_acceptance.py:180` + `tier_a_live_incremental_dispatch.py:39-48` | `run_source_live_acceptance` 先 `ensure_isolated_db`（migration+registry sync），dispatch 再 `_prepare_sandbox`（migration+raw mkdir），同 DB 双路径                                                                                                                                                                                            | dispatch 假定 DB 已由 acceptance 初始化，删 `_prepare_sandbox` 内重复 `apply_migrations`；或合并为 `tier_a_live_acceptance.ensure_isolated_db` 唯一入口                                                                                                                       | `uv run pytest tests/test_tier_a_live_harness.py -q`；acceptance `--quick` exit 0                                                                                                                                              |
| A2-P2-001 | P2  | 死函数 `_sync_result_passed`               | `backend/app/ops/tier_a_live_acceptance.py:157-165`                           | 编写后未接入 `run_source_live_acceptance`（全仓仅定义处 1 命中）                                                                                                                                                                                                                                                                                | 删除函数；若需 dict 形态解析，复用 dispatch `_extract_sync_status`                                                                                                                                                                                                            | `rg _sync_result_passed` 零命中；`uv run pytest tests/test_tier_a_live_harness.py -q`                                                                                                                                          |
| A2-P2-002 | P2  | `run_tier_a_live_incremental` 不可达分支   | `backend/app/ops/tier_a_live_incremental_dispatch.py:454-459`                 | 454-457 已将 `COMPLETED`+0 rows normalize 为 `EMPTY_RESPONSE`，458-459 第二处 `if sync_status == "COMPLETED"` 永假                                                                                                                                                                                                                              | 删 458-459；保留 normalize 与 detail 拼接一处                                                                                                                                                                                                                                 | `uv run pytest tests/test_tier_a_live_dispatch.py -q`                                                                                                                                                                          |
| A2-P2-003 | P2  | harness 重复负向 gate 测                   | `tests/test_tier_a_live_harness.py:111-140`                                   | `test_liveFetchGate_*` 与 `test_livePort_noSilentFallback*` 同调 `create_fred_fetch_port(use_mock=False)` + 同断言，docstring 目的重叠                                                                                                                                                                                                          | 合并为单测或 `@pytest.mark.parametrize("label", [...])`；保留 S00「无 env 闸 / 无 silent fallback」单一证据                                                                                                                                                                   | `uv run pytest tests/test_tier_a_live_harness.py -q`；用例数 -1、断言等价                                                                                                                                                      |

---

## 计划外发现

| ID        | P   | 标题                                   | 锚点                                                                                                                                                                         | 根因                                                                                                                                           | 修复方案                                                                                                             | 验证                                                                                                                      |
| --------- | --- | -------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| A2-P2-004 | P2  | 双份 pass-status 常量                  | `tier_a_live_acceptance.py:27` · `tier_a_live_incremental_dispatch.py:19`                                                                                                    | 两处独立 `frozenset`；仓内已有 `macro_incremental_common._SERIES_SUCCESS_STATUSES`                                                             | 抽 `tier_a_live_status.py` 或复用 common 并扩展 `OK/SUCCESS/PLANNED`；两模块 import 同一常量                         | `rg '\_PASS_SYNC_STATUSES\\                                                                                               | \_PASS_STATUSES'` 仅定义 1 处；`uv run pytest tests/test_tier_a_live_dispatch.py -q` |
| A2-P3-001 | P3  | port 源 live bootstrap 未随 macro 收敛 | `fred_macro_incremental_support.py:76-117` · `deribit_incremental_support.py:71-108` · `alpha_vantage/cninfo/sec_edgar_incremental_support.py` 各 `bootstrap_*_live_e2e_ctx` | macro 5 源已用 `bootstrap_macro_live_e2e_ctx`；fred/deribit/av/cninfo/sec 仍各 ~35-44 行相同骨架（env·ResourceGuard·db·raw·port·orch·service） | 新增 `tests/live_incremental_support.py` 泛型 `bootstrap_port_live_e2e_ctx(...)`；各 support 文件保留源特有常量/seed | 五文件各减 ≥20 行；`uv run pytest tests/test_*_incremental_e2e.py -m network -q`（`--run-network`）                       |
| A2-P3-002 | P3  | dispatch 未使用 import                 | `tier_a_live_incremental_dispatch.py:240`                                                                                                                                    | `create_world_bank_fetch_port` import；`port_factory` 实际用 `create_world_bank_incremental_port`                                              | 删 line 240                                                                                                          | `ruff check backend/app/ops/tier_a_live_incremental_dispatch.py` 或 `uv run pytest tests/test_tier_a_live_dispatch.py -q` |

已对抗搜索：`tests/*incremental_support.py` 全目录 · `test_*_incremental_e2e.py` live 段 · `tier_a_live_*` 生产模块 · `deribit_port.py` diff；`deribit_port` live 修复判定为必要非 bloat；`LiveIncrementalOutcome.passed` 仅测试消费（`test_tier_a_live_dispatch.py`），属轻微 YAGNI，未单独开 finding（<20 行且已有测试价值）。

[REDACTED]
