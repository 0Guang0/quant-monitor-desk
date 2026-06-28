# Repair/Debt Lite Plan — B3V-L5R Layer5 / Model Schema Reconcile

> **Playbook ID:** B3V-L5R (`B3V-C06`)  
> **轨道:** debt-lite（playbook §5.2）  
> **模型:** `composer-2.5`  
> **Trellis task-dir:** `.trellis/tasks/round3v-layer5-model-schema-reconcile`  
> **本阶段:** 轻量 Plan only — **禁止**改 `backend/app/layer5_evidence/**` runtime、**禁止** registry 三件套 commit  
> **WAVE0 SSOT:** `WAVE0_BATCH3V_TO_ISSUES_INDEX.md` §2（L5R-BOOT..L5R-CLOSE）· 竖条冻结见 `research/vertical-slices.md`

---

## Source of truth

| 项            | 值                                                                                                                                 |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| 任务卡        | `docs/implementation_tasks/ROUND_3_VERIFIED_AUDIT_CLEANUP/BATCH_3V_VERIFIED_AUDIT_CLEANUP/B03_01_layer5_model_schema_reconcile.md` |
| Manifest      | `BATCH_3V_TASK_CARD_MANIFEST.md` → `B3V-C06`                                                                                       |
| 协调手册      | `BATCH_3V_COORDINATOR_PLAYBOOK.md` §3.1 + §3.7 + §5.2                                                                              |
| Hardening     | `BATCH_3V_HARDENING_RULES.md` §6 reconcile-first                                                                                   |
| Phase 8D      | `.trellis/spec/guides/round3-repair-debt-worktree-plan.md` + `complex-task-planning-protocol.md` §8D                               |
| 工具路由      | `agent-toolchain.md`（GitNexus + codebase-memory 同级交叉核实）                                                                    |
| base branch   | `master`（post Batch 01；含 `376e30e6`）                                                                                           |
| target branch | `review/round3v-layer5-model-schema-reconcile`                                                                                     |
| worktree      | `C:\Users\Guang\Desktop\quant-monitor-desk-wt-b3v-l5r`                                                                             |
| owner agent   | B3V-L5R Plan → 核对 agent（同分支）                                                                                                |

## 决策与目标

**reconcile-first（Hardening §6）：** 对照 post Batch 01 master（`376e30e6`+）核对审计 `VR-L5-001` / `VR-MODEL-001`，不重复实现已完成 023 staged runtime。

| VR ID          | Plan 预判（Execute 前须实测确认）                                                                                                                                       | 预期处置                                                                                                                     |
| -------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `VR-L5-001`    | 证据链 builder / provenance / agent-text / manual review / lineage hash **已在 staged runtime + pytest 覆盖**（`376e30e6`；`AUDIT_DEFERRED` `R3-TASK-023` 已 RESOLVED） | **stale close**（独立证据：`test_layer5_evidence_chain.py` + `test_layer5_evidence_foundation.py`）                          |
| `VR-MODEL-001` | L3/L4/L5 表多数 **designed + staged runtime**，**无 migration**；`MIGRATION_COVERAGE.md` 缺 L3/L4 段；`test_migration_coverage.py` **worktree 已建**（6 tests）           | **矩阵落盘 + docs 对齐**；缺 migration 表 **re-defer → Round 3F**；`test_migration_coverage.py` 作 closure test（MODEL-02 TDD 证据保留） |

**允许表述：** stale reconciled · designed/implemented/deferred matrix · precise re-defer to Round 3F · staged-only evidence  
**禁止表述：** production-ready · Layer5 production-ready · designed table = migrated table

## Boundary（§2.5 / §2.6 SSOT）

