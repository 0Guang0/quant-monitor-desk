# Project Overview — R3H-04（Plan 1a）

> ≤1 页 · GitNexus 轻量概览

## 模块锚点

| 区域 | 现状 | R3H-04 动作 |
| --- | --- | --- |
| `fetch_ports/kalshi_port.py` | **不存在** | 新建 mock/replay port |
| `fetch_ports/polymarket_port.py` | **不存在** | 新建 mock/replay port |
| `fetch_ports/web_search_evidence_port.py` | **不存在** | 新建 evidence-only port |
| `normalizers/probability_signal.py` | **不存在** | 新建 SSOT normalizer |
| `evidence/manual_review_staging.py` | **不存在** | 新建 staging 桥接 |
| `layer5_evidence/foundation.py` | 存在 | smoke 消费方；只读 |
| `normalizers/evidence_bundle.py` | 存在 | `finalize_bundle` / `reject_over_cap` 复用 |
| registry 三源 | `proposed_disabled_source` | → `READY_WITH_EVIDENCE` 或 ADR |

## 数据流（目标）

```text
FetchRequest → *_port.py (mock/replay)
  → probability_signal.py / web evidence bundle
  → manual_review_staging.py (web_search only)
  → route_planner evidence-only route
  → Layer5 foundation (need_human_review for web)
```

## 并行冲突面

- 共享：`source_registry.yaml`、`source_capabilities.yaml`、`source_route_contract.yaml`、`contract_coverage.yaml`、`test_catalog.yaml`
- **只改** kalshi / polymarket / web_search 行
- 与 R3H-03 无 adapter 文件重叠

## 参照模式

- Port 模式：`coingecko_port.py` / `fred_port.py`（R3H-01/02）
- Evidence：`evidence_bundle.finalize_bundle`
- Route 负例：R3H-02 validation-only / clean-write block 测试风格
