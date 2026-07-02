# R3Y_post_r3x_strict_adversarial_audit — Post-R3X 严格对抗性审计

## 1. 任务性质

本任务是只读 review / audit 任务，不是实现任务。

目标是在主线收尾完成后，对 PROMPT_11–17 / R3X 修复结果、真实数据 staged pilot、ponytail 修复、审计 registry 收口进行更严格的二次对抗性审计。

本任务不是再次泛泛扫 69 项，而是对“已修复/已闭合/已通过”的结论做反证：验证修复是否真的进入 runtime path、测试是否覆盖行为而非表面、真实数据 staged pilot 是否仍存在绕过 source route / WriteManager / ValidationGate / ResourceGuard 的路径。

## 2. 分支与工作方式

- 建议分支：`review/round3-post-r3x-strict-adversarial-audit`
- 基准分支：最新用户确认完成收尾后的 `master`
- 目标合并：默认不合并实现代码；若用户批准归档审计报告，可合并审计报告
- 工作方式：只读审计；允许生成 task-local review report / evidence，但不得修改实现代码、契约、配置或 DB

## 3. 任务目标

完成后必须回答：

1. PROMPT_11–17 宣称 closed/fixed 的项目是否真的闭合？
2. 哪些修复只是测试绿，但 runtime path 仍未覆盖？
3. 真实数据 staged pilot 是否仍可能绕过 DataSourceService、RoutePlanner、WriteManager、ValidationGate、ResourceGuard？
4. `production DB no-mutation proof` 在 DB 存在、缺失、schema-only、row-count-only 四类情形下是否可信？
5. source registry / capability / platform matrix / adapters 是否存在新的 drift？
6. validation-only source、disabled source、authorization-required source 是否仍不会被默认启用或 clean-write？
7. Layer2 / Layer5 lineage 与真实 source_fetch_ids / source_content_hashes 是否兼容？
8. registry 文件是否准确反映已解决、未解决、deferred 项，是否存在“报告 closed 但 registry 未闭合”的不一致？
9. 下一步是否允许进入 `real-data staged pilot v2` 与 `read-only data health v1`？

## 4. /to-issues 垂直切片

执行者必须在 Plan 阶段使用 `/to-issues` skill。切片必须是 tracer-bullet vertical slices：每个 issue 都是一条可独立领取、可独立验证、端到端穿透相关集成层的薄切片，而不是按 schema / API / tests / docs 等层级横切。每个 issue 必须包含：Title、What to build or verify、Acceptance criteria、Blocked by、Evidence output、Test or verification plan。若存在依赖，必须先执行 blocker issue。

本任务不需要发布到外部 issue tracker；但任务卡和执行计划必须使用同等结构，确保执行 agent 能直接领取并完成。

执行者必须把本任务拆成以下垂直 issue，并逐 issue 输出 PASS / WARN / BLOCK。不得只写一份总评。

| Issue ID   | 垂直切片                              | 必须验证的行为                                                                       | 最低产出                       |
| ---------- | ------------------------------------- | ------------------------------------------------------------------------------------ | ------------------------------ |
| R3Y-AUD-01 | R3X closed claims 反证                | PROMPT_11–17 中 FIXED / ALREADY_CLOSED 是否有真实实现、测试与 evidence               | closed-claim matrix            |
| R3Y-AUD-02 | Source route / DataSourceService 反证 | fetch 是否一定先 route；disabled/validation-only source 是否 fail-closed             | source-route adversarial notes |
| R3Y-AUD-03 | Write / Validation / Conflict 反证    | clean write 是否经 WriteManager + ValidationGate；severe conflict 是否阻断           | write-gate adversarial notes   |
| R3Y-AUD-04 | Real-data staged pilot 反证           | staged pilot 是否只写 raw/staging/sandbox；是否存在 bypass 或 weak no-mutation proof | pilot-path audit notes         |
| R3Y-AUD-05 | Lineage / evidence foundation 反证    | Layer2/Layer5 是否正确传播 source IDs、hashes、as_of、no-future-data                 | lineage/evidence notes         |
| R3Y-AUD-06 | Registry consistency 反证             | RESOLVED / UNRESOLVED / AUDIT_DEFERRED 是否与报告一致                                | registry-drift table           |
| R3Y-AUD-07 | Test quality 反证                     | 关键测试是否覆盖 runtime 行为，不只是 import/存在性                                  | test-depth findings            |
| R3Y-AUD-08 | Go/no-go gate                         | 是否允许 staged pilot v2、data health v1、sandbox clean rehearsal                    | final PASS/WARN/BLOCK          |

每个 issue 必须有：目标、读取文件、实际核查方法、结论、证据路径、阻塞项、建议下一步。

## 5. 工程纪律与执行规则

- 文档和计划优先使用中文；代码、路径、命令、契约字段、专用术语可保留英文。
- 本审计任务不得写正式代码；若为了验证而新增或调整测试，测试必须遵守 `/testing-guidelines`。
- 所有新增或调整的测试必须注明：覆盖范围、测试对象、目的或目标。
- 若审计发现需要代码修复，只能提出 issue / finding，不得在本 review 分支修复。
- 测试可以修正表达，但不能改变原始验证目标。
- 审计中运行测试后，必须记录完整命令、结果与无法运行原因。

## 6. 必读索引文件

执行前必须读取并摘要以下文件。此清单是最低要求，不是上限；执行者必须根据项目地图、contract authority、import/call graph、task evidence、测试失败信息继续追溯相关文件。

### 5.1 项目协议与最新收尾状态

