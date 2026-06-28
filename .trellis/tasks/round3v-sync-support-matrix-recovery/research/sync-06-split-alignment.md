# Research: SYNC-06 拆票与三件套对齐

- **Query**: WAVE0 INDEX §0.2 + §6 要求 SYNC-06 拆 06A/B/C；同步 vertical-slices、MASTER、implement.jsonl
- **Scope**: internal
- **Date**: 2026-06-28

## Findings

### WAVE0 SSOT 位置

| File Path | Description |
|-----------|-------------|
| `docs/implementation_tasks/ROUND_3_VERIFIED_AUDIT_CLEANUP/BATCH_3V_VERIFIED_AUDIT_CLEANUP/WAVE0_BATCH3V_TO_ISSUES_INDEX.md` | §0.2 quiz 裁决；§6 C04 竖条 + SYNC-06A/B/C issue 骨架 |
| **worktree 缺口** | 上述文件 **尚未** 出现在 `quant-monitor-desk-wt-b3v-sync` worktree（仅主仓 `quant-monitor-desk` 有 untracked 副本） |

### MASTER §8/§9 建议映射（Plan agent 须写入 MASTER.plan.md）

| 旧 | 新 ID | MASTER §9 | 证据文件（路径 A） |
|----|-------|-----------|-------------------|
| SYNC-06 单步 | SYNC-06A | **9.6** | `9.6-red.txt` / `9.6-green.txt`（recovery smoke / impl） |
| — | SYNC-06B | **9.7** | `9.7-red.txt` / `9.7-green.txt`（crash + recovery pytest 全量） |
| — | SYNC-06C | **9.8** | `registry_proposed_delta.yaml` + `repair-evidence/registry-ready.md` |

**已执行分支现状（路径 A）：** 既有 `9.6-*` 证据同时覆盖 06A+06B 实现与 pytest；Plan 重冻结时可：
- 保留 `9.6` 映射 06A，复制/拆分说明至 `9.7` 指向同一 green（retroactive），或
- Execute 重跑时严格分步产出 `9.7-*`

### implement.jsonl 须更新行（Plan agent 写入 task 根，非 research）

Boot 块保留；**至少**改以下 reason 并 **追加** WAVE0 + 分步测试指针：

```jsonl
{"file": ".trellis/tasks/round3v-sync-support-matrix-recovery/research/vertical-slices.md", "reason": "extract: SYNC-BOOT..05 + 06A/B/C | for: §8 order"}
{"file": "docs/implementation_tasks/ROUND_3_VERIFIED_AUDIT_CLEANUP/BATCH_3V_VERIFIED_AUDIT_CLEANUP/WAVE0_BATCH3V_TO_ISSUES_INDEX.md", "reason": "extract: §0.2 §6 SYNC-06 split SSOT | for: §8 §9.6-9.8"}
{"file": "docs/decisions/ADR-001-ingestion-validation-write-transaction-boundary.md", "reason": "extract: COMPLETED ordering | for: §9.5-9.8"}
{"file": "tests/test_sync_orchestrator.py", "reason": "extract: parity/deferred/crash/recovery tests | for: §9.1-9.3 §9.7 SYNC-06B"}
{"file": "backend/app/sync/orchestrator.py", "reason": "extract: recover_stuck_writing_job | for: §9.6 SYNC-06A"}
{"file": "backend/app/sync/runners.py", "reason": "extract: post_write_pre_complete_hook | for: §9.5 §9.6"}
{"file": ".trellis/tasks/round3v-sync-support-matrix-recovery/research/registry_proposed_delta.yaml", "reason": "extract: VR-SYNC proposed close | for: §9.8 SYNC-06C"}
{"file": ".trellis/tasks/round3v-sync-support-matrix-recovery/repair-evidence/sync-crash-window-runbook.md", "reason": "extract: ops recovery runbook | for: §9.8 SYNC-06C"}
```

### integration-ledger.md 须改锚点

| source | 旧 for_ac_step | 新 for_ac_step |
|--------|----------------|----------------|
| `research/vertical-slices.md` | SYNC-01..06 | SYNC-BOOT..05 + 06A/B/C |

### 三件套清单（v3 轨道 · manifest_protocol_version 3）

| 件 | 路径 | SYNC-06 拆票状态 |
|----|------|------------------|
| 活卡/MASTER | `MASTER.plan.md` | **待更新** §8 行 6→06A/B/C；§9.6 拆 9.6/9.7/9.8 |
| implement | `implement.jsonl` | **待更新** vertical-slices reason + WAVE0 + §9.6-9.8 指针 |
| 垂直切片 | `research/vertical-slices.md` | **已同步** WAVE0 §6 |
| 追溯 | `research/original-plan-trace.md` | **已同步** 06A/B/C 行 |
| AUDIT | `AUDIT.plan.md` | 须引用 §9.7/9.8 AC（若存在） |

### validate-plan-freeze / check_docs_specs_indexed（2026-06-28 快照）

| 命令 | 结果 | 说明 |
|------|------|------|
| `python .trellis/scripts/task.py validate-plan-freeze .trellis/tasks/round3v-sync-support-matrix-recovery` | **exit 0** | 基于**旧**单步 SYNC-06 MASTER；更新 MASTER 后须重跑 |
| `uv run python scripts/check_docs_specs_indexed.py` | **exit 0** | WAVE0 文件未入库时不影响（未在 generated index 强制项） |

### C04 ← C01 Execute 门控

| 阶段 | 规则 |
|------|------|
| Plan | 可与 C01 并行 |
| Execute SYNC-06* | rebase **已 merge** 的 `fix/round3v-contract-drift-write-modes`；只读 `write_contract.yaml` / `WriteManager` |
| Merge | Wave 0 序 6，**推荐** C01 已合 integration |

## Caveats / Not Found

- worktree **缺少** `WAVE0_BATCH3V_TO_ISSUES_INDEX.md` — 主会话须 cherry-pick 或 copy 自主仓后再 commit
- Research agent **无权** 修改 `MASTER.plan.md` / `implement.jsonl` / git commit — 须 Plan 主 agent 完成剩余三件套与 worktree commit
- 分支已有 Execute 证据（`9.0`–`9.6` green）；拆票后 `evidence_index.json` 须 Plan/Execute 协调是否追加 `9.7`/`9.8`
