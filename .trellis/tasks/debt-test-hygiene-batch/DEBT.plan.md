# Repair/Debt Lite Plan — 测试卫生临时批次（test-hygiene-batch）

> **状态：** 草案，待用户核对后派发  
> **task_track：** `debt-lite`  
> **Source of truth：** 用户确认的临时批次意图（注释对齐 → ponytail 重构 → 性能优化 → 清理候选）  
> **base branch：** `master`（派发前由主会话 `git fetch` 并确认 HEAD 与远程一致）

---

## 1. 目标与阶段（3+1）

| 阶段 | 代号                  | 内容                                                                    | 并行                |
| ---- | --------------------- | ----------------------------------------------------------------------- | ------------------- |
| A    | `align-ponytail`      | 注释-代码对齐 + `/ponytail full` 重构（**不改任何测试注释**）           | 9 桶 agent 并行     |
| B    | `perf`                | 仅对 baseline profile 筛出的慢测做性能优化（**测试价值不变**；见 §1.1） | 按桶二次派发        |
| C    | `deletion-candidates` | 各桶产出删除**候选** YAML，**不删文件**                                 | 9 桶 + MERGE-C 汇总 |
| D    | `deletion-exec`       | 用户批准后单 agent 执行删除 + catalog/registry 收口                     | 用户 gate 后        |

**硬约束（全阶段）：**

- 禁止修改：模块/用例 docstring 及行内 `#` 注释中描述测试意图的文本
- 禁止修改：`backend/` 及一切非本桶 allowed 的正式实现代码
- 禁止：`git commit` / `git push`（agent 只改工作区；合并与提交由 MERGE-C / 主会话执行）
- 注释与 `tests/test_catalog.yaml` / 契约文档矛盾时：**改代码以符合注释**，并在 `{bucket}-comment-conflicts.md` 上报，不得 silent 改注释
- **测试价值守恒（全阶段，Phase B 最严）：** 禁止为性能或简洁而删除、弱化、或「等价替换」测试；见 §1.1

### §1.1 测试价值守恒（硬门禁）

**原则：** 任何阶段的改动不得降低测试原本要守卫的价值。性能与 ponytail 简洁化只能在**不改变测试价值**的前提下进行。

**全阶段禁止（含 Phase A ponytail 与 Phase B perf）：**

| 禁止行为                                                                   | 示例                                                       |
| -------------------------------------------------------------------------- | ---------------------------------------------------------- |
| 为提速**删除**用例或**合并**导致覆盖变弱                                   | 删掉 `@pytest.mark.network` 用例「因为 CI 慢」             |
| 为提速**简化**断言或验证路径                                               | 从 HTTP 响应体校验退化为「只 assert 200」                  |
| 用 mock/stub/fake **替代注释要求的真实环境**                               | 注释写「真实网络 fetch」却改成 `monkeypatch` 返回固定 JSON |
| 用「等价」逻辑**偷换**被测路径                                             | 注释测 subprocess CLI 却改成直接 import 内部函数           |
| 为复用 fixture **缩小**注释声明的边界条件                                  | 删掉 multi-trade-date / fail-closed 分支只留 happy path    |
| Phase B 以「语义不变」为由**减少** `@pytest.mark.network` 等标记的实际执行 | 默认 skip 本可 `--run-network` 跑的 live 用例              |

**注释/标记优先推断测试价值：**

- 模块或用例 docstring 写明「真实网络 / live fetch / vendor E2E / subprocess / 生产等价」→ **必须保留该真实路径**，Phase B 仅允许优化 setup/teardown、共享只读资源、减少与被测路径无关的重复 IO。
- `@pytest.mark.network` 及 `conftest` 中 `--run-network` 门控 **不得**为性能而删除或改为永久 skip；默认 CI 跳过 live 网络是既有策略，不是本批次「优化掉网络」的许可。
- 注释要求 DB 迁移、真实 DuckDB、WriteManager 写路径等 → 不得用纯 unit mock 替代，除非注释本身允许 mock。

**允许的性能优化（价值不变）：**

- 提升 fixture `scope`（session/module）共享**只读**或**隔离良好**的 DB/目录
- 合并**与被测路径无关**的重复 `read_text()` / 全 repo 扫描（gate 测试读 docs 仍须覆盖注释所列文件）
- 同一文件内去重复 import/setup，不减少 assert 条数或 match 严格度
- 平移耗时的非被测准备步骤（如一次性 migration）到更广 scope 的 fixture

