# R3X_real_data_staged_pilot — 真实数据源 staged pilot 任务

## 1. 任务性质

本任务是受控真实数据接入 pilot，不是 production-live 启用任务。

目标是在最小、安全、可回滚、可审计的边界内，使用真实数据源生成 raw / staging / sandbox evidence，并验证 route、fetch、validation、quality、conflict、no-mutation proof 能否在真实数据下暴露问题。

本任务必须保持 staged-only / sandbox-first，不得默认写 production clean table。

## 2. 分支与工作方式

- 建议分支：`feature/round3-real-data-staged-pilot`
- 基准分支：用户指定的最新 `master` 或 `integration/round3`
- 目标合并：`integration/round3`
- 工作方式：先 plan + safety checklist，再实现最小 pilot，再执行小样本验证

## 3. 任务目标

完成后必须回答：

1. 哪些默认允许的数据源能实际 fetch？
2. 哪些数据源因为 schema、网络、字段、权限、口径、频率或返回空数据失败？
3. route preview 是否能解释 source selected / skipped / disabled / capability missing？
4. fetch result 是否包含 source_used、status、row_count、schema/content hash、raw path 等必要 evidence？
5. raw / staging / sandbox evidence 是否可追溯且不污染 production DB？
6. validation report 能否生成，并且能暴露真实字段/质量问题？
7. conflict / source divergence 是否能被记录或明确 deferred？
8. no-mutation proof 是否证明 production clean tables 未被修改？
9. 下一步哪些 source/domain 可扩大样本，哪些必须 re-defer？

## 4. 数据源范围

### 4.1 第一批允许候选

仅允许无需本机授权、无需交易终端、无需用户提供凭据的小样本源：

- `baostock`：A 股历史日线 / basic financial 仅限小样本
- `akshare`：validation-only，小样本 A 股日线、指数、sector/macro staged-only
- `cninfo`：filing / announcement metadata 小样本；大文件抓取默认不启用

### 4.2 默认 deferred

- `tdx_pytdx`：本任务不得 live fetch；只能 route preview。live/manual probe 必须走单独用户授权任务。
- `qmt_xtdata`：不得启用，不得连接本机终端。
- `qmt_xqshare`：不得启用，不得连接 remote host。
- `yahoo_finance`：默认 deferred；如要接入必须单独说明 terms-sensitive / validation-only / no production default。
- FRED / macro live：不得 live；macro supplementary 仍 staged-only。

## 5. 样本边界

默认样本必须极小：

```yaml
max_symbols: 1-3
max_trade_days: 5-20
max_rows_per_source_domain: 100
max_network_calls_per_run: 10
full_market_scan: forbidden
full_history_backfill: forbidden
production_clean_write: forbidden_by_default
```

任何扩大样本、提高 row cap、增加 source/domain 都必须在 plan 中解释原因，并通过 ResourceGuard 或等价 caps。

## 6. 必读索引文件

执行前必须读取并摘要以下文件。此清单是最低要求，不是上限；执行者必须根据项目地图、source registry、contract authority、route planner、adapter import graph、测试失败信息继续追溯相关文件。

### 6.1 协议与项目地图

- `AGENTS.md`
- `CLAUDE.md`
- `.trellis/workflow.md`
- `.trellis/spec/guides/complex-task-planning-protocol.md`
- `.trellis/spec/guides/round3-repair-debt-worktree-plan.md`
- `ROUND3_BATCH_IMPLEMENTATION_MAP.md`
- `docs/ROUND3_HANDOFF.md`
- `docs/AUDIT_DEFERRED_REGISTRY.md`
- `docs/UNRESOLVED_ISSUES_REGISTRY.md`

### 6.2 数据源、路由、质量、写入、安全契约

- `docs/modules/data_sources.md` if present
- `docs/modules/source_route_plan.md`
- `docs/modules/data_validation_and_conflict.md`
- `docs/modules/write_manager.md`
- `docs/modules/duckdb_and_parquet.md`
- `docs/modules/local_file_system.md`
- `docs/quality/production_live_pilot_policy.md`
- `docs/quality/staged_acceptance_policy.md`
- `docs/ops/db_inspect_cli.md`
- `docs/ops/data_health_cli.md`
- `specs/datasource_registry/source_registry.yaml`
- `specs/datasource_registry/source_capabilities.yaml`
- `specs/contracts/data_adapter_contract.md`
- `specs/contracts/datasource_service_contract.yaml`
- `specs/contracts/source_route_contract.yaml`
- `specs/contracts/write_contract.yaml`
- `specs/contracts/data_quality_rules.yaml`
- `specs/contracts/source_conflict_rules.yaml`
- `specs/contracts/resource_limits.yaml`
- `specs/contracts/runtime_versions.md`

### 6.3 实现与测试

