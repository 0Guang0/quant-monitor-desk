# R3X_data_source_routing_blockers — 数据源/路由 blocker 修复任务

## 1. 任务性质

本任务是最小修复任务，目标是解除真实数据 staged pilot 前的数据源、能力、路由、service facade blocker。

本任务不是生产数据源启用任务，不证明 production-live readiness，不允许把任何 disabled/validation-only source 提升为 production Primary。

## 2. 分支与工作方式

- 建议分支：`fix/round3-data-source-routing-blockers`
- 基准分支：用户指定的最新 `master` 或 `integration/round3`
- 目标合并：`integration/round3`
- 工作方式：先 RED tests，再做最小修复，再跑定向 gate

## 3. 背景与目的

最新对抗性审计指出，当前数据源层存在配置、契约和 runtime 路由之间的 drift，真实数据接入前必须先确保：

1. registry 声明的 domain 能被 route planner 解释。
2. capability 声明与 adapter/service contract 不冲突。
3. disabled source 不会被默认选中。
4. validation source 不会被静默提升为 Primary。
5. DataSourceService 不会静默覆盖用户请求来源而无审计信息。
6. route preview 能解释 source 选择、跳过、禁用、缺能力、需授权等状态。

## 4. 优先修复范围

必须优先核实并处理以下问题；如果某项已由其他分支修复，必须记录证据而不是重复修改。

### 4.1 HIGH / blocker

- FetchResult 状态集合约与实现不同步：实现中存在 `DISABLED_SOURCE` / `NOT_PUBLISHED_YET` 等状态但 contract 未列出。
- 已声明或具备 capability 的 data domains 缺少 `domain_roles`，导致 `SourceRoutePlanner` 无法正常 route。

### 4.2 MEDIUM / pilot blocker candidate

- `_default_operation()` 对 registry/capability 中的 domain 映射不完整。
- `platform_source_matrix.yaml` 与 registry/capability source 覆盖不一致。
- cninfo / yahoo / akshare / baostock adapter 支持域与 registry/capability 声明不一致。
- `DataSourceService.fetch()` 不得静默覆盖 `FetchRequest.source_id` 而无 audit/quality flag/route explanation。
- disabled source、auth-required source、env-required source 必须产生可解释 route status。

## 5. 必读索引文件

执行前必须读取并摘要以下文件。此清单是最低要求，不是上限；执行者必须根据 `ROUND3_BATCH_IMPLEMENTATION_MAP.md`、contract authority 字段、import graph、测试失败信息继续追溯相关文件。

### 5.1 协议与项目地图

- `AGENTS.md`
- `CLAUDE.md`
- `.trellis/workflow.md`
- `.trellis/spec/guides/complex-task-planning-protocol.md`
- `.trellis/spec/guides/round3-repair-debt-worktree-plan.md`
- `ROUND3_BATCH_IMPLEMENTATION_MAP.md`
- `docs/ROUND3_HANDOFF.md`
- `docs/AUDIT_DEFERRED_REGISTRY.md`
- `docs/UNRESOLVED_ISSUES_REGISTRY.md`

### 5.2 数据源设计与契约

- `docs/modules/data_sources.md` if present
- `docs/modules/source_route_plan.md`
- `docs/modules/data_validation_and_conflict.md`
- `docs/quality/production_live_pilot_policy.md`
- `docs/quality/staged_acceptance_policy.md`
- `specs/datasource_registry/source_registry.yaml`
- `specs/datasource_registry/source_capabilities.yaml`
- `specs/contracts/data_adapter_contract.md`
- `specs/contracts/datasource_service_contract.yaml`
- `specs/contracts/source_route_contract.yaml`
- `specs/contracts/platform_source_matrix.yaml`
- `specs/contracts/source_capability_contract.yaml`
- `specs/contracts/source_conflict_rules.yaml`
- `specs/contracts/runtime_versions.md`

### 5.3 实现与测试

- `backend/app/datasources/`
- `backend/app/datasources/adapters/`
- `backend/app/datasources/route_planner.py`
- `backend/app/datasources/service.py`
- `backend/app/datasources/source_registry.py`
- `backend/app/datasources/capability_registry.py`
- `backend/app/datasources/fetch_result.py`
- `backend/app/ops/interface_probe.py`
- `tests/test_source_capabilities.py`
- `tests/test_source_route_planner.py`
- `tests/test_datasource_service.py`
- `tests/test_data_adapter_contract.py`
- `tests/test_platform_source_matrix.py`
- `tests/test_interface_probe_018c.py`
- `tests/test_production_live_pilot_policy.py`

