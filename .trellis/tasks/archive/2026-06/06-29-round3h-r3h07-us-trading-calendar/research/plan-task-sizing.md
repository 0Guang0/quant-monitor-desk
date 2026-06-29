# Plan 加固 — planning-and-task-breakdown

> **Skill:** `planning-and-task-breakdown` · **日期：** 2026-06-29

## 依赖图

```text
S07-BOOT（基线矩阵 + RED）
  └→ S07-01 ─┬→ S07-02 ─┐
             └→ S07-03 ─┴→ S07-04 → S07-CLOSE
```

**串行：** S07-02 与 S07-03 可并行（不同文件组），但 S07-04 需两者 GREEN。

---

## 任务规模评估

| 切片      | 规模   | 触达文件                                            | 风险                |
| --------- | ------ | --------------------------------------------------- | ------------------- |
| S07-BOOT  | **XS** | 矩阵 md + 1 RED 测                                  | 低                  |
| S07-01    | **S**  | `us_trading_calendar.py` + 新测                     | 低 — 镜像 CN        |
| S07-02    | **M**  | 3 ports + `fetch_window` + normalizer 调用 + 契约测 | **中** — 多源一致性 |
| S07-03    | **S**  | `market_structure.py` + fixture + layer4 测         | 中                  |
| S07-04    | **S**  | 负向测 + CN 回归                                    | 中 — 假日边界       |
| S07-CLOSE | **XS** | audit/registry                                      | 低                  |

---

## Checkpoint

| CP       | 完成后          | 验证                                    |
| -------- | --------------- | --------------------------------------- |
| **CP-1** | BOOT + S07-01   | 日历模块测绿；矩阵 OPEN≤8               |
| **CP-2** | S07-02 + S07-03 | US `trading_sessions` + layer4 假日拒绝 |
| **CP-3** | S07-04 + CLOSE  | CAL-US CLOSED · 全量 pytest             |

---

## 风险与缓解

| 风险                     | 缓解                                         |
| ------------------------ | -------------------------------------------- |
| 只改 yahoo 不改 stooq/AV | 切片 AC 点名三源；矩阵行 1–3                 |
| CN 日历回归              | 专用回归测 + 禁止改 `cn_trading_calendar`    |
| R3H02 测翻转破坏 replay  | 先 RED 再 GREEN；replay fixture 加交易日过滤 |
| 2030+ 假日精度           | ponytail + ADR-026；不阻塞 CAL-US            |

---

## planning-and-task-breakdown 验证清单

- [x] 每切片有验收标准
- [x] 每切片有验证命令
- [x] 依赖顺序正确
- [x] 无 XL 单片
- [x] Checkpoint 已定义
