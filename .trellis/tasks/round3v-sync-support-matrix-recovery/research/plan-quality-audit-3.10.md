# Plan 质检 §3.10 — B3V-SYNC

> Playbook `BATCH_3V_COORDINATOR_PLAYBOOK.md` §3.10 Agent-2 必填

| 路径 | 已入 MASTER/implement 或 DEBT.plan | 摘要一句 | 遗漏风险 |
|------|-----------------------------------|----------|----------|
| `BATCH_3V_COORDINATOR_PLAYBOOK.md` §3.1 | MASTER §0 Source Context §3.1 | 共用底座与全局规则 | 无 |
| `BATCH_3V_COORDINATOR_PLAYBOOK.md` §3.5 | MASTER §0 §3.5 + implement.jsonl | SYNC 专属输入与 write_manager 只读 | 无 |
| `B02_04_sync_job_support_and_recovery.md` | MASTER §1–§8 + implement | VR-SYNC-002/001 与六切片 | 无 |
| `specs/contracts/sync_job_contract.yaml` | MASTER §5 §9.1 + implement | implemented/reserved 契约 | 无 |
| `backend/app/sync/orchestrator.py` | MASTER §4 §9 + implement | deferred + run_* 入口 | 无 |
| `backend/app/sync/runners.py` | MASTER §9.5 + implement | crash-window 注入点 | 无 |
| `backend/app/db/write_manager.py` | MASTER §0 只读 + implement | 模式参考；禁止改语义 | 无 |
| `specs/contracts/write_contract.yaml` | MASTER §0 只读 + implement | B3V-OPS 独占 | 合并须在 OPS 后 |
| `docs/decisions/ADR-001-*.md` | MASTER §2 §9.5 + implement | COMPLETED 在写提交后 | 无 |
| `tests/test_sync_orchestrator.py` | MASTER §5.1 §9 + implement | 主测试（替代 test_sync_runners） | 无 |
| `tests/test_r3x_residual_open_items_closure.py` | MASTER §9.4 + implement | advA3_016 purpose 更新 | 无 |
| `tests/test_write_manager.py` | MASTER §5.4 + implement | 回归 | 无 |
| `docs/UNRESOLVED_ISSUES_REGISTRY.md` | MASTER §9.4 | D2-P1-1 proposed delta | 主会话批闭合 |
| `quant_monitor_desk_verified_audit_report_2026-06-25_v3_INDEX.md` | MASTER §2 + implement | VR 路由 | 无 |
| `research/sync-001-handoff.md` | MASTER §9.6 | VR-SYNC-001 路径 B 落盘 | 仅路径 B 时 Execute 创建 |
| `docs/modules/sync_jobs.md` | — | **不存在** | 已纠偏至契约 YAML + data_sync_orchestrator 模块 doc |

**复检结论**：遗漏风险列均为「无」或已纠偏/门控。
