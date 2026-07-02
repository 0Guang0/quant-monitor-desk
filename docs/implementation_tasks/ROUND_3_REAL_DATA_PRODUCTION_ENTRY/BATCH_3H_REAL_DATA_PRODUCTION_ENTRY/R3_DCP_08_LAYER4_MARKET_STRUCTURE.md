# R3-DCP-08 — Layer4 市场结构 + US 日历绑真源（最小竖切）

> **规划 ID：** R3-DCP-08  
> **Wave：** 4d · **并行轨 0708-B**  
> **Trellis：** `.trellis/tasks/wave4-r3-dcp-08-layer4/` · Plan v4.1 · debt-lite  
> **Module：** G4 Layer4 markets · C1 registry（mootdx/eastmoney 口径）  
> **评级：** G4 `R3→R4`  
> **前置：** R3H-07 ✅ · R3-DCP-05 ✅ · R3-DCP-06 ✅  
> **分支：** `feature/wave4-r3-dcp-08-layer4`  
> **Worktree：** `../quant-monitor-desk-wt-dcp08`  
> **状态：** 🟢 DONE · Repair 关账 @ R3-DCP-08

---

## 1. Goal（人话）

Layer4 市场结构目前 **US 日历**已有 R3H-07，但市场快照仍主要靠 staged fixture。本票让 **一个** `market_id`（建议 `US_EQ` 或 `CN_A` P0）从 **Tier A clean / 真日历** 读入 → 产出 market structure snapshot → pytest 绿；并承接 registry 台账中 mootdx dry-run 路由与东财口径文档化（**不关** `R3-B2.75-REQ2-EM` 真网 hist）。

---

## 2. 价值

- Wave 4 主线：G4 最小竖切
- 台账承接：`ACC-EASTMONEY-TAXONOMY-001`（registry notes + 产品路径 SSOT）、`ACC-MOOTDX-DRYRUN-ROUTE-001`（dry-run 与真跑路由一致）
- 承接 `ACC-LAYER-E2E-LIVE-001` **L4 子集**

---

## 3. 约束

| 约束 | 要求 |
| ---- | ---- |
| 输入 SSOT | Tier A clean + `TradingCalendar`（R3H-07）；禁止 staged 冒充 PASS |
| 金路径 | MarketAdapter → breadth/snapshot builder → lineage |
| 真网 | 默认 replay；live env-gate + 隔离库 |
| Schema | 无新 migration 除非 Plan 审计 + ADR 证明必需 |
| 范围 | **一个** market_id P0 竖切 |
| REQ2-EM | **禁止** 用本票关闭 Eastmoney hist 真网（硬约束 §3） |
| 参考项目 | L1/L2/L3 **仅** `参考项目/**` |
| Registry | mootdx/eastmoney 改动 → 主会话排队 merge |

---

## 4. 架构触点

```text
Tier A clean + US TradingCalendar (R3H-07)
        ↓
MarketAdapter（US_EQ 或 CN_A P0）
        ↓
MarketSnapshotBuilder → lineage
        ↓
replay e2e pytest
```

**设计权威：** `docs/modules/layer4_market_structure.md` · `backend/app/layer4_markets/`

---

## 5. Acceptance criteria

- [x] 一个 P0 `market_id` 从 clean/日历读入并产出可断言 market snapshot
- [x] `tests/test_layer4_*_clean_e2e.py`（或等价）GREEN
- [x] `ACC-MOOTDX-DRYRUN-ROUTE-001`：dry-run `selected_source_id` 与 `--source-id mootdx` 真跑路由一致（registry reconcile 或 runtime 对齐，Plan 定案）
- [x] `ACC-EASTMONEY-TAXONOMY-001`：capabilities/registry notes 更新（**不关** REQ2-EM）
- [x] `ACC-LAYER-E2E-LIVE-001` L4 子集关账
- [x] `research/reference-adoption-dcp08.md` 含参考项目 L1/L2/L3
- [x] Plan v4.1 包齐；`validate-plan-freeze` exit 0
- [x] `uv run pytest -q` exit 0

---

## 6. 非目标

- 全部 8 个 market_id 一次落地
- Eastmoney `stock_zh_a_hist` 真网 hist（Batch 6 REQ2）
- L3/L5 全链
- FRED live primary

---

## 7. Trellis 入口

`.trellis/tasks/wave4-r3-dcp-08-layer4/research/00-EXECUTION-ENTRY.md`（Plan 产出）
