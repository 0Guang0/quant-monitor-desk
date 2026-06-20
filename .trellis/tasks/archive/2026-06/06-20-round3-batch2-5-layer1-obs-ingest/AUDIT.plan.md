# Audit 计划 — Round 3 Batch 2.5 Layer 1 Observation Ingestion Bridge

> 读者：主会话 + PH-A0–PH-A5 阶段审计 + A1–A8 维度审计  
> 必读：本文 + `audit.jsonl`；A5 另读 MASTER §2；Execute §10 证据只读。

---

## 0. 元信息

| 字段            | 值                                                      |
| --------------- | ------------------------------------------------------- |
| 任务 slug       | `06-20-round3-batch2-5-layer1-obs-ingest`               |
| audit.jsonl     | 第一条 = 本文件                                         |
| AUDIT_PROD_ROOT | `.audit-sandbox/r3b25-audit-prod-equiv`                 |
| AUDIT_SANDBOX   | `.audit-sandbox/r3b25-audit`                            |
| 阶段审计        | **PH-A0–PH-A5 强制**（018A §10；与维度 A1–A8 编号分离） |

## 1. 维度 — Agent — Skill 冻结清单

### 1.1 阶段门控审计（Execute 五阶段串行）

| 阶段  | Agent ID     | Skill                                                     | 本任务 | 产出 |
| ----- | ------------ | --------------------------------------------------------- | ------ | ---- |
| PH-A0 | audit-phase0 | doubt-driven-development                                  | 必做   | §3.0 |
| PH-A1 | audit-phase1 | doubt-driven-development                                  | 必做   | §3.1 |
| PH-A2 | audit-phase2 | doubt-driven-development                                  | 必做   | §3.2 |
| PH-A3 | audit-phase3 | doubt-driven-development                                  | 必做   | §3.3 |
| PH-A4 | audit-phase4 | doubt-driven-development                                  | 必做   | §3.4 |
| PH-A5 | audit-phase5 | verification-before-completion + doubt-driven-development | 必做   | §3.5 |

### 1.2 标准维度审计（批次完成后）

| 维度 | Agent ID         | Skill                                                     | 本任务 | 产出 |
| ---- | ---------------- | --------------------------------------------------------- | ------ | ---- |
| A1   | audit-spec       | trellis-check + doubt-driven-development                  | 必做   | §4.1 |
| A2   | audit-ponytail   | ponytail-review + doubt-driven-development                | 必做   | §4.2 |
| A3   | audit-security   | security-and-hardening + doubt-driven-development         | 必做   | §4.3 |
| A4   | audit-quality    | code-review-and-quality + doubt-driven-development        | 必做   | §4.4 |
| A5   | audit-completion | verification-before-completion + doubt-driven-development | 必做   | §4.5 |
| A6   | audit-perf       | systematic-debugging + doubt-driven-development           | 必做   | §4.6 |
| A7   | audit-ops        | doubt-driven-development                                  | 必做   | §4.7 |
| A8   | audit-test-gap   | testing-guidelines + doubt-driven-development             | 必做   | §4.8 |
| A9   | —                | —                                                         | 必做   | §5   |

## 2. 维度验证矩阵

### 2.1 阶段门控（018A §10 — Execute 不得跳阶段）

| 阶段  | 验证类型        | 命令 / 检查                                                                                        | 环境            | 隔离      | 通过条件                   | 证据 → |
| ----- | --------------- | -------------------------------------------------------------------------------------------------- | --------------- | --------- | -------------------------- | ------ |
| PH-A0 | read-only       | 对照 `phase0_db_contract_gate.md` + Phase 0 pytest 日志                                            | local           | 无写      | 无未分类 BLOCKER；AC-P0-\* | §3.0   |
| PH-A1 | read-only       | 只读 inspect；`ops_db_inspect_contract.yaml` 字段 + copy provenance                                | local           | 无写      | 零 mutation；AC-P1-\*      | §3.1   |
| PH-A2 | read-only       | `phase2_no_mutation_proof.md` + 行数对比                                                           | local           | 无写      | AC-P2-\*                   | §3.2   |
| PH-A3 | read-only       | 无 clean observation delta；ResourceGuard 证据                                                     | local           | 无写      | AC-P3-\*                   | §3.3   |
| PH-A4 | read-only       | WriteManager + DbValidationGate + lineage + post-inspect                                           | local           | 无写      | AC-P4-\*                   | §3.4   |
| PH-A5 | cli-sandbox     | `uv run pytest tests/test_layer1_ingestion_gates.py tests/test_layer1_observation_ingestion.py -q` | audit-sandbox   | tmp DB    | AC-GATE 子集               | §3.5   |
| PH-A5 | audit-prod-path | 复制 `data/` → `AUDIT_PROD_ROOT/data`；复跑 ingestion tests；prod hash 不变                        | audit-prod-path | copy only | handoff + registry         | §3.5   |

### 2.2 标准维度（批次完成后）

