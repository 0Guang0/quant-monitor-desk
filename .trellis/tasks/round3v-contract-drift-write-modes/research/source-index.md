# 来源索引 — B3V-OPS Contract Drift & Write Modes

> Plan / Audit 读本文件 · Execute 只读 `implement.jsonl` + `context_pack.json`

---

## A. 血缘追溯

| 字段 | 值 |
| ---- | -- |
| Round / Batch | Round 3V.1 · `BATCH_3V_VERIFIED_AUDIT_CLEANUP` |
| Item ID | B3V-C01 / Playbook B3V-OPS |
| 任务卡 | `docs/implementation_tasks/ROUND_3_VERIFIED_AUDIT_CLEANUP/BATCH_3V_VERIFIED_AUDIT_CLEANUP/B02_01_contract_drift_and_write_modes.md` |
| 分支 | `fix/round3v-contract-drift-write-modes` |
| Worktree | `../quant-monitor-desk-wt-b3v-ops` |
| VR-* | `VR-OPS-001`, `VR-WRITE-001` |

### AC 映射 → MASTER §4

| 任务卡 § | MASTER AC | 验证链 |
| -------- | --------- | ------ |
| §2 VR-OPS-001 | AC-OPS-DRIFT | S1 → §9.1–9.2 |
| §2 VR-WRITE-001 | AC-WRITE-SPLIT | S2 → §9.3–9.4 |
| §2 reserved 语义 | AC-WRITE-RESERVED | S3 → §9.5 |
| §4 Forbidden | AC-BOUND | §3.2 · Audit A3 |
| §8 Done（无 registry） | AC-EVIDENCE | §10 · 主会话 registry |

### 漂移现状（Plan 预研）

| 触点 | 契约 | 运行时 | 缺口 |
| ---- | ---- | ------ | ---- |
| key_tables | `ops_db_inspect_contract.yaml` L164–185 | `db_inspector.KEY_TABLES` | 双份维护；内容当前一致 |
| deferred_item_mapping | contract L187–212 | `db_inspector.DEFERRED_ITEM_MAPPING` | 双份维护；结构等价 |
| write modes | `write_contract.yaml` 扁平 5 模式 | `SUPPORTED_MODES`×2 + `UNSUPPORTED_MODES`×3 | 契约未分 implemented/reserved |
| 部分漂移测 | — | `test_layer1_ingestion_gates` 仅 key_tables 子集 | 无 deferred 全量漂移测 |
| reserved 拒绝 | — | `WriteManager.write` L394–400 | 有测但无契约 parity |

---

## B. 输入 manifest（E1 · implement.jsonl 来源）

| 路径 | 类别 | manifest | extract / for |
| ---- | ---- | -------- | ------------- |
| `B02_01_contract_drift_and_write_modes.md` | 任务卡 | summary | Plan AC（**必须读原文**见 MASTER） |
| `BATCH_3V_TASK_CARD_MANIFEST.md` | 协调 | required | C01 依赖 |
| `BATCH_3V_HARDENING_RULES.md` | 规则 | required | §3–§7 |
| `BATCH_3V_COORDINATOR_PLAYBOOK.md` | 协调 | required | §3.1+§3.2+§4 |
| `ops_db_inspect_contract.yaml` | 契约 | required | §9.1–9.2 |
| `write_contract.yaml` | 契约 | required | §9.3–9.5 |
| `db_inspector.py` | 接线 | required | §9.1–9.2 |
| `write_manager.py` | 接线 | required | §9.3–9.5 |
| `tests/test_ops_db_inspector.py` | 测试 | required | 回归 |
| `tests/test_write_manager.py` | 测试 | required | 回归 |
| `tests/test_contract_drift_ops_write.py` | 测试 | deferred | §5.1 Execute 创建 |

---

## C. 六类覆盖自检

| 类别 | 路径 | [x] |
| ---- | ---- | --- |
| 决策 | `BATCH_3V_HARDENING_RULES.md` · `staged_acceptance_policy.md` | [x] |
| 规则 | `GLOBAL_*.md` · Playbook §2.5/§2.6 | [x] |
| 架构 | `module_boundary_matrix.md`（ops/db 边界） | [x] |
| 需求 | B02_01 任务卡 · MASTER §3 | [x] |
| 契约 | `ops_db_inspect_contract.yaml` · `write_contract.yaml` · `runtime_versions.md` | [x] |
| 接线 | `db_inspector.py` · `write_manager.py` · 相关 tests | [x] |

**索引完整**

---

## D. 机器路由

权威数据在 **`context_pack.json`**（本任务根目录）。 由 `context_router.py --task` 写入；本段不重复列举。

## E. implement.jsonl 槽位

1. `MASTER.plan.md` · 2. `context_pack.json` · 3. `trellis-execute/SKILL.md` · 4+ ledger `required`
