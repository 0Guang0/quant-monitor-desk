# R3Y_real_data_staged_pilot_v2 — 真实数据 staged pilot v2 扩样与质量暴露

## 1. 任务性质

本任务是受控真实数据接入扩样任务，不是 production-live 启用任务。

目标是在 PROMPT_14 staged pilot 已完成、主线收尾已完成的基础上，扩大真实数据 raw/staging/sandbox 样本，验证 baostock / cninfo / akshare validation 的真实可用性与失败模式，并生成更完整的 validation / conflict / data-quality evidence。

本任务必须保持 staged-only / sandbox-first，不得默认写 production clean table，不得声称 production-live readiness。

## 2. 分支与工作方式

- 建议分支：`feature/round3-real-data-staged-pilot-v2`
- 基准分支：最新用户确认完成收尾后的 `master`
- 目标合并：`integration/round3` 或用户指定的下一批集成分支
- 工作方式：先 `/to-issues` 垂直切片计划，再 TDD/RED-GREEN 实现，再执行小样本真实数据验证

## 3. 任务目标

完成后必须回答：

1. baostock 在扩大 symbol / date window 后是否仍能稳定生成 raw/staging evidence？
2. cninfo metadata 在扩大样本后是否仍能提供可验证字段结构？
3. akshare validation 网络失败是否可复现、是否可通过安全 retry / proxy-aware path 改善；若不能，是否明确 re-defer？
4. source route matrix 是否解释每个 selected / skipped / disabled / validation-only 状态？
5. validation report 是否能暴露真实数据字段缺失、schema drift、row_count、quality_flags、source_used 问题？
6. conflict summary 是否能记录 primary-vs-validation 的比较状态或明确 deferred reason？
7. raw/staging evidence 是否有 content_hash / source_fetch_id / relative path / vendor_api / as_of_timestamp？
8. production DB no-mutation proof 是否在主线存在 `data/duckdb/quant_monitor.duckdb` 时仍可信？
9. 是否可以进入 sandbox clean-write rehearsal？

## 4. /to-issues 垂直切片

执行者必须在 Plan 阶段使用 `/to-issues` 思路将本任务拆成以下垂直 issue。每个 issue 必须有 RED/GREEN 测试或明确不可测试原因、evidence 文件、done criteria。

| Issue ID   | 垂直切片                          | 要实现/验证的功能                                                                          | 验收证据                       |
| ---------- | --------------------------------- | ------------------------------------------------------------------------------------------ | ------------------------------ |
| R3Y-SP2-01 | Pilot v2 plan/caps                | 定义 pilot_id、allowed sources/domains、symbol/date/window/row/network caps、sandbox paths | plan + caps JSON               |
| R3Y-SP2-02 | baostock expanded sample          | 扩大 cn_equity_daily_bar 小样本，生成 raw/staging evidence                                 | baostock manifest + tests      |
| R3Y-SP2-03 | cninfo metadata expanded sample   | 扩大 announcement/filing metadata 小样本，验证字段结构                                     | cninfo manifest + schema notes |
| R3Y-SP2-04 | akshare validation retry/re-defer | validation-only 重试，记录 NETWORK_ERROR / SUCCESS / EMPTY_RESPONSE taxonomy               | akshare taxonomy evidence      |
| R3Y-SP2-05 | route preview matrix v2           | selected/skipped/disabled/validation-only/user-auth-required 状态完整输出                  | route_preview_matrix_v2.json   |
| R3Y-SP2-06 | validation report v2              | 对真实 staging evidence 输出 field/schema/row_count/source_used/quality_flags 检查         | validation_report_v2.json      |
| R3Y-SP2-07 | conflict summary v2               | primary-vs-validation 比较或明确 conflict deferred reason                                  | conflict_check_summary_v2.json |
| R3Y-SP2-08 | production no-mutation proof v2   | 在 production DB 存在与不存在两种情形下证明 staged-only                                    | no_mutation_proof_v2.md        |
| R3Y-SP2-09 | close/re-defer matrix             | 对每个 source/domain 给出 expand / retry / re-defer / block                                | pilot_v2_closeout.json         |

不得把这些 issue 合并成一个“脚本跑通”结果。每个 issue 都必须能被审查者单独判断。

## 5. 数据源范围

### 5.1 允许源

- `baostock`：主线 staged/raw 小样本；可扩大 symbol 与 date window，但不得 full market scan。
- `cninfo`：metadata 小样本；大文件 / PDF 默认不启用。
- `akshare`：validation-only；可 retry 小样本 validation path，但不得作为唯一事实源，不得 clean-write。

### 5.2 默认 deferred / 禁止启用

- `tdx_pytdx`：仅 route preview；不得 live fetch，除非用户另开授权任务。
- `qmt_xtdata` / `qmt_xqshare`：不得启用。
- `yahoo_finance`：默认 deferred；除非单独用户确认 validation-only 范围。
- FRED / macro live：不得 live；macro supplementary 仍 staged-only。

## 6. 默认样本边界

默认 cap：

```yaml
max_symbols: 3-5
max_trade_days: 20-60
max_rows_per_source_domain: 500
max_network_calls_per_run: 25
full_market_scan: forbidden
full_history_backfill: forbidden
production_clean_write: false
```

若执行者认为需要更大样本，必须先在 plan 中给出原因、风险控制、ResourceGuard caps，并取得用户/coordinator 明确批准。

## 7. 必读索引文件

执行前必须读取并摘要以下文件。此清单是最低要求，不是上限；执行者必须根据 source registry、route planner、adapter imports、pilot code、测试失败信息继续追溯相关文件。

