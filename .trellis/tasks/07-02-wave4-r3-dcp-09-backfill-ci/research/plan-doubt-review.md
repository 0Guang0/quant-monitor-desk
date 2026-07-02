# Plan Doubt Review — R3-DCP-09

## Doubt Cycles

### D1 — 是否需要新 BackfillRunner？

| 项        | 内容                                                         |
| --------- | ------------------------------------------------------------ |
| CLAIM     | 须新产品 runner                                              |
| EXTRACT   | `BackfillShardRunner` 已覆盖分片/断点/validate/write           |
| DOUBT     | 重复造轮子                                                   |
| RECONCILE | **复用**；仅补 CLI + cap 参数                                |
| STOP      | actionable → S01 接 orchestrator                             |

### D2 — Cap 放 CLI 还是 runner？

| 项        | 内容                                                         |
| --------- | ------------------------------------------------------------ |
| CLAIM     | runner 内硬编码 cap                                          |
| EXTRACT   | `plan_backfill_shards` 已纯函数；smoke 直接调用              |
| DOUBT     | runner 改签名冲击面大                                        |
| RECONCILE | cap 在 planner + CLI 校验；runner 吃已截断的 date_end         |
| STOP      | actionable → S00 contract                                    |

### D3 — nightly 放 workflow 还是仅文档？

| 项        | 内容                                                         |
| --------- | ------------------------------------------------------------ |
| CLAIM     | 仅 `docs/ops` 即可满足 AC                                    |
| EXTRACT   | 活卡 §5 要求「CI nightly 配置**或**文档化入口」              |
| DOUBT     | 文档 alone 易漂移                                            |
| RECONCILE | **workflow + docs** 双交付；docs 为本地复现 SSOT             |
| STOP      | actionable → S04                                             |

### D4 — findings 全 fail vs severity 过滤？

| 项        | 内容                                                         |
| --------- | ------------------------------------------------------------ |
| CLAIM     | 任何 finding 都 fail nightly                                 |
| EXTRACT   | live 脚本含 `EXPECTED_DEFER` plan_alignment                    |
| DOUBT     | 政策性 defer 导致 nightly 永红                               |
| RECONCILE | `--fail-on-severity HIGH,CRITICAL`；MEDIUM defer 记 evidence |
| STOP      | actionable → S05                                             |

### D5 — 参考项目树为空？

| 项        | 内容                                                         |
| --------- | ------------------------------------------------------------ |
| CLAIM     | 无法做 L1/L2/L3                                              |
| EXTRACT   | DCP-05 已登记同路径；guardrails 要求 task-local 记录         |
| DOUBT     | Execute 无法 RED 前实读                                      |
| RECONCILE | Plan 登记路径+行号；Execute 须实读或 grill 用户补参考树    |
| STOP      | trade-off · Execute boot 验证                                |

## 分类汇总

| 类型       | 数量 |
| ---------- | ---- |
| actionable | 4    |
| trade-off  | 1    |
| noise      | 0    |
