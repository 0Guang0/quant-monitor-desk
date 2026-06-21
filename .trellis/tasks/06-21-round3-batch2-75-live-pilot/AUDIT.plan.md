# Audit 计划 — Round 3 Batch 2.75 Production Live Pilot Gate

> 读者：主会话 + PH-B0–PH-B6 + A1–A8  
> 必读：本文 + `audit.jsonl`；所有 Audit agent 必须读取与自身维度相关的 `audit.jsonl` 条目。  
> A1 / A5 / A8 必须倒查原始任务卡、项目地图、轮次地图、任务输入索引、unresolved coverage 与 Plan trace artifacts。  
> A5 另读 MASTER §2 / §8 / §10 / §11 与 Execute evidence。

---

## 0. 元信息

| 字段            | 值                                            |
| --------------- | --------------------------------------------- |
| slug            | `06-21-round3-batch2-75-live-pilot`           |
| AUDIT_PROD_ROOT | `.audit-sandbox/r3b275-audit-prod-equiv`      |
| AUDIT_SANDBOX   | `.audit-sandbox/r3b275-audit`                 |
| 阶段审计        | **PH-B0–PH-B6**（018B phases；与 A1–A8 分离） |

## 0.1 Audit Trace Authority Set（必读倒查源）

Audit 阶段不得只验证 Execute 是否按 MASTER 执行，还必须验证 MASTER / AUDIT 是否完整继承原始任务、项目地图、轮次地图与 unresolved registry。

以下文件是 Batch 2.75 的 trace authority set（`audit.jsonl` 已列入；A1/A5/A8 **must read original** 倒查源）：

| 类别                      | 文件                                                                                   | 必读 agent | 用途                                                                                          |
| ------------------------- | -------------------------------------------------------------------------------------- | ---------- | --------------------------------------------------------------------------------------------- |
| 原始任务                  | `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/018B_production_live_pilot_gate.md` | A1, A5, A8 | 倒查 Batch 2.75 原始 scope、授权字段、三 micro-pilot、边界、registry closeout 与 verification |
| implementation task index | `docs/implementation_tasks/README.md`                                                  | A1         | 验证 Plan 是否遵守原始任务包入口                                                              |
| task input bridge         | `docs/implementation_tasks/TASK_INPUT_CONTEXT_INDEX.md`                                | A1, A5     | 验证 Plan 是否读取执行者必读上下文                                                            |
| unresolved coverage       | `docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md`                           | A1, A5, A8 | 验证未闭合项是否进入 MASTER AC / Execute §8 / Audit matrix                                    |
| 项目地图                  | `MIGRATION_MAP.md`                                                                     | A1, A5     | 验证实现目录、docs/specs 边界、模块映射未遗漏                                                 |
| 轮次地图                  | `ROUND3_BATCH_IMPLEMENTATION_MAP.md`                                                   | A1, A5     | 验证 Batch 2.75 item IDs、source bundle、out-of-scope 与 handoff                              |
| 原计划追溯                | `research/original-plan-trace.md`                                                      | A1, A5     | 验证原始任务章节到 MASTER AC 的映射                                                           |
| 输入清单                  | `research/input-inventory.md`                                                          | A1         | 验证六类关键信息是否覆盖                                                                      |
| 项目地图遗漏检查          | `research/project-map-omission-check.md`                                               | A1, A5     | 验证项目地图倒查结论是否可信                                                                  |
| context packing ledger    | `research/integration-ledger.md`                                                       | A1, A5, A8 | 验证 inline / summary+pointer / pointer / filtered 决策是否合理                               |

如果任一 trace authority 文件缺失、未读、或与 MASTER / AUDIT 存在未解释差异，A1 或 A5 必须将其列入 `audit.report.md` §4.3，不得 PASS。

## 1. Skill 冻结

### 1.1 阶段门控

