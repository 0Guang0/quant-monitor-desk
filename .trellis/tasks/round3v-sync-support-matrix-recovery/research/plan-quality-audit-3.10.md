# Plan 质检 §3.10 — B3V-SYNC

> Playbook `BATCH_3V_COORDINATOR_PLAYBOOK.md` §3.10 Agent-2 必填  
> **复检：** 2026-06-28 · Plan 1290b2e（SYNC-06A/B/C → §9.6/9.7/9.8）

| 路径 | 已入 MASTER/implement 或 DEBT.plan | 摘要一句 | 遗漏风险 |
|------|-----------------------------------|----------|----------|
| `BATCH_3V_COORDINATOR_PLAYBOOK.md` §3.1 | MASTER §0 Source Context §3.1 | 共用底座与全局规则 | 无 |
| `BATCH_3V_COORDINATOR_PLAYBOOK.md` §3.5 | MASTER §0 §3.5 + implement.jsonl | SYNC 专属输入与 write_manager 只读 | 无 |
| `B02_04_sync_job_support_and_recovery.md` | MASTER §1–§8 + implement L7 | VR-SYNC-002/001 与 SYNC-BOOT..05 + 06A/B/C | 无 |
| `WAVE0_BATCH3V_TO_ISSUES_INDEX.md` §0.2 + §6 | MASTER §1.6 + implement L7 | SYNC-06 拆票 SSOT | 无 |
| `research/vertical-slices.md` | MASTER §8 + implement L6 | SYNC-BOOT..05 + 06A/B/C 垂直切片 | 无 |
| `specs/contracts/sync_job_contract.yaml` | MASTER §5 §9.1 + implement L16 | implemented/reserved 契约 | 无 |
| `backend/app/sync/orchestrator.py` | MASTER §4 §9 + context-closure.md | deferred + recovery（E11a 指针） | 无 |
| `backend/app/sync/runners.py` | MASTER §9.5 + context-closure.md | crash-window hook（E11a 指针） | 无 |
| `backend/app/db/write_manager.py` | MASTER §0 只读 + implement L20 | 模式参考；禁止改语义 | 无 |
| `specs/contracts/write_contract.yaml` | MASTER §0 只读 + implement L17 | B3V-OPS 独占；合并须在 OPS 后 | 无 |
| `docs/decisions/ADR-001-*.md` | MASTER §2 §9.5–9.8 + implement L18 | COMPLETED 在写提交后 | 无 |
| `tests/test_sync_orchestrator.py` | MASTER §5.1 §9 + context-closure.md | 主测试（替代 test_sync_runners） | 无 |
| `tests/test_r3x_residual_open_items_closure.py` | MASTER §9.4 + implement L19 | advA3_016 purpose 更新 | 无 |
| `tests/test_write_manager.py` | MASTER §5.4 + implement L20 | 回归 | 无 |
| `docs/UNRESOLVED_ISSUES_REGISTRY.md` | MASTER §3.1 三件套 + implement L25 | D2-P1-1 proposed delta；主会话批闭合 | 无 |
| `docs/AUDIT_DEFERRED_REGISTRY.md` | MASTER §3.1 三件套 + implement L26 | defer 行只读对照 | 无 |
| `quant_monitor_desk_verified_audit_report_2026-06-25_v3_INDEX.md` | MASTER §2 + implement L11 | VR-SYNC-001/002 路由 | 无 |
| `research/context-closure.md` | implement L8 + MASTER §0.3 | E11 动态闭包；§9.6–9.7 接线指针 | 无 |
| `research/registry_proposed_delta.yaml` | MASTER §9.4 §9.8 + implement L23 | SYNC-06C 关账 proposed delta | 无 |
| `research/sync-001-handoff.md` | MASTER §9.6–9.8 路径 B | VR-SYNC-001 re-defer 落盘（路径 B 时创建） | 无 |
| `repair-evidence/sync-crash-window-runbook.md` | MASTER §9.8 + implement L24 | 运维 recovery runbook | 无 |
| `docs/modules/sync_jobs.md` | MASTER §0 纠偏 | **不存在**；已纠偏至契约 YAML + `data_sync_orchestrator.md` | 无 |
| `tests/test_sync_runners.py` | MASTER §5.1 substitution | **不存在**；已纠偏至 `test_sync_orchestrator.py` | 无 |

**复检结论**：遗漏风险列 **全为「无」**；幽灵路径已纠偏并写入 MASTER §5.1。
