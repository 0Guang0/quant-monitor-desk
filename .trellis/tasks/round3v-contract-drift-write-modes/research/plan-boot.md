# Plan Boot — round3v-contract-drift-write-modes (B3V-OPS / B3V-C01)

## 用户目标

消除 `ops db-inspect` 与 `WriteManager` 写模式在 YAML 契约与运行时之间的歧义；用可检测漂移测试证明 `VR-OPS-001`、`VR-WRITE-001` 可闭合（**registry 行由主会话收口，本任务禁止 registry 闭合**）。

## 依赖与 gate

| 依赖 | 状态 | Plan 处理 |
| ---- | ---- | --------- |
| Post Batch 01 master 基线 | 已满足 | 只读 inspect + 既有 WriteManager |
| `B3V-REG` / `B3V-L5R` 并行 | 可并行 | 禁止改 registry 三件套 |
| `B3V-DATA` schema_hash | 后续 | 禁止改 validation_gate |
| GitNexus `WriteManager` impact | HIGH (31 upstream) | Execute 每步 `impact()`；最小 diff |

## AC 草稿

- **AC-OPS-DRIFT**：`ops_db_inspect_contract.yaml` 为 key_tables + deferred_item_mapping 唯一真源（或运行时从 YAML 加载）；漂移测试失败即阻断。
- **AC-WRITE-SPLIT**：`write_contract.yaml` 区分 `implemented_modes` / `reserved_modes`；`implemented_modes == WriteManager.SUPPORTED_MODES`。
- **AC-WRITE-RESERVED**：reserved 模式稳定 `ValueError`，不执行写、不伪装可用。
- **AC-BOUND**：无 DB 写、无 live fetch、无 reserved 模式实现、无 production clean write、**无 registry 闭合**。

## 原计划已读

- `docs/implementation_tasks/README.md` + `TASK_INPUT_CONTEXT_INDEX.md`
- `GLOBAL_EXECUTION_RULES.md` · `GLOBAL_TESTING_POLICY.md` · `GLOBAL_RESOURCE_LIMITS.md` · `GLOBAL_TASK_TEMPLATE.md`
- `ROUND_3_VERIFIED_AUDIT_CLEANUP/BATCH_3V_VERIFIED_AUDIT_CLEANUP/README.md`
- `B02_01_contract_drift_and_write_modes.md`（B3V-C01 任务卡）
- `BATCH_3V_TASK_CARD_MANIFEST.md` · `BATCH_3V_HARDENING_RULES.md` · `BATCH_3V_COORDINATOR_PLAYBOOK.md` §3.1+§3.2+§4
- `quant_monitor_desk_verified_audit_report_2026-06-25_v3_INDEX.md`（VR 路由）
- `UNRESOLVED_ITEM_TASK_COVERAGE.md`（B3V-C01 行）

**Phase P0 complete**