- `backend/app/datasources/`
- `backend/app/datasources/adapters/`
- `backend/app/storage/raw_store.py`
- `backend/app/storage/staged_evidence.py`
- `backend/app/db/validation_gate.py`
- `backend/app/db/write_manager.py`
- `backend/app/sync/`
- `backend/app/ops/db_inspector.py`
- `backend/app/ops/live_pilot.py`
- `tests/test_datasource_service.py`
- `tests/test_vendor_fetch_e2e.py`
- `tests/test_data_adapter_contract.py`
- `tests/test_source_route_planner.py`
- `tests/test_source_capabilities.py`
- `tests/test_raw_store.py`
- `tests/test_db_validation_gate.py`
- `tests/test_ops_db_inspector.py`
- `tests/test_production_live_pilot_policy.py`

### 6.4 最新审计与 blocker 状态

如果存在，必须读取：

- `docs/quality/adversarial_audit_report.md`
- `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3X_data_source_routing_blockers.md`
- `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3X_db_write_validation_blockers.md`
- 相关 `.trellis/tasks/**/execute-evidence/*mutation*`
- 相关 `.trellis/tasks/**/execute-evidence/*source*`
- 相关 `.trellis/tasks/**/execute-evidence/*route*`

### 6.5 当前批次完成物与审计检查

用户已确认当前批次四个分支已经完成。真实数据 staged pilot 必须基于这些完成物的最新状态规划，尤其不能绕过刚完成的 019/023A 语义和 018C 授权边界。

必须追溯：

- `feature/round3-019-layer2-sensor`：Layer2 输入/输出、snapshot lineage、source fields、no-future-data、double_count_guard。
- `feature/round3-023a-evidence-foundation`：evidence identity、source_fetch_ids、source_content_hashes、manual-review flags、Agent text not fact source。
- `review/round3-019-plan-audit`：对 019 是否可继续、是否有 BLOCK/WARN、是否要求修复的最终判断。
- `debt/r3b275-018c-live-manual-probe-plan`：tdx_pytdx 的授权语句、host/port 来源、sandbox path、ResourceGuard caps、no-mutation proof、close/re-defer criteria；本 pilot 仍不得执行 TDX live fetch。
- integration/coordinator artifacts：若存在 merge report、post-merge gate 或当前批次审计报告，必须读取；若不可见，记录 `MISSING_CURRENT_BATCH_EVIDENCE`。

## 7. 允许修改范围

只在计划明确后修改最小必要文件。候选范围：

- `backend/app/ops/` pilot runner or source probe module
- `backend/app/datasources/` only if adapter/service narrow fixes are needed
- `backend/app/storage/` only if raw/staged evidence path handling is needed
- `scripts/` only for thin CLI wrapper, if existing project pattern requires it
- `tests/test_vendor_fetch_e2e.py`
- `tests/test_datasource_service.py`
- `tests/test_raw_store.py`
- `tests/test_production_live_pilot_policy.py`
- task-local Trellis plan/evidence files

## 8. 禁止事项

禁止：

- production clean write by default
- full market scan
- full history backfill
- unbounded network calls
- TDX live fetch
- 启用本机或远程交易终端接入
- 将 akshare validation-only 结果写为唯一事实源
- 将 tdx_pytdx 设为 Primary 或 fallback
- live FRED
- 写 production DB migration
- 删除或放宽 existing gates
- 因 pilot 成功而声称 production-live readiness

## 9. Pilot 设计要求

计划必须定义：

```yaml
pilot_id: string
run_mode: staged_only | sandbox_only
allowed_sources: [baostock, akshare, cninfo]
allowed_domains: explicit list
symbols: explicit list
date_window: explicit start/end or recent N days
row_caps: explicit caps
network_call_caps: explicit caps
output_paths: sandbox/raw/staging evidence paths
production_db_path: explicit path, read-only/no-mutation proof target
clean_write_allowed: false by default
route_preview_required: true
validation_report_required: true
no_mutation_proof_required: true
failure_taxonomy: explicit statuses
close_or_redefer_criteria: explicit
```

## 10. Required evidence

必须生成或记录：

- route preview matrix
- source fetch attempt summary
- raw evidence manifest
- staging evidence manifest
- validation report summary
- source/domain success/failure taxonomy
- production DB no-mutation proof
- ResourceGuard caps result
- close / re-defer decision

## 11. 验证命令

最低命令：

```bash
pytest tests/test_source_capabilities.py -q
pytest tests/test_source_route_planner.py -q
pytest tests/test_datasource_service.py -q
pytest tests/test_data_adapter_contract.py -q
pytest tests/test_raw_store.py -q
pytest tests/test_db_validation_gate.py -q
pytest tests/test_ops_db_inspector.py -q
pytest tests/test_production_live_pilot_policy.py -q
```

如果新增或改动 vendor fixture / pilot E2E tests：

```bash
pytest tests/test_vendor_fetch_e2e.py -q
```

不得运行无边界 live/full-market 命令。

## 12. 完成标准

- 至少一个允许 source/domain 完成小样本 staged/raw evidence，或明确失败原因
- 每个失败 source/domain 有可解释 status 和 re-defer reason
- production clean tables 无 mutation proof
- route preview 与 selected/skipped/disabled 状态一致
- validation report 能反映真实数据质量或明确缺口
- 不声称 production-live readiness
- 合并报告列出成功源、失败源、字段/口径问题、DB/schema 问题、下一步扩大或 re-defer 建议