| 维度                | 内容                                                                                                                                                                                                                                                     |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **§2.5 文件锁**     | `backend/app/layer5_evidence/**` **默认只读**；runtime 缺口 → 独立 follow-up 分支 `feature/round3-023c-*` 或 Round 3F migration 分支                                                                                                                     |
| **§2.6 B3V-L5R**    | **Owns：** 核对矩阵、registry/docs 更新、targeted pytest · **Must not own：** 默认改 `layer5_evidence/**`；production-ready 声称（playbook §2.6 原文）                                                                                                  |
| **Owns（可写）**    | `research/l5-reconcile-matrix.md` · `research/*.md` · `docs/schema/MIGRATION_COVERAGE.md`（L3/L4/L5 段）· `docs/architecture/04_data_architecture.md`（矩阵引用，最小 diff）· `tests/test_migration_coverage.py` · proposed registry delta YAML       |
| **Must not own**    | `layer5_evidence/**` runtime · migration SQL 文件（Round 3F）· sync/write/validation/rawstore runtime · migration 009 语义 · registry 三件套直接 commit · production DB 写                                                                               |
| **§8.6 未改什么**   | sync/write/validation/rawstore runtime · migration 009 语义 · 主会话 registry 直接 commit（playbook §8.6 负向边界）                                                                                                                                      |
| **production/data** | 无 live fetch · 无 clean write · db-inspect 只读                                                                                                                                                                                                         |
| **non-goals**       | 不重复 023 实现 · 不水平合并关两个 VR · 不删 `deferred_to_023b` 类注记无证据                                                                                                                                                                             |

## 基线证据（Plan 期已核实）

| 检查项                                   | 结果                                                         | 指针                                                                                            |
| ---------------------------------------- | ------------------------------------------------------------ | ----------------------------------------------------------------------------------------------- |
| Batch 01 Layer5 merge                    | `376e30e6` merge(wave-d): B01-023 full Layer5 evidence chain | `docs/AUDIT_DEFERRED_REGISTRY.md` `R3-TASK-023`                                                 |
| `test_layer5_evidence_chain.py`          | 7 tests，五字段齐全                                          | `tests/test_layer5_evidence_chain.py`                                                           |
| `test_layer5_evidence_foundation.py`     | 6 tests（含 lineage hash / identity hash）                   | `tests/test_layer5_evidence_foundation.py`                                                      |
| targeted pytest（worktree）              | 13 passed（2026-06-25 Plan 跑）                              | `uv run pytest tests/test_layer5_evidence_chain.py tests/test_layer5_evidence_foundation.py -q` |
| `test_migration_coverage.py`             | **6 tests**（worktree 已建；MODEL-02 TDD RED→GREEN 证据路径保留） | `tests/test_migration_coverage.py` · `execute-evidence/b03-model-03-red/green.txt`              |
| migrations 001–011                       | 无 `industry_chain_*` / `market_*` / L5 建模表               | `backend/app/db/migrations/`                                                                    |
| GitNexus `context(EvidenceChainBuilder)` | symbol not found（索引滞后）                                 | codebase-memory 命中 `evidence_chain.py:23` — Execute 前 `node .gitnexus/run.cjs analyze`       |

---

## Vertical slices（WAVE0 §2 · L5R-BOOT..L5R-CLOSE）

> **SSOT 竖条：** `research/vertical-slices.md`  
> L5 轨（`L5-01`/`L5-02`）与 MODEL 轨（`MODEL-01`/`MODEL-02`）**分轨**；`L5R-CLOSE` **独立**关账切片（per-VR proposed delta，**禁止**水平合并关账）。

