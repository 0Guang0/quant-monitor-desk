# Phase B3 perf-value-checklist

| 用例/模块                            | 原测试价值                      | 优化手段                        | 价值仍完整 |
| ------------------------------------ | ------------------------------- | ------------------------------- | ---------- |
| `test_initDb_runTwice_isIdempotent`  | 同库二次 apply 空列表；005 一条 | `validation_con` 复用 module db | Y          |
| `test_layer1_ingestion_gates` 扫描族 | 文档/契约文本覆盖               | `_repo_text` lru_cache          | Y          |

| 评估后回滚             | 理由                                                      |
| ---------------------- | --------------------------------------------------------- |
| `plannedJob` bootstrap | 全 suite call 0.96s→1.07s；注释未要求 registry sync_to_db |

全量 pytest：**PASS**（串行，~119s）
