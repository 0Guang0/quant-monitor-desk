# Project Overview — Round 3 Batch 2 Layer 1 (≤1 page)

> Phase 1a · GitNexus/Codegraph 轻量概览 · 2026-06-20

## 当前代码基线

| 区域                             | 状态                                                        |
| -------------------------------- | ----------------------------------------------------------- |
| `backend/app/layer1_axes/`       | 仅 `__init__.py` 占位                                       |
| `configs/layer1_axes.yml`        | 已存在：`spec_root` + 五轴 enabled 列表                     |
| Layer 1 DuckDB 表                | **未迁移** — 设计 DDL 在 `layer1_global_regime_panel.md` §6 |
| `validation_report.rule_version` | migration 008 已加 — lineage consumer 前置闭合              |
| Batch 1 inspect CLI              | archived PASS — DB 只读证据已就绪                           |

## 本批实现焦点

```text
specs/layer1_axes/restructured_axes_v1_1/**
        ↓ AxisSpecLoader (017)
axis_registry / axis_indicator_registry / axis_indicator_profile
        ↓ fixture or staged axis_observation (测试)
AxisFeatureEngine → axis_feature_snapshot (018)
        ↓
AxisInterpretationEngine → axis_interpretation_snapshot (018)
        ↓ lineage envelope (R3-EARLY-LINEAGE-CONSUMERS)
DuckDBWriteManager (clean snapshot tables)
```

## 关键依赖（只读理解）

- **WriteManager：** 所有 clean 表写入必经 `DuckDBWriteManager` + `validation_report_id`
- **DataQualityValidator：** 已写入 `rule_version`、`source_fetch_ids_json` — 快照应引用
- **ResourceGuard：** 特征计算默认 eco；禁止全历史无界窗口扫描
- **契约：** `layer1_axis_contract.yaml` 字段与 `forbidden_output_terms`；`snapshot_lineage_contract.yaml` 必填 lineage 字段

## 风险 / 注意

1. 任务卡路径 `backend/layers/` 与仓库 `backend/app/layer1_axes/` 不一致 — MASTER 已纠偏
2. 五轴 YAML 体量大 — Execute 按 spec 解析，Plan 不内嵌全文
3. 本批**不**实现 FastAPI `/api/layer1/*`（Round 4）或全量 `Layer1AxisFetcher` 生产调度
4. FORBIDDEN / BlindSpot 指标：登记 registry，**不**进入 observation（设计 §13）

## 前置 gate

- Batch 1: `06-20-round3-batch1-early-ops` audit PASS
- Round 2.6: contract + routing service gate archived PASS
