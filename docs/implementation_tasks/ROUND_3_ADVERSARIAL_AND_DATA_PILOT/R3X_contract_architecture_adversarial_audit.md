# R3X_contract_architecture_adversarial_audit — Round 3 全项目设计/契约/架构对抗性审计

## 1. 任务性质

本任务是只读 review / audit 任务，不是实现任务。

目标是在最新项目进度下，逐文件对照项目设计文档、契约、架构、规则、定义、业务功能与当前实现，深挖：

- implementation deviation：实现与设计/契约不一致
- runtime gap：文件存在但未接入运行路径
- vulnerability：可导致数据污染、越权写入、路径逃逸、静默降级、安全风险的问题
- architectural drift：模块边界、调用路径、职责归属偏离架构
- data/source/db risk：数据源、路由、DB schema、写入、校验、审计链路风险
- completion quality：完成质量不足、测试空洞、文档过时、死代码、伪实现

本任务必须基于最新主线或 integration 分支实际内容，不得只基于旧记忆或单个交接文件判断。

## 2. 分支与工作方式

- 建议分支：`review/round3-contract-architecture-adversarial-audit`
- 基准分支：用户指定的最新 `master` 或 `integration/round3`
- 工作方式：只读审计；允许新增任务本地 review report / findings report，但不得修改实现代码、契约、配置或 DB
- 合并方式：若用户确认归档，可通过 `integration/round3` 合入；默认不直接合入 master

## 3. 任务目标

完成后必须回答：

1. 目前项目完成质量如何？
2. 哪些设计文档/契约/架构/规则/业务定义已有实现？
3. 哪些实现只是 skeleton / stub / surface-level compliance？
4. 哪些文件之间存在 contract drift？
5. 哪些 runtime path 绕过了设计规定的 guard / validator / WriteManager / ResourceGuard？
6. 哪些问题阻塞真实数据 staged pilot？
7. 哪些问题阻塞 production-live readiness？
8. 哪些问题可以 deferred，但必须进入 registry？
9. 是否存在重复登记、误报或已在 `docs/UNRESOLVED_ISSUES_REGISTRY.md` 覆盖的问题？

## 4. 必读索引文件

执行前必须读取并摘要以下文件。此清单是最低要求，不是上限；执行者还必须根据项目地图、引用链、import/call graph、任务卡、契约中的 authority 字段继续追溯相关文件。

### 4.1 项目协议与总入口

- `AGENTS.md`
- `CLAUDE.md`
- `.trellis/workflow.md`
- `.trellis/spec/guides/complex-task-planning-protocol.md`
- `.trellis/spec/guides/round3-repair-debt-worktree-plan.md`
- `ROUND3_BATCH_IMPLEMENTATION_MAP.md`
- `docs/ROUND3_HANDOFF.md`
- `docs/INDEX.md`
- `docs/START_HERE.md`
- `docs/AUDIT_DEFERRED_REGISTRY.md`
- `docs/UNRESOLVED_ISSUES_REGISTRY.md`
- `docs/RESOLVED_ISSUES_REGISTRY.md`

### 4.2 架构与模块设计

- `docs/architecture/`
- `docs/modules/`
- `docs/quality/`
- `docs/ops/`
- `docs/schema/`
- `docs/api/`
- `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md`
- `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`
- `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md`

### 4.3 机器契约与 registry

- `specs/contracts/`
- `specs/datasource_registry/source_registry.yaml`
- `specs/datasource_registry/source_capabilities.yaml`
- `specs/contracts/source_route_contract.yaml`
- `specs/contracts/datasource_service_contract.yaml`
- `specs/contracts/write_contract.yaml`
- `specs/contracts/data_quality_rules.yaml`
- `specs/contracts/source_conflict_rules.yaml`
- `specs/contracts/snapshot_lineage_contract.yaml`
- `specs/contracts/runtime_versions.md`
- `specs/contracts/module_boundary_contract.yaml`

### 4.4 实现与测试入口

- `backend/app/`
- `scripts/`
- `tests/`
- `configs/`
- `frontend/` only for shell/frontend contract drift
- `migrations/` or schema migration directory if present

### 4.5 最新审计材料

如果存在，必须读取并核实：

- `docs/quality/adversarial_audit_report.md`
- 最近一批 `.trellis/tasks/**/execute-evidence/merge_gate_report.md`
- 最近一批 `.trellis/tasks/**/execute-evidence/*validation*`

### 4.6 当前批次完成物与审计检查

用户已确认当前批次四个分支已经完成。执行者必须把这些分支的完成物、审计检查与 evidence 纳入本轮判断；如果某项在当前 base 不可见，必须记录为 `MISSING_CURRENT_BATCH_EVIDENCE`，不得假设已通过。

必须追溯：

