# GitNexus summary — R3G-01（Phase 1b）

## Query: sandbox clean write / WriteManager / staged pilot

| 符号                                      | 角色              | Plan 结论                                           |
| ----------------------------------------- | ----------------- | --------------------------------------------------- |
| `WriteManager.write`                      | clean 表合并      | rehearsal_runner 必须调用；impact 前须分析          |
| `DbValidationGate`                        | 写前校验          | 与 staged_pilot `_StagedPilotValidationGate` 同模式 |
| `run_staged_pilot` / `StagedPilotRequest` | 现有 sandbox 编排 | **参考** compose 顺序，不 fork 为第二 runner        |
| `DataSourceService`                       | fetch             | 候选三源路由                                        |
| `SourceRoutePlanner`                      | provider 选择     | baostock/cninfo/fred                                |
| `ResourceGuard`                           | 资源 cap          | 排练 job 前                                         |
| `run_data_health_profile`                 | 写前 DQ           | 调用既有 profiles，不新造规则集                     |
| `load_authorization_yaml` (fred)          | FRED 授权         | R3G-01 复用校验语义 + R3G cap                       |

## Query: sandbox_clean_write

- **无现有符号** — greenfield `backend/app/ops/sandbox_clean_write/`
- 契约测试已引用路径，实现尚未存在

## Impact 预判（Execute 前必跑）

| 拟修改符号                          | 方向                            | 风险                      |
| ----------------------------------- | ------------------------------- | ------------------------- |
| 新 `rehearsal_runner`               | 新模块                          | LOW — 无 upstream 至生产  |
| `data_commands.py`                  | 增子命令                        | MEDIUM — CLI 入口；仅追加 |
| `sandbox_clean_write_contract.yaml` | 可能补 `cli`/`authorization` 节 | LOW                       |

**警告：** `staged_pilot.py` 为 HIGH fan-in；R3G-01 **不得**修改其行为，仅只读参考。

## 禁止模式（guardrails 已有）

- `runtime_import_from_reference_project`
- `jq2ptrade_disallowed_api_surface`
- `agent_triggered_write_path`
- `copied_openbb_runtime_source`

## Execute 建议顺序

1. `rehearsal_plan` + authorization（RED）
2. `rehearsal_loader` + `rehearsal_report`（可并行 TDD）
3. `rehearsal_runner`（gate compose）
4. CLI
5. 集成测试 + guardrails + 全库 pytest