### 7.1 项目协议与当前收尾

- `AGENTS.md`
- `CLAUDE.md`
- `.trellis/workflow.md`
- `.trellis/spec/guides/complex-task-planning-protocol.md`
- `.trellis/spec/guides/round3-repair-debt-worktree-plan.md`
- `ROUND3_BATCH_IMPLEMENTATION_MAP.md`
- `docs/AUDIT_DEFERRED_REGISTRY.md`
- `docs/UNRESOLVED_ISSUES_REGISTRY.md`
- `docs/RESOLVED_ISSUES_REGISTRY.md`

### 7.2 前序任务与证据

- `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3X_real_data_staged_pilot.md`
- `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3Y_post_r3x_strict_adversarial_audit.md`
- `docs/implementation_tasks/ROUND_3_PARALLEL_PROMPTS/PROMPT_14_feature_round3_real_data_staged_pilot.md`
- `.trellis/tasks/feature-round3-real-data-staged-pilot/execute-evidence/merge_gate_report.md`
- `.trellis/tasks/feature-round3-real-data-staged-pilot/execute-evidence/pilot_closeout.json`
- `.trellis/tasks/feature-round3-real-data-staged-pilot/execute-evidence/route_preview_matrix.json`
- `.trellis/tasks/feature-round3-real-data-staged-pilot/execute-evidence/source_fetch_attempt_summary.json`
- `.trellis/tasks/feature-round3-real-data-staged-pilot/execute-evidence/raw_evidence_manifest.json`
- `.trellis/tasks/feature-round3-real-data-staged-pilot/execute-evidence/staging_evidence_manifest.json`
- `.trellis/tasks/feature-round3-real-data-staged-pilot/execute-evidence/validation_report_summary.json`
- `.trellis/tasks/feature-round3-real-data-staged-pilot/execute-evidence/production_db_no_mutation_proof.md`
- `.trellis/tasks/fix-round3-post14-audit-staged-pilot/execute-evidence/merge_gate_report.md`
- `.trellis/tasks/fix-round3-r3x-residual-open-items-closure/execute-evidence/merge_gate_report.md`

### 7.3 设计、契约、实现

- `docs/modules/data_validation_and_conflict.md`
- `docs/modules/write_manager.md`
- `docs/modules/duckdb_and_parquet.md`
- `docs/ops/db_inspect_cli.md`
- `docs/ops/data_health_cli.md`
- `docs/quality/production_live_pilot_policy.md`
- `docs/quality/staged_acceptance_policy.md`
- `specs/datasource_registry/source_registry.yaml`
- `specs/datasource_registry/source_capabilities.yaml`
- `specs/contracts/data_adapter_contract.md`
- `specs/contracts/datasource_service_contract.yaml`
- `specs/contracts/source_route_contract.yaml`
- `specs/contracts/write_contract.yaml`
- `specs/contracts/data_quality_rules.yaml`
- `specs/contracts/source_conflict_rules.yaml`
- `specs/contracts/resource_limits.yaml`
- `backend/app/ops/staged_pilot.py`
- `backend/app/ops/staged_pilot_fetch_ports.py`
- `backend/app/ops/mutation_proof.py`
- `backend/app/datasources/`
- `backend/app/storage/`
- `backend/app/db/`
- `tests/test_staged_pilot.py`
- `tests/test_datasource_service.py`
- `tests/test_source_route_planner.py`
- `tests/test_source_capabilities.py`
- `tests/test_raw_store.py`
- `tests/test_db_validation_gate.py`
- `tests/test_production_live_pilot_policy.py`

## 8. 允许修改范围

只在 plan 中列明后修改最小必要文件。候选范围：

- `backend/app/ops/staged_pilot.py`
- `backend/app/ops/staged_pilot_fetch_ports.py`
- `backend/app/ops/mutation_proof.py`
- `backend/app/datasources/` only for narrow pilot-required fix
- `backend/app/storage/` only for raw/staging evidence handling
- `tests/test_staged_pilot.py`
- `tests/test_vendor_fetch_e2e.py`
- `tests/test_production_live_pilot_policy.py`
- task-local Trellis evidence

## 9. 禁止事项

禁止：

- production clean write by default
- production migration
- full market scan
- full history backfill
- unbounded network calls
- TDX live fetch
- QMT / xqshare enablement
- validation-only source 作为唯一事实源
- tdx_pytdx Primary / fallback
- live FRED
- 因 staged pilot 成功而声称 production-live readiness

## 10. 验证命令

最低命令：

```bash
python -m pytest tests/test_staged_pilot.py -q
python -m pytest tests/test_source_capabilities.py tests/test_source_route_planner.py tests/test_datasource_service.py -q
python -m pytest tests/test_raw_store.py tests/test_db_validation_gate.py tests/test_ops_db_inspector.py tests/test_production_live_pilot_policy.py -q
```

若新增/改动 vendor fixture 或 e2e：

```bash
python -m pytest tests/test_vendor_fetch_e2e.py -q
```

## 11. 完成标准

- 所有 `/to-issues` issue 有 evidence 文件。
- 至少 baostock 或 cninfo 一个 source/domain 完成扩大样本 staged/raw evidence；失败项有 clear taxonomy。
- akshare validation 成功则仅 validation-only；失败则明确 re-defer。
- 生成 route preview v2、raw/staging manifest v2、validation report v2、conflict summary v2、no-mutation proof v2、closeout v2。
- production clean tables 未修改。
- 明确是否允许进入 sandbox clean-write rehearsal。
