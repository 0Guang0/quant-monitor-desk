# Integration Audit — R3H-04（Plan 5d · doubt-driven-development）

> **closure: PASS**（Plan 阶段）

## CLAIM → DOUBT → RECONCILE

| CLAIM | DOUBT | RECONCILE |
| --- | --- | --- |
| 三源可 mock READY | web_search 无真实 API | mock stub + manual_review；Grill-me #1 待用户 |
| 不改 resource_guard | 活卡 §4 列出 resource_guard | BRANCH 边界优先；端口内 cap |
| 不碰 R3H-03 | 共享 registry 文件 | 只改三行 + coordinator manifest |
| probability 共用 normalizer | kalshi vs polymarket 字段差 | 统一 schema + 可选字段 |
| Layer5 smoke 足够 | R3H-05 全层 | 本卡仅 §9.7 smoke；禁止越界 |

## doc-gap

| GAP | 处理 |
| --- | --- |
| 活卡 §4 含 `resource_guard.py` 但 BRANCH 未授权 | frozen §7 注明端口内 cap；Execute 禁止改 resource_guard |
| `manual_review_staging.py` 无先例 | 参照 `layer5_evidence.foundation` 校验契约新建 |

## adversarial 攻击面

1. web_search 路由误选 clean writer → §9.6 负例 + route contract
2. 预测价格字段升格为事实 → schema 禁止字段 + 测试
3. registry 并行覆盖 CN 源 → §9.5 manifest 只列三源
4. OpenBB runtime 混入 → A3 rg 禁止 import

## closure

Plan 可冻结；Execute 未决仅 #1（真实搜索 API）不阻塞 mock-first 路径。
