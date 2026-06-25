# Plan QC Report — B3V-STOR RawStore Atomic Write

> **Agent:** Plan 质检 Agent-2 · **model:** composer-2.5  
> **Worktree:** `../quant-monitor-desk-wt-b3v-stor`  
> **输入:** `MASTER.plan.md` · `implement.jsonl` · `vertical-slices.md` · `plan.freeze.md`  
> **对照:** Playbook §2.5/§2.6 · §3.4 · §3.9 · §3.10 · `B02_03_rawstore_atomic_write.md`

---

## 1. 执行摘要

| 项 | 结果 |
| --- | --- |
| 初检发现项 | **2**（均为 advisory，非阻断） |
| 已修复 | **0**（无需回 Plan 修文） |
| 复检遗留 | **0** 阻断项 |
| `validate-plan-freeze` | **exit 0**（2026-06-25，本 session 复跑确认） |
| `check_docs_specs_indexed.py` | **exit 0** |
| `BATCH_3V_SELF_CHECK.md` | **PASS_FOR_DISPATCH**（playbook 引用） |
| **裁决** | **`PASS_FOR_EXECUTE`** |

---

## 2. 门禁复跑

```text
python .trellis/scripts/task.py validate-plan-freeze .trellis/tasks/round3v-rawstore-atomic-write
→ Plan freeze validation passed (exit 0)

python scripts/check_docs_specs_indexed.py
→ OK: docs/specs indexed (exit 0)
```

| Manifest Gate | 状态 |
| --- | --- |
| implement.jsonl 第一条 = MASTER | PASS（L1） |
| integration-ledger in implement.jsonl | PASS（L5） |
| audit.jsonl 第一条 = AUDIT.plan.md | PASS |
| meta.manifest_protocol_version = "3" | PASS（task.json / plan.freeze） |

---

## 3. Playbook §3.4 B3V-STOR 分支必读（零遗漏）

| 路径 | MASTER | implement.jsonl | 摘要一句 | 遗漏风险 |
| --- | --- | --- | --- | --- |
| `B02_03_rawstore_atomic_write.md` | [x] §3.4 | L8 | 五切片 AC / forbidden | 无 |
| `backend/app/storage/raw_store.py` | [x] §3.4 | L27 | save 写路径独占 | 无 |
| `backend/app/storage/path_compat.py` | [x] §3.4 | L28 | write_bytes → atomic helper | 无 |
| `specs/contracts/snapshot_lineage_contract.yaml` | [x] §3.4 | L26 | 证据链只读对照 | 无 |
| `tests/test_raw_store.py` | [x] §3.4 | L30 | 基线 + crash/idempotency 扩展 | 无 |
| `quant_monitor_desk_verified_audit_report_2026-06-25_v3_INDEX.md` | [x] §3.4 | L15 | `VR-STOR-001` 路由 | 无 |
| `specs/contracts/resource_limits.yaml` | [x] §3.2 | L25 | MAX_RAW 邻接（Plan 增补，合理） | 无 |

**§3.4 结论：** 6/6 playbook 行 + 1 合理增补，分支必读无缺口。

---

## 4. Playbook §3.1 共用底座（condensed 核对）

MASTER Source Context Index §3.1 以合并行覆盖 playbook 长表；implement.jsonl 对 Execute 精读路径已列槽位。

| 类别 | 代表路径 | MASTER | implement | 遗漏风险 |
| --- | --- | --- | --- | --- |
| 协调 | playbook · manifest · README · hardening · adversarial · self_check | [x] | L9–L14 | 无 |
| 路线图 / 协议 | `PROJECT_IMPLEMENTATION_ROADMAP` · Phase 8D · `agent-toolchain` | [x] | L22；协议仅 MASTER 摘要 | **advisory**¹ |
| 审计 / VR | v3_INDEX · `UNRESOLVED_ITEM_TASK_COVERAGE` | [x] | L15–L16 | 无 |
| Handoff | `ROUND3_HANDOFF.md` | [x] | L17 | 无 |
| 全局 | GLOBAL ×4 | [x] | L18–L21 | 无 |
| 架构 | `MIGRATION_MAP` · `authority_graph.yaml` | [x] | L23–L24 | 无 |
| Registry 三件套 | AUDIT_DEFERRED / UNRESOLVED / RESOLVED | [x] 合并行「只读」 | 仅 coverage 映射 L16 | **advisory**² |
| 契约（共用） | `write_contract.yaml` · `runtime_versions.md` | 未单列 | 未入 implement | **advisory**³ |

