# Repair/Debt Lite Plan — B3V-L5R Layer5 / Model Schema Reconcile

> **Playbook ID:** B3V-L5R (`B3V-C06`)  
> **轨道:** debt-lite（playbook §5.2）  
> **模型:** `composer-2.5`  
> **Trellis task-dir:** `.trellis/tasks/round3v-layer5-model-schema-reconcile`  
> **本阶段:** 轻量 Plan only — **禁止**改 `backend/app/layer5_evidence/**` runtime、**禁止** registry 三件套 commit

---

## Source of truth

| 项 | 值 |
| --- | --- |
| 任务卡 | `docs/implementation_tasks/ROUND_3_VERIFIED_AUDIT_CLEANUP/BATCH_3V_VERIFIED_AUDIT_CLEANUP/B03_01_layer5_model_schema_reconcile.md` |
| Manifest | `BATCH_3V_TASK_CARD_MANIFEST.md` → `B3V-C06` |
| 协调手册 | `BATCH_3V_COORDINATOR_PLAYBOOK.md` §3.1 + §3.7 + §5.2 |
| Hardening | `BATCH_3V_HARDENING_RULES.md` §6 reconcile-first |
| Phase 8D | `.trellis/spec/guides/round3-repair-debt-worktree-plan.md` + `complex-task-planning-protocol.md` §8D |
| 工具路由 | `agent-toolchain.md`（GitNexus + codebase-memory 同级交叉核实） |
| base branch | `master`（post Batch 01；含 `376e30e6`） |
| target branch | `review/round3v-layer5-model-schema-reconcile` |
| worktree | `C:\Users\Guang\Desktop\quant-monitor-desk-wt-b3v-l5r` |
| owner agent | B3V-L5R Plan → 核对 agent（同分支） |

## 决策与目标

**reconcile-first（Hardening §6）：** 对照 post Batch 01 master（`376e30e6`+）核对审计 `VR-L5-001` / `VR-MODEL-001`，不重复实现已完成 023 staged runtime。

| VR ID | Plan 预判（Execute 前须实测确认） | 预期处置 |
| --- | --- | --- |
| `VR-L5-001` | 证据链 builder / provenance / agent-text / manual review / lineage hash **已在 staged runtime + pytest 覆盖**（`376e30e6`；`AUDIT_DEFERRED` `R3-TASK-023` 已 RESOLVED） | **stale close**（独立证据：`test_layer5_evidence_chain.py` + `test_layer5_evidence_foundation.py`） |
| `VR-MODEL-001` | L3/L4/L5 表多数 **designed + staged runtime**，**无 migration**；`MIGRATION_COVERAGE.md` 缺 L3/L4 段；`test_migration_coverage.py` **不存在** | **矩阵落盘 + docs 对齐**；缺 migration 表 **re-defer → Round 3F**；Execute 新建 `test_migration_coverage.py` 作 closure test |

**允许表述：** stale reconciled · designed/implemented/deferred matrix · precise re-defer to Round 3F · staged-only evidence  
**禁止表述：** production-ready · Layer5 production-ready · designed table = migrated table

## Boundary（§2.5 / §2.6 SSOT）

| 维度 | 内容 |
| --- | --- |
| **§2.5 文件锁** | `backend/app/layer5_evidence/**` **默认只读**；runtime 缺口 → 独立 follow-up 分支 `feature/round3-023c-*` 或 Round 3F migration 分支 |
| **Owns（可写）** | `research/l5-reconcile-matrix.md` · `research/*.md` · `docs/schema/MIGRATION_COVERAGE.md`（L3/L4/L5 段）· `docs/architecture/04_data_architecture.md`（矩阵引用，最小 diff）· **新建** `tests/test_migration_coverage.py` · proposed registry delta YAML |
| **Must not own** | `layer5_evidence/**` runtime · migration SQL 文件（Round 3F）· sync/write/validation/rawstore · registry 三件套直接 commit · production DB 写 |
| **production/data** | 无 live fetch · 无 clean write · db-inspect 只读 |
| **non-goals** | 不重复 023 实现 · 不水平合并关两个 VR · 不删 `deferred_to_023b` 类注记无证据 |

## 基线证据（Plan 期已核实）

