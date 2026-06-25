# Original plan trace — B3V-C01

| 字段 | 值 |
| ---- | -- |
| Round / Batch | Round 3V.1 · `BATCH_3V_VERIFIED_AUDIT_CLEANUP` |
| Manifest ID | `B3V-C01` |
| Playbook ID | `B3V-OPS` |
| 任务卡 | `B02_01_contract_drift_and_write_modes.md` |
| 分支 | `fix/round3v-contract-drift-write-modes` |
| VR-* | `VR-OPS-001`, `VR-WRITE-001` |

## 任务卡切片 → MASTER §8

| 任务卡切片 | MASTER 切片 | VR / AC |
| ---------- | ----------- | ------- |
| B02-OPS-01 | OPS-01 | VR-OPS-001 |
| B02-OPS-02 | OPS-02 | VR-OPS-001 |
| B02-WRITE-01 | WRITE-01 | VR-WRITE-001 |
| B02-WRITE-02 | WRITE-02 | VR-WRITE-001 |
| B02-WRITE-03 | WRITE-03 | VR-WRITE-001 |
| B02-CLOSE-01 | **排除** | 主会话 registry；Plan 禁止 |

## AC 对照

| 任务卡 Done | MASTER AC | 验证 |
| ----------- | --------- | ---- |
| VR-OPS-001 闭合或 re-defer | AC-OPS-DRIFT | §9.1–9.2 · drift pytest |
| VR-WRITE-001 闭合或 re-defer | AC-WRITE-SPLIT + AC-WRITE-RESERVED | §9.3–9.5 · parity pytest |
| 无 production DB mutation | AC-BOUND | §10 · 只读 inspect |
| 漂移可检测 | AC-OPS-DRIFT + AC-WRITE-SPLIT | §5.3 |

## 引用文档

| 文档 | 用途 |
| ---- | ---- |
| `specs/contracts/ops_db_inspect_contract.yaml` | db-inspect SSOT |
| `specs/contracts/write_contract.yaml` | 写模式契约 |
| `backend/app/ops/db_inspector.py` | 运行时对照 |
| `backend/app/db/write_manager.py` | SUPPORTED/UNSUPPORTED |
| `docs/quality/staged_acceptance_policy.md` | 分层验收 |
| `specs/contracts/runtime_versions.md` | runtime 锁 |
