# 来源索引 — B3V-STOR RawStore Atomic Write

> **Plan / Audit 读本文件** · Execute 只读 `implement.jsonl` + `context_pack.json`

---

## A. 血缘追溯

| 字段          | 值                                                                                      |
| ------------- | --------------------------------------------------------------------------------------- |
| Round / Batch | Round 3V · `BATCH_3V_VERIFIED_AUDIT_CLEANUP`                                            |
| Item ID       | `B02_03` / Manifest `B3V-C03`                                                           |
| 任务卡        | `docs/implementation_tasks/ROUND_3_VERIFIED_AUDIT_CLEANUP/BATCH_3V_VERIFIED_AUDIT_CLEANUP/B02_03_rawstore_atomic_write.md` |
| Playbook      | `BATCH_3V_COORDINATOR_PLAYBOOK.md` §3.1 + §3.4 + §4                                     |
| gate / 分支   | post Batch 01 master / `fix/round3v-rawstore-atomic-write`                              |
| Owned VR      | `VR-STOR-001`                                                                           |

### AC 映射 → MASTER §4

| 任务卡切片 / AC              | MASTER AC   | 验证链   |
| ---------------------------- | ----------- | -------- |
| 原子 helper + temp 清理      | AC-STOR-01  | §9.1     |
| RawStore.save 走原子写       | AC-STOR-02  | §9.2     |
| 写异常目标不变/不存在        | AC-STOR-03  | §9.3     |
| 同 hash 幂等                 | AC-STOR-04  | §9.4     |
| `VR-STOR-001` registry 闭合  | AC-STOR-05  | §9.5     |

### 路径纠偏

无。任务卡与 playbook §8.3 验收命令一致。

---

## B. 输入 manifest（E1 · implement.jsonl 来源）

| 路径                                                                 | 类别   | manifest | extract / for        |
| -------------------------------------------------------------------- | ------ | -------- | -------------------- |
| `B02_03_rawstore_atomic_write.md`                                    | 任务卡 | required | Plan AC              |
| `BATCH_3V_COORDINATOR_PLAYBOOK.md`                                   | 协调   | required | §2.5/§2.6/§8.3       |
| `BATCH_3V_HARDENING_RULES.md`                                        | 规则   | required | 停止条件             |
| `backend/app/storage/raw_store.py`                                   | 接线   | required | §9.2 改码目标        |
| `backend/app/storage/path_compat.py`                                 | 接线   | required | §9.1 原子 helper     |
| `tests/test_raw_store.py`                                            | 测试   | required | §5.1 RED/GREEN       |
| `specs/contracts/resource_limits.yaml`                             | 契约   | inherited | MAX_RAW 对照        |
| `specs/contracts/snapshot_lineage_contract.yaml`                     | 契约   | inherited | 证据链只读          |
| `docs/quality/quant_monitor_desk_verified_audit_report_2026-06-25_v3_INDEX.md` | 审计 | required | VR-STOR-001 路由 |

---

## C. 六类覆盖自检

| 类别 | 路径                                                    | [x] |
| ---- | ------------------------------------------------------- | --- |
| 决策 | `BATCH_3V_VERIFIED_AUDIT_CLEANUP/README.md`             | [x] |
| 规则 | `GLOBAL_*.md` · `BATCH_3V_HARDENING_RULES.md`           | [x] |
| 架构 | `MIGRATION_MAP.md` · `authority_graph.yaml`（storage）  | [x] |
| 需求 | `B02_03_*.md` + MASTER §3                               | [x] |
| 契约 | `resource_limits.yaml` · `snapshot_lineage_contract.yaml` | [x] |
| 接线 | `raw_store.py` · `path_compat.py` · `test_raw_store.py` | [x] |

**索引完整**

---

## D. 机器路由

权威数据在 **`context_pack.json`**（本任务根目录）。 由 `context_router.py --task` 写入；本段不重复列举。

## E. implement.jsonl 槽位

1. `MASTER.plan.md` · 2. `context_pack.json` · 3. `trellis-execute/SKILL.md` · 4+ ledger `required`
