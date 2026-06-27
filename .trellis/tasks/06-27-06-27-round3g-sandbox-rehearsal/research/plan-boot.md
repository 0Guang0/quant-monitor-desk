# Plan boot — R3G-01 Sandbox Clean-Write Rehearsal

<!-- trellis-plan-boot-complete -->

**Phase P0 complete** · 原计划已读

## 任务定位

| 项       | 值                                                                                                                           |
| -------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Task ID  | R3G-01                                                                                                                       |
| Batch    | 3G — Sandbox Clean Write                                                                                                     |
| 分支     | `feature/round3g-sandbox-rehearsal`                                                                                          |
| 活任务卡 | `docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/R3G_01_SANDBOX_CLEAN_WRITE_REHEARSAL.md` |
| 契约     | `specs/contracts/sandbox_clean_write_contract.yaml`                                                                          |

## 价值陈述（冻结须内联）

在 **sandbox DB only** 下，用 **baostock / cninfo（metadata only）/ 用户授权 fred** 三条窄路径，证明 raw→staged→data health→validation→WriteManager→sandbox clean 表→rehearsal 报告→rollback 可审计。**不**打开生产写入门（R3G-03 不在范围）；**不**证五层全量端到端。

## 前置（已满足）

- Batch 3F-R **CLOSED**（R3FR-07）
- `qmd data health` read-only runtime + data_health_profiles 已存在
- `provider_catalog.yaml` SSOT（25 源）；fred `requires_user_authorization: true`
- 契约门禁测试 `tests/test_round3g_sandbox_clean_write_rehearsal.py` 已绿（契约层）
- **用户已确认**：R3G-01 排练允许授权使用 FRED（须 explicit authorization artifact）

## 实现形态（对齐活卡 §5）

```text
backend/app/ops/sandbox_clean_write/
  __init__.py
  rehearsal_plan.py
  rehearsal_loader.py
  rehearsal_runner.py
  rehearsal_report.py
backend/app/cli/data_commands.py   # 子命令 sandbox-clean-write rehearse
```

编排器 **compose** 现有门禁：`DataSourceService`、`SourceRoutePlanner`、`ResourceGuard`、`DbValidationGate`、`WriteManager`、R3F-R data-health profiles。**禁止** ad-hoc bypass runner。

## 非目标

- 生产 DB mutation / R3G-03 limited production entry
- 扩大 L1 ingest allowlist（`ENV-E1-DGS10`）冒充完成
- QMT/TDX/xqshare/Yahoo 生产主路径
- `参考项目/**` runtime import / OpenBB runtime copy
- Agent 触发写 / 并行 R3G-02/R3G-03

## FRED 授权 artifact（Plan 设计）

| 项          | 约定                                                                                                            |
| ----------- | --------------------------------------------------------------------------------------------------------------- |
| 默认路径    | `.audit-sandbox/round3g/fred_user_authorization.yaml`                                                           |
| CLI 覆盖    | `--fred-authorization <path>`                                                                                   |
| 格式        | YAML；字段对齐 `fred_sandbox_pilot` + 契约 cap                                                                  |
| 必填        | `authorization_present: true`、`source_id: fred`、`domain: macro_series`、`allow_production_clean_write: false` |
| cap         | `max_series: 3`（契约 r3g01）、`max_window_days: 120`、显式 series 列表                                         |
| fail-closed | 候选集含 fred 且无有效 artifact → 拒绝；`enabled_by_default: false` 与 catalog 一致                             |
| 措辞        | catalog 用 `production_default_enabled`（非 `production_default_allowed`）                                      |

## 候选 cap（契约 SSOT）

见 `sandbox_clean_write_contract.yaml` → `candidate_caps` → r3g01\_\* 字段。

## GitNexus Plan 探索结论

- `WriteManager` 已被 `staged_pilot.py` 等消费；R3G-01 应仿 staged_pilot 编排，非新建平行写链
- `sandbox_clean_write/**` 目录 **尚不存在** — greenfield 模块
- `data_commands.py` 尚无 `sandbox-clean-write` 子命令