### 5.4 最新审计材料

如果存在，必须读取：

- `docs/quality/adversarial_audit_report.md`
- 相关 `.trellis/tasks/**/execute-evidence/*source*`
- 相关 `.trellis/tasks/**/execute-evidence/*route*`

### 5.5 当前批次完成物与审计检查

用户已确认当前批次四个分支已经完成。执行者必须纳入这些完成物中与数据源、路由、source role、staged-only、tdx_pytdx、snapshot lineage、evidence foundation 相关的检查结果。

必须追溯：

- `feature/round3-019-layer2-sensor`：是否新增 source/domain 依赖、是否误用 validation source、是否影响 snapshot lineage source fields。
- `feature/round3-023a-evidence-foundation`：source_fetch_ids / source_content_hashes / evidence identity 是否与 datasource contract 一致。
- `review/round3-019-plan-audit`：关于 019 source misuse、live/FRED、production-readiness claim 的 PASS/BLOCK/WARN。
- `debt/r3b275-018c-live-manual-probe-plan`：tdx_pytdx authorization、route preview、disabled validation-only、no-live-fetch 相关结论。
- integration/coordinator artifacts：若存在 merge report、post-merge gate 或当前批次审计报告，必须读取；若不可见，记录 `MISSING_CURRENT_BATCH_EVIDENCE`。

## 6. 允许修改范围

只在计划明确后修改最小必要文件。候选范围：

- `specs/contracts/data_adapter_contract.md`
- `specs/datasource_registry/source_registry.yaml`
- `specs/datasource_registry/source_capabilities.yaml`
- `specs/contracts/platform_source_matrix.yaml`
- `specs/contracts/source_route_contract.yaml` only if contract gap is proven
- `backend/app/datasources/`
- `backend/app/datasources/adapters/`
- `tests/test_source_capabilities.py`
- `tests/test_source_route_planner.py`
- `tests/test_datasource_service.py`
- `tests/test_data_adapter_contract.py`
- `tests/test_platform_source_matrix.py`
- task-local Trellis plan/evidence files

## 7. 禁止事项

禁止：

- 将 `tdx_pytdx` 设为 Primary
- 将 `tdx_pytdx` 设为 enabled-by-default
- 将 QMT / xqshare / Yahoo 设为默认启用
- 把 validation source 静默当 Primary 用
- 新增 silent fallback
- 关闭 Eastmoney hist Request 2
- 声称 production-live readiness
- 做 live network fetch
- 写 production DB
- 引入大型新依赖
- 借修 route 扩大实现到 real-data pilot

## 8. 修复规则

1. 先写或补 RED tests，证明当前 drift。
2. 每个 registry domain 必须明确：primary、validation、fallback_policy、enabled state、requires_source_enabled、disabled behavior。
3. 每个 route failure 必须输出可解释状态：`DISABLED_SOURCE`、`NO_AVAILABLE_SOURCE`、`CAPABILITY_MISSING`、`USER_AUTH_REQUIRED`、`RESOURCE_GUARD_PAUSED` 等。
4. `selected_source_id` 只能在 `route_status=READY` 时非空。
5. `DataSourceService` 必须先 route，再 adapter construction。
6. source override 行为必须显式记录，不得静默改写请求意图。
7. contract 与 implementation 状态枚举必须同步。
8. 对暂不能实现的 source/domain，要明确 disabled/deferred，不得让配置表现为可用但 runtime 不可用。

## 9. 验证命令

最低命令：

```bash
pytest tests/test_source_capabilities.py -q
pytest tests/test_source_route_planner.py -q
pytest tests/test_datasource_service.py -q
pytest tests/test_data_adapter_contract.py -q
pytest tests/test_platform_source_matrix.py -q
pytest tests/test_production_live_pilot_policy.py -q
```

若改动 018C / interface probe 相关路径，再运行：

```bash
pytest tests/test_interface_probe_018c.py -q
```

若改动 docs/specs 链接，运行：

```bash
python scripts/check_doc_links.py
```

## 10. 完成标准

- 所有 declared domain 要么可 route preview，要么有明确 disabled/deferred reason
- FetchResult 状态集合约与实现同步
- disabled source 不会被默认 selected
- validation source 不会被静默提升 Primary
- DataSourceService 仍是 production fetch facade
- 没有 production-live readiness claim
- 合并报告列出改动文件、测试结果、剩余 deferred source/domain
