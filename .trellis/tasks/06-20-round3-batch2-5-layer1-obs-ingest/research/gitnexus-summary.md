# GitNexus Summary — Round 3 Batch 2.5 (Plan 1b)

> 需求锚定深度分析 · defer 自 P0b · 2026-06-20

## 查询焦点

Layer 1 observation ingestion；DataSourceService → pipeline → WriteManager；`axis_observation` clean write。

## 符号与 blast radius（Plan 结论）

| 符号                                             | 风险   | 直接上游/下游                    |
| ------------------------------------------------ | ------ | -------------------------------- |
| `DataSourceService.fetch`                        | HIGH   | orchestrator, runners, tests     |
| `DuckDBWriteManager.write`                       | HIGH   | pipeline, layer1 snapshot writer |
| `SyncValidationPipeline`                         | MEDIUM | orchestrator incremental path    |
| `AxisFeatureEngine` / `AxisInterpretationEngine` | MEDIUM | ingestion Phase 4 快照重建       |
| `layer1_axes/*` (new ingestion)                  | MEDIUM | 仅本批新增；不得 import adapters |

## 推荐实现切点

1. **`backend/app/layer1_axes/ingestion.py`** — `Layer1ObservationIngestionService`：编排 route preview、micro-fetch、observation 映射、调用现有 snapshot 引擎。
2. **复用** `DataSourceService` + `SyncValidationPipeline` 模式，不新建 parallel gold path。
3. **默认 staged**：扩展 `FixtureFetchPort` 或 `macro_supplementary` fixture，避免 Phase 3 默认触网 FRED。

## Execute 前 impact 清单

改前必须 `impact()`：`DataSourceService`, `WriteManager`, `SyncValidationPipeline`, `layer1_axes` 新模块。

## analysis_waiver

`false` — 1b 已产出；Execute 6.pre 须 `gitnexus-execute-summary.md`。
