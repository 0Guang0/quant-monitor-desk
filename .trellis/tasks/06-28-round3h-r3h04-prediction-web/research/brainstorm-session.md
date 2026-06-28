# Brainstorm Session — R3H-04（Plan 2a）

## 方案草图

| 选项 | 描述 | 结论 |
| --- | --- | --- |
| A | 单文件 `prediction_adapter.py` 藏三源 | **否决** — 违反 per-source auth/cap/evidence |
| B | kalshi + polymarket 共用 `probability_signal` | **采纳** |
| C | web_search 复用 macro evidence normalizer | **否决** — 输出类型不同（manual_review） |
| D | 新建 `manual_review_staging` 模块 | **采纳** — 与 layer5 对齐 |
| E | 直接扩 `official_macro` normalizer | **否决** — 语义污染 |

## prd 薄索引指向

`prd.md` → frozen + EXECUTION_INDEX
