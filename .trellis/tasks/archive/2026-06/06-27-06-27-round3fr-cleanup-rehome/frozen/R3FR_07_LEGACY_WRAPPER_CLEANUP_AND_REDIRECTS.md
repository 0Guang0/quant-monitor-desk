<!-- FROZEN: Plan protocol v4 · do not edit · source: docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/R3FR_07_LEGACY_WRAPPER_CLEANUP_AND_REDIRECTS.md · frozen_at: 2026-06-26T17:58:48Z -->

# R3FR-07 — Legacy Wrapper Cleanup and Redirects

> **Batch:** Batch 3F-R — Mature Reference Adoption Refactor  
> **Module movement:** Remove or redirect thin wrappers only after replacement implementations are stronger and tested.  
> **Execution posture:** cleanup/hardening only; no new feature scope; no evidence deletion.

---

## 1. 任务目标

关闭 Batch 3F-R：清理/重定向旧薄 wrapper 与过时规划叙事，使路线图下一入口为 Round 3G；不引入新功能、不删历史证据、不宣称 production-live。

```yaml
reference_project:
  path: n/a
  license: n/a
  allowed_use: forbidden_until_review
  qmd_target_files: []
  direct_copy_allowed: false
  rewrite_required: []
  forbidden_semantics:
    - new_runtime_adoption_during_cleanup
  attribution_required: false
```

## 2. 预期结果

| ID       | 可验证结果                                                                               |
| -------- | ---------------------------------------------------------------------------------------- |
| AC-07-01 | 规划文档不再声称 `health_check` 仍返回 `not_implemented_phase_c`                         |
| AC-07-02 | `check_daily_bars` / `health_check` / TDX probe wrapper 带 canonical redirect 说明       |
| AC-07-03 | `PROJECT_IMPLEMENTATION_ROADMAP` + `docs/ROUND3_HANDOFF` 标明 3F-R CLOSED、3G 为下一入口 |
| AC-07-04 | Batch 3G README 前置条件引用已完成的 3F-R 产出，不再写「被 3F-R 阻塞」                   |
| AC-07-05 | `MODULE_COMPLETION_RATING` 反映 R3FR-05 provider catalog 已合并                          |
| AC-07-06 | 任务卡 §5 五档 + `test_r3fr07` + `test_provider_catalog` + 全量 pytest 绿                |
| AC-07-07 | `ROUND3_BATCH_IMPLEMENTATION_MAP` checkpoint 反映 3F-R 关门                              |
| AC-07-08 | `R3FR_01_REFERENCE_INVENTORY` redirect 卡完好（guardrails 仍绿）                         |

## 3. 输入文件

- `docs/implementation_tasks/README.md`
- `docs/implementation_tasks/TASK_INPUT_CONTEXT_INDEX.md`
- `docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md`
- `PROJECT_IMPLEMENTATION_ROADMAP.md`
- `docs/ROUND3_HANDOFF.md`
- `ROUND3_BATCH_IMPLEMENTATION_MAP.md`
- `MODULE_COMPLETION_RATING.md`
- `BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/README.md`
- `BATCH_3FR_TASK_CARD_MANIFEST.md`
- `BATCH_3FR_COORDINATOR_PLAYBOOK.md`
- `BATCH_3FR_HARDENING_RULES.md`（尤其 §9 Cleanup boundary）
- `ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/README.md`
- `specs/contracts/reference_adoption_guardrails.yaml`
- `specs/contracts/data_quality_rules.yaml`（`ops_cli_profiles`）
- 已归档 Trellis：`06-26-round3fr-data-health-cli` · `06-26-round3fr-tdx-provider` · `06-26-round3fr-provider-catalog`

## 4. 相关代码文件

```text
backend/app/ops/data_health.py::check_daily_bars
backend/app/cli/data_commands.py::health_check
backend/app/ops/interface_probe_fetch_ports.py
backend/app/ops/tdx_manual_probe.py
tests/test_reference_adoption_guardrails.py
tests/test_r3fr07_legacy_wrapper_cleanup.py（新建）
docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/**
docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/**
PROJECT_IMPLEMENTATION_ROADMAP.md
MODULE_COMPLETION_RATING.md
docs/ROUND3_HANDOFF.md
```

## 5. 现有模式 / 参考

- R3FR-02+06：`run_data_health_profile` + `market_bar_p0` 为 data health canonical runtime（`ecf64f06`）
- R3FR-03：`TdxPytdxFetchPort` + `TdxPytdxProbeFetchPort` 瘦委托（`22086d59`）
- R3FR-05：provider catalog SSOT（`6c1a0d37`）
- `test_reference_adoption_guardrails.py` 已有 inventory redirect / 地图不是工单 测试 — 扩展而非重复

## 6. 技术约束

