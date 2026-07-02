# R3-DCP-08 — `/to-issues` 垂直切片

> **SSOT：** 切片 AC 仅本文件 · Plan v4.1  
> **P0 market_id：** `US_EQ`  
> **依赖：** R3H-07 ✅ · R3-DCP-05 ✅ · R3-DCP-06 ✅

---

## 垂直切片规则

1. 每片 tracer-bullet：单职责；可独立 pytest 绿。
2. RED → GREEN 证据：`research/execute-evidence/s08-NN-red.txt` → `s08-NN-green.txt`
3. registry 三件套：**S08-REG-* 主会话 merge**（本轨仅 `registry_proposed_delta.yaml`）
4. staged 022 测 **不得** 回归红

---

## 依赖图

```text
S08-BOOT (clean e2e support + catalog)
  → S08-READ (CleanBreadthReader / calendar row)
  → S08-ADAPTER (USEquityCleanMarketAdapter)
  → S08-BUILD (MarketStructureBuilder tier_a_clean 入口)
  → S08-E2E (test_layer4_us_equity_clean_e2e.py)
  ∥ S08-REG-MOOTDX (dry-run 路由 + registry delta)
  ∥ S08-REG-EM (eastmoney taxonomy notes — 不关 REQ2-EM)
  → S08-L4-E2E-LEDGER (ACC-LAYER-E2E-LIVE-001 L4 子集证据)
  → S08-CLOSE (loop_maintain + validate-execute-handoff)
```

---

## 切片总表

| Slice | What to build | Acceptance criteria | Blocked by | 测试 / 证据 |
|-------|---------------|---------------------|------------|-------------|
| **S08-BOOT** | `tests/layer4_clean_e2e_support.py`；`test_catalog.yaml` 登记 | bootstrap sandbox DB + seed US bars 可复用 | — | support import 绿 |
| **S08-READ** | `layer4_markets/clean_read.py`：从 `security_bar_1d` 聚合 breadth；calendar 行来自 `us_trading_calendar` | 单元测：已知 bar 集 → advancers/decliners 可断言 | S08-BOOT | `test_layer4_clean_read.py` |
| **S08-ADAPTER** | `USEquityCleanMarketAdapter`：`load_calendar` / `load_breadth` | adapter 仅读 clean + SSOT；不写 clean | S08-READ | adapter 单测 |
| **S08-BUILD** | `MarketStructureBuilder.build(..., source_mode="tier_a_clean")`；lineage `source_dataset_ids` 含 clean 表名 | staged 路径不变；022 全绿 | S08-ADAPTER | `test_layer4_market_structure.py` 全绿 |
| **S08-E2E** | `tests/test_layer4_us_equity_clean_e2e.py` | US_EQ 从 replay clean 读入；`source` 不含 `staged_fixture`；breadth 可断言 | S08-BUILD | e2e pytest 绿 |
| **S08-REG-MOOTDX** | `registry_proposed_delta.yaml` + `sync_mootdx_incremental` dry-run `selected_source_id==mootdx` | **ACC-MOOTDX-DRYRUN-ROUTE-001** 关账；去掉 runtime `validation_only` hack（registry 反映后） | S08-BOOT | `test_qmd_data_sync_tier_a_router.py` 扩展 |
| **S08-REG-EM** | eastmoney capabilities/registry notes + ops 产品路径 SSOT | **ACC-EASTMONEY-TAXONOMY-001** 部分关账；**不关** `R3-B2.75-REQ2-EM` | — | `rg ACC-EASTMONEY specs/datasource_registry/` |
| **S08-L4-E2E-LEDGER** | `research/l4-e2e-live-evidence.md` 绑定 ACC-LAYER-E2E-LIVE-001 L4 | L4 子集 [x]：US_EQ clean→snapshot→lineage | S08-E2E | 证据 md + pytest |
| **S08-CLOSE** | `loop_maintain` · `validate-execute-handoff` | 全量 `uv run pytest -q` exit 0 | 全部 | execute-evidence |

---

## 台账承接映射

| 台账 ID | 切片 | 关账方式 |
|---------|------|----------|
| `ACC-MOOTDX-DRYRUN-ROUTE-001` | S08-REG-MOOTDX | registry delta + dry-run JSON 对齐 + 测绿 |
| `ACC-EASTMONEY-TAXONOMY-001` | S08-REG-EM | notes/ops 文档；**不关** REQ2-EM |
| `ACC-LAYER-E2E-LIVE-001` L4 | S08-L4-E2E-LEDGER + S08-E2E | L4 US_EQ clean e2e 证据 |

---

## Issue 骨架

```markdown
### [S08-E2E] US_EQ Tier A clean → Layer4 breadth snapshot

**What:** CleanMarketAdapter + e2e pytest
**AC:** test_layer4_us_equity_clean_e2e green; no staged_fixture in source fields
**Blocked by:** S08-BUILD
**Verify:** uv run pytest tests/test_layer4_us_equity_clean_e2e.py -q
```
