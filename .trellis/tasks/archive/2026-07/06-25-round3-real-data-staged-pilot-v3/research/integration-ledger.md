# Integration Ledger — B01-C04 staged pilot v3

> Plan 5c · v3 context packing

## 打包策略

| 策略            | 含义                       |
| --------------- | -------------------------- |
| inline          | MASTER §0/§3 已摘要        |
| summary+pointer | MASTER 摘要 + 原稿         |
| pointer         | implement extract/for 精读 |
| blocked         | WL 未合并 — Execute 硬停   |

## ledger

| source                                                                                         | category     | strategy        | master_anchor | execute_extract     | for_ac_step   |
| ---------------------------------------------------------------------------------------------- | ------------ | --------------- | ------------- | ------------------- | ------------- |
| `research/integration-ledger.md`                                                               | rule         | inline          | MASTER §0.4   | v3 boot routing     | §9.0          |
| `docs/quality/coordination/BATCH_01_MAIN_SESSION_COORDINATOR_PLAYBOOK.md`                      | rule         | summary+pointer | MASTER §3     | §2.5/§2.6 文件锁    | 全 AC         |
| `docs/implementation_tasks/ROUND_3_DATA_PRODUCTION_READINESS/BATCH_01_HARDENING_RULES.md`      | rule         | summary+pointer | MASTER §0     | §3 授权 YAML        | live fetch    |
| `docs/implementation_tasks/ROUND_3_DATA_PRODUCTION_READINESS/R3E_real_data_staged_pilot_v3.md` | business     | pointer         | MASTER §2     | SP3-01..06 AC       | AC-SP3-\*     |
| `docs/implementation_tasks/ROUND_3_DATA_PRODUCTION_READINESS/R3D_model_input_whitelist.md`     | business     | blocked         | MASTER §1.5   | WL 输出路径         | AC-SP3-01     |
| `specs/contracts/source_conflict_rules.yaml`                                                   | contract     | pointer         | MASTER §6     | dry-run conflict    | AC-SP3-05     |
| `specs/contracts/data_quality_rules.yaml`                                                      | contract     | pointer         | MASTER §6     | validation 字段     | AC-SP3-02..03 |
| `specs/datasource_registry/source_registry.yaml`                                               | contract     | pointer         | MASTER §3     | proposed delta only | registry      |
| `backend/app/ops/staged_pilot.py`                                                              | wiring       | pointer         | MASTER §4     | v2 基线 → v3        | §9.1–9.6      |
| `backend/app/ops/staged_pilot_fetch_ports.py`                                                  | wiring       | pointer         | MASTER §4     | fetch ports         | §9.2–9.4      |
| `tests/test_staged_pilot.py`                                                                   | wiring       | pointer         | MASTER §5     | v2 回归             | §9.0 Tier A   |
| `tests/test_real_data_staged_pilot_v3.py`                                                      | wiring       | pointer         | MASTER §5     | v3 RED/GREEN        | §9.1–9.6      |
| `docs/quality/production_live_pilot_policy.md`                                                 | decision     | summary+pointer | MASTER §0     | staged-only gate    | AC-SP3-06     |
| `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3X_real_data_staged_pilot.md`   | business     | pointer         | MASTER §1.6   | v1 evidence format  | 对照          |
| `backend/app/validators/data_quality.py`                                                       | wiring       | pointer         | MASTER §4     | validation 复用     | AC-SP3-02..03 |
| `backend/app/validators/source_conflict.py`                                                    | wiring       | pointer         | MASTER §4     | conflict dry-run    | AC-SP3-05     |
| `backend/app/ops/live_pilot_fetch_ports.py`                                                    | wiring       | pointer         | MASTER §4     | 只读邻接            | 边界          |
| `docs/AUDIT_DEFERRED_REGISTRY.md`                                                              | decision     | summary+pointer | MASTER §0     | AKSHARE/EM 债       | closeout      |
| `docs/modules/write_manager.md`                                                                | architecture | pointer         | MASTER §4     | sandbox write       | AC-SP3-06     |

## inline 清单

- §0 staged-only + WL Execute 硬停 + live 2026-06-24 授权
- §3.2 defer：FRED/TDX/QMT/Yahoo production、clean write、registry commit
- forbidden：hand-picked symbols、full market、PDF bulk
