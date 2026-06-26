# Audit 计划 — R3FR-05 Provider Catalog

追溯：`EXECUTION_INDEX.md` §2 + `research/plan-adversarial-audit.report.md`

## 0.1 Trace Authority Set

| 类别               | 文件                                               |
| ------------------ | -------------------------------------------------- |
| 活任务卡 / frozen  | R3FR_05_PROVIDER_CATALOG_OPENBB_REFERENCE.md       |
| 索引               | EXECUTION_INDEX.md                                 |
| 对抗审计           | research/plan-adversarial-audit.report.md          |
| integration-ledger | research/integration-ledger.md                     |
| round map          | ROUND3_BATCH_IMPLEMENTATION_MAP.md                 |
| project map        | docs/generated/project_map.generated.json          |
| guardrails         | specs/contracts/reference_adoption_guardrails.yaml |

## 1. 本任务验证覆写

| 维  | 本任务 | 命令                                                                                                                                                                                           | 环境          |
| --- | ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------- |
| A3  | 必做   | `rg "参考项目/OpenBB" backend/ scripts/` + guardrails                                                                                                                                          | local         |
| A6  | 不用   | SKIP — 无 perf SLA                                                                                                                                                                             | —             |
| A7  | 不用   | SKIP — 无 migrate CLI                                                                                                                                                                          | —             |
| A8  | 必做   | `uv run pytest tests/test_provider_catalog.py tests/test_source_capabilities.py tests/test_reference_adoption_guardrails.py tests/test_source_registry.py -q --basetemp=.audit-sandbox/pytest` | audit-sandbox |

## 2. DoD

7.pre → gitnexus-audit-summary.md → A1–A8 → audit.report.md
