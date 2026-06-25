# Original Plan Trace — B3V-SYNC

| 来源 | MASTER §2 AC | 备注 |
|------|--------------|------|
| `B02_04` §2 VR-SYNC-002 | AC-SYNC-002 | implemented/reserved 契约 + runtime parity |
| `B02_04` §2 VR-SYNC-001 | AC-SYNC-001 | crash-window 测试或 3F.4 handoff |
| `B02_04` §5 B02-SYNC-01 | SYNC-01 | 契约 support matrix |
| `B02_04` §5 B02-SYNC-02 | SYNC-02 | implemented parity test |
| `B02_04` §5 B02-SYNC-03 | SYNC-03 | reserved deferred error |
| `B02_04` §5 B02-SYNC-04 | SYNC-04 | registry D2-P1-1 文案 |
| `B02_04` §5 B02-SYNC-05 | SYNC-05 | R3-PARTIAL-5 审查 |
| `B02_04` §5 B02-SYNC-06 | SYNC-06 | VR-SYNC-001 关闭或 handoff |
| `PROJECT_IMPLEMENTATION_ROADMAP.md` R3V-B02-SYNC-01/02 | AC-SYNC-002/001 | Batch 3V.1 |
| `BATCH_3V_COORDINATOR_PLAYBOOK.md` §8.4 | AC-SYNC-PLAYBOOK | PASS 子 AC |
| `docs/decisions/ADR-001-ingestion-validation-write-transaction-boundary.md` | SYNC-05 约束 | COMPLETED 在写提交后单独 transition |
| Registry `D2-P1-1` | SYNC-04 | runners 未实现 |
| Registry `R3-PARTIAL-5` | SYNC-05/06 | COMPLETED vs write crash window |