**Phase B 额外产出（必交）：** `bucket-{ID}-perf-value-checklist.md` — 每个被优化用例一行，声明「原测试价值」与「优化后仍保留的同一价值」，MERGE-C 逐条对照 diff 审查；任一行无法证明价值守恒 → 该优化不得 merge。

---

## 2. 分桶表（Phase A 所有权）

| 桶 ID       | 分支名                                  | Owner                | 文件数 | Allowed test modules |
| ----------- | --------------------------------------- | -------------------- | ------ | -------------------- |
| **G**       | `debt/test-hygiene/bucket-g-gate`       | agent-G              | 13     | 见 §2.1              |
| **L1**      | `debt/test-hygiene/bucket-l1-layer1`    | agent-L1             | 6      | 见 §2.2              |
| **L23**     | `debt/test-hygiene/bucket-l23-layers`   | agent-L23            | 6      | 见 §2.3              |
| **DS**      | `debt/test-hygiene/bucket-ds-sync`      | agent-DS             | 15     | 见 §2.4              |
| **VAL**     | `debt/test-hygiene/bucket-val-storage`  | agent-VAL            | 11     | 见 §2.5              |
| **OPS**     | `debt/test-hygiene/bucket-ops-cli`      | agent-OPS            | 9      | 见 §2.6              |
| **LOOP**    | `debt/test-hygiene/bucket-loop-trellis` | agent-LOOP           | 9      | 见 §2.7              |
| **AUD**     | `debt/test-hygiene/bucket-audit-r3x`    | agent-AUD            | 5      | 见 §2.8              |
| **SMK**     | `debt/test-hygiene/bucket-smk-smoke`    | agent-SMK            | 1      | 见 §2.9              |
| **MERGE-C** | `debt/test-hygiene/merge-coordinator`   | 主会话 / merge agent | —      | 见 §5                |

**共享/support 文件（默认禁止各桶直接改）：**

| 路径                                 | 写权限                                                      |
| ------------------------------------ | ----------------------------------------------------------- |
| `tests/conftest.py`                  | 仅 MERGE-C（各桶需在 `{bucket}-conftest-requests.md` 提案） |
| `tests/db_helpers.py`                | MERGE-C 或 VAL 桶（需 MERGE-C 锁）                          |
| `tests/contract_gate_support.py`     | 仅 G 桶只读；改动的 PR 必须 MERGE-C review                  |
| `tests/service_path_support.py`      | 仅 DS 桶，MERGE-C 锁                                        |
| `tests/fixtures/**`                  | 所属桶只读；新增 fixture 文件须 MERGE-C 批准                |
| `tests/test_catalog.yaml`            | **仅 MERGE-C**（Phase D 或 catalog purpose 对齐时）         |
| `specs/context/authority_graph.yaml` | **仅 MERGE-C**                                              |
| `docs/ops/verification_commands.md`  | **禁止本批次修改**                                          |

### §2.1 桶 G — Gate / Policy / Round3

```
tests/test_batch3_staged_downstream_gate.py
tests/test_batch25_production_data_gate.py
tests/test_batch275_live_pilot_gate.py
tests/test_production_live_pilot_policy.py
tests/test_fred_staged_semantics.py
tests/test_round3_audit_registry_alignment.py
tests/test_round3_verification_command_matrix.py
tests/test_trellis_audit_trace_authority.py
tests/test_unresolved_item_task_coverage.py
tests/test_global_execution_rules.py
tests/test_staged_pilot.py
tests/test_production_gate.py
tests/test_manifest_protocol.py
```

### §2.2 桶 L1 — Layer1 Ingestion

```
tests/test_layer1_axis_loader.py
tests/test_layer1_interpretation.py
tests/test_layer1_ingestion_gates.py
tests/test_layer1_observation_ingestion.py
tests/test_observation_mapper.py
tests/test_ingestion_validation_migration.py
```

### §2.3 桶 L23 — Layer2 / Layer3 / Lineage

```
tests/test_layer2_sensor_loader.py
tests/test_layer3_loader.py
tests/test_layer3_snapshot_builder.py
tests/test_snapshot_lineage_kernel.py
tests/test_layer5_evidence_foundation.py
tests/test_resource_guard.py
```

### §2.4 桶 DS — DataSource / Adapter / Sync / E2E

