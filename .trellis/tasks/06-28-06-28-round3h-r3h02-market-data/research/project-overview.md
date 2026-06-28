# Project Overview — R3H-02（Plan 1a）

> GitNexus `query("market data fetch port yahoo route planner")` · 2026-06-28

## 模块地图（与本任务相关）

| 区域                    | 路径                                                  | 现状                                          |
| ----------------------- | ----------------------------------------------------- | --------------------------------------------- |
| Fetch ports（官方宏观） | `backend/app/datasources/fetch_ports/fred_port.py` 等 | R3H-01 已交付；**本任务参照模式**             |
| Fetch ports（市场）     | `fetch_ports/alpha_vantage_port.py` 等                | **缺失**                                      |
| Adapters skeleton       | `adapters/yahoo_finance.py`                           | SkeletonAdapterBase；仅 `us_equity_daily_bar` |
| Normalizers             | `normalizers/official_macro.py`                       | R3H-01 SSOT；**无 market_data/crypto**        |
| Route                   | `route_planner.py`, `capability_registry.py`          | 生产路由；五源待 READY 测                     |
| Resource guard          | `core/resource_guard.py`                              | 已有；须接 market caps                        |
| 3G pilot                | `rehearsal_loader.py` yahoo bundle                    | bars.json 与 baostock 共享形状                |
| Staged pilot            | `staged_pilot.py`, `limited_production_entry.py`      | yahoo 在 validation 列表                      |

## 五源 registry 快照

| source_id     | default_role | validation_only | capabilities.status |
| ------------- | ------------ | --------------- | ------------------- |
| alpha_vantage | Primary      | false           | proposed_disabled   |
| stooq         | Validation   | true            | proposed_disabled   |
| yahoo_finance | Validation   | true            | 有 operations 定义  |
| deribit       | Primary      | false           | proposed_disabled   |
| coingecko     | Validation   | true            | proposed_disabled   |

## 3H 目标数据流

```text
FetchPort (mock/replay default)
  → market_data_evidence_v1 / crypto_market_evidence_v1
  → route_planner READY|DISABLED
  → registry notes: READY_WITH_EVIDENCE
  → Layer2/L4/L5 smoke（非 R3H-05）
```

## 开放 gap（路线图）

- G2 交易日窗：自然日 cap（本卡 ponytail）；完整 SSOT → R3H-03
- G16 yahoo live-wire：本卡 replay-first 闭合；live 为 optional
- G13 validation 写 clean：保持 validation-only 语义

**Phase 1a complete**
