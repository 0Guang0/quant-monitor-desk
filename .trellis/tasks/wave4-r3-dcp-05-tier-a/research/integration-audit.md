# Integration Audit — R3-DCP-05（Plan 5d）

## CLAIM → DOUBT → RECONCILE

| CLAIM                        | DOUBT                         | RECONCILE                                |
| ---------------------------- | ----------------------------- | ---------------------------------------- |
| 11/11 必须 clean 写          | sec_edgar/deribit 无 clean 表 | ADR-028 migration 015 + S00              |
| 复制 fred 模板 5 次          | 宏运行文件膨胀                | ponytail：第三份后抽 shared base         |
| debt-lite 够用               | 8D 禁 migration               | 升格 complex v4.1                        |
| baostock live 仅改 mock 旗标 | 旁路 live-fetch 不一致        | 复用 `build_product_live_service` + gate |

## 六类检查（Plan 期）

| 类   | 状态           | 备注                         |
| ---- | -------------- | ---------------------------- |
| 契约 | PASS_WITH_GAPS | ADR-028 新表；015 待 Execute |
| 测试 | GAP            | 9 源 incremental e2e 待建    |
| 安全 | PASS           | 隔离库 + live gate           |
| 架构 | PASS           | 金路径不变                   |
| 文档 | PASS           | Plan 包齐                    |
| 运维 | PASS           | 东财 SSOT 在 S13             |

## adversarial（对抗性审计）

| 检查项                      | 结果 |
| --------------------------- | ---- |
| plan-doubt-review D1–D6     | PASS |
| 用户 11/11 裁决记入 ADR-028 | PASS |
| 参考 L 梯仅 `参考项目/**`   | PASS |

## doc-gap

| GAP                    | 路由                               |
| ---------------------- | ---------------------------------- |
| migration 015 SQL      | Execute S00                        |
| 9 源 incremental tests | Execute S03–S11                    |
| `context_pack.json`    | Plan 期用既有 baostock/fred 测路径 |

**Phase 5d complete · PASS_WITH_GAPS**
