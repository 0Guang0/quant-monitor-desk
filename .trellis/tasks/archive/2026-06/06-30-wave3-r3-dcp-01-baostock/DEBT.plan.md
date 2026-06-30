# Repair/Debt Lite Plan — wave3-r3-dcp-01-baostock

## Source of truth

- **规划 ID:** R3-DCP-01
- **活卡:** `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3_DCP_01_BAOSTOCK_INCREMENTAL.md`
- **INDEX:** `R3_DCP_TO_ISSUES_INDEX.md` §1
- **base branch:** `master`
- **target branch:** `feature/wave3-r3-dcp-01-baostock`
- **worktree:** `../quant-monitor-desk-wt-dcp01`
- **owner agent:** Execute agent（Plan 仅交付本文件）

## Boundary

### allowed files

```text
backend/app/sync/watermark.py                    # 新建
backend/app/sync/watermark*.py                   # 轨 A 拥有
backend/app/sync/runners.py                      # 仅 date→FetchRequest 注入（协调轨 B；共享锁见 §4）
tests/test_sync_runners.py                       # S02 回归（若 runner 行为变更需同步）
tests/service_path_support.py                    # S03 可选 E2E helper（若新建）
backend/app/cli/data_commands.py
backend/app/cli/main.py                          # 若需子命令注册
backend/app/datasources/fetch_ports/baostock_port.py
backend/app/datasources/adapters/baostock.py     # 若 staging 映射需补字段
backend/app/ops/**                               # 仅 baostock 增量 smoke（可选）
tests/test_*baostock*
tests/test_*incremental*                         # 本轨新增
tests/test_catalog.yaml                          # 登记新测；merge 排队
specs/datasource_registry/source_registry.yaml   # 仅 baostock 行
specs/datasource_registry/source_capabilities.yaml
.trellis/tasks/06-30-wave3-r3-dcp-01-baostock/**
```

### forbidden files

```text
backend/app/sync/orchestrator.py                 # 共享锁；CLI 直调 run_incremental，不改 orchestrator
backend/app/datasources/fetch_ports/fred_port.py
backend/app/ops/fred_*.py
tests/test_*fred*
backend/app/db/migrations/**
data/duckdb/quant_monitor.duckdb
```

### production/data boundary

- 默认 `QMD_DATA_ROOT=.audit-sandbox/user-live`（或测试 `tmp_path`）
- **禁止** silent 写 canonical `data/duckdb/`
- Live fetch 须 `QMD_ALLOW_LIVE_FETCH` + `gate_live_fetch_port`；CI 默认 replay

### explicit non-goals

- fred 宏观增量（R3-DCP-02）
- FullLoad / Backfill 产品 CLI
- 新 schema migration
- CN 交易日历完整实现
- Tier A 全源扩展（Wave 4）

---

## Vertical slices（Execute 阶段 · 共 5 片）