| 序 | Slice ID | Source ID | AC（完成标准） | Allowed files | Forbidden | Verification | Evidence path |
| -- | -------- | --------- | -------------- | ------------- | --------- | ------------ | ------------- |
| 0 | **L5R-BOOT** | — | post Batch 01 基线：`376e30e6` + 现有 Layer5 pytest 绿 | `execute-evidence/` | runtime 改 | `pytest test_layer5_evidence_chain.py` 绿 | `execute-evidence/l5r-boot-pytest.txt` |
| 1 | **L5-01** | `VR-L5-001` | 证据链能力矩阵：builder / provenance / upstream / port — 每行 **implemented / staged / gap** | `research/l5-reconcile-matrix.md` §2 | `layer5_evidence/**` | 只读对照 runtime | `research/l5-reconcile-matrix.md` |
| 2 | **L5-02** | `VR-L5-001` | 矩阵每行有 test 名；agent-text / manual review / lineage hash 无回归 | `research/l5-reconcile-matrix.md` · `research/layer5-evidence-chain-reconcile.md` | runtime | `pytest test_layer5_evidence_chain.py` + `test_layer5_evidence_foundation.py` 全绿 | `execute-evidence/b03-l5-02-pytest.txt` |
| 3 | **MODEL-01** | `VR-MODEL-001` | L3/L4/L5 designed / implemented(staged) / deferred(migration) 三列矩阵 | `research/model-table-matrix.md` · `research/l5-reconcile-matrix.md` §3 · `research/model-schema-table-reconcile.md` | migration SQL | 每表 design_ssot + evidence 列 | `research/model-table-matrix.md` |
| 4 | **MODEL-02** | `VR-MODEL-001` | `MIGRATION_COVERAGE.md` L3/L4/L5 与矩阵一致；**TDD** `test_migration_coverage.py` 绿 | `docs/schema/MIGRATION_COVERAGE.md` · `tests/test_migration_coverage.py` | 弱化断言 | `pytest test_migration_coverage.py` + `check_docs_specs_indexed.py` exit 0 | `execute-evidence/b03-model-02-docs.txt` · `b03-model-03-red/green.txt` |
| 5 | **L5R-CLOSE** | per-VR（见下） | **独立**关账：per-VR 证据 bundle → `registry_proposed_delta.yaml`；**不**声称 production-ready | `research/registry_proposed_delta.yaml` · 矩阵 §1 | registry 三件套 commit | 双 mandatory pytest 绿（见下节） | `execute-evidence/b03-l5-close.txt`（`VR-L5-001`）· `b03-model-close.txt`（`VR-MODEL-001`） |

**L5R-CLOSE per-VR 证据（禁止水平合并）：** `VR-L5-001` → `b03-l5-close.txt` + chain/foundation pytest；`VR-MODEL-001` → `b03-model-close.txt` + `test_migration_coverage.py`；registry YAML 两行独立 proposed delta。

**WAVE0 §2 证据路径映射：** `9.0-green.txt` → `l5r-boot-pytest.txt` · `9.1-green.txt` → `b03-l5-02-pytest.txt` · `9.2-green.txt` → `b03-model-02-docs.txt` + `b03-model-03-red/green.txt`

**任务卡 legacy 映射：** `L5-01`≈`B03-L5-01` · `L5-02`≈`B03-L5-02` · `MODEL-01`≈`B03-MODEL-01` · `MODEL-02`≈`B03-MODEL-02`+`B03-MODEL-03` · `L5R-CLOSE`≈`B03-L5-CLOSE`+`B03-MODEL-CLOSE`（agent）+ `B03-CLOSE-01`（主会话 registry）

**VR-L5-001 gap（不阻塞 stale close，写入矩阵 follow-up）：** DB 持久化表 → `VR-MODEL-001`/Round 3F；023 全量 financial/valuation/event 表 → designed only

## 强制 targeted pytest 计划（playbook §8.6 · 关账门禁）

```bash
uv sync --locked
uv run pytest tests/test_layer5_evidence_chain.py -q          # L5-02 · VR-L5-001
uv run pytest tests/test_migration_coverage.py -q               # MODEL-02 · VR-MODEL-001
uv run python scripts/check_docs_specs_indexed.py
```

| 测试 | 切片 | VR | Plan 基线（2026-06-28 worktree） |
| ---- | ---- | -- | -------------------------------- |
| `tests/test_layer5_evidence_chain.py` | L5-02 | `VR-L5-001` | 7 tests — **须绿** |
| `tests/test_layer5_evidence_foundation.py` | L5-02 | `VR-L5-001` | 6 tests — L5-02 补充 |
| `tests/test_migration_coverage.py` | MODEL-02 | `VR-MODEL-001` | 6 tests — **须绿**（TDD RED→GREEN 在 MODEL-02） |

