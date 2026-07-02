# R3-DCP-08 Plan Context Engineering

> Phase 5b · context-engineering

## Context Hierarchy L1–L5 映射

| Level | 本任务内容 |
|-------|------------|
| L1 | 宏观轴（DCP-06 已关）— **不本票范围** |
| L2 | 跨资产（DCP-07 并行轨）— **只读不碰** |
| L3 | 产业链 — **不本票范围** |
| L4 | **本票主战场** — US_EQ market structure |
| L5 | 个股证据 — **边界：不写 L5 历史表** |

## PROJECT CONTEXT（Execute 可复制）

```text
任务：R3-DCP-08 Layer4 US_EQ clean 竖切
分支：feature/wave4-r3-dcp-08-layer4
worktree：quant-monitor-desk-wt-dcp08
P0 market_id：US_EQ
输入：security_bar_1d (Tier A clean) + us_trading_calendar (R3H-07)
输出：market_breadth_snapshot 行 + lineage envelope
台账：ACC-MOOTDX · ACC-EASTMONEY(部分) · ACC-LAYER-E2E L4
硬约束：不关 R3-B2.75-REQ2-EM；registry 主会话 merge
```

## Level 3 源码表

| 模块 | 路径 | Execute 何时读 |
|------|------|----------------|
| Builder | `layer4_markets/market_structure.py` | S08-BUILD |
| Calendar SSOT | `ops/data_health_profiles/us_trading_calendar.py` | S08-READ/ADAPTER |
| Bar incremental | `ops/alpha_vantage_incremental_run.py` | S08-BOOT seed 模式 |
| mootdx sync | `cli/data_commands.py` sync_mootdx_incremental | S08-REG-MOOTDX |
| Registry | `specs/datasource_registry/source_registry.yaml` | S08-REG-* |
| L1 e2e support | `tests/layer1_clean_e2e_support.py` | S08-BOOT 模板 |

## §5.2 开工必读（摘要）

全部 `research/*.md`（除 plan-boot）+ EXTERNAL-INDEX §A + 当前切片 `to-issues-slices.md` §

## §5.3 情境路由（摘要）

| 情境 | 打开 |
|------|------|
| 改 breadth 聚合 | `layer4-tier-a-research.md` · `docs/modules/layer4_market_structure.md` §5.5 |
| 改 US 日历 | ADR-026 · `us_trading_calendar.py` |
| mootdx dry-run | `registry_proposed_delta.yaml` · ACC-MOOTDX §4 |
| eastmoney 口径 | ops `data_sync_quick_reference.md` · **不关 REQ2-EM** |
| 参考项目 | `reference-adoption-dcp08.md` |