```
tests/test_datasource_service.py
tests/test_source_registry.py
tests/test_source_route_planner.py
tests/test_source_capabilities.py
tests/test_platform_source_matrix.py
tests/test_r3x_data_source_routing_blockers.py
tests/test_data_adapter_contract.py
tests/test_adapter_skeletons.py
tests/test_sync_orchestrator.py
tests/test_sync_jobs.py
tests/test_sync_pipeline_contract.py
tests/test_sync_migration.py
tests/test_batch_d_orchestration_flow.py
tests/test_vendor_fetch_e2e.py
tests/test_tdx_live_manual_probe_authorization.py
```

### §2.5 桶 VAL — Validation / Storage / Schema

```
tests/test_write_manager.py
tests/test_db_validation_gate.py
tests/test_data_quality_validator.py
tests/test_source_conflict_validator.py
tests/test_batch_c_validation_flow.py
tests/test_raw_store.py
tests/test_duckdb_connection.py
tests/test_schema_migration.py
tests/test_schema_contract.py
tests/test_sql_identifiers.py
tests/test_path_compat.py
```

### §2.6 桶 OPS — Ops / CLI / Config / Security

```
tests/test_ops_db_inspector.py
tests/test_ops_interface_probe.py
tests/test_interface_probe_018c.py
tests/test_data_cli_contract.py
tests/test_config.py
tests/test_config_templates.py
tests/test_dependency_extras_contract.py
tests/test_api_security_contract.py
tests/test_reference_adoption_guardrails.py
```

### §2.7 桶 LOOP — Loop Engineering / Trellis / Docs / Scaffold

```
tests/test_loop_engineering_flow.py
tests/test_docs_specs_indexed.py
tests/test_documentation_index.py
tests/test_trellis_validate_plan.py
tests/test_trellis_validate_execute.py
tests/test_docstring_quadruple_coverage.py
tests/test_module_boundaries.py
tests/test_project_scaffold.py
tests/test_backend_smoke.py
```

### §2.8 桶 AUD — Audit / R3X Remediation

```
tests/test_audit_fixes.py
tests/test_audit_remediation.py
tests/test_r3x_ponytail_pilot_prep_bucket_a.py
tests/test_r3x_ponytail_structural_bucket_b.py
tests/test_r3x_residual_open_items_closure.py
```

### §2.9 桶 SMK — Smoke

```
tests/smoke/test_foundation_smoke.py
```

**合计：** 75 个测试模块（74 × `test_*.py` + 1 smoke）

---

## 3. 禁止删清单（Phase C/D 硬门禁）

以下路径 **任何阶段不得删除或 rename**；Phase C 不得列入 `deletion_candidates.yaml`：

### 3.1 Round 3 CI Gate（`scripts/check_test_catalog.py` ROUND3_GATE_MODULES）

```
tests/test_trellis_audit_trace_authority.py
tests/test_round3_audit_registry_alignment.py
tests/test_unresolved_item_task_coverage.py
tests/test_batch25_production_data_gate.py
tests/test_production_live_pilot_policy.py
tests/test_batch3_staged_downstream_gate.py
tests/test_fred_staged_semantics.py
```

### 3.2 验证命令矩阵（`docs/ops/verification_commands.md`）

```
tests/test_round3_verification_command_matrix.py
tests/test_batch275_live_pilot_gate.py   # 含 @pytest.mark.network；默认 -m "not network"
```

### 3.3 `specs/context/authority_graph.yaml` 登记的全部 tests（46 条引用，去重 35 模块）

```
tests/test_layer1_axis_loader.py
tests/test_layer1_interpretation.py
tests/test_layer1_ingestion_gates.py
tests/test_layer1_observation_ingestion.py
tests/test_observation_mapper.py
tests/test_batch25_production_data_gate.py
tests/test_batch275_live_pilot_gate.py
tests/test_production_live_pilot_policy.py
tests/test_fred_staged_semantics.py
tests/test_layer2_sensor_loader.py
tests/test_snapshot_lineage_kernel.py
tests/test_batch3_staged_downstream_gate.py
tests/test_resource_guard.py
tests/test_layer5_evidence_foundation.py
tests/test_trellis_audit_trace_authority.py
tests/test_datasource_service.py
tests/test_source_registry.py
tests/test_source_route_planner.py
tests/test_source_capabilities.py
tests/test_platform_source_matrix.py
tests/test_r3x_data_source_routing_blockers.py
tests/test_write_manager.py
tests/test_db_validation_gate.py
tests/test_data_quality_validator.py
tests/test_source_conflict_validator.py
tests/test_batch_c_validation_flow.py
tests/test_staged_pilot.py
tests/test_ops_db_inspector.py
tests/test_ops_interface_probe.py
tests/test_interface_probe_018c.py
tests/test_production_gate.py
tests/test_round3_verification_command_matrix.py
tests/test_round3_audit_registry_alignment.py
tests/test_unresolved_item_task_coverage.py
tests/test_schema_migration.py
tests/test_schema_contract.py
tests/test_sync_migration.py
tests/test_sync_orchestrator.py
tests/test_sync_jobs.py
tests/test_sync_pipeline_contract.py
tests/test_path_compat.py
tests/test_raw_store.py
tests/test_duckdb_connection.py
```

