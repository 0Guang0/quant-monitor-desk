# Research: SYNC-06 拆票与三件套对齐

- **Query**: WAVE0 INDEX §0.2 + §6 要求 SYNC-06 拆 06A/B/C；同步 vertical-slices、MASTER、implement.jsonl
- **Scope**: internal
- **Date**: 2026-06-28

## Findings

### WAVE0 SSOT 位置

| File Path | Description |
|-----------|-------------|
| `docs/implementation_tasks/ROUND_3_VERIFIED_AUDIT_CLEANUP/BATCH_3V_VERIFIED_AUDIT_CLEANUP/WAVE0_BATCH3V_TO_ISSUES_INDEX.md` | §0.2 quiz 裁决；§6 C04 竖条 + SYNC-06A/B/C issue 骨架 |
| **worktree 缺口** | ~~上述文件 **尚未** 出现在 worktree~~ → **已入库**（1290b2e 起） |

### MASTER §8/§9 映射（Plan 1290b2e 已冻结）

| 旧 | 新 ID | MASTER §9 | 证据文件（路径 A） |
|----|-------|-----------|-------------------|
| SYNC-06 单步 | SYNC-06A | **9.6** | `9.6-red.txt` / `9.6-green.txt`（recovery smoke / impl） |
| — | SYNC-06B | **9.7** | `9.7-red.txt` / `9.7-green.txt`（crash + recovery pytest 全量） |
| — | SYNC-06C | **9.8** | `registry_proposed_delta.yaml` + `repair-evidence/registry-ready.md` |

**已执行分支现状（路径 A）：** 既有 `9.6-*` 证据同时覆盖 06A+06B；`evidence_index.json` 中 `9.7` retroactive 指向 `9.6-green.txt`（见 MASTER §9.7 说明）。

### implement.jsonl 状态（Plan 1290b2e 已写入）

Boot 块保留；vertical-slices / WAVE0 / context-closure / §9.6–9.8 指针 **已落盘**（见 task 根 `implement.jsonl`）。

### integration-ledger.md 须改锚点

| source | 旧 for_ac_step | 新 for_ac_step |
|--------|----------------|----------------|
| `research/vertical-slices.md` | SYNC-01..06 | SYNC-BOOT..05 + 06A/B/C |

### 三件套清单（v3 轨道 · manifest_protocol_version 3）

| 件 | 路径 | SYNC-06 拆票状态 |
|----|------|------------------|
| 活卡/MASTER | `MASTER.plan.md` | **已冻结** §8 06A/B/C；§9.6/9.7/9.8 |
| implement | `implement.jsonl` | **已更新** WAVE0 + context-closure + §9.6–9.8 |
| 垂直切片 | `research/vertical-slices.md` | **已同步** WAVE0 §6 |
| 追溯 | `research/original-plan-trace.md` | **已同步** 06A/B/C 行 |
| AUDIT | `AUDIT.plan.md` | **已引用** §9.7 pytest / §9.8 handoff（A5） |

### validate-plan-freeze / check_docs_specs_indexed（2026-06-28 Plan 质检）

| 命令 | 结果 | 说明 |
|------|------|------|
| `python .trellis/scripts/task.py validate-plan-freeze .trellis/tasks/round3v-sync-support-matrix-recovery` | **exit 0** | 1290b2e + Plan 质检修复后复检 |
| `uv run python scripts/check_docs_specs_indexed.py` | **exit 0** | — |

### C04 ← C01 Execute 门控

| 阶段 | 规则 |
|------|------|
| Plan | 可与 C01 并行 |
| Execute SYNC-06* | rebase **已 merge** 的 `fix/round3v-contract-drift-write-modes`；只读 `write_contract.yaml` / `WriteManager` |
| Merge | Wave 0 序 6，**推荐** C01 已合 integration |

## Caveats / Not Found

- ~~worktree **缺少** `WAVE0_BATCH3V_TO_ISSUES_INDEX.md`~~ → **已闭合**
- `evidence_index.json`：`9.7` retroactive 指向 `9.6-green.txt`；`9.8` → `registry-ready.md`