¹ `agent-toolchain.md` 由 `trellis-execute/SKILL.md`（implement L3）间接路由；Execute Boot 可接受。  
² STOR-05 仅产出 **proposed delta**；registry 三件套 commit 归主会话（§0 边界 · grill-me Q6）— 与任务卡一致。  
³ 写模式契约为 B3V-OPS 域；本任务 §3.2 明确 out `WriteManager`，不构成 STOR Execute 阻断。

---

## 5. §3.9 Plan 追溯规则

| 规则 | 核查 | 状态 |
| --- | --- | --- |
| **索引行** | §3.4 全行双覆盖；§3.1 合并行 + implement 槽位 | PASS |
| **VR 追溯** | `VR-STOR-001` → AC-STOR-05 → S5 → §9.5 → `registry_proposed_delta.yaml` | PASS |
| **负向边界** | MASTER §0 Must not own 抄 §2.6；禁 registry commit / prod DB / gate / sync | PASS |
| **切片垂直** | STOR-01..05 各绑单一 AC；禁止水平合并 VR（§7 · vertical-slices） | PASS |
| **证据路径** | `execute-evidence/9.x-*.txt` + `research/registry_proposed_delta.yaml` | PASS |
| **复检** | 本节 §6 §3.10 表；无未修复阻断遗漏 | PASS |

---

## 6. §3.10 Plan 质检输出表（Agent-2 必填）

| 路径 | 已入 MASTER/implement | 摘要一句 | 遗漏风险 |
| --- | --- | --- | --- |
| Playbook §3.1 共用底座 | [x] §3.1 表 | Batch 3V 纪律 + 全局 + 架构 | 无 |
| Playbook §3.4 B3V-STOR | [x] §3.4 表 | raw_store / path_compat / tests / VR | 无 |
| `B02_03_rawstore_atomic_write.md` | [x] | 原子写五切片 + forbidden | 无 |
| `BATCH_3V_HARDENING_RULES.md` | [x] | §1.5 停止条件 | 无 |
| `BATCH_3V_COORDINATOR_PLAYBOOK.md` §2.5/§2.6 | [x] §0 边界 | 文件锁 + Must not own | 无 |
| `specs/contracts/snapshot_lineage_contract.yaml` | [x] | 证据链只读 | 无 |
| `specs/contracts/resource_limits.yaml` | [x] | MAX_RAW 邻接 | 无 |
| `research/gitnexus-summary.md` | [x] | RawStore impact **MEDIUM** | 无 |
| `validate-plan-freeze` | [x] | 2026-06-25 exit 0（复跑） | 无 |
| `authority_graph.yaml` storage 域 | [x] | context_pack 路由 | 无 |
| `vertical-slices.md` | [x] | STOR-01..05 冻结 | 无 |
| `original-plan-trace.md` | [x] | B02_03 → MASTER AC 映射 | 无 |
| `integration-ledger.md` | [x] | ≥12 行 v3 packing | 无 |

---

## 7. STOR-01..05 垂直切片核对

| ID | vertical-slices | MASTER §8 | MASTER §9 | B02_03 §5 | AC | 依赖 | 独立可测 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| STOR-01 | `write_bytes_atomic` + helper 测 | 序 1 | §9.1 | B02-STOR-01 | AC-STOR-01 | — | 是 |
| STOR-02 | `RawStore.save` 接线 | 序 2 | §9.2 | B02-STOR-02 | AC-STOR-02 | STOR-01 | 是（`-k save_writes\|save_pathLayout` 匹配既有测名） |
| STOR-03 | crash 模拟 | 序 3 | §9.3 | B02-STOR-03 | AC-STOR-03 | STOR-02 | 是 |
| STOR-04 | 幂等 | 序 4 | §9.4 | B02-STOR-04 | AC-STOR-04 | STOR-02 | 是（可与 STOR-03 并行） |
| STOR-05 | VR closeout | 序 5 | §9.5 | B02-STOR-05 | AC-STOR-05 | STOR-03..04 | 是（文件存在性 RED） |

