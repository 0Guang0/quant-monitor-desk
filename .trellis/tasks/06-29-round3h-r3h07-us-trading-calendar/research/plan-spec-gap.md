# Plan 加固 — spec-driven-development

> **Skill:** `spec-driven-development` · **任务：** R3H-07 · **日期：** 2026-06-29

## ASSUMPTIONS

1. R3H-10 CLOSED — fetch 金路径经 `DataSourceService`。
2. 无新 migration；US 日历 in-memory frozenset（ADR-026）。
3. crypto 源维持 `calendar_days`。
4. CN `cn_trading_calendar` 不回退。

---

## 六要素覆盖

| 要素                  | 状态 | SSOT                                                                         |
| --------------------- | ---- | ---------------------------------------------------------------------------- |
| **Objective**         | ✅   | 活卡 §1 · INDEX §2                                                           |
| **Commands**          | ✅   | 见下                                                                         |
| **Project Structure** | ✅   | `ops/data_health_profiles/` · `datasources/fetch_ports/` · `layer4_markets/` |
| **Code Style**        | ✅   | ponytail · 镜像 CN 模块                                                      |
| **Testing Strategy**  | ✅   | TDD RED→GREEN · `execute-evidence/9.x-*.txt`                                 |
| **Boundaries**        | ✅   | 见下                                                                         |
| **Success Criteria**  | ✅   | `to-issues-slices.md` + INDEX §2                                             |

---

## Commands

```bash
uv run pytest -q
uv run pytest -q tests/test_market_data_adapters.py tests/test_layer4_market_structure.py
uv run pytest -q tests/test_cn_market_adapters.py -k calendar
python .trellis/scripts/task.py validate-plan-freeze .trellis/tasks/06-29-round3h-r3h07-us-trading-calendar
```

---

## Boundaries

| 层级          | 内容                                                      |
| ------------- | --------------------------------------------------------- |
| **Always**    | 每切片后全量 pytest；改 ports 前 GitNexus `impact`        |
| **Ask first** | 扩 US 日历 beyond 2030；新 DDL；改 CN 日历                |
| **Never**     | 万年历扫描；per-source 假日表；crypto 改 trading_sessions |

---

## Open Questions

| ID     | 项                       | 裁决                                                             |
| ------ | ------------------------ | ---------------------------------------------------------------- |
| ~~U1~~ | US 权威 NYSE vs NASDAQ   | **[x]** ADR-026 合并 frozenset                                   |
| ~~U2~~ | Layer4 US_EQ 范围        | **[x]** 仅 calendar 绑定 + 假日拒绝；`L4-US-DEFERRED` 不全量开放 |
| ~~U3~~ | R3H02 `calendar_days` 测 | **[x]** S07-02 翻转至 `trading_sessions`                         |

---

## spec-driven-development 验证清单

- [x] 六要素已扫描
- [x] 成功标准可测
- [x] Boundaries 三档
- [x] Open Questions 已裁决（ADR-026）