**禁止：** 仅只读 report 关 `VR-*`；无上述 pytest 绿不得进入 `L5R-CLOSE`。

## 研究产物路径（Plan 预定）

| 路径 | 切片 | 用途 |
| ---- | ---- | ---- |
| `research/l5-reconcile-matrix.md` | L5-01 / L5-02 / L5R-CLOSE | per-VR 摘要 + §2 L5 能力 + §3 表矩阵详表 |
| `research/model-table-matrix.md` | MODEL-01 | WAVE0 §2 交付物 SSOT（汇总层） |
| `research/model-schema-table-reconcile.md` | MODEL-01 | 研究笔记 / migration inventory |
| `research/vertical-slices.md` | Plan | WAVE0 竖条冻结 |
| `research/registry_proposed_delta.yaml` | L5R-CLOSE | 主会话批闭合提案 |

---

## §3.1 共用底座索引（已入 Plan）

| 类别     | 路径                                                                                 | Plan 落点           |
| -------- | ------------------------------------------------------------------------------------ | ------------------- |
| 协调     | playbook · BATCH_3V package · README                                                 | Source of truth     |
| 协调     | `PROJECT_IMPLEMENTATION_ROADMAP.md` Round 3V.2                                       | 决策表              |
| 协调     | `round3-repair-debt-worktree-plan.md` §8D · `agent-toolchain.md`                     | 本文结构            |
| 审计     | `quant_monitor_desk_verified_audit_report_2026-06-25_v3_INDEX.md`                    | VR 路由             |
| 审计     | `BATCH_3V_HARDENING_RULES.md` §6                                                     | reconcile-first     |
| Registry | `AUDIT_DEFERRED` / `UNRESOLVED` / `RESOLVED` · `UNRESOLVED_ITEM_TASK_COVERAGE.md`    | proposed delta only |
| Handoff  | `ROUND3_HANDOFF.md` · post Batch 01 checkpoint                                       | 基线 `376e30e6`     |
| 全局     | `GLOBAL_EXECUTION_RULES.md` · `GLOBAL_TESTING_POLICY.md` · `GLOBAL_TASK_TEMPLATE.md` | Boundary + 五字段   |
| 契约     | `layer5_evidence_contract.yaml` · `snapshot_lineage_contract.yaml`                   | B03-L5-02 对照      |
| 架构     | `04_data_architecture.md` · `MIGRATION_COVERAGE.md` · `schema.sql`                   | B03-MODEL-\*        |

## §3.7 B3V-L5R 分支索引（playbook 逐行）

| 路径                                                                            | 用途            | 已入 Plan       | 摘要一句                    | 遗漏风险 |
| ------------------------------------------------------------------------------- | --------------- | --------------- | --------------------------- | -------- |
| `023_implement_layer5_evidence_chain.md` · `023A_layer5_evidence_foundation.md` | 023 权威        | B03-L5-01/02    | 全量目标 vs staged 实现边界 | 无       |
| `docs/modules/layer5_evidence_chain.md`                                         | Layer5 模块文档 | B03-MODEL-02    | 与矩阵交叉核对 overclaim    | 无       |
| `backend/app/layer5_evidence/`                                                  | runtime         | Boundary 只读   | 8 模块文件；023b staged     | 无       |
| `tests/test_layer5_evidence_chain.py`                                           | 强制 pytest     | L5-02 / L5R-CLOSE | 7 tests 绿                | 无       |
| `tests/test_layer5_evidence_foundation.py`                                      | 强制 pytest     | L5-02 / L5R-CLOSE | 6 tests 绿（VR-L5-001 补充） | 无    |
| `tests/test_migration_coverage.py`                                              | 强制 pytest     | MODEL-02 / L5R-CLOSE | 6 tests 绿             | 无       |
| `research/model-table-matrix.md`                                                | MODEL-01 SSOT   | MODEL-01          | WAVE0 §2 交付物           | 无       |
| `specs/schema/schema.sql`                                                       | 表 SSOT 设计    | B03-MODEL-01    | L5 仅 2 表；无 L3/L4        | 无       |
| `docs/schema/MIGRATION_COVERAGE.md`                                             | 覆盖文档        | B03-MODEL-02    | L3/L4/L5 段与矩阵对齐       | 无       |
| `docs/quality/..._v3_INDEX.md`                                                  | VR 路由         | Source of truth | stale / matrix              | 无       |