| 检查项 | 结果 | 指针 |
| --- | --- | --- |
| Batch 01 Layer5 merge | `376e30e6` merge(wave-d): B01-023 full Layer5 evidence chain | `docs/AUDIT_DEFERRED_REGISTRY.md` `R3-TASK-023` |
| `test_layer5_evidence_chain.py` | 7 tests，五字段齐全 | `tests/test_layer5_evidence_chain.py` |
| `test_layer5_evidence_foundation.py` | 6 tests（含 lineage hash / identity hash） | `tests/test_layer5_evidence_foundation.py` |
| targeted pytest（worktree） | 13 passed（2026-06-25 Plan 跑） | `uv run pytest tests/test_layer5_evidence_chain.py tests/test_layer5_evidence_foundation.py -q` |
| `test_migration_coverage.py` | **不存在** | blocker → slice `B03-MODEL-03` |
| migrations 001–011 | 无 `industry_chain_*` / `market_*` / L5 建模表 | `backend/app/db/migrations/` |
| GitNexus `context(EvidenceChainBuilder)` | symbol not found（索引滞后） | codebase-memory 命中 `evidence_chain.py:23` — Execute 前 `node .gitnexus/run.cjs analyze` |

---

## Vertical slices（B03-L5-* 与 B03-MODEL-* 分离）

> 每 slice **仅一个 VR 或可测子 AC**；禁止水平合并关账。

### Track A — `VR-L5-001`（`B03-L5-*`）

| Slice | Source ID | AC（完成标准） | Allowed files | Forbidden files | Verification | Evidence path |
| --- | --- | --- | --- | --- | --- | --- |
| **B03-L5-01** | `VR-L5-001` / `R3V-B03-L5-01` | 证据链能力矩阵落盘：builder、provenance、upstream trace、port 边界 — 每行 **implemented / staged-only / gap** | `research/l5-reconcile-matrix.md` §VR-L5-001 | runtime | 只读对照 `backend/app/layer5_evidence/**` | `research/l5-reconcile-matrix.md` |
| **B03-L5-02** | `VR-L5-001` | 核对 agent-text rejection、manual review、lineage/identity hash 测试指针；确认 post-`376e30e6` 无回归 | `research/l5-reconcile-matrix.md` · `research/layer5-evidence-chain-reconcile.md` | `layer5_evidence/**` | `uv run pytest tests/test_layer5_evidence_chain.py tests/test_layer5_evidence_foundation.py -q` 全绿 | `execute-evidence/b03-l5-02-pytest.txt` |
| **B03-L5-CLOSE** | `VR-L5-001` | **独立** stale close 证据：commit `376e30e6` + 上列 pytest 名 + 矩阵行 `resolution=stale`；**不**声称 production-ready | `research/l5-reconcile-matrix.md` · `research/registry_proposed_delta.yaml` | registry 三件套 commit | 同上 pytest + 矩阵 §Closure | `execute-evidence/b03-l5-close.txt` |

**VR-L5-001 已知 gap（不阻塞 stale close，须写入矩阵 follow-up）：**

- DB 持久化 `instrument_registry` / `security_bar_1d` migration — 归 `VR-MODEL-001` / Round 3F
- `financial_statement_snapshot` / `valuation_snapshot` / `event_registry` 等 023 全量表 — designed only
- WriteManager 落库路径 — 未在本 reconcile 范围

### Track B — `VR-MODEL-001`（`B03-MODEL-*`）

| Slice | Source ID | AC（完成标准） | Allowed files | Forbidden files | Verification | Evidence path |
| --- | --- | --- | --- | --- | --- | --- |
| **B03-MODEL-01** | `VR-MODEL-001` / `R3V-B03-MODEL-01` | L3/L4/L5 **designed / implemented(staged runtime) / deferred(migration)** 三列矩阵；含 `schema.sql` vs module doc 命名差（`security_bar_1d` vs `security_bar_daily`） | `research/l5-reconcile-matrix.md` §VR-MODEL-001 · `research/model-schema-table-reconcile.md` | migration SQL | 矩阵每表有 evidence 列 | `research/l5-reconcile-matrix.md` |
| **B03-MODEL-02** | `VR-MODEL-001` | 更新 `MIGRATION_COVERAGE.md` L3/L4/L5 段与矩阵一致；**不**把 DEFERRED 标为 DONE | `docs/schema/MIGRATION_COVERAGE.md` · `docs/architecture/04_data_architecture.md`（最小） | `backend/app/db/migrations/**` | `uv run python scripts/check_docs_specs_indexed.py` exit 0 | `execute-evidence/b03-model-02-docs.txt` |
| **B03-MODEL-03** | `VR-MODEL-001` | **TDD 新建** `tests/test_migration_coverage.py`：断言 designed 表无 migration；L1 axis 表 migration 011 DONE；五字段 docstring | `tests/test_migration_coverage.py` · `tests/test_catalog.yaml`（若 CI 要求） | 弱化断言过关 | `uv run pytest tests/test_migration_coverage.py -q` 绿 | `execute-evidence/b03-model-03-red.txt` / `-green.txt` |
| **B03-MODEL-CLOSE** | `VR-MODEL-001` | **独立** closure：矩阵 + pytest + docs 一致；migration 缺口 **re-defer** Round 3F（owner + closure test 指针） | `research/l5-reconcile-matrix.md` · `research/registry_proposed_delta.yaml` | registry commit | `test_migration_coverage` + `test_layer5_evidence_chain` 双绿 | `execute-evidence/b03-model-close.txt` |