- `AGENTS.md`
- `CLAUDE.md`
- `.trellis/workflow.md`
- `.trellis/spec/guides/complex-task-planning-protocol.md`
- `.trellis/spec/guides/round3-repair-debt-worktree-plan.md`
- `ROUND3_BATCH_IMPLEMENTATION_MAP.md`
- `docs/ROUND3_HANDOFF.md`
- `docs/AUDIT_DEFERRED_REGISTRY.md`
- `docs/UNRESOLVED_ISSUES_REGISTRY.md`
- `docs/RESOLVED_ISSUES_REGISTRY.md`

### 5.2 R3X / Post14 / Ponytail 审计与收口材料

- `docs/quality/adversarial_audit_report.md`
- `docs/quality/adversarial_audit_post14_contract_ponytail_lane.md`
- `docs/quality/PONYTAIL_MODULE_SCAN_20260622.md`
- `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3X_contract_architecture_adversarial_audit.md`
- `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3X_data_source_routing_blockers.md`
- `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3X_db_write_validation_blockers.md`
- `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3X_real_data_staged_pilot.md`
- `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3X_residual_open_items_closure.md`
- `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3X_ponytail_pilot_prep_bucket_a.md`
- `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3X_ponytail_low_touch_bucket_c.md`

### 5.3 PROMPT 与执行 evidence

- `docs/implementation_tasks/ROUND_3_PARALLEL_PROMPTS/PROMPT_11_review_round3_contract_architecture_adversarial_audit.md`
- `docs/implementation_tasks/ROUND_3_PARALLEL_PROMPTS/PROMPT_12_fix_round3_data_source_routing_blockers.md`
- `docs/implementation_tasks/ROUND_3_PARALLEL_PROMPTS/PROMPT_13_fix_round3_db_write_validation_blockers.md`
- `docs/implementation_tasks/ROUND_3_PARALLEL_PROMPTS/PROMPT_14_feature_round3_real_data_staged_pilot.md`
- `docs/implementation_tasks/ROUND_3_PARALLEL_PROMPTS/PROMPT_15_fix_round3_r3x_residual_open_items_closure.md`
- `docs/implementation_tasks/ROUND_3_PARALLEL_PROMPTS/PROMPT_16_fix_round3_ponytail_pilot_prep_bucket_a.md`
- `docs/implementation_tasks/ROUND_3_PARALLEL_PROMPTS/PROMPT_17_debt_round3_ponytail_low_touch.md`
- `.trellis/tasks/feature-round3-real-data-staged-pilot/execute-evidence/`
- `.trellis/tasks/fix-round3-data-source-routing-blockers/merge_gate_report.md`
- `.trellis/tasks/fix-round3-db-write-validation-blockers/execute-evidence/merge_gate_report.md`
- `.trellis/tasks/fix-round3-post14-audit-staged-pilot/execute-evidence/`
- `.trellis/tasks/fix-round3-post14-audit-registry-docs/execute-evidence/`
- `.trellis/tasks/fix-round3-r3x-residual-open-items-closure/execute-evidence/merge_gate_report.md`
- `.trellis/tasks/fix-round3-ponytail-pilot-prep-bucket-a/execute-evidence/merge_gate_report.md`

### 5.4 设计、契约、实现

- `docs/modules/data_sources.md` if present
- `docs/modules/source_route_plan.md` if present
- `docs/modules/data_validation_and_conflict.md`
- `docs/modules/write_manager.md`
- `docs/modules/duckdb_and_parquet.md`
- `docs/modules/layer2_cross_asset_sensor.md`
- `docs/ops/db_inspect_cli.md`
- `docs/ops/data_health_cli.md`
- `docs/quality/production_live_pilot_policy.md`
- `docs/quality/staged_acceptance_policy.md`
- `specs/datasource_registry/source_registry.yaml`
- `specs/datasource_registry/source_capabilities.yaml`
- `specs/contracts/`
- `backend/app/datasources/`
- `backend/app/db/`
- `backend/app/storage/`
- `backend/app/sync/`
- `backend/app/ops/`
- `backend/app/layer2_sensors/`
- `backend/app/layer5_evidence/`
- `tests/`

## 6. 允许产出

- task-local review report
- issue matrix / closed-claim matrix
- list of verified blockers/warnings/suggestions
- read-only test logs

## 7. 禁止事项

禁止：

- 修改实现代码
- 修改 docs/specs 来匹配审计结论
- 写 production DB
- 运行 migration
- 执行真实 source fetch
- 启用 disabled/authorization-required source
- 运行 full market scan / full history scan
- 将未核实的 merge report 结论直接当事实

## 8. 验证建议

只允许安全只读测试。建议至少运行或记录无法运行原因：

```bash
python -m pytest tests/test_r3x_residual_open_items_closure.py -q
python -m pytest tests/test_staged_pilot.py -q
python -m pytest tests/test_datasource_service.py tests/test_source_route_planner.py tests/test_source_capabilities.py -q
python -m pytest tests/test_db_validation_gate.py tests/test_write_manager.py tests/test_raw_store.py -q
python -m pytest tests/test_layer2_sensor_loader.py tests/test_layer5_evidence_foundation.py -q
python -m pytest tests/test_round3_audit_registry_alignment.py -q
python scripts/check_doc_links.py
```

## 9. 完成标准

- 每个 `/to-issues` issue 都有 PASS / WARN / BLOCK。
- 明确是否允许 `feature/round3-real-data-staged-pilot-v2` 继续扩样。
- 明确是否允许 `feature/round3-readonly-data-health-v1` 实现并合并。
- 明确是否存在阻塞 sandbox clean-write rehearsal 的问题。
- 所有 HIGH/WARN finding 都有文件引用和复现路径。
- 输出最终 gate：`PASS_ALLOW_NEXT_BATCH` / `WARN_ALLOW_WITH_CONTROLS` / `BLOCK_FIX_FIRST`。