### 3.4 Loop / CI 基础设施测试

```
tests/test_loop_engineering_flow.py
tests/test_docs_specs_indexed.py
tests/test_documentation_index.py
tests/test_trellis_validate_plan.py
tests/test_trellis_validate_execute.py
tests/smoke/test_foundation_smoke.py
tests/test_backend_smoke.py
tests/test_project_scaffold.py
```

### 3.5 删除候选额外条件（全部满足才可 **提议** 删除，仍须用户 Phase D 批准）

1. `tests/test_catalog.yaml` 中 `type: protocol` 且 `verifies.docs/specs/rules` 均为空
2. 不被 §3.1–§3.4 任何列表引用
3. 不被 `scripts/check_test_catalog.py` CURATED 块引用
4. agent 在候选条目中附：`reason`、`last_known_purpose`、`replacement_coverage`（哪条测试已覆盖同等断言）
5. **禁止**以「运行慢 / 占资源 / CI 耗时」为 `reason` 提议删除（性能问题走 Phase B + §1.1，不得靠删测解决）

---

## 4. 验证命令

### 4.1 批次 Baseline（派发前，MERGE-C / 主会话执行一次）

```powershell
cd C:\Users\Guang\Desktop\quant-monitor-desk
uv run python -m pytest tests/ -q --tb=no 2>&1 | Tee-Object .trellis/tasks/debt-test-hygiene-batch/execute-evidence/baseline-full-pytest.txt
uv run python -m pytest tests/ -q --durations=30 2>&1 | Tee-Object .trellis/tasks/debt-test-hygiene-batch/execute-evidence/baseline-durations.txt
uv run python scripts/check_test_catalog.py 2>&1 | Tee-Object .trellis/tasks/debt-test-hygiene-batch/execute-evidence/baseline-test-catalog.txt
uv run python scripts/loop_maintain.py 2>&1 | Tee-Object .trellis/tasks/debt-test-hygiene-batch/execute-evidence/baseline-loop-maintain.txt
```

### 4.2 每桶 Phase A 完成（各 agent 必跑）

将 `{BUCKET}` 替换为 G|L1|L23|DS|VAL|OPS|LOOP|AUD|SMK；`{paths}` 为本桶全部模块：

```powershell
uv run python -m pytest {paths} -q --tb=short
```

示例（桶 L1）：

```powershell
uv run python -m pytest tests/test_layer1_axis_loader.py tests/test_layer1_interpretation.py tests/test_layer1_ingestion_gates.py tests/test_layer1_observation_ingestion.py tests/test_observation_mapper.py tests/test_ingestion_validation_migration.py -q --tb=short
```

### 4.3 每桶 Phase B 性能（仅 profile 命中模块）

**前置：** 已提交 `bucket-{ID}-perf-value-checklist.md`（§1.1）；MERGE-C 批准后方可改代码。

```powershell
uv run python -m pytest {slow_module} -q --durations=0
# 优化后对比 baseline-durations.txt 中同模块耗时
```

**Phase B 禁止项（与 §1.1 一致）：** 不得删除用例、不得弱化 assert、不得用 mock 替代注释要求的真实网络/DB/CLI 路径。

**含 `@pytest.mark.network` 的模块：** 优化后须额外跑（若环境允许）：

```powershell
uv run python -m pytest {slow_module} -q --run-network
```

若本机无法跑 live 网络，在 `perf-value-checklist.md` 注明 `network: not-run-locally`，且 diff 不得包含任何 mock 掉网络调用或删除 network 用例的改动。

### 4.4 Merge Gate（每桶合并进 integration 分支前，MERGE-C）

```powershell
uv run python -m pytest tests/ -q --tb=no
uv run python scripts/check_test_catalog.py
uv run python scripts/loop_maintain.py
uv run python scripts/check_docs_specs_indexed.py
uv run python scripts/generate_project_map.py --check
```

### 4.5 Phase D 删除执行后（额外）