| 阶段  | Agent         | Skill                                                     | 产出 |
| ----- | ------------- | --------------------------------------------------------- | ---- |
| PH-B0 | audit-phase0  | doubt-driven-development                                  | §3.0 |
| PH-B1 | audit-phase1  | doubt-driven-development                                  | §3.1 |
| PH-B2 | audit-phase2  | doubt-driven-development                                  | §3.2 |
| PH-B3 | audit-phase3  | doubt-driven-development                                  | §3.3 |
| PH-B4 | audit-phase4  | doubt-driven-development                                  | §3.4 |
| PH-B5 | audit-phase45 | doubt-driven-development                                  | §3.5 |
| PH-B6 | audit-phase5  | verification-before-completion + doubt-driven-development | §3.6 |

### 1.2 维度 A1–A8

标准栈（trellis-check, ponytail, security, quality, completion, perf, ops, test-gap）+ doubt-driven-development；A9 主会话汇总。

## 2. 维度验证矩阵（摘要）

| 阶段/维            | 验证类型        | 通过条件                                     | 环境                     |
| ------------------ | --------------- | -------------------------------------------- | ------------------------ |
| PH-B0              | read-only       | AC-PM\* + fail-closed tests                  | local                    |
| PH-B1              | read-only       | baseline + zero mutation                     | local                    |
| PH-B2              | read-only       | route matrix 3 requests                      | local                    |
| PH-B3              | read-only       | raw evidence + prod DB delta 0               | local + network evidence |
| PH-B4              | read-only       | validation; no default clean write           | local                    |
| PH-B5              | cli-sandbox     | smoke or re-defer documented                 | audit-sandbox            |
| PH-B6              | cli-sandbox     | PILOT\_\* + registry                         | audit-sandbox            |
| A5 audit-prod-path | copy            | prod DB hash unchanged                       | AUDIT_PROD_ROOT          |
| A3                 | static          | no production DB write path                  | local                    |
| A6                 | cli-sandbox     | micro-fetch elapsed ≤ 30s per request eco    | audit-sandbox            |
| **A1**             | read-only       | original-source trace（见 §2.1）             | local                    |
| **A5**             | trace-ac        | AC source-chain trace（见 §2.1）             | local / audit-prod-path  |
| **A8**             | pytest-isolated | original-red-flags test-gap trace（见 §2.1） | audit-sandbox            |

### 2.1 A1 / A5 / A8 倒查职责（Plan omission gate）

**A1 必须执行 original-source trace：**

- 对照 `018B_production_live_pilot_gate.md`、`ROUND3_BATCH_IMPLEMENTATION_MAP.md`、`MIGRATION_MAP.md`、`TASK_INPUT_CONTEXT_INDEX.md`、`UNRESOLVED_ITEM_TASK_COVERAGE.md`。
- 验证原始任务、项目地图、轮次地图、unresolved coverage 中的 required / deferred / filtered 项是否进入：
  - MASTER §0.6 Source Context Index
  - MASTER §1.3 子交付物表
  - MASTER §2 AC
  - MASTER §8 执行步骤
  - AUDIT.plan §2 / PH-B0–PH-B6
  - `audit.jsonl` 或明确 filtered/deferred reason
- 若发现原始任务或 registry 项未进入上述任一位置，必须标记为 Plan omission，列入 §4.3。

**A5 必须执行 AC source-chain trace：**

- 从原始任务卡 `018B`、Round3 map、unresolved coverage、四 registry 出发，逐项追溯到 MASTER §2 AC。
- 每个 tracked ID / alias 必须能追溯到 close / re-defer / owner / phase / closure test。
- 对以下项必须逐项判定：
  - `R3-B2.75-PROD-LIVE-PILOT`
  - `R3-B2.75-01`
  - `GLOBAL-P2-01`
  - `B2.5-O-05`
  - `R3-B25-PERF-BUDGET-01`
  - `R3-B25-HYG-03`
  - `R3-B25-HYG-01` ingestion split out-of-scope
  - `B2.5-O-06` / `A9-*` migration 008 out-of-scope
  - `R3-B25-HYG-02` frontend bundle out-of-scope
  - Batch 6 release gates / `qmd data` production CLI out-of-scope
- A5 不得只检查 Execute evidence 是否存在；必须验证 evidence 是否覆盖原始 source-chain。

**A8 必须执行 original-red-flags test-gap trace：**

