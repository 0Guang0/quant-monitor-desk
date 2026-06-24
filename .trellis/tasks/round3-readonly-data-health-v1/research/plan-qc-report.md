# Plan QC Report — C-20 read-only data health v1

> **Agent:** Plan 质检 Agent-2 · **model:** composer-2.5  
> **输入:** `MASTER.plan.md` · `implement.jsonl` · `vertical-slices.md`  
> **对照:** Playbook §3.6 · §8.1 · MAP §2.2 C-20 allowed/forbidden

---

## 1. 执行摘要

| 项 | 结果 |
| --- | --- |
| 初检发现项 | **7** |
| 已修复 | **7** |
| 复检遗留 | **0** |
| `validate-plan-freeze` | **exit 0**（复检后） |
| 可派发 Execute | **是**（`composer-2.5` only） |

---

## 2. 权威索引核对表（§3.1 + §3.2 零遗漏）

### 2.1 Playbook §3.1 共用底座（20 行）

| 路径 | MASTER | implement.jsonl | 摘要一句 | 遗漏风险 |
| ---- | ------ | --------------- | -------- | -------- |
| `WAVE_C_MAIN_SESSION_COORDINATOR_PLAYBOOK.md` | [x] | [x] L10 | Wave C 铁律、§8.1 PASS | 无 |
| `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §2.2–§2.6 | [x] | [x] L11 | C-20 allowed/forbidden | 无 |
| `.trellis/spec/guides/round3-repair-debt-worktree-plan.md` §6 | [x] | [x] L12 | 一分支一文件组 | 无 |
| `docs/AUDIT_DEFERRED_REGISTRY.md` | [x] | [x] L13 | defer 只读 | 无 |
| `docs/UNRESOLVED_ISSUES_REGISTRY.md` | [x] | [x] L14 | OPEN 对照 | 无 |
| `docs/RESOLVED_ISSUES_REGISTRY.md` | [x] | [x] L15 | 防重复打开 | 无 |
| `docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md` | [x] | [x] L16 | ID 映射 | 无 |
| `docs/ROUND3_HANDOFF.md` | [x] | [x] L17 | staged-only 入口 | 无 |
| `docs/quality/staged_acceptance_policy.md` | [x] | [x] L18 | 分层验收 | 无 |
| `docs/quality/production_live_pilot_policy.md` | [x] | [x] L19 | 不得 production-live | 无 |
| `docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md` | [x] | [x] L20 | Batch3 staged 门禁 | 无 |
| `docs/quality/ROUND3_TEST_DOCSTRING_HYGIENE_PLAN.md` | [x] | [x] L21 | 五字段 docstring | 无 |
| `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md` | [x] | [x] L22 | 实现边界 | 无 |
| `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md` | [x] | [x] L23 | 语义断言 | 无 |
| `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md` | [x] | [x] L24 | eco / ResourceGuard | 无 |
| `specs/contracts/runtime_versions.md` | [x] | [x] L25 | uv/pytest 权威 | 无 |
| `specs/contracts/write_contract.yaml` | [x] | [x] L26 | 零写路径 | 无 |
| `specs/contracts/resource_limits.yaml` | [x] | [x] L27 | scan cap | 无 |
| `specs/contracts/snapshot_lineage_contract.yaml` | [x] | [x] L28 | 快照血缘 | 无 |
| `docs/architecture/module_boundary_matrix.md` | [x] | [x] L29 | ops vs layer4 | 无 |
| `MIGRATION_MAP.md` | [x] | [x] L30 | ops 落点 | 无 |

### 2.2 Playbook §3.2 C-20 专属

| 路径 | MASTER | implement.jsonl | 摘要一句 | 遗漏风险 |
| ---- | ------ | --------------- | -------- | -------- |
| `PROMPT_20_feature_round3_readonly_data_health_v1.md` | [x] | [x] L8 | 九切片 + allowed | 无 |
| `R3Y_readonly_data_health_v1.md` | [x] | [x] L7 | AC / schema 权威 | 无 |
| `R3Y_execution_discipline_addendum.md` | [x] | [x] L9 | TDD/ponytail | 无 |
| `docs/ops/data_health_cli.md` | [x] | [x] L31 | CLI/报告设计 | 无 |
| `docs/ops/db_inspect_cli.md` | [x] | [x] L32 | db-inspect 分工 | 无 |
| `docs/ops/verification_commands.md` | [x] | [x] L33 | Round3 gate pytest | 无 |
| `docs/modules/data_validation_and_conflict.md` | [x] | [x] L34 | validator 语义 | 无 |
| `docs/modules/duckdb_and_parquet.md` | [x] | [x] L35 | 只读 DuckDB | 无 |
| `docs/modules/write_manager.md` | [x] | [x] L36 | 禁旁路写 clean | 无 |
| `docs/modules/data_sources.md` | [x] | [x] L37 | disabled source | 无 |
| `docs/modules/ops_and_performance.md` | [x] | [x] L38 | ops 边界 | 无 |
| `ROUND3_WAVE_B_PENDING_FIX_REGISTRY.md` §3 | [x] | [x] L39 | REQ2-EM DEFERRED | 无 |
| `specs/contracts/data_quality_rules.yaml` | [x] | [x] L40 | rule_id SSOT | 无 |
| `specs/contracts/source_conflict_rules.yaml` | [x] | [x] L41 | 冲突只读 | 无 |
| `specs/contracts/ops_db_inspect_contract.yaml` | [x] | [x] L42 | inspect 合约 | 无 |
| `specs/contracts/source_route_contract.yaml` | [x] | [x] L43 | validation_only | 无 |
| `specs/contracts/ops_health_check_contract.yaml` | [x] | [x] L44 | health envelope | 无 |
| `specs/datasource_registry/source_registry.yaml` | [x] | [x] L45 | source 启用 | 无 |
| `specs/datasource_registry/source_capabilities.yaml` | [x] | [x] L46 | capability | 无 |
| `archive/.../staged-pilot-v2/execute-evidence/` | [x] | [x] L47 | v2 evidence 优先 | 无 |
| `.trellis/tasks/feature-round3-real-data-staged-pilot/execute-evidence/` | [x] | [x] L48 | PROMPT_14 回退 | **已修**（原误用 archive 子路径） |
| `backend/app/ops/db_inspector.py` | [x] | [x] L57 | InspectReport | 无 |
| `backend/app/ops/staged_pilot.py` | [x] | [x] L58 | manifest 常量 | 无 |
| `backend/app/ops/mutation_proof.py` | [x] | [x] L59 | no-mutation | 无 |
| `backend/app/db/validation_gate.py` | [x] | [x] L60 | validation_report | 无 |
| `backend/app/validators/data_quality.py` | [x] | [x] L61 | DQ validator | 无 |
| `backend/app/validators/source_conflict.py` | [x] | [x] L62 | conflict | 无 |
| `tests/test_ops_db_inspector.py` | [x] | [x] L63 | 邻接回归 | 无 |
| `tests/test_staged_pilot.py` | [x] | [x] L64 | staged pilot | 无 |
| `tests/test_data_quality_validator.py` | [x] | [x] L65 | DQ 回归 | 无 |
| `tests/test_source_conflict_validator.py` | [x] | [x] L66 | 冲突回归 | 无 |
| `tests/test_db_validation_gate.py` | [x] | [x] L67 | gate 回归 | 无 |
| `tests/test_raw_store.py` | [x] | [x] L68 | raw store | 无 |

### 2.3 PROMPT §5 / R3Y §7 补索引（§3.6 任务卡缺口）

| 路径 | MASTER | implement.jsonl | 摘要一句 | 遗漏风险 |
| ---- | ------ | --------------- | -------- | -------- |
| `AGENTS.md` | [x] | [x] | Trellis 路由 | **已补** |
| `CLAUDE.md` | [x] | [x] | GitNexus 协议 | **已补** |
| `.trellis/workflow.md` | [x] | [x] | 阶段机 | **已补** |
| `complex-task-planning-protocol.md` | [x] | [x] | Plan freeze | **已补** |
| `backend/app/storage/raw_store.py` | [x] | [x] | staging 路径 | **已补** |
| `backend/app/datasources/source_registry.py` | [x] | [x] | source 启用 | **已补** |
| `fix-round3-post14-audit-staged-pilot/.../merge_gate_report.md` | [x] | [x] | post14 merge gate | **已补** |
| `tests/fixtures/data_health/` | [x] | [x] | 合成 fixture | **已补** |

### 2.4 authority_graph `ops` 1-hop（手工核对）

| 路径 | implement | 说明 |
| ---- | --------- | ---- |
| `datasource_service_contract.yaml` | [x] L71 | 邻接 |
| `api_security_contract.yaml` | [x] L72 | 邻接 |
| `ops_and_performance_v1_2.md` | [x] L73 | 邻接 |
| `source_capability_contract.yaml` | [x] L74 | 邻接 |
| `research/worktree-slices.md` | [x] L70 | Wave C 文件锁 |

---

## 3. Playbook §8.1 PASS → MASTER §2 子 AC

| §8.1 维度 | MASTER §2 | 验证链 | 状态 |
| --------- | --------- | ------ | ---- |
| Plan | AC-DH-PLAN | freeze + implement 覆盖 DH-01..09 | PASS |
| 实现 | AC-DH-IMPL | §8.8 只读 | PASS |
| 业务 AC | AC-DH-BIZ | §8.9 v2 evidence | PASS |
| 规则面 | AC-DH-RULES | §5.3b 13 rule_id | **已修** |
| 切片证据 | AC-DH-SLICE | §8.1–8.9 RED/GREEN | PASS |
| 测试 | AC-DH-TEST | 五字段 + ponytail | PASS |
| MAP 验证 | AC-DH-MAP | §10 Tier A | PASS |
| Audit | AC-DH-AUDIT | AUDIT.plan | PASS |
| 边界 | AC-DH-BOUND | §3.3 forbidden | PASS |
| 门禁陈述 | AC-DH-GATE | `sandbox_clean_write_gate_ready` + `gate_rationale` | **已补** |

---

## 4. R3Y-DH-01..09 独立可测性

| ID | §8 | RED 焦点 | 独立可测 |
| --- | --- | -------- | -------- |
| R3Y-DH-01 | 8.1 | model roundtrip | 是 |
| R3Y-DH-02 | 8.2 | loader missing manifest | 是 |
| R3Y-DH-03 | 8.3 | `-k dataHealthDailyBar`（4 rule） | 是 |
| R3Y-DH-04 | 8.4 | metadata empty title | 是 |
| R3Y-DH-05 | 8.5 | `-k dataHealthLineage`（6 rule） | 是 |
| R3Y-DH-06 | 8.6 | `-k dataHealthStaleness`（2 rule） | 是 |
| R3Y-DH-07 | 8.7 | JSON + text report | 是 |
| R3Y-DH-08 | 8.8 | CLI read-only exit 0 | 是 |
| R3Y-DH-09 | 8.9 | v2 evidence + gate 字段 | 是 |

九切片与 `vertical-slices.md` 一一对应；多 rule 切片用 `-k` 前缀聚合同步 RED/GREEN，不新增 §8 步。

---

## 5. 专项检查

### 5.1 staged-only / forbidden（MAP §2.2）

| 约束 | MASTER | 状态 |
| ---- | ------ | ---- |
| allowed: `data_health*.py`, `test_ops_data_health.py`, evidence | §1.3 / §3.1 | PASS |
| forbidden: layer4, staged_evidence, registry trio, prod write, fetch | §3.3 / §0 | PASS |
| REQ2-EM DEFERRED | §0 | PASS |
| 不得声称 production-live | §0 / AC-DH-BOUND | PASS |

### 5.2 测试真实行为 + tests/ ponytail

| 检查项 | 结论 |
| ------ | ---- |
| 语义断言（非 call-only） | §5.0 + GLOBAL_TESTING_POLICY 已索引；每 `test_*` 断言 `rule_id` / `overall_status` |
| 五字段 docstring | `test_ops_data_health.py` 全函数已含 |
| ponytail fixture | `tests/fixtures/data_health/` 已入 manifest；§5.3b 要求每 rule 一条最小坏行 |
| Plan stub RED | 全 `test_*` `pytest.fail` — Execute §8.0 基线可红 |

### 5.3 §2.2 / §2.3 铁律

| 项 | MASTER |
| --- | ------ |
| TDD RED→GREEN | §8.x |
| 测试 ponytail §2.2.2 | §0.3b / §5.0 |
| 五字段 §2.2.1 | §5.0 |
| `composer-2.5` only | §0 第 5 条 |

---

## 6. 发现项与修复清单

| # | 发现 | 严重度 | 修复 |
| --- | ---- | ------ | ---- |
| F1 | PROMPT_14 回退路径误为 `archive/.../feature-round3-real-data-staged-pilot`（不存在） | 高 | 改为 `.trellis/tasks/feature-round3-real-data-staged-pilot/execute-evidence/` |
| F2 | PROMPT §5 / R3Y §7 缺 AGENTS/CLAUDE/workflow/plan-protocol | 中 | 补 MASTER Source Index + implement.jsonl |
| F3 | 缺 `storage/`、`datasources/` 邻接（任务卡 §6.4） | 中 | 索引 `raw_store.py`、`source_registry.py` |
| F4 | 缺 post14 `merge_gate_report.md` | 低 | 补索引 |
| F5 | §5.3 仅 6/13 rule_id 有测试映射 | 高 | 新增 §5.3b 矩阵 + 10 个 `test_*` stub |
| F6 | §8.1「门禁陈述」未单列 AC；§6 缺 gate 字段 | 中 | AC-DH-GATE + `sandbox_clean_write_gate_ready` / `gate_rationale` |
| F7 | `tests/fixtures/data_health/` 未入 manifest | 低 | 补 implement.jsonl |

---

## 7. 复检结论

- §3.1 **21/21** 行已索引（含 MIGRATION_MAP）
- §3.2 **全部** playbook 行 + PROMPT §5 补项已索引
- §8.1 **10/10** PASS 行已在 MASTER §2 有子 AC
- R3Y-DH-01..09 **9/9** 可独立 RED/GREEN
- **遗留项：0**
- **`validate-plan-freeze`：exit 0**

**Execute 派发：** 可派发 Agent-3；模型 **`composer-2.5`**；禁 `composer-2.5-fast`。