| Slice               | Source ID                    | AC                                                        | Allowed files                                                                                                | Forbidden files                | Verification                                                                               | Evidence                                  |
| ------------------- | ---------------------------- | --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ | ------------------------------ | ------------------------------------------------------------------------------------------ | ----------------------------------------- |
| **S01-WATERMARK**   | R3-DCP-01 §5                 | 空表/有数据/边界日 watermark 单测绿                       | `sync/watermark.py`, `tests/test_baostock_incremental_watermark.py`                                          | fred\*, migration              | `uv run pytest tests/test_baostock_incremental_watermark.py -q`                            | `research/execute-evidence/s01-green.txt` |
| **S02-RUNNER-WIRE** | R3-DCP-01 §4 · INDEX P4 前置 | `FetchRequest` 携带 `start_time/end_time`；spec.date 透传 | `sync/runners.py`, `tests/test_sync_runners.py`（回归）, watermark tests 扩面                                | `orchestrator.py` 大改         | `uv run pytest tests/test_baostock_incremental_watermark.py tests/test_sync_runners.py -q` | `s02-green.txt`                           |
| **S03-E2E-INCR**    | 活卡 §5 · INDEX P4           | service + orchestrator replay 端到端写 `security_bar_1d`  | `baostock_port.py`, `tests/test_baostock_incremental_e2e.py`, `tests/service_path_support.py`（若需 helper） | `fred_port`, `orchestrator.py` | `uv run pytest tests/test_baostock_incremental_e2e.py -q`                                  | `s03-green.txt`                           |
| **S04-IDEMPOTENT**  | 活卡 §5                      | 重复跑行数不增                                            | 同上 + 可能 `adapters/baostock.py`                                                                           | —                              | e2e 内 `test_*repeatRun*` + `uv run pytest tests/test_baostock_incremental_e2e.py -q`      | `s04-green.txt`                           |
| **S05-CLI**         | INDEX P5                     | `qmd data sync` dry-run 可审计；replay 真跑 smoke         | `cli/data_commands.py`, `cli/main.py`, `tests/test_qmd_data_sync_baostock.py`                                | —                              | `uv run pytest tests/test_qmd_data_sync_baostock.py -q`                                    | `s05-green.txt`                           |

**Registry 切片（主会话协调，可并入 S05 或单独 merge）：**

| Slice            | AC                                                           | Files                                                                                           | Verification                             |
| ---------------- | ------------------------------------------------------------ | ----------------------------------------------------------------------------------------------- | ---------------------------------------- |
| **S06-REGISTRY** | test_catalog 登记；capabilities/registry 与 replay path 一致 | `tests/test_catalog.yaml`, `source_capabilities.yaml`, `source_registry.yaml`（仅 baostock 行） | `uv run python scripts/loop_maintain.py` |

> Plan 阶段切片 **P1–P2**（调研 + Plan-Audit）由主会话闸门完成，不计入上表。

---

## Execute 顺序

```text
S01 → S02 → S03 → S04 → S05 → S06（可与 S05 并行由 coordinator）
```

每片 TDD：RED 证据 → GREEN → 本片 pytest。

---

## Merge gate

| 检查          | 命令                                                                                                                                        |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| 靶向测试      | `uv run pytest tests/test_baostock_incremental_watermark.py tests/test_baostock_incremental_e2e.py tests/test_qmd_data_sync_baostock.py -q` |
| 全量          | `uv run pytest -q` exit 0                                                                                                                   |
| Loop maintain | `uv run python scripts/loop_maintain.py`                                                                                                    |
| GitNexus      | Execute 改 symbol 前 `impact()`；提交前 `detect_changes()`                                                                                  |
| 隔离库证明    | 测试日志 / evidence 显示 `tmp_path` 或 `QMD_DATA_ROOT`，无 canonical duckdb 写                                                              |

---

## Audit / Repair 承接

- Execute 完成后派发 A1–A8（见 `AUDIT.plan.md`）
- P6 Repair：ledger 无待修复 + 全量 pytest 绿 → 主会话 merge

---

## 调研依赖（Execute Boot 必读）

1. `research/plan-boot.md`
2. `research/reference-adoption-dcp01.md`
3. `research/architecture-dcp01.md`
4. 活卡 + INDEX §1
5. `backend/app/sync/orchestrator.py`, `runners.py`, `baostock_port.py`
6. **`agent-prompts/EXECUTE-REFERENCE-READ-GATE.md`** — 主仓 `C:\Users\Guang\Desktop\quant-monitor-desk\参考项目\` 实读清单
7. **RED 前产出** `research/execute-reference-read-evidence.md`（门禁表满才可 S01 RED）

### 主仓参考项目（worktree 无 `参考项目/`）

| 文件                                                              | 等级                        |
| ----------------------------------------------------------------- | --------------------------- |
| `参考项目/EasyXT/data_manager/auto_data_updater.py`               | L2 概念 / forbidden runtime |
| `参考项目/EasyXT/data_manager/unified_data_interface.py` L172-237 | forbidden 反例              |
