# Brainstorm — R3H-06（Plan 2a）

## 方案对比

| 方案 | 描述                                              | 裁决                               |
| ---- | ------------------------------------------------- | ---------------------------------- |
| A    | 单 migration 013 含 bar + disclosure；**无 VIEW** | **采纳** @ 用户 2026-06-29         |
| B    | 013 bar + 014 disclosure 拆文件                   | 备选 — 仅当 013 review 过大        |
| C    | 保留 market_bar_clean 为实体表同步双写            | **否决** — G6 双写风险             |
| D    | 仅 DDL 不改 pilot 路径                            | **否决** — 测无法证 G5             |
| E    | sync orchestrator 默认改全局 clean 表名           | **否决** — 范围过大；先 pilot 路径 |

## 风险表

| 风险                                  | 缓解                                                 |
| ------------------------------------- | ---------------------------------------------------- |
| r3g03 测大面积改                      | **无 VIEW**；分步 9.8 改 `security_bar_1d` + rg 门禁 |
| axis_observation 列不匹配 fred bundle | 9.4 专用 mapper + 契约测                             |
| coordinator 误以为可并行改 schema     | frozen §8 + INDEX 分支锁                             |

**Phase 2a complete**