---

## Hardening 摘要（Execute 强制）

| 规则               | L5R 落地                                         |
| ------------------ | ------------------------------------------------ |
| §6 reconcile-first | 先读 `376e30e6` + pytest；再决定是否 stale       |
| §7 vertical slice  | L5 vs MODEL 分轨；每 VR 独立 CLOSE               |
| §5 hard stop       | 无 migration 不得标 implemented DB table         |
| §4 TDD             | `test_migration_coverage.py` 须 RED→GREEN        |
| Registry           | agent 仅 `research/registry_proposed_delta.yaml` |

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

## §3.9 Plan 追溯规则（playbook · debt-lite Plan质检）

| 规则         | L5R 落地                                                                                         | 状态 |
| ------------ | ------------------------------------------------------------------------------------------------ | ---- |
| **索引行**   | §3.1 + §3.7 每路径在 DEBT.plan 或 `research/l5-reconcile-matrix.md` 有对应行                     | ✅   |
| **VR 三联**  | `VR-L5-001` → L5-01/02/CLOSE；`VR-MODEL-001` → MODEL-01/02/CLOSE；均有 Source ID → AC → verification | ✅   |
| **负向边界** | Boundary 抄 §2.6 Must not own + §8.6 未改什么                                                   | ✅   |
| **切片垂直** | L5R-BOOT..CLOSE 六竖条；L5/MODEL 分轨；L5R-CLOSE per-VR 证据 bundle，禁止水平 report 关账        | ✅   |
| **证据路径** | `execute-evidence/*` + `research/*` 已预定；WAVE0 Step 列已映射                                    | ✅   |
| **复检**     | §3.10 遗漏风险列全「无」                                                                         | ✅   |

---

## §3.10 Plan 质检自检表

