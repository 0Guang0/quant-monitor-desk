# Contract Compliance Evidence — R3-DCP-05

> **Purpose:** 工程契约还债关账（doubt 跟进 · 2026-07-02）  
> **Branch:** `feature/wave4-r3-dcp-05-tier-a`

---

## 1. GitNexus

### 1.1 `detect_changes`（scope=all vs master）

| 字段                      | 值      |
| ------------------------- | ------- |
| changed_files             | 39      |
| changed_symbols (indexed) | 12      |
| affected_processes        | 0       |
| risk_level                | **low** |

未索引到 `tier_a_sync_router` / `sync_baostock_incremental` 等 CLI 符号（索引滞后于 Repair diff）。

### 1.2 `impact()`（upstream · summaryOnly）

| target                             | 结果                    |
| ---------------------------------- | ----------------------- |
| `sync_baostock_incremental`        | not found（索引 stale） |
| `_require_audit_sandbox_data_root` | not found               |
| `sync_tier_a_by_source_id`         | not found               |

**Remediation:** `node .gitnexus/run.cjs analyze` 后复跑 impact（2026-07-02 复跑仍 not found — MCP 索引滞后）。

**人工 blast radius（grep）：**

| symbol                             | 直接调用方                                                                                |
| ---------------------------------- | ----------------------------------------------------------------------------------------- |
| `sync_tier_a_by_source_id`         | `data_commands.sync_plan` · `tests/test_qmd_data_sync_tier_a_router.py`                   |
| `sync_baostock_incremental`        | `tier_a_sync_router` · `data_commands.sync_plan` · `tests/test_qmd_data_sync_baostock.py` |
| `_require_audit_sandbox_data_root` | `sync_tier_a_by_source_id` · `sync_baostock_incremental` · `sync_mootdx_incremental`      |

风险：**LOW–MEDIUM**（CLI + 测试；无 DB schema / 公共 API 面变更）。

---

## 2. 门禁（关账顺序）

| 顺序 | 命令                                                                                          | 期望                                                                | 证据时间                            |
| ---- | --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- | ----------------------------------- |
| 1    | `uv run pytest -q`                                                                            | exit 0                                                              | 2026-07-02                          |
| 2    | `python .trellis/scripts/task.py validate-plan-freeze .trellis/tasks/wave4-r3-dcp-05-tier-a`  | exit 0                                                              | 2026-07-02                          |
| 3    | `python .trellis/scripts/task.py validate-repair-close .trellis/tasks/wave4-r3-dcp-05-tier-a` | exit 0                                                              | 2026-07-02（含 DOUBT-001 阶段外置） |
| 4    | `uv run python scripts/loop_maintain.py`                                                      | OK                                                                  | 2026-07-02                          |
| —    | `validate-audit-handoff`                                                                      | **Repair 后不适用**（ledger 已「已修复」；A9 门禁仅在进 Repair 前） | —                                   |

活卡 §5 `[x]` 勾选 **在本文件门禁全绿之后**（见 `R3_DCP_05_TIER_A_INCREMENTAL.md` §5 脚注）。

---

## 3. TDD 还债说明

| 批次                              | 契约                    | 实际                                             | 补救                                                                                                       |
| --------------------------------- | ----------------------- | ------------------------------------------------ | ---------------------------------------------------------------------------------------------------------- |
| Repair 29 项                      | 正式代码先 RED 再 GREEN | 实现主导、测后补                                 | 全量 pytest + 维度 e2e 作回归锚                                                                            |
| doubt 跟进（sandbox/fail-closed） | 同上                    | 先改 `data_commands`/`tier_a_sync_router` 后加测 | `test_tierASyncRouter_dryRun_nonSandbox*` / `userLive*` / `baostock_resourceGuard*` + fred sandbox fixture |

**声明：** 历史顺序违反 TDD；当前测网阻止回退，不改写已交付测试的「目的/目标」。

---

## 4. 阶段外置（ponytail · doubt RECONCILE）

| ID                            | 问题                                          | disposition | 登记                                                                                                              |
| ----------------------------- | --------------------------------------------- | ----------- | ----------------------------------------------------------------------------------------------------------------- |
| `ACC-MOOTDX-DRYRUN-ROUTE-001` | mootdx dry-run `selected_source_id` 可≠mootdx | 阶段外置    | `docs/quality/待修复清单.md` §4 · `PROJECT_IMPLEMENTATION_ROADMAP.md` §3.5.2 · `audit-repair-ledger.md` DOUBT-001 |

代码：`data_commands.sync_mootdx_incremental` ponytail 注释；真跑仍 `selected_source_id == mootdx` fail-closed。

---

## 5. doubt 跟进代码摘要

- `_require_audit_sandbox_data_root`：拒 non-`.audit-sandbox` + `user-live`
- `sync_baostock_incremental` / `sync_mootdx_incremental` dry-run：sandbox 门控、水位仅 sandbox 可读、guard/route fail-closed
- `sync_plan`：删除 unreachable fred dry-run 分支
