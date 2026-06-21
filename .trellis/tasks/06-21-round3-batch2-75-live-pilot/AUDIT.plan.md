# Audit 计划 — Round 3 Batch 2.75 Production Live Pilot Gate

> 读者：主会话 + PH-B0–PH-B6 + A1–A8  
> 必读：本文 + `audit.jsonl`；A5 读 MASTER §2。

---

## 0. 元信息

| 字段            | 值                                            |
| --------------- | --------------------------------------------- |
| slug            | `06-21-round3-batch2-75-live-pilot`           |
| AUDIT_PROD_ROOT | `.audit-sandbox/r3b275-audit-prod-equiv`      |
| AUDIT_SANDBOX   | `.audit-sandbox/r3b275-audit`                 |
| 阶段审计        | **PH-B0–PH-B6**（018B phases；与 A1–A8 分离） |

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

| 阶段/维            | 验证类型    | 通过条件                                  | 环境                     |
| ------------------ | ----------- | ----------------------------------------- | ------------------------ |
| PH-B0              | read-only   | AC-PM\* + fail-closed tests               | local                    |
| PH-B1              | read-only   | baseline + zero mutation                  | local                    |
| PH-B2              | read-only   | route matrix 3 requests                   | local                    |
| PH-B3              | read-only   | raw evidence + prod DB delta 0            | local + network evidence |
| PH-B4              | read-only   | validation; no default clean write        | local                    |
| PH-B5              | cli-sandbox | smoke or re-defer documented              | audit-sandbox            |
| PH-B6              | cli-sandbox | PILOT\_\* + registry                      | audit-sandbox            |
| A5 audit-prod-path | copy        | prod DB hash unchanged                    | AUDIT_PROD_ROOT          |
| A3                 | static      | no production DB write path               | local                    |
| A6                 | cli-sandbox | micro-fetch elapsed ≤ 30s per request eco | audit-sandbox            |

## 3. 阶段产出与检查清单

### 3.0 PH-B0 — Phase -1 / Phase 0 gate（reconciliation + fail-closed）

**Agent:** audit-phase0 · **Skill:** doubt-driven-development

| #    | 检查项                                                    | 证据                        | 通过 |
| ---- | --------------------------------------------------------- | --------------------------- | ---- |
| B0-1 | `phase_minus1_reconciliation.md` 含五 tracked ID          | execute-evidence            |      |
| B0-2 | 四 registry 读证 `phase-1-registry-read.txt`              | execute-evidence            |      |
| B0-3 | not-in-scope + R2b 互斥注释                               | reconciliation md           |      |
| B0-4 | fail-closed tests 绿（无 network）                        | pytest log                  |      |
| B0-5 | `phase0_authorization_record.md` 含 source risk rationale | execute-evidence            |      |
| B0-6 | 授权文件与三请求参数一致                                  | batch275_user_authorization |      |

**产出:** `research/audit-ph-b0-reconciliation.md`

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
- [ ] PH-B0–PH-B6 PASS
- [ ] A1–A8 + A9
- [ ] prod-path hash proof