| 维  | 验证类型        | 命令 / 检查                                                                                                                                             | 环境            | 隔离      | 通过条件                  | 证据 → |
| --- | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- | --------- | ------------------------- | ------ |
| A1  | read-only       | 对照 018A §5 + MASTER §0.6 + 契约 YAML                                                                                                                  | local           | 无写      | 无 scope 泄漏             | §4.1   |
| A2  | review-only     | ponytail-review `backend/app/layer1_axes/ingestion.py`                                                                                                  | local           | 无写      | 无过度抽象                | §4.2   |
| A3  | static          | `rg create_adapter layer1_axes`；Phase 1/2 mutation；DbValidationGate on clean path                                                                     | local           | 无写      | 无违规路径                | §4.3   |
| A4  | review-only     | 语义测试非 call-only；prerequisite validator tests 仍绿                                                                                                 | local           | 无写      | pipeline tests 质量       | §4.4   |
| A5  | trace-ac        | AC-P0..P4 ↔ §8 evidence                                                                                                                                 | local           | 无写      | 全 AC 可追溯              | §4.5   |
| A5  | cli-sandbox     | `.audit-sandbox/r3b25-audit` 复跑 layer1 ingestion tests                                                                                                | audit-sandbox   | tmp DB    | 与 Execute 一致           | §4.5   |
| A5  | read-only       | 抽检 `execute-evidence/8.x-green.txt` + `phase*_*.md` 真实性                                                                                            | local           | 无写      | 非占位符                  | §4.5   |
| A5  | audit-prod-path | 复制 `data/` → `AUDIT_PROD_ROOT`；`uv run pytest tests/test_layer1_ingestion_gates.py tests/test_layer1_observation_ingestion.py -q`；prod DB hash 不变 | audit-prod-path | copy only | 与 Execute 声称一致       | §4.5   |
| A6  | cli-sandbox     | micro-fetch 单指标 `ENV-E1-DGS10`；`ResourceGuard` eco；测 elapsed + RSS                                                                                | audit-sandbox   | tmp       | elapsed ≤ 5s；RSS ≤ 512MB | §4.6   |
| A6  | audit-prod-path | 同上在 `AUDIT_PROD_ROOT` 数据副本上复跑                                                                                                                 | audit-prod-path | copy      | prod 树未修改             | §4.6   |
| A7  | cli-sandbox     | `init_db` 二次应用 migration 011 策略；DB hash 前后对比                                                                                                 | audit-sandbox   | copy DB   | 无 prod 污染              | §4.7   |
| A7  | audit-prod-path | 项目 `data/duckdb/` hash 审计前后不变                                                                                                                   | audit-prod-path | read-only | 无污染                    | §4.7   |
| A8  | pytest-isolated | 补边界：validation fail、severe conflict、manual review、Phase 0 gate                                                                                   | audit-sandbox   | tmp       | 新测绿或 §5 修复项        | §4.8   |
| A8  | audit-prod-path | 复跑 018A Phase 0 命令块 + ingestion 全量                                                                                                               | audit-prod-path | copy      | 全绿                      | §4.8   |

## 3. 阶段审计产出与检查单（PH-A0–PH-A5）

| 阶段       | 产出文件                              | 018A §10 检查项                                                                 |
| ---------- | ------------------------------------- | ------------------------------------------------------------------------------- |
| §3.0 PH-A0 | `research/audit-ph-a0-phase0-gate.md` | 契约/DB gate；forbidden import；schema 偏差分类                                 |
| §3.1 PH-A1 | `research/audit-ph-a1-inventory.md`   | inspect 字段；零 mutation；copy provenance                                      |
| §3.2 PH-A2 | `research/audit-ph-a2-route.md`       | route 字段/状态；无 mutation；disabled 源行为                                   |
| §3.3 PH-A3 | `research/audit-ph-a3-staging.md`     | fetch_log；file_registry；ResourceGuard；无 clean write                         |
| §3.4 PH-A4 | `research/audit-ph-a4-clean-write.md` | validation_report；conflict severity；WriteManager；lineage；post-inspect delta |
| §3.5 PH-A5 | `research/audit-ph-a5-final.md`       | 跨阶段回归；registry；handoff；§9 全表                                          |

## 4. 维度审计产出（A1–A8）

| 维度    | 产出文件                        |
| ------- | ------------------------------- |
| §4.1 A1 | `research/audit-a1-spec.md`     |
| §4.2 A2 | `research/audit-a2-ponytail.md` |
| §4.3 A3 | `research/audit-a3-security.md` |
| §4.4 A4 | `research/audit-a4-quality.md`  |
| §4.5 A5 | `research/audit-a5-trace.md`    |
| §4.6 A6 | `research/audit-a6-perf.md`     |
| §4.7 A7 | `research/audit-a7-ops.md`      |
| §4.8 A8 | `research/audit-a8-test-gap.md` |

## 5. Audit Source Trace

| Item ID                 | 原文                                                             | AC                    | 证据                          |
| ----------------------- | ---------------------------------------------------------------- | --------------------- | ----------------------------- |
| `R3-B2.5-L1-OBS-INGEST` | `018A` §3,§8–13                                                  | AC-TRACE-1, AC-P0..P4 | phase0–4 + final              |
| route/service           | `source_route_contract.yaml`, `datasource_service_contract.yaml` | AC-P2-\*, AC-P3-1     | route preview + service tests |
| write/validation        | `write_contract.yaml`, ADR-001, `validation_gate.py`             | AC-P4-1,2             | write_audit_log               |
| lineage                 | `snapshot_lineage_contract.yaml`                                 | AC-P4-4               | lineage rows                  |
| inspect                 | `ops_db_inspect_contract.yaml`                                   | AC-P1-\*, AC-P4-5     | inventory json/md             |
| Batch 2 gate            | archived audit A4-09                                             | AC-PRE, AC-P4-4       | handoff                       |
| registry                | `AUDIT_DEFERRED_REGISTRY.md`, `UNRESOLVED_ISSUES_REGISTRY.md`    | AC-REG-1              | `final_registry_update.md`    |

## 6. Audit DoD

- [ ] 7.pre `gitnexus-audit-summary.md`
- [ ] PH-A0–PH-A5 阶段签字（串行）
- [ ] A1–A8 维度完成（含 audit-prod-path 行）
- [ ] A9 汇总 PASS / PASS_WITH_FIXES / FAIL
