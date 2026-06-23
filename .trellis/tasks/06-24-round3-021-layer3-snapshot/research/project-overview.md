# Project overview — 021 Layer3 snapshot builder (Plan 1a)

> GitNexus 轻量概览 · ≤1 页

## 模块定位

- **包：** `backend/app/layer3_chains/`（已有 `loader.py` + `models.py`）
- **职责：** staged loader 结果 + staged L5 bars → daily snapshot 行 + mapping view + lineage envelope
- **非职责：** live L5 ingest、L4 lineage、registry 写、API/CLI

## 020 输出（须复用）

`IndustryChainLoader.load()` → `IndustryChainLoadResult`（chains/anchors/nodes/edges）

## 019/020 模式（须复用）

- L2 `CrossAssetSnapshotBuilder` — as_of 过滤、lineage builder、ResourceGuard 形态
- L2 `Layer2LineageBuilder` — `core/snapshot_lineage.py` kernel
- L3 loader — `staged_fixture_only` bundle manifest

## 契约锚点

`snapshot_lineage_contract.yaml`：

- required_fields（D-09：Layer3 不复制 Layer1 全套，仅 contract 子集）
- `no_future_data`、`validation_tests` 三名

## 风险

| 风险                    | 缓解                          |
| ----------------------- | ----------------------------- |
| 误做 live L5 fetch      | staged L5 manifest + AC-021-6 |
| 越界关 ADV-R3X 全量项   | §3.2 register + 停止条件 #7   |
| scope 漂移到 layer2/4/5 | slice forbidden 列表          |

## Blast radius（Plan 预估）

- 新建 `snapshot_builder.py`；caller 仅 tests
- 参考只读：`layer2_sensors/snapshot_builder.py`、`loader.py`
