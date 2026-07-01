# Plan doubt review — R3-DCP-05

## Doubt cycle

| #   | CLAIM                    | DOUBT              | RECONCILE                                           | 分类                            |
| --- | ------------------------ | ------------------ | --------------------------------------------------- | ------------------------------- |
| D1  | 11/11 必须 clean 写入    | 缺表怎么办？       | ADR-028 migration 015 + 扩 BAR/MACRO 域             | **actionable** — 已接受         |
| D2  | debt-lite 够吗？         | 8D.1 禁 migration  | 用户裁决 + schema → **complex v4.1**                | **actionable**                  |
| D3  | 每源只做一个 domain？    | alpha 有 7 domains | ADR-028 canonical 表；其余域后续波次                | **trade-off** — 已文档化        |
| D4  | 复制 5 份 macro run？    | 维护成本           | ponytail：第三份后抽 `macro_incremental_base`       | **trade-off**                   |
| D5  | mootdx validation_only？ | 为何 Tier A 增量？ | `live_tier_router` Tier A；registry 角色≠增量试点域 | **noise** — 已澄清              |
| D6  | OpenBB 能否 L1 拷贝？    | license            | architecture_only → L3 对齐 only                    | **actionable** — forbidden copy |

## STOP

无未 reconciled 的 blocking doubt。Plan 可冻结。

## 用户决策记录

- **2026-07-02：** 11/11 全 clean 写入 — 拒绝 staging-only ponytail。
