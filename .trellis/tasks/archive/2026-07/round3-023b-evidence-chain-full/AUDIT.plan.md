# AUDIT 计划 — round3-023b-evidence-chain-full

> 读者：主会话 + A1–A8 · audit.jsonl 第一条 = 本文件  
> **must read original task card** — `023_implement_layer5_evidence_chain.md` 为 AC 原文权威

---

## 0. 元信息

| 字段            | 值                                        |
| --------------- | ----------------------------------------- |
| 任务 slug       | `round3-023b-evidence-chain-full`         |
| AUDIT_PROD_ROOT | `.audit-sandbox/r3-023b-audit-prod-equiv` |

## 1. 维度 — Skill 冻结

| 维  | Agent            | Skill                                                     | 本任务   | 已执行   |
| --- | ---------------- | --------------------------------------------------------- | -------- | -------- |
| A1  | audit-spec       | trellis-check + doubt-driven-development                  | 必做     | [ ]      |
| A2  | audit-ponytail   | ponytail-review + doubt-driven-development                | 必做     | [ ]      |
| A3  | audit-security   | security-and-hardening + doubt-driven-development         | 必做     | [ ]      |
| A4  | audit-quality    | code-review-and-quality + doubt-driven-development        | 必做     | [ ]      |
| A5  | audit-completion | verification-before-completion + doubt-driven-development | 必做     | [ ]      |
| A6  | audit-perf       | doubt-driven-development                                  | **不用** | [ ] SKIP |
| A7  | audit-ops        | doubt-driven-development                                  | 必做     | [ ]      |
| A8  | audit-test-gap   | testing-guidelines + doubt-driven-development             | 必做     | [ ]      |
| A9  | 主会话           | —                                                         | 必做     | [ ]      |

## 2. 维度验证矩阵

| 维  | 验证类型        | 命令 / 检查                                                                       | 环境            | 通过条件                   | 已执行 |
| --- | --------------- | --------------------------------------------------------------------------------- | --------------- | -------------------------- | ------ |
| A1  | read-only       | 对照 `layer5_evidence_contract.yaml`、`layer5_security_evidence.md`、MASTER §2/§3 | local           | scope 无泄漏；023A 未推翻  | [ ]    |
| A2  | review-only     | ponytail-review `layer5_evidence/**` + `tests/test_layer5_evidence_chain.py`      | local           | 复用 foundation；最小 diff | [ ]    |
| A3  | static          | `rg` live fetch / forbidden 路径 / registry 写                                    | local           | 无 mutation                | [ ]    |
| A4  | review-only     | chain trace + agent-not-fact + conflict ADR 一致                                  | local           | 无阻断质量问题             | [ ]    |
| A5  | trace-ac        | AC-023-1..6 ↔ §9 evidence + playbook §8.4                                         | local           | 全 AC 可追溯               | [ ]    |
| A5  | cli-sandbox     | `.audit-sandbox/r3-023b` 复跑 chain + foundation tests                            | audit-sandbox   | 与 Execute 一致            | [ ]    |
| A5  | audit-prod-path | 复制树到 `AUDIT_PROD_ROOT`；Tier A pytest                                         | audit-prod-path | 无污染                     | [ ]    |
| A6  | —               | **本任务跳过 — builder 无 hot path/SLA**                                          | —               | SKIP                       | [ ]    |
| A7  | cli-sandbox     | 无 production DB 写；Track B 未混 Batch 01 PR 声称                                | audit-sandbox   | 无 prod 写                 | [ ]    |
| A8  | pytest-isolated | 五字段 docstring；补边界：空 upstream ids / severe without queue                  | audit-sandbox   | 新测绿或记入 report        | [ ]    |
| A8  | audit-prod-path | 复跑 `test_layer5_evidence_foundation.py` + batch3 gate                           | audit-prod-path | 全绿                       | [ ]    |

### 2.2 A6 SKIP

本任务跳过性能审计 — evidence chain builder 仅处理小型 staged fixture。

## 3. Audit Source Trace

| Item       | 原文                                                 | AC          | 证据                                 |
| ---------- | ---------------------------------------------------- | ----------- | ------------------------------------ |
| `023`      | `023_implement_layer5_evidence_chain.md`             | AC-023-\*   | `test_layer5_evidence_chain.py`      |
| `023A`     | foundation 归档                                      | AC-023-1,3  | `test_layer5_evidence_foundation.py` |
| contract   | `layer5_evidence_contract.yaml`                      | AC-023-1..3 | contract 测试名                      |
| conflict   | `data_validation_and_conflict.md` + ADR-023          | AC-023-4    | severe→queued test                   |
| roadmap    | `R3D-023-01`..`05`                                   | AC-023-1..5 | §8 切片                              |
| playbook   | `BATCH_01_MAIN_SESSION_COORDINATOR_PLAYBOOK.md` §8.4 | AC-023-6    | §2.1                                 |
| UNRESOLVED | `R3-PARTIAL-4` / `R2-RISK-2`                         | AC-023-4,5  | ADR / port test                      |

## 4. Audit DoD

- [ ] 7.pre `gitnexus-audit-summary.md`
- [ ] A1–A8（A6 SKIP）
- [ ] A9 汇总 PASS / FAIL
- [ ] Track B 边界未被 Execute 越界
- [ ] playbook §8.4 子 AC 全勾
