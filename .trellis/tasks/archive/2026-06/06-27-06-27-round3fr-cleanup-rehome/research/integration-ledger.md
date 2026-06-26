# Integration Ledger — R3FR-07

> Phase 5c · 文件触达与合并协调

## 分支

`chore/round3fr-cleanup-rehome`（自 `master`）

## 允许修改（Execute）

| 路径                                                                                                                  | 理由                                  |
| --------------------------------------------------------------------------------------------------------------------- | ------------------------------------- |
| `backend/app/ops/data_health.py`                                                                                      | `check_daily_bars` redirect/DRY       |
| `backend/app/cli/data_commands.py`                                                                                    | `health_check` 注释                   |
| `backend/app/ops/interface_probe_fetch_ports.py`                                                                      | TDX delegate 注释                     |
| `backend/app/ops/tdx_manual_probe.py`                                                                                 | 编排边界注释                          |
| `tests/test_r3fr07_legacy_wrapper_cleanup.py`                                                                         | 新建 AC 测试                          |
| `tests/test_reference_adoption_guardrails.py`                                                                         | 扩展 3F-R close 断言                  |
| `docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/**`                                                    | manifest/README redirect              |
| `docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/README.md`                        | 解除 3F-R 阻塞表述                    |
| `PROJECT_IMPLEMENTATION_ROADMAP.md`                                                                                   | 3F-R CLOSED / 3G next                 |
| `docs/ROUND3_HANDOFF.md`                                                                                              | 同步 handoff                          |
| `MODULE_COMPLETION_RATING.md`                                                                                         | provider catalog rating               |
| `ROUND3_BATCH_IMPLEMENTATION_MAP.md`                                                                                  | checkpoint 行                         |
| `docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/BATCH_3G_COORDINATOR_PLAYBOOK.md` | §0 门禁措辞                           |
| `docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/BATCH_3G_TASK_CARD_MANIFEST.md`   | 3G 结构参照                           |
| `tests/test_catalog.yaml`                                                                                             | 经 `loop_maintain --fix` 登记新测模块 |
| `.trellis/tasks/06-27-06-27-round3fr-cleanup-rehome/**`                                                               | 本任务证据                            |

## 禁止修改

| 路径                                                                | 理由                        |
| ------------------------------------------------------------------- | --------------------------- |
| `specs/datasource_registry/source_registry.yaml` 等 registry 三件套 | 无 registry reconcile scope |
| `backend/app/datasources/fetch_ports/tdx_pytdx_port.py`             | R3FR-03 已结案              |
| `backend/app/ops/data_health_profiles/**` 行为扩展                  | 非新 profile scope          |
| `.trellis/tasks/archive/**` 删除                                    | 证据保留                    |
| `参考项目/**`                                                       | 禁止 runtime import         |

## 合并门

1. 任务卡 §5 targeted pytest 绿
2. `uv run pytest -q` 全绿
3. `uv run python scripts/loop_maintain.py` exit 0
4. `validate-execute-handoff` exit 0（Execute 末）
5. 主会话合并 `master`；**之后** 才开 3G

## 并行

**无。** R3FR-07 单分支串行；registry 无需协调者（本任务不改 registry）。