- 切片与 `original-plan-trace.md` 一一对应。  
- §5.3 新测名与 §9.1/9.3/9.4 RED 命令一致。  
- §9.2 使用 `-k "save_writes or save_pathLayout"` 覆盖 `test_save_writesFileAndComputesHash` / `test_save_pathLayout_matchesConvention`（已 grep 确认）。

---

## 8. RawStore GitNexus Impact（MEDIUM）

| 字段 | 值 | Plan 落点 |
| --- | --- | --- |
| Target | `RawStore` (`raw_store.py`) | `research/gitnexus-summary.md` |
| Risk | **MEDIUM** | MASTER §0.1 6.pre · §1.5 #5 |
| d=1 callers | 6 | gitnexus-rawstore-impact.md |
| Total impacted | 18 | §6 Tier B `uv run pytest -q` |
| Strategy | `path_compat.write_bytes_atomic` + `save` 单行替换 | MASTER §2.1 · §0.3a ponytail |

**结论：** MEDIUM 已记录；无 HIGH/CRITICAL；§1.5 #5 要求升级时主会话批准；全量 pytest 为合并门禁 — 可 Execute。

---

## 9. VR-STOR-001 — proposed delta only

| 检查项 | 证据 | 状态 |
| --- | --- | --- |
| Execute 禁止直接 commit registry 三件套 | MASTER §0 Must not own | PASS |
| STOR-05 交付物 | `research/registry_proposed_delta.yaml`（非三件套路径） | PASS |
| RED/GREEN | §9.5 文件存在性门控 | PASS |
| 主会话闭合 | grill-me Q6 · integration-ledger inline · prd.md | PASS |
| 任务卡 §8 Done | resolved **or** re-defer — delta 路径满足 proposed | PASS |

**结论：** VR 关闭流程为 **proposed delta only**；与 Batch 3V §2.1 主会话批处理纪律一致。

---

## 10. §2.5 / §2.6 边界与停止条件

| 约束 | MASTER | 状态 |
| --- | --- | --- |
| Owns: `raw_store.py` · `path_compat.py` · `test_raw_store.py` | §0 表 | PASS |
| Must not: validation_gate · sync · WriteManager · registry commit | §0 表 · §3.2 out | PASS |
| 无 production clean write / live fetch / prod DB | §1.4 · hardening | PASS |
| Windows 长路径回归 | §7 · 保留 `test_save_windowsLongPath_*` | PASS |
| crash 仍见截断 → 禁 STOR-03 GREEN | §1.5 #6 | PASS |

---

## 11. 发现项清单

| # | 发现 | 严重度 | 处置 |
| --- | --- | --- | --- |
| A1 | §3.1 中 `write_contract.yaml` / `runtime_versions.md` 未入 implement.jsonl | 低 advisory | STOR out-of-scope；MASTER §3.2 已排除 WriteManager |
| A2 | Registry 三件套未逐文件入 implement（仅 coverage 映射） | 低 advisory | STOR-05 proposed-only；主会话闭合 — 符合设计 |

**无 BLOCKING 项。**

---

## 12. 裁决

### `PASS_FOR_EXECUTE`

**理由：**

1. `validate-plan-freeze` exit 0（本 session 复跑）。  
2. Playbook §3.4 分支必读 **100%** 覆盖；§3.9 追溯链完整。  
3. STOR-01..05 垂直切片、AC、RED/GREEN、依赖与 `vertical-slices.md` / `B02_03` 对齐。  
4. RawStore **MEDIUM** impact 已文档化，缓解策略明确（最小 diff + 全量 pytest）。  
5. `VR-STOR-001` 严格 **proposed delta only**，无 registry 三件套 commit 越权。  
6. §3.10 表遗漏风险列：分支项均为「无」；§3.1 advisory 两项不阻断 STOR Execute。

**Execute 派发约束（提醒，非阻断）：**

- 模型：`composer-2.5` only（playbook §4.1）。  
- Boot：逐行 Read `implement.jsonl`；先读 `integration-ledger.md`。  
- 改 symbol 前再跑 GitNexus `impact()`；若升至 HIGH/CRITICAL 停。  
- **不得** `task.py start` 前自行 start — 待用户/协调者「计划批准」。

---

*质检日期：2026-06-25 · Agent-2 Plan QC · 无 Execute*
