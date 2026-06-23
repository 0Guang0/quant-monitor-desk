# 来源索引 — Round 3 020 Layer3 industry chain loader

> **Plan / Audit 读本文件** · Execute 只读 `implement.jsonl` + `context_pack.json`

---

## A. 血缘追溯

| 字段 | 值 |
| ---- | -- |
| Round / Batch | Round 3 Batch 4 |
| Item ID | `020` |
| 任务卡 | `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/020_implement_layer3_industry_chain_loader.md` |
| Batch 地图 | `ROUND3_BATCH_IMPLEMENTATION_MAP.md` § Batch 4 |
| gate / 分支 | `019` merged + staged gate / `feature/round3-020-layer3-loader` |

### AC 映射 → MASTER §2

| 任务卡 | MASTER AC | 验证链 |
| ------ | --------- | ------ |
| §1 加载五类 registry | AC-020-1 | §8.2 |
| §9 node/edge 引用校验 | AC-020-2 | §8.3–8.5 |
| §9 event_only 私有公司 | AC-020-3 | §8.4 |
| §9 P0 来源 / source_keys | AC-020-4 | §8.4 |
| §16 staged-only | AC-020-5 | §8.2 |
| §11 验收命令 | AC-020-6 | §10 |

### 路径纠偏

| 文档路径 | 仓库实际 |
| -------- | -------- |
| `specs/layer3_global_industry_chains_v1_2/` | `specs/layer3_global_industry_chains/layer3_global_industry_chains_v1_2/` |

---

## B. 输入 manifest（E1 · implement.jsonl 来源）

| 路径 | 类别 | manifest | extract / for |
| ---- | ---- | -------- | ------------- |
| `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/020_implement_layer3_industry_chain_loader.md` | 任务卡 | required | Plan AC |
| `docs/modules/layer3_industry_shock_anchor.md` | spec | required | AC-020-* |
| `specs/contracts/layer3_loader_contract.yaml` | contract | required | AC-020-2/4 |
| `specs/layer3_global_industry_chains/layer3_global_industry_chains_v1_2/layer3_global_industry_chain_registry.yaml` | domain | required | AC-020-1 |
| `specs/layer3_global_industry_chains/layer3_global_industry_chains_v1_2/layer3_anchor_registry.json` | domain | required | AC-020-1 |
| `specs/layer3_global_industry_chains/layer3_global_industry_chains_v1_2/layer3_node_registry.json` | domain | required | AC-020-2 |
| `specs/layer3_global_industry_chains/layer3_global_industry_chains_v1_2/layer3_edge_registry.json` | domain | required | AC-020-2 |
| `specs/layer3_global_industry_chains/layer3_global_industry_chains_v1_2/layer3_cross_chain_edge_registry.json` | domain | required | AC-020-2 |
| `backend/app/layer2_sensors/sensor_loader.py` | wiring | inherited | §8.2 模式 |
| `docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md` | rule | required | §0 staged |
| `specs/contracts/snapshot_lineage_contract.yaml` | contract | deferred | 021/023A |
| `tests/test_layer3_loader.py` | 测试 | deferred | §5.1 Execute 创建 |
| `tests/fixtures/layer3_*` | fixture | deferred | §8.2 Execute 创建 |

---

## C. 六类覆盖自检

| 类别 | 路径 | [x] |
| ---- | ---- | --- |
| 决策 | `docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md`；D-09 ADR-0003 | [x] |
| 规则 | `GLOBAL_*.md`；`staged_acceptance_policy.md` | [x] |
| 架构 | `docs/architecture/03_runtime_flows.md`；`04_data_architecture.md` | [x] |
| 需求 | 任务卡 `020` + MASTER §3 | [x] |
| 契约 | `layer3_loader_contract.yaml` | [x] |
| 接线 | `sensor_loader.py`（019）；`layer3_chains/__init__.py` 占位 | [x] |

**索引完整**

---

## D. 机器路由

权威数据在 **`context_pack.json`**（本任务根目录）。 由 `context_router.py --task` 写入；本段不重复列举。

## E. implement.jsonl 槽位

1. `MASTER.plan.md` · 2. `context_pack.json` · 3. `trellis-execute/SKILL.md` · 4+ ledger `required`
