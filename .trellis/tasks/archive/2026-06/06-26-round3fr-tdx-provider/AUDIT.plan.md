# Audit 计划 — R3FR-03 TDX Provider Refactor

| slug | `06-26-round3fr-tdx-provider` |

---

## 0.1 Trace Authority Set

| 类别               | 文件                                                                                                                                    |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------------------- |
| 原始任务卡         | `docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/R3FR_03_TDX_PROVIDER_REFACTOR.md`  |
| batch README       | `docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/README.md`                         |
| playbook           | `docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_COORDINATOR_PLAYBOOK.md` |
| task README        | `docs/implementation_tasks/README.md`                                                                                                   |
| task input index   | `docs/implementation_tasks/TASK_INPUT_CONTEXT_INDEX.md`                                                                                 |
| unresolved         | `docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md`                                                                            |
| project map        | `MIGRATION_MAP.md`                                                                                                                      |
| roadmap            | `PROJECT_IMPLEMENTATION_ROADMAP.md`                                                                                                     |
| 执行索引           | `EXECUTION_INDEX.md`                                                                                                                    |
| 对抗性 Plan 审计   | `research/adversarial-plan-audit.report.md`                                                                                             |
| integration-ledger | `research/integration-ledger.md`                                                                                                        |
| 授权 MD            | `docs/quality/tdx_pytdx_live_manual_probe_authorization_2026-06-24.md`                                                                  |
| guardrails         | `specs/contracts/reference_adoption_guardrails.yaml`                                                                                    |

---

## 1. 本任务验证覆写

| 维  | 命令                                                                                                                                                                                                                                                   | 通过条件       |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------- |
| A3  | `rg "参考项目" backend/app` exit 1；`rg "auto_login\|order_target" backend/app/datasources/fetch_ports backend/app/datasources/normalizers`                                                                                                            | 无匹配         |
| A5  | 对照 `EXECUTION_INDEX` §0.1 每条 AC + `adversarial-plan-audit.report.md` 闭合                                                                                                                                                                          | 无 OPEN ADV    |
| A6  | **SKIP** — 无 perf SLA                                                                                                                                                                                                                                 | —              |
| A7  | `uv run python -m backend.app.cli.main data health --help`                                                                                                                                                                                             | 非 placeholder |
| A8  | `uv run pytest tests/test_tdx_pytdx_port.py tests/test_tdx_manual_probe.py tests/test_tdx_live_manual_probe_authorization.py tests/test_reference_adoption_guardrails.py tests/test_source_capabilities.py -k tdx --basetemp=.audit-sandbox/pytest -q` | 全绿           |
