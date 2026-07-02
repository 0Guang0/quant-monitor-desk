# Plan Context — R3-DCP-10

## Context Hierarchy L1–L5 映射

| Level | 本任务 |
| --- | --- |
| L1 全局 | Wave 4 G5 · ACC-LAYER-E2E G5 子集 |
| L2 模块 | Layer5 evidence · A3 storage/evidence |
| L3 源码 | `layer5_evidence/` · `evidence_bundle.py` · `mootdx_port.py` |
| L4 切片 | S01 bridge · S02 e2e |
| L5 情境 | 改 provenance → ENTRY §5.3 |

## PROJECT CONTEXT（Execute 可复制）

```text
任务：R3-DCP-10 Layer5 绑真源
P0：cn_equity_daily_bar / mootdx / sh.600519 / security_bar_1d
前置：DCP-05 ✅ · R3H-08 env-gate ✅
禁止：staged provenance 占位 · bypass WriteManager · 参考项目 runtime
ADR-031 provenance mapping
测试：先 RED test_layer5_provenance_bridge → test_layer5_mootdx_bar_clean_e2e
```

## Level 3 源码表

| 模块 | 路径 | 切片 |
| --- | --- | --- |
| Provenance bridge | `layer5_evidence/provenance.py` | S01 |
| Bundle helper | `normalizers/evidence_bundle.py` | S01 |
| CN market | `normalizers/cn_market.py` | S02 |
| Mootdx port | `fetch_ports/mootdx_port.py` | S02 只读 |
| Incremental | `ops/mootdx_incremental_run.py` | S02 只读 |
| Foundation | `layer5_evidence/foundation.py` | S02 |
| Lineage | `layer5_evidence/lineage.py` | S02 |
| Raw store | `storage/raw_store.py` | S02 只读 |
| E2E precedent | `tests/test_mootdx_incremental_e2e.py` | S02 模板 |

## 开工必读 vs 情境路由

| 类型 | 路径 |
| --- | --- |
| 开工必读 | ENTRY §5.2 = §5.1 + EXTERNAL §A + ADR-031 |
| 改 mapping | `reference-adoption-dcp10.md` §4 · ADR-031 |
| 改 e2e | `to-issues-slices.md` S02 · `incremental_mootdx_support.py` |
| 台账 | `待修复清单.md` ACC-LAYER-E2E · S03 |

与 `00-EXECUTION-ENTRY.md` §5.2/§5.3 对齐。
