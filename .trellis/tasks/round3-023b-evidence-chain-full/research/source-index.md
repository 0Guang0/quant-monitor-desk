# 来源索引 — Round 3 023b full Layer5 evidence chain (B01-023)

> **Plan / Audit 读本文件** · Execute 只读 `implement.jsonl` + `context_pack.json`

---

## A. 血缘追溯

| 字段 | 值 |
| --- | --- |
| Round / Batch | Round 3 Batch 5 / Wave D **Track B** |
| Playbook ID | `B01-023` |
| Item ID | `023` / `023b` |
| 任务卡 | `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/023_implement_layer5_evidence_chain.md` |
| 前置切片 | `023A_layer5_evidence_foundation.md`（归档 `06-22-round3-023a-evidence-foundation`） |
| Batch 地图 | `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §2.3 Serial |
| Playbook | `docs/quality/coordination/BATCH_01_MAIN_SESSION_COORDINATOR_PLAYBOOK.md` §0、§3.2、§8.4 |
| gate / 分支 | §16：`022` + L3/L4 稳定 / `feature/round3-023b-evidence-chain-full` |

### Roadmap AC 映射 → MASTER §2

| Roadmap ID | MASTER AC | 验证链 |
| --- | --- | --- |
| `R3D-023-01` | AC-023-1 | §8#1 / §9.1 |
| `R3D-023-02` | AC-023-2 | §8#2 / §9.2 |
| `R3D-023-03` | AC-023-3 | §8#3 / §9.3 |
| `R3D-023-04` | AC-023-4 | §8#4 / §9.4 |
| `R3D-023-05` | AC-023-5 | §8#5 / §9.5 |
| playbook §8.4 + 任务卡 §11 | AC-023-6 | §10 |

### §16 前提检查

| 前提 | worktree 状态 | Execute 前复检 |
| --- | --- | --- |
| `023A` foundation merged | ✅ `foundation.py` / `test_layer5_evidence_foundation.py` 存在 | foundation pytest 绿 |
| `021` Layer3 integration | ✅ `layer3_chains/snapshot_builder.py` | `test_layer3_snapshot_builder.py` 绿 |
| `022` Layer4 integration | ✅ `layer4_markets/market_structure.py` | `test_layer4_market_structure.py` 绿 |
| 全量 pytest 基线 | Plan 时未跑 | **阻塞项**：Execute Boot 须 `uv run pytest -q` 全绿 |

### 路径纠偏

| Playbook 路径 | 状态 | 替代口径 |
| --- | --- | --- |
| `PROMPT_023b` | **不存在** | 任务卡 + §16 + 023A 归档 |
| `financial_statement` / `valuation_snapshot` 全量 ingestion | **defer** | contract `deferred_to_023b` → 本任务 staged validator only |
| registry 三件套闭合 | **主会话** | 本任务仅 proposed delta in evidence |

---

## B. 输入 manifest（E1 · implement.jsonl 来源）

| 路径 | 类别 | manifest | extract / for |
| --- | --- | --- | --- |
| `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/023_implement_layer5_evidence_chain.md` | 任务卡 | required | Plan AC §16/§17 |
| `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/023A_layer5_evidence_foundation.md` | 任务卡 | required | 023A 边界对照 |
| `docs/modules/layer5_security_evidence.md` | spec | required | AC-023-1..3 |
| `specs/contracts/layer5_evidence_contract.yaml` | contract | required | AC-023-1..3 |
| `specs/contracts/snapshot_lineage_contract.yaml` | contract | required | AC-023-2,3 |
| `docs/modules/data_validation_and_conflict.md` | spec | required | AC-023-4 |
| `backend/app/layer5_evidence/foundation.py` | wiring | inherited | 023A 延续 |
| `backend/app/layer3_chains/snapshot_builder.py` | wiring | inherited | upstream L3 |
| `backend/app/layer4_markets/market_structure.py` | wiring | inherited | upstream L4 |
| `tests/test_layer5_evidence_foundation.py` | 测试 | required | 回归 |
| `tests/test_layer5_evidence_chain.py` | 测试 | deferred | §5.1 Execute 创建 |
| `docs/quality/coordination/BATCH_01_MAIN_SESSION_COORDINATOR_PLAYBOOK.md` | rule | required | §3.2 / §8.4 |
| `docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md` | rule | required | R3-PARTIAL-4 / R2-RISK-2 |

---

## C. 六类覆盖自检

| 类别 | 路径 | [x] |
| --- | --- | --- |
| 决策 | `BATCH3_STAGED_DOWNSTREAM_GATE.md`；D-09（layer5 module doc）；ADR-023 conflict | [x] |
| 规则 | `GLOBAL_*.md`；`BATCH_01_HARDENING_RULES.md`；playbook §2.2 | [x] |
| 架构 | `03_runtime_flows.md`；`04_data_architecture.md`；`module_boundary_matrix.md` | [x] |
| 需求 | 任务卡 `023` + roadmap `R3D-023-*` + MASTER §3 | [x] |
| 契约 | `layer5_evidence_contract.yaml`；`snapshot_lineage_contract.yaml` | [x] |
| 接线 | 023A foundation；L3/L4 snapshot builders；`write_manager.md`（defer clean write） | [x] |

**索引完整**

---

## D. 机器路由

权威数据在 **`context_pack.json`**（本任务根目录）。 由 `context_router.py --task` 写入；本段不重复列举。

## E. implement.jsonl 槽位

1. `MASTER.plan.md` · 2. `context_pack.json` · 3. `trellis-execute/SKILL.md` · 4+ ledger `required`