| 路径                                      | 已入 DEBT.plan          | 摘要一句                                                                           | 遗漏风险 |
| ----------------------------------------- | ----------------------- | ---------------------------------------------------------------------------------- | -------- |
| `B03_01_layer5_model_schema_reconcile.md` | ✅ §Source + slices     | 任务卡 AC 映射 B03-L5/MODEL/CLOSE                                                  | 无       |
| `BATCH_3V_COORDINATOR_PLAYBOOK.md` §3.1   | ✅ §3.1 表              | 共用底座                                                                           | 无       |
| §3.7 B3V-L5R 索引                         | ✅ §3.7 表              | 逐路径落点（含 foundation pytest）                                                 | 无       |
| `BATCH_3V_HARDENING_RULES.md` §6          | ✅ Hardening 摘要       | reconcile-first                                                                    | 无       |
| `BATCH_3V_TASK_CARD_MANIFEST.md` §3 C06   | ✅ Source of truth      | branch ownership                                                                   | 无       |
| `agent-toolchain.md`                      | ✅ Source of truth      | GitNexus + codebase-memory                                                         | 无       |
| `round3-repair-debt-worktree-plan.md` §8D | ✅ Source + Merge gate  | debt-lite 模板                                                                     | 无       |
| `023` / `023A` 任务卡                     | ✅ §3.7                 | 只读对照                                                                           | 无       |
| `layer5_evidence_contract.yaml`           | ✅ §3.1 契约行          | B03-L5-02                                                                          | 无       |
| `04_data_architecture.md`                 | ✅ B03-MODEL-02 allowed | 矩阵引用                                                                           | 无       |
| `authority_graph.yaml`                    | ✅ Merge gate           | `test_migration_coverage` 已入 `test_catalog.yaml`；Execute 跑 `loop_maintain --fix` | 无       |
| `GLOBAL_TASK_TEMPLATE.md` §15             | ✅ Hardening + Boundary | 无 production 声称                                                                 | 无       |
| `VR-L5-001` closure test                  | ✅ L5-02 + L5R-CLOSE    | chain + foundation pytest 独立证据                                                 | 无       |
| `VR-MODEL-001` closure test               | ✅ MODEL-02 + L5R-CLOSE | `test_migration_coverage.py` 6 tests + TDD 证据路径                                | 无       |
| `WAVE0_BATCH3V_TO_ISSUES_INDEX.md` §2     | ✅ Vertical slices 表   | L5R-BOOT..CLOSE 冻结；证据路径已映射                                               | 无       |
| `research/l5-reconcile-matrix.md`         | ✅ 研究产物表           | per-VR 矩阵 SSOT                                                                   | 无       |
| `research/registry_proposed_delta.yaml`   | ✅ L5R-CLOSE            | per-VR proposed delta；agent 不 commit registry                                    | 无       |
| `research/vertical-slices.md`             | ✅ WAVE0 竖条冻结       | `/to-issues` 等价                                                                  | 无       |
| playbook §2.6 / §8.6 边界                 | ✅ Boundary 表          | Owns/Must not own + 未改什么                                                       | 无       |
| playbook §5.2 禁止水平关账                | ✅ L5R-CLOSE 分轨       | per-VR 证据 bundle                                                                 | 无       |

**Plan 质检结论：** `PASS_FOR_DISPATCH`（2026-06-28 Plan 复检：§3.10 零遗留；竖条 L5R-BOOT..CLOSE 对齐 WAVE0 §2；双 VR 独立 closure test + 独立关账证据）

---

## Proposed registry deltas（主会话批处理 — agent 不 commit）

见 `research/registry_proposed_delta.yaml`。

**摘要：**

- `VR-L5-001` → `RESOLVED`（subtype: `audit_stale_reconciled`）；evidence: `376e30e6` + `test_layer5_evidence_chain.py` + `test_layer5_evidence_foundation.py`
- `VR-MODEL-001` → `RESOLVED`（subtype: `matrix_aligned`）**或** `AUDIT_DEFERRED`（若 Round 3F migration 仍为 blocking narrative）；evidence: `research/l5-reconcile-matrix.md` + `test_migration_coverage.py`
- 新增/更新 `AUDIT_DEFERRED` 行：`R3-MODEL-L3L4-MIGRATION` — L3/L4 建模表 migration ownership → Round 3F Batch 6

---

## Blockers

| ID             | 描述                                                                      | Owner                    | 解除路径                           |
| -------------- | ------------------------------------------------------------------------- | ------------------------ | ---------------------------------- |
| **BLK-L5R-01** | ~~`test_migration_coverage.py` 不存在~~ → **已解除**（worktree 6 tests 绿） | —                        | MODEL-02 Execute 已完成            |
| **BLK-L5R-02** | Registry 三件套禁止 agent commit                                          | 主会话 merge coordinator | `L5R-CLOSE` → `B03-CLOSE-01` 批处理 |
| **BLK-L5R-03** | L3/L4 表无 `schema.sql` 集中定义 — 矩阵须注明 SSOT 分裂                   | MODEL-01                 | `model-table-matrix.md` design_ssot 列 |
| **BLK-L5R-04** | GitNexus 索引未命中 `EvidenceChainBuilder`                                | Execute boot             | `node .gitnexus/run.cjs analyze`   |
| **BLK-L5R-05** | WAVE0 INDEX 未在 worktree（仅 main repo）— Plan 引用路径须用 docs 绝对路径 | Plan                     | 已写入 `vertical-slices.md`        |