```powershell
uv run python scripts/loop_maintain.py --fix
uv run python -m pytest tests/ -q
uv run python scripts/check_test_catalog.py
```

---

## 5. 证据目录结构

```
.trellis/tasks/debt-test-hygiene-batch/
├── DEBT.plan.md                          # 本文件
├── task.json                             # 派发前由主会话创建（meta.task_track=debt-lite）
├── research/
│   ├── agent-prompts/                    # 各桶派发 prompt（按桶单文件）
│   │   ├── bucket-G-gate.md
│   │   ├── bucket-L1-layer1.md
│   │   ├── …
│   │   └── MERGE-C-coordinator.md
│   └── deletion_candidates/              # Phase C 汇总（禁止在此阶段删文件）
│       ├── bucket-G-candidates.yaml
│       ├── …
│       └── MERGED-deletion_candidates.yaml
└── execute-evidence/
    ├── baseline-full-pytest.txt
    ├── baseline-durations.txt
    ├── baseline-test-catalog.txt
    ├── baseline-loop-maintain.txt
    ├── bucket-{ID}-align-checklist.md    # Phase A：每用例五问
    ├── bucket-{ID}-pytest-green.txt      # Phase A：桶内 pytest 输出
    ├── bucket-{ID}-comment-conflicts.md  # 注释 vs catalog/契约 矛盾上报
    ├── bucket-{ID}-conftest-requests.md  # 需改 conftest 时的提案（可选）
    ├── bucket-{ID}-perf-notes.md         # Phase B：优化前后耗时
    ├── bucket-{ID}-perf-value-checklist.md  # Phase B 必交：测试价值守恒逐用例声明
    ├── bucket-{ID}-deletion-candidates.yaml
    └── merge_gate_report.md              # MERGE-C 最终合并报告
```

### Phase A 对齐 checklist 模板（写入 `bucket-{ID}-align-checklist.md`）

每个 `test_*` 函数一行：

| 用例       | 被测对象一致 | 验证点覆盖 | 失败含义一致 | 无注释外行为 | ponytail 已复用现有 helper |
| ---------- | ------------ | ---------- | ------------ | ------------ | -------------------------- |
| `test_foo` | Y/N          | Y/N        | Y/N          | Y/N          | Y/N                        |

---

## 6. Vertical slices 与 AC

| Slice             | Phase | Owner          | AC                                                                         | Verification                       |
| ----------------- | ----- | -------------- | -------------------------------------------------------------------------- | ---------------------------------- |
| TH-A-G … TH-A-SMK | A     | 各桶 agent     | 桶内全部用例 checklist 全 Y；pytest 绿；无注释 diff                        | §4.2                               |
| TH-B-\*           | B     | 原桶 agent     | 耗时或内存改善可证明；**测试价值 checklist 全行通过**；无 §1.1 禁止项 diff | §4.3 + perf-value-checklist + §4.4 |
| TH-C-\*           | C     | 各桶 + MERGE-C | 产出 candidates YAML；无 §3 禁止删项                                       | 人工 review                        |
| TH-D              | D     | 单 agent       | 用户批准后删除；catalog/graph 同步；全绿                                   | §4.5                               |

---

## 7. Merge 顺序与协调

1. 创建 integration 分支：`debt/test-hygiene/integration`（from `master`）
2. 按顺序 merge 桶分支（减少 conftest 冲突）：**SMK → LOOP → AUD → OPS → VAL → L1 → L23 → DS → G**
3. 每桶 merge 后跑 §4.4；失败则在该桶分支修复，不得跨桶改文件
4. Phase B 在 integration 绿后再开第二轮 worktree
5. Phase C 候选汇总后 **停止**，等待用户书面批准 Phase D

---

## 8. Explicit non-goals

- 不修改测试注释文本
- 不修改 `backend/` 生产代码
- 不新增 pytest 插件或依赖
- 不在 Phase C 直接删除任何测试文件
- 不为性能删除、简化测试，或以 mock/等价路径牺牲注释要求的真实环境（§1.1）
- 不 force-push `master`

---

## 9. 用户 Gate

- [ ] 分桶表与文件归属无误
- [ ] 禁止删清单覆盖所有 CI gate
- [ ] 验证命令与证据路径可接受
- [ ] **测试价值守恒（§1.1）** — 禁止为性能删测/弱测/mock 偷换真实环境
- [ ] 批准派发 Phase A（9 并行 agent + MERGE-C baseline）

**用户确认后**，主会话按 `research/agent-prompts/` 展开派发；本响应不自动启动 agent。
