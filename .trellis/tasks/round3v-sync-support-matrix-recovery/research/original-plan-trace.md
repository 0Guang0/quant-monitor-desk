# Original Plan Trace — B3V-SYNC

> 映射：`NNN_*.md` / WAVE0 INDEX → MASTER §2 AC · §8/§9 步骤  
> **SYNC-06 拆票 SSOT：** `WAVE0_BATCH3V_TO_ISSUES_INDEX.md` §0.2 + §6

| 来源 | MASTER §2 AC / §9 | 备注 |
|------|-------------------|------|
| `B02_04` §2 VR-SYNC-002 | AC-SYNC-002 · §9.1–9.3 | implemented/reserved 契约 + runtime parity |
| `B02_04` §2 VR-SYNC-001 | AC-SYNC-001 · §9.5–9.8 | crash-window 三票（06A/B/C） |
| `B02_04` §5 B02-SYNC-01 | SYNC-01 · §9.1 | 契约 support matrix |
| `B02_04` §5 B02-SYNC-02 | SYNC-02 · §9.2 | implemented parity test |
| `B02_04` §5 B02-SYNC-03 | SYNC-03 · §9.3 | reserved deferred error |
| `B02_04` §5 B02-SYNC-04 | SYNC-04 · §9.4 | registry D2-P1-1 文案 |
| `B02_04` §5 B02-SYNC-05 | SYNC-05 · §9.5 | R3-PARTIAL-5 审查 + hook |
| `B02_04` §5 B02-SYNC-06 | **拆为 06A/B/C** | 见下表 |
| WAVE0 §6 SYNC-06A | SYNC-06A · §9.6 | 最小 recovery 实现 **或** handoff 草稿（路径 B） |
| WAVE0 §6 SYNC-06B | SYNC-06B · §9.7 | crash-window pytest；路径 B **skip** |
| WAVE0 §6 SYNC-06C | SYNC-06C · §9.8 | VR-SYNC-001 关账 **或** handoff 定稿 + re-defer |
| `PROJECT_IMPLEMENTATION_ROADMAP.md` R3V-B02-SYNC-01/02 | AC-SYNC-002/001 | Batch 3V.1 |
| `BATCH_3V_COORDINATOR_PLAYBOOK.md` §8.4 | AC-SYNC-PLAYBOOK | PASS 子 AC |
| `docs/decisions/ADR-001-ingestion-validation-write-transaction-boundary.md` | SYNC-05/06 约束 | COMPLETED 在写提交后单独 transition |
| Registry `D2-P1-1` | SYNC-04 | runners 未实现 → deferredId delta |
| Registry `R3-PARTIAL-5` | SYNC-05..06C | COMPLETED vs write crash window |

## 任务卡 B02-SYNC-06 → 三票映射

| 原卡切片 | WAVE0 ID | GitHub issue 建议标题 |
|----------|----------|----------------------|
| B02-SYNC-06（实现） | SYNC-06A | `[B3V-SYNC] VR-SYNC-001 最小恢复实现` |
| B02-SYNC-06（测试） | SYNC-06B | `[B3V-SYNC] crash-window pytest WRITING→COMPLETED` |
| B02-SYNC-06（关账） | SYNC-06C | `[B3V-SYNC] VR-SYNC-001 关账或 handoff 闭合` |
