# Project Map Omission Check — R3FR-07

> Plan 对抗性审计 ADV-07-23 · 倒查 cleanup targets 是否全部进入 Execute 路由

## 活任务卡 §3 / cleanup targets 对照

| 路径                                             | EXECUTION_INDEX §3                        | integration-ledger | 步骤    |
| ------------------------------------------------ | ----------------------------------------- | ------------------ | ------- |
| `backend/app/ops/data_health.py`                 | runtime（非 manifest）                    | 允许               | 9.2     |
| `backend/app/cli/data_commands.py`               | runtime                                   | 允许               | 9.3     |
| `backend/app/ops/interface_probe_fetch_ports.py` | runtime                                   | 允许               | 9.4     |
| `backend/app/ops/tdx_manual_probe.py`            | runtime                                   | 允许               | 9.4     |
| `docs/implementation_tasks/README.md`            | must-read                                 | 允许               | 9.1/9.5 |
| `BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/*.md`     | 双 README + MANIFEST must-read            | 允许               | 9.1     |
| `BATCH_3G_SANDBOX_CLEAN_WRITE/*.md`              | README + MANIFEST + COORDINATOR must-read | 允许               | 9.5     |
| `PROJECT_IMPLEMENTATION_ROADMAP.md`              | must-read                                 | 允许               | 9.5     |
| `MODULE_COMPLETION_RATING.md`                    | must-read                                 | 允许               | 9.5     |
| `ROUND3_BATCH_IMPLEMENTATION_MAP.md`             | must-read                                 | 允许               | 9.5     |
| `docs/ROUND3_HANDOFF.md`                         | must-read                                 | 允许               | 9.5     |

## 契约 / ops（CLI cleanup 必读）

| 路径                                      | §3        |
| ----------------------------------------- | --------- |
| `specs/contracts/data_cli_contract.yaml`  | must-read |
| `docs/ops/data_health_cli.md`             | must-read |
| `specs/contracts/data_quality_rules.yaml` | must-read |

## 归档 replacement 证据（只读）

| 路径                                                                               | §3               |
| ---------------------------------------------------------------------------------- | ---------------- |
| `archive/.../06-26-round3fr-data-health-cli/research/execute-evidence-summary.md`  | execute-required |
| `archive/.../06-26-round3fr-tdx-provider/research/execute-evidence-summary.md`     | execute-required |
| `archive/.../06-26-round3fr-provider-catalog/research/execute-evidence-summary.md` | execute-required |

## 遗漏闭合

**无未登记 cleanup target。** 修复前遗漏项已写入 `EXECUTION_INDEX.md` §3 并 `generate-manifests`。

## 故意不列入 §3

| 路径                                              | 理由                    |
| ------------------------------------------------- | ----------------------- |
| `docs/implementation_tasks/.../R3FR_07_*.md` 活卡 | v4：Execute 只读 frozen |
| `参考项目/**`                                     | 本任务禁止 runtime 采纳 |
