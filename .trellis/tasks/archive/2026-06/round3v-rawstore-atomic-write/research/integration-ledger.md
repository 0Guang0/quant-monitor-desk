# Integration Ledger — B3V-STOR

> Plan 5c · v3 context packing

## 打包策略

| 策略            | 含义                       |
| --------------- | -------------------------- |
| inline          | MASTER §0/§3 已摘要        |
| summary+pointer | MASTER 摘要 + 原稿         |
| pointer         | implement extract/for 精读 |

## ledger

| source                                                                         | category     | strategy        | master_anchor | execute_extract           | for_ac_step |
| ------------------------------------------------------------------------------ | ------------ | --------------- | ------------- | ------------------------- | ----------- |
| `research/integration-ledger.md`                                               | rule         | inline          | MASTER §0.4   | v3 boot routing           | §9.0        |
| `research/grill-me-session.md`                                                 | decision     | summary+pointer | MASTER §2.2   | 原子写放 path_compat 决策 | AC-STOR-01  |
| `BATCH_3V_ADVERSARIAL_AUDIT.md`                                                | decision     | summary+pointer | MASTER §7     | 禁止水平合并 VR           | 全 AC       |
| `B02_03_rawstore_atomic_write.md`                                              | business     | pointer         | MASTER §2     | 任务卡 AC/切片            | AC-STOR-\*  |
| `BATCH_3V_COORDINATOR_PLAYBOOK.md`                                             | rule         | summary+pointer | MASTER §0     | §2.5/§2.6 文件锁          | 全 AC       |
| `BATCH_3V_HARDENING_RULES.md`                                                  | rule         | summary+pointer | MASTER §1.5   | 禁 production 写          | 全 AC       |
| `backend/app/storage/raw_store.py`                                             | wiring       | pointer         | MASTER §4     | save 写路径               | §9.2        |
| `backend/app/storage/path_compat.py`                                           | wiring       | pointer         | MASTER §4     | write_bytes_atomic        | §9.1        |
| `tests/test_raw_store.py`                                                      | wiring       | pointer         | MASTER §5     | crash/idempotency         | §9.3–9.4    |
| `specs/contracts/resource_limits.yaml`                                         | contract     | pointer         | MASTER §3     | MAX_RAW_FILE_BYTES        | §9.2        |
| `specs/contracts/snapshot_lineage_contract.yaml`                               | contract     | pointer         | MASTER §3     | 证据链只读                | —           |
| `research/gitnexus-summary.md`                                                 | architecture | summary+pointer | MASTER §2     | impact MEDIUM             | Boot        |
| `docs/quality/quant_monitor_desk_verified_audit_report_2026-06-25_v3_INDEX.md` | business     | pointer         | MASTER §4     | VR-STOR-001               | AC-STOR-05  |
| `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`                           | rule         | pointer         | MASTER §5     | 五字段/TDD                | §9          |

## inline 清单

- §0 Batch 3V 边界：无 production DB / 无 live fetch
- §3.2 out：FileRegistry 语义、validation_gate、sync、registry 三件套
- forbidden：POSIX-only 目录 fsync 作为 Windows 硬依赖
- registry：agent proposed delta only