### 汇总切片（主会话）

| Slice | Source ID | AC | Allowed | Verification |
| --- | --- | --- | --- | --- |
| **B03-CLOSE-01** | manifest §4 | 主会话批处理 registry：`VR-L5-001` stale · `VR-MODEL-001` resolved-with-matrix 或 re-defer 行 | proposed delta only | 主会话 §7.3 |

---

## §3.1 共用底座索引（已入 Plan）

| 类别 | 路径 | Plan 落点 |
| --- | --- | --- |
| 协调 | playbook · BATCH_3V package · README | Source of truth |
| 协调 | `PROJECT_IMPLEMENTATION_ROADMAP.md` Round 3V.2 | 决策表 |
| 协调 | `round3-repair-debt-worktree-plan.md` §8D · `agent-toolchain.md` | 本文结构 |
| 审计 | `quant_monitor_desk_verified_audit_report_2026-06-25_v3_INDEX.md` | VR 路由 |
| 审计 | `BATCH_3V_HARDENING_RULES.md` §6 | reconcile-first |
| Registry | `AUDIT_DEFERRED` / `UNRESOLVED` / `RESOLVED` · `UNRESOLVED_ITEM_TASK_COVERAGE.md` | proposed delta only |
| Handoff | `ROUND3_HANDOFF.md` · post Batch 01 checkpoint | 基线 `376e30e6` |
| 全局 | `GLOBAL_EXECUTION_RULES.md` · `GLOBAL_TESTING_POLICY.md` · `GLOBAL_TASK_TEMPLATE.md` | Boundary + 五字段 |
| 契约 | `layer5_evidence_contract.yaml` · `snapshot_lineage_contract.yaml` | B03-L5-02 对照 |
| 架构 | `04_data_architecture.md` · `MIGRATION_COVERAGE.md` · `schema.sql` | B03-MODEL-* |

## §3.7 B3V-L5R 分支索引（playbook 逐行）

| 路径 | 用途 | 已入 Plan | 摘要一句 | 遗漏风险 |
| --- | --- | --- | --- | --- |
| `023_implement_layer5_evidence_chain.md` · `023A_layer5_evidence_foundation.md` | 023 权威 | B03-L5-01/02 | 全量目标 vs staged 实现边界 | 低 — 不重复实现 |
| `docs/modules/layer5_evidence_chain.md` | Layer5 模块文档 | B03-MODEL-02 | 与矩阵交叉核对 overclaim | 中 — 文档可能列全量表 |
| `backend/app/layer5_evidence/` | runtime | Boundary 只读 | 8 模块文件；023b staged | 低 |
| `tests/test_layer5_evidence_chain.py` | 强制 pytest | B03-L5-02/CLOSE | 7 tests 绿 | 低 |
| `tests/test_migration_coverage.py` | 强制 pytest | B03-MODEL-03 | **待建** | **高 — blocker** |
| `specs/schema/schema.sql` | 表 SSOT 设计 | B03-MODEL-01 | L5 仅 2 表；无 L3/L4 | 中 |
| `docs/schema/MIGRATION_COVERAGE.md` | 覆盖文档 | B03-MODEL-02 | 缺 L3/L4；L5 标 N/A | 中 |
| `docs/quality/..._v3_INDEX.md` | VR 路由 | Source of truth | stale / matrix | 低 |

---

## Hardening 摘要（Execute 强制）

| 规则 | L5R 落地 |
| --- | --- |
| §6 reconcile-first | 先读 `376e30e6` + pytest；再决定是否 stale |
| §7 vertical slice | L5 vs MODEL 分轨；每 VR 独立 CLOSE |
| §5 hard stop | 无 migration 不得标 implemented DB table |
| §4 TDD | `test_migration_coverage.py` 须 RED→GREEN |
| Registry | agent 仅 `research/registry_proposed_delta.yaml` |

## Merge gate（Phase 8D §8D.5）