- 对照 `018B`、`production_live_pilot_policy.md`、`GLOBAL_TESTING_POLICY.md`、`UNRESOLVED_ITEM_TASK_COVERAGE.md`。
- 验证以下边界均有测试或 explicit audit check：
  - fail-closed authorization
  - one source/domain/operation per pilot request
  - tiny allowlist 不得扩源
  - `baostock` primary path
  - `akshare` validation-only 不得升 Primary
  - `akshare` `DGS10` 不得关闭 FRED primary
  - optional `cninfo` 不得默认纳入
  - route non-READY stops request
  - no fixture/staged fallback
  - no production DB mutation
  - no clean write by default
  - no full-market / full-history / backfill / reconcile
  - no ingestion R2b–R2d same sprint
  - no Batch 3 / 019 implementation
- 若测试只覆盖 MASTER 压缩后的路径，而未覆盖原始任务中的 Red Flags，必须列入 §4.3。

## 3. 阶段产出与检查清单

### 3.0 PH-B0 — Phase -1 / Phase 0 gate（reconciliation + fail-closed）

**Agent:** audit-phase0 · **Skill:** doubt-driven-development

| #    | 检查项                                                                                                                                                               | 证据                                     | 通过 |
| ---- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- | ---- |
| B0-1 | `phase_minus1_reconciliation.md` 含五 tracked ID                                                                                                                     | execute-evidence                         |      |
| B0-2 | 四 registry 读证 `phase-1-registry-read.txt`                                                                                                                         | execute-evidence                         |      |
| B0-3 | not-in-scope + R2b 互斥注释                                                                                                                                          | reconciliation md                        |      |
| B0-4 | fail-closed tests 绿（无 network）                                                                                                                                   | pytest log                               |      |
| B0-5 | `phase0_authorization_record.md` 含 source risk rationale                                                                                                            | execute-evidence                         |      |
| B0-6 | 授权文件与三请求参数一致                                                                                                                                             | batch275_user_authorization              |      |
| B0-7 | original-source trace authority set 已读；018B / ROUND3 map / MIGRATION_MAP / unresolved coverage 均能映射到 MASTER AC / §8 / AUDIT §2 或 explicit filtered/deferred | audit-ph-b0-reconciliation §source-trace |      |

**产出:** `research/audit-ph-b0-reconciliation.md`（含 §source-trace 小节记录 B0-7）

### 3.1 PH-B1 — Phase 1 baseline

| #    | 检查项                        | 证据                            | 通过 |
| ---- | ----------------------------- | ------------------------------- | ---- |
| B1-1 | baseline inventory json/md    | phase1_baseline_inventory.\*    |      |
| B1-2 | capability snapshot           | phase1_capability_snapshot.json |      |
| B1-3 | production DB 零 mutation     | phase1_no_mutation_proof.md     |      |
| B1-4 | data-root inventory（若适用） | baseline json                   |      |

**产出:** `research/audit-ph-b1-baseline.md`

### 3.2 PH-B2 — Phase 2 route matrix

| #    | 检查项                        | 证据                             | 通过 |
| ---- | ----------------------------- | -------------------------------- | ---- |
| B2-1 | 三请求 route preview JSON     | phase2_route_preview_matrix.json |      |
| B2-2 | 每请求 `route_status` 记录    | matrix json                      |      |
| B2-3 | ResourceGuard 决策快照        | matrix / test payload            |      |
| B2-4 | 非 READY 停止码证据（若失败） | failure artifact                 |      |
| B2-5 | 无 fixture fallback           | gate tests                       |      |

**产出:** `research/audit-ph-b2-route.md`

### 3.3 PH-B3 — Phase 3 HITL + raw fetch

| #    | 检查项                        | 证据                                   | 通过 |
| ---- | ----------------------------- | -------------------------------------- | ---- |
| B3-1 | HITL 文件存在且先于 fetch     | phase3_hitl_user_confirmation.md       |      |
| B3-2 | sandbox raw evidence JSON     | phase3_raw_micro_fetch_evidence.json   |      |
| B3-3 | production DB delta = 0       | phase3_no_production_mutation_proof.md |      |
| B3-4 | Request 2 不升 Primary        | evidence per-request                   |      |
| B3-5 | Request 3 不关闭 FRED primary | evidence `fred_primary_deferred`       |      |
| B3-6 | content hash + fetch_log 字段 | evidence json                          |      |