- `feature/round3-019-layer2-sensor`：changed files、MASTER/AUDIT plan、Layer2 tests、snapshot lineage / no-future-data / double_count_guard evidence、merge report。
- `feature/round3-023a-evidence-foundation`：changed files、MASTER/AUDIT plan、Layer5 evidence foundation tests、Agent-text-not-fact-source / manual-review evidence、merge report。
- `review/round3-019-plan-audit`：review report、PASS/BLOCK/WARN 结论、blockers/warnings/suggestions、与 019 实现分支的对应修正情况。
- `debt/r3b275-018c-live-manual-probe-plan`：planning-only output、authorization checklist、no-live-fetch proof、tdx_pytdx disabled validation-only 状态保持证据。
- integration/coordinator artifacts：若存在 `integration/round3` merge report、conflict notes、post-merge gate、审计补充报告，必须读取。

## 5. 审计方法

每个 finding 必须按以下结构记录：

```yaml
id: ADV-R3X-<area>-<number>
severity: HIGH | MEDIUM | LOW
dimension: deviation | gap | vulnerability | risk | completion_quality | test_gap | doc_drift
status: NEW | DUPLICATE | ALREADY_DEFERRED | NEEDS_VERIFICATION
claim: one-line finding
expected: design/contract/rule expectation with file reference
actual: implementation behavior with file reference
impact: concrete risk
blocks_real_data_pilot: true|false
blocks_production_live: true|false
recommended_action: fix | defer | document | test | user_decision
suggested_branch: optional branch name
```

## 6. 强制审计维度

### 6.1 数据源与路由

- source registry 是否覆盖所有 declared domains
- source capabilities 是否与 adapters / service / route planner 一致
- disabled source 是否永远不会被默认选中
- validation source 是否不会被静默提升为 Primary
- `tdx_pytdx` 是否仍 disabled-by-default / validation-only
- QMT / xqshare 是否必须用户授权
- route preview 是否可解释跳过原因
- SourceRoutePlan 是否在 adapter construction 前生成
- DataSourceService 是否是唯一 production fetch facade

### 6.2 DB / Write / Validation / Conflict

- clean table write 是否只能通过 WriteManager
- validation gate 是否完整执行 `write_contract.yaml` 中拒绝条件
- schema hash / content hash / source_used / quality_flags 是否完整传播
- severe conflict 是否阻止 clean write
- audit log 是否在 rollback/exception 路径可追踪
- production DB 是否可通过 read-only inspect 验证 no-mutation
- migration docs 是否与实际 migration 一致

### 6.3 Layer 与业务语义

- Layer1 guardrails 是否进入 runtime commit path
- 禁止交易动作语义是否被拒绝而不是静默改写
- Layer2 / Layer3 / Layer4 / Layer5 是否越界提前实现
- snapshot lineage 是否满足 no-future-data / hashes / upstream IDs
- Agent prose 是否不会成为 fact source
- double count guard 是否真实覆盖，不只是字段存在

### 6.4 Ops / CLI / Security / Frontend shell

- ops tools 是否 read-only by default
- 是否存在 free SQL / unsafe flag / secret leak / raw row dump
- config secret policy 是否落实到 `.gitignore` 与 tests
- frontend shell 是否与 API route contract 明显 drift
- scripts 是否有测试覆盖并遵循 production gate role

## 7. 边界与禁止事项

禁止：

- 修改实现代码
- 修改契约或 docs 来“修复”审计发现
- 写 production DB
- 触发 migration
- 触发外部网络 fetch
- 启用 QMT / xqshare / tdx live
- 运行 full market / full history scan
- 直接 merge feature 分支
- 将未核实 finding 作为事实提交

允许：

- 读取文件
- 运行只读/定向测试
- 生成 task-local review report
- 对已有审计报告做交叉验证
- 标记误报、重复项、已 deferred 项

## 8. 验证命令建议

仅在不会写生产 DB、不会触发网络、不会扩大缓存污染的前提下运行：

```bash
pytest tests/test_source_capabilities.py -q
pytest tests/test_source_route_planner.py -q
pytest tests/test_datasource_service.py -q
pytest tests/test_db_validation_gate.py -q
pytest tests/test_write_manager.py -q
pytest tests/test_sync_orchestrator.py -q
pytest tests/test_ops_db_inspector.py -q
pytest tests/test_module_boundaries.py -q
pytest tests/test_round3_audit_registry_alignment.py -q
pytest tests/test_unresolved_item_task_coverage.py -q
```

若命令会写缓存或被环境阻塞，必须记录原因。

## 9. 完成标准

- 输出 PASS / WARN / BLOCK 总结
- 输出 HIGH / MEDIUM / LOW findings
- 标明哪些 findings 阻塞真实数据 staged pilot
- 标明哪些 findings 阻塞 production-live readiness
- 标明哪些 findings 只是 deferred / cleanup
- 每个 HIGH finding 必须有至少一处设计/契约引用与一处实现引用
- 明确下一批修复分支建议