```bash
uv sync --locked
uv run pytest tests/test_layer5_evidence_chain.py -q
uv run pytest tests/test_migration_coverage.py -q
uv run python scripts/check_docs_specs_indexed.py
uv run pytest -q
uv run python scripts/loop_maintain.py --fix   # 若触达 docs/
```

- 对抗性审计：`agents/audit-adversarial-authority.md`
- 主会话：registry 批闭合 + §7.2 merge #2

---

## §3.10 Plan 质检自检表

| 路径 | 已入 DEBT.plan | 摘要一句 | 遗漏风险 |
| --- | --- | --- | --- |
| `B03_01_layer5_model_schema_reconcile.md` | ✅ §Source + slices | 任务卡 AC 映射 B03-L5/MODEL/CLOSE | 无 |
| `BATCH_3V_COORDINATOR_PLAYBOOK.md` §3.1 | ✅ §3.1 表 | 共用底座 | 无 |
| §3.7 B3V-L5R 索引 | ✅ §3.7 表 | 逐路径落点 | 无 — `test_migration_coverage` 标高 |
| `BATCH_3V_HARDENING_RULES.md` §6 | ✅ Hardening 摘要 | reconcile-first | 无 |
| `BATCH_3V_TASK_CARD_MANIFEST.md` §3 C06 | ✅ Source of truth | branch ownership | 无 |
| `agent-toolchain.md` | ✅ Source of truth | GitNexus + codebase-memory | 无 |
| `round3-repair-debt-worktree-plan.md` §8D | ✅ Source + Merge gate | debt-lite 模板 | 无 |
| `023` / `023A` 任务卡 | ✅ §3.7 | 只读对照 | 无 |
| `layer5_evidence_contract.yaml` | ✅ §3.1 契约行 | B03-L5-02 | 无 |
| `04_data_architecture.md` | ✅ B03-MODEL-02 allowed | 矩阵引用 | 低 — Execute 最小 diff |
| `authority_graph.yaml` | ⚠️ Execute boot | `layer5_evidence` 已映射；`test_migration_coverage` 新模块须 `loop_maintain --fix` | 中 — Execute 门禁 |
| `GLOBAL_TASK_TEMPLATE.md` §15 | ✅ Hardening + Boundary | 无 production 声称 | 无 |
| `VR-L5-001` closure test | ✅ B03-L5-02/CLOSE | chain+foundation pytest | 无 |
| `VR-MODEL-001` closure test | ✅ B03-MODEL-03/CLOSE | **新建** migration_coverage pytest | 高 — 文件缺失，已排 slice |
| `/to-issues` 等价 | ✅ Vertical slices 表 | debt-lite 冻结 | 无 |

**Plan 质检结论：** `PASS_FOR_DISPATCH`（附注：`test_migration_coverage.py` 为 Execute blocker，已在 B03-MODEL-03 预定 TDD）

---

## Proposed registry deltas（主会话批处理 — agent 不 commit）

见 `research/registry_proposed_delta.yaml`。

**摘要：**

- `VR-L5-001` → `RESOLVED`（subtype: `audit_stale_reconciled`）；evidence: `376e30e6` + `test_layer5_evidence_chain.py` + `test_layer5_evidence_foundation.py`
- `VR-MODEL-001` → `RESOLVED`（subtype: `matrix_aligned`）**或** `AUDIT_DEFERRED`（若 Round 3F migration 仍为 blocking narrative）；evidence: `research/l5-reconcile-matrix.md` + `test_migration_coverage.py`
- 新增/更新 `AUDIT_DEFERRED` 行：`R3-MODEL-L3L4-MIGRATION` — L3/L4 建模表 migration ownership → Round 3F Batch 6

---

## Blockers

| ID | 描述 | Owner | 解除路径 |
| --- | --- | --- | --- |
| **BLK-L5R-01** | `tests/test_migration_coverage.py` 不存在，playbook §8.6 强制门禁无法满足 | B3V-L5R Execute | B03-MODEL-03 TDD 新建 |
| **BLK-L5R-02** | Registry 三件套禁止 agent commit | 主会话 merge coordinator | B03-CLOSE-01 批处理 |
| **BLK-L5R-03** | L3/L4 表无 `schema.sql` 集中定义（仅 module doc）— 矩阵须注明 SSOT 分裂 | B3V-L5R Execute | B03-MODEL-01 矩阵 `design_ssot` 列 |
| **BLK-L5R-04** | GitNexus 索引未命中 `EvidenceChainBuilder`（与 codebase-memory 冲突） | 任意 agent pre-edit | `node .gitnexus/run.cjs analyze` |