**产出:** `research/audit-ph-b3-raw-fetch.md`

### 3.4 PH-B4 — Phase 4 validation + conflict

| #    | 检查项                          | 证据                          | 通过 |
| ---- | ------------------------------- | ----------------------------- | ---- |
| B4-1 | validation report on raw        | phase4_validation_report.json |      |
| B4-2 | conflict inspect 或 no-conflict | phase4_conflict_inspect.txt   |      |
| B4-3 | 默认无 clean write              | gate test + report            |      |
| B4-4 | severe 阻断 clean write         | validation severity           |      |
| B4-5 | production DB 仍不变            | delta proof                   |      |

**产出:** `research/audit-ph-b4-validation.md`

### 3.5 PH-B5 — Phase 4.5 perf budget

| #    | 检查项                                 | 证据                            | 通过 |
| ---- | -------------------------------------- | ------------------------------- | ---- |
| B5-1 | `phase45_perf_budget.json` schema 完整 | owner/phase/closure_test/status |      |
| B5-2 | smoke 在隔离 data-root 或 re-defer     | AUDIT_DEFERRED row              |      |
| B5-3 | bounded + ResourceGuard                | smoke log                       |      |
| B5-4 | 不作 live 授权依据                     | closeout wording                |      |

**产出:** `research/audit-ph-b5-perf.md`

### 3.6 PH-B6 — Phase 5 closeout

| #    | 检查项                       | 证据                     | 通过 |
| ---- | ---------------------------- | ------------------------ | ---- |
| B6-1 | 单一 `PILOT_*` 状态          | final_pilot_closeout.md  |      |
| B6-2 | 四 registry 一致             | final_registry_update.md |      |
| B6-3 | Batch 3 handoff 模板字段完整 | final_registry_update.md |      |
| B6-4 | §10 Tier A–G 全绿            | final_pytest_output.txt  |      |
| B6-5 | prod-path hash 不变          | audit A5                 |      |
| B6-6 | AC-REG-2 checklist           | closeout md              |      |

**产出:** `research/audit-ph-b6-closeout.md`

## 3.7 阶段文件索引

| 阶段  | 文件                                     |
| ----- | ---------------------------------------- |
| PH-B0 | `research/audit-ph-b0-reconciliation.md` |
| PH-B1 | `research/audit-ph-b1-baseline.md`       |
| PH-B2 | `research/audit-ph-b2-route.md`          |
| PH-B3 | `research/audit-ph-b3-raw-fetch.md`      |
| PH-B4 | `research/audit-ph-b4-validation.md`     |
| PH-B5 | `research/audit-ph-b5-perf.md`           |
| PH-B6 | `research/audit-ph-b6-closeout.md`       |

## 4. Audit Source Trace

| Item ID                  | 原文                    | AC        | 证据                        |
| ------------------------ | ----------------------- | --------- | --------------------------- |
| R3-B2.75-PROD-LIVE-PILOT | 018B §5–9               | AC-P0..P4 | phase0–4 evidence           |
| R3-B2.75-01              | policy + authorization  | AC-P3,P5  | phase3 + closeout           |
| B2.5-O-05                | ENV-E1-DGS10 / FRED     | AC-P3-5   | closeout wording            |
| R3-B25-PERF-BUDGET-01    | smoke script            | AC-P45    | phase45                     |
| route/service            | contracts + service.py  | AC-P2,P3  | route matrix + fetch        |
| conflict                 | source_conflict + rules | AC-P4-5   | phase4_conflict_inspect.txt |
| inspect                  | ops_db_inspect_contract | AC-P1,P3  | baseline + delta            |
| Batch 2.5 staged         | final_registry_update   | AC-PRE    | no promotion                |

## 5. Audit DoD

- [ ] 7.pre gitnexus-audit-summary.md
- [ ] 7.pre.1 Trace Authority Presence Check（manifest 入口完整；缺失则退回 Plan）
- [ ] PH-B0–PH-B6 PASS
- [ ] A1–A8 + A9
- [ ] prod-path hash proof
