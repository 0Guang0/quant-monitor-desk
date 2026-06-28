# 来源索引 — B3V-DATA schema_hash fail-closed

> Plan / Audit 读本文件 · Execute 只读 `implement.jsonl` + `context_pack.json`

---

## A. 血缘追溯

| 字段 | 值 |
|------|-----|
| Round / Batch | Round 3V · `BATCH_3V_VERIFIED_AUDIT_CLEANUP` |
| Item ID | `B3V-C02` / Playbook `B3V-DATA` |
| 任务卡 | `docs/implementation_tasks/ROUND_3_VERIFIED_AUDIT_CLEANUP/BATCH_3V_VERIFIED_AUDIT_CLEANUP/B02_02_schema_hash_fail_closed.md` |
| Batch 地图 | `docs/implementation_tasks/ROUND_3_VERIFIED_AUDIT_CLEANUP/README.md` |
| VR | `VR-DATA-001` |
| gate / 分支 | post Batch 01 master / `fix/round3v-schema-hash-fail-closed` |

### AC 映射 → MASTER §4

| 任务卡 §6 / §8 | MASTER AC | 验证链 |
|----------------|-----------|--------|
| 结构化 SUCCESS 须 schema_hash | AC-DATA-01 | DATA-01 → §9.1 |
| CSV/Parquet 推导 | AC-DATA-02 | DATA-02 → §9.2 |
| Gate 缺失 hash 拒绝 | AC-DATA-03 | DATA-03 → §9.3 |
| 损坏文件不可写 | AC-DATA-04 | DATA-04 → §9.4 |
| hash 漂移仍拒绝 | AC-DATA-05 | DATA-03 回归 → §9.3 |

### 路径纠偏

- `B02-DATA-05` registry 闭合不在 Execute；主会话 §7 批处理。

---

## B. 输入 manifest

| 路径 | 类别 | manifest | extract / for |
|------|------|----------|---------------|
| `B02_02_schema_hash_fail_closed.md` | 任务卡 | Plan trace | AC |
| `data_adapter_contract.md` | 契约 | required | DATA-01 |
| `write_contract.yaml` | 契约 | required | DATA-03 |
| `data_quality_rules.yaml` | 契约 | required | SCHEMA_DRIFT |
| `resource_limits.yaml` | 契约 | required | 有界推导上限 |
| `skeleton_base.py` | 接线 | required | DATA-02 |
| `adapters/__init__.py` + `source_registry.py` | 接线 | read-only | §3.3 邻接（playbook `registry.py` 纠偏） |
| `validation_gate.py` | 接线 | required | DATA-03 |
| `test_db_validation_gate.py` | 测试 | required | §5.1 |
| `test_adapter_skeletons.py` | 测试 | required | §5.1 |
| `test_data_adapter_contract.py` | 测试 | required | §5.1 |
| `test_data_quality_validator.py` | 测试 | optional | SCHEMA_DRIFT 邻接 |

---

## C. 六类覆盖自检

| 类别 | 路径 | [x] |
|------|------|-----|
| 决策 | `ROUND_3_VERIFIED_AUDIT_CLEANUP/DECISIONS.md`（无独立文件 → README） | [x] |
| 规则 | `GLOBAL_*.md` ×3 + `BATCH_3V_HARDENING_RULES.md` | [x] |
| 架构 | `docs/modules/data_validation_and_conflict.md` | [x] |
| 需求 | `B02_02` + MASTER §3 | [x] |
| 契约 | `data_adapter_contract.md`, `write_contract.yaml` | [x] |
| 接线 | `skeleton_base.py`, `validation_gate.py`, `fetch_log.py` | [x] |

**索引完整**

---

## D. 机器路由

权威数据在 **`context_pack.json`**（本任务根目录）。 由 `context_router.py --task` 写入；本段不重复列举。

## E. implement.jsonl 槽位

1. `MASTER.plan.md` · 2. `context_pack.json` · 3. `trellis-execute/SKILL.md` · 4+ ledger required