- cleanup/hardening only；禁止新 runtime 采纳、禁止 production clean write
- 旧 wrapper 可保留为 compatibility shim，但必须 docstring/模块注释指向 canonical 实现
- 不得删除 `.trellis/tasks/archive/**` 证据；仅更新索引与 redirect 说明
- 设计/契约文件不写当前完成度标签（完成度只在 `MODULE_COMPLETION_RATING.md`）

## 7. 资源约束

- 无 live fetch、无 DB 写入、无全市场扫描
- Execute 每步 GREEN 后跑 targeted pytest；批次末全量 pytest

## 8. 边界约束

| 禁止                | 说明                                              |
| ------------------- | ------------------------------------------------- |
| 新功能 scope        | 不加新 profile、不扩 provider、不启用 live source |
| 删证据              | 归档 Trellis / execute-evidence 只读              |
| 中央 inventory      | 不得创建或依赖 `reference_adoption_inventory.md`  |
| 弱化测试            | 不得为通过而改测试目的                            |
| master 直接 Execute | 分支 `chore/round3fr-cleanup-rehome`              |

## 9. 实现步骤

1. **9.0 Boot** — 捕获任务卡 §5 targeted pytest 基线
2. **9.1 规划叙事清理** — 修正仍声称 placeholder 的 3F-R README/manifest；不删历史卡，加 redirect/DONE 注记
3. **9.2 data health shim redirect** — `check_daily_bars` docstring + 可选 DRY 委托 `data_health_profiles` 共享 OHLCV 规则（行为不变）
4. **9.3 CLI health redirect** — `health_check` 模块注释指向 `run_data_health_profile`；新增文档 guardrail 测试
5. **9.4 TDX wrapper redirect** — `interface_probe_fetch_ports` / `tdx_manual_probe` 顶部 canonical 边界说明
6. **9.5 3F-R 关门 + 3G 入口** — 更新 ROADMAP、HANDOFF、3G README、MODULE_COMPLETION_RATING
7. **9.6 guardrails + loop** — 扩展 `test_reference_adoption_guardrails`；`loop_maintain.py`
8. **9.7 全量验收** — `uv run pytest -q`

## 10. 测试要求

| 文件                                          | 目的                                 |
| --------------------------------------------- | ------------------------------------ |
| `tests/test_r3fr07_legacy_wrapper_cleanup.py` | AC-07-01~05 文档与 redirect 契约     |
| `tests/test_reference_adoption_guardrails.py` | 3F-R/3G 治理边界延续                 |
| 任务卡 §5 既有模块测试                        | 回归 R3FR-02/03/06 不被 cleanup 破坏 |

## 11. 验收命令

```bash
uv run pytest tests/test_reference_adoption_guardrails.py -q
uv run pytest tests/test_qmd_data_cli.py tests/test_ops_data_health.py -q
uv run pytest tests/test_tdx_manual_probe.py tests/test_tdx_live_manual_probe_authorization.py -q
uv run pytest tests/test_documentation_index.py tests/test_docs_specs_indexed.py -q
uv run pytest tests/test_r3fr07_legacy_wrapper_cleanup.py -q
uv run python scripts/loop_maintain.py
uv run pytest -q
```

## 12. 完成标准

- 活任务卡 §2 全部 AC 有测试或 doc guardrail 覆盖
- Batch 3F-R manifest 全部 DONE；ROADMAP 下一入口为 3G
- 无 open 3F-R 项阻塞 3G（条件 A 满足）
- Trellis `validate-execute-handoff` 通过（Execute 后）

## 13. Red Flags

- 把 cleanup 做成新 feature 切片
- 删除归档证据或弱化 R3FR-02/03/05/06 测试
- 在契约/架构文件写「当前仅完成 x%」
- 未跑全量 pytest 就宣称 batch close

## 14. 输出要求

汇报：改动文件列表、每步证据路径、未完成 DEFERRED 项（B2.5-O-05 等仍属 3H）、全量 pytest 结果。

---

## 附录 A — 原任务卡 cleanup targets（保留）

Review and update:

```text
backend/app/ops/data_health.py::check_daily_bars
backend/app/cli/data_commands.py::health_check
backend/app/ops/interface_probe_fetch_ports.py
backend/app/ops/tdx_manual_probe.py
docs/implementation_tasks/README.md
docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/*.md
docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/*.md
PROJECT_IMPLEMENTATION_ROADMAP.md
MODULE_COMPLETION_RATING.md
```

## 附录 B — Required cleanup behavior

- Old wrappers may remain only as compatibility redirects to the new QMD-owned profile/provider implementation.
- Historical task cards may remain only with redirect notes if their old instruction is obsolete.
- No `reference_adoption_inventory.md` may become an execution dependency.
- No production claims may be introduced by cleanup.
- No historical evidence file may be deleted without redirect/index update.
- No design/contract/architecture file should be polluted with current completion ratings.

## 附录 C — Overengineering stop gate

Follow-up work for affected modules must be: complete next batch | full-stable closure batch | hardening/regression batch — not one-flag micro-slices.
