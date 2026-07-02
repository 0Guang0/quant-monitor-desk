# R3-DCP-08 Plan Doubt Review

> Phase 5c · doubt-driven-development

---

## Cycle 1 — P0 market_id 选型（US_EQ vs CN_A）

| 步骤 | 内容 |
|------|------|
| **CLAIM** | 活卡建议 `US_EQ` 或 `CN_A`；须定一个 P0 |
| **EXTRACT** | US：R3H-07 已接线 · Tier A `us_equity_daily_bar` clean · 022 US 测已有。CN：mootdx/baostock clean · cn calendar · registry 债更直接 |
| **DOUBT** | CN_A 是否更贴合 mootdx registry 片？活卡架构图写「US TradingCalendar (R3H-07)」是否暗示 US_EQ？ |
| **RECONCILE** | registry 片（S08-REG-*）与 L4 竖切 **正交**：mootdx/eastmoney 属 `cn_equity_daily_bar` 域，可在 US_EQ L4 完成同时关 ACC-MOOTDX/EM。**活卡 §4 架构** 明确 R3H-07 US 日历为输入 SSOT → **定案 US_EQ** |
| **STOP** | actionable → ADR-033 |

**分类：** actionable · 已定案 **US_EQ**

---

## Cycle 2 — registry mootdx primary 是否替换 baostock

| 步骤 | 内容 |
|------|------|
| **CLAIM** | ACC-MOOTDX 关账条件写「mootdx 升为 primary」 |
| **EXTRACT** | 当前 domain primary=baostock；mootdx validation_only；runtime hack 提升 validation_only |
| **DOUBT** | 全局 primary 改 mootdx 会破坏 baostock 产品路径 |
| **RECONCILE** | **双轨语义**：domain default primary 保持 baostock；`--source-id mootdx` 时 effective primary=mootdx（registry notes + dry-run JSON 显式 `selected_source_id=mootdx`）；mootdx `validation_only: false` 仅当 enabled 且 explicit sync |
| **STOP** | registry_proposed_delta.yaml + ADR-033 §registry |

**分类：** actionable · trade-off documented

---

## Cycle 3 — breadth 聚合是否需 sector/index

| 步骤 | 内容 |
|------|------|
| **CLAIM** | 设计文档 §5 含 index/sector 表 |
| **EXTRACT** | 活卡 AC 仅「market snapshot」+ breadth；022 仅 breadth+calendar |
| **DOUBT** | 是否 scope creep |
| **RECONCILE** | ponytail：仅 breadth+calendar；index/sector → Wave 5+ |
| **STOP** | 非目标确认 |

**分类：** noise · 已排除

---

## Cycle 4 — 新 migration 是否必需

| 步骤 | 内容 |
|------|------|
| **CLAIM** | clean read 可能需要新表 |
| **EXTRACT** | `security_bar_1d` 已存在（DCP-05）；market_* 表 022 未写 DB |
| **DOUBT** | migration 015+ 是否还要加 |
| **RECONCILE** | 本票 **read-only** 聚合 + 内存 snapshot；**无新 migration** |
| **STOP** | ADR-033 |

**分类：** actionable · 无 migration

---

## 汇总

| 分类 | 计数 |
|------|------|
| actionable | 3（均已 reconcile） |
| trade-off | 1（mootdx 双轨 primary） |
| noise | 1 |
