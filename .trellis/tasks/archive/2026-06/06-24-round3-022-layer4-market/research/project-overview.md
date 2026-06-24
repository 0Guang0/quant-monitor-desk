# Project overview — 022 Layer4 market structure (Plan 1a)

> GitNexus 轻量概览 · ≤1 页

## 模块定位

- **包：** `backend/app/layer4_markets/`（当前仅 `__init__.py`）
- **职责：** staged fixture → market registry / calendar / breadth / snapshot 行 + lineage envelope
- **非职责：** Layer5 全量行情、live vendor fetch、API/CLI、registry 写

## 021 上游（只读依赖）

`backend/app/layer3_chains/snapshot_builder.py` — Layer3 日度快照与 lineage 模式；`upstream_snapshot_ids` 可引用 staged L3 snapshot_id。

## L2/L3 模式（须复用）

- `backend/app/layer2_sensors/snapshot_builder.py` + `lineage.py` — as_of 过滤、lineage builder
- `backend/app/core/snapshot_lineage.py` — `LINEAGE_REQUIRED_FIELDS` kernel
- `backend/app/layer3_chains/lineage.py` — Layer3 lineage 形态参考

## 契约锚点

- `specs/contracts/layer4_market_contract.yaml` — 表模型 + quality_rules + boundaries
- `specs/contracts/snapshot_lineage_contract.yaml` — lineage + `no_future_data`
- `docs/modules/layer4_market_structure.md` — MarketAdapter 接口与表 DDL 语义

## 风险

| 风险                         | 缓解                                |
| ---------------------------- | ----------------------------------- |
| live 全市场扫描              | staged fixture + ResourceGuard      |
| 越界改 ops/staged/registry   | MAP §2.2 forbidden + §3.3           |
| 复制 Layer5 大表 / L1 标准化 | contract boundaries + D-09          |
| 声称 production-live         | §0 staged limitations + batch3 gate |

## Blast radius（Plan 预估）

- **新建：** `market_structure.py`（+ 可选 `lineage.py` / `models.py`）
- **caller：** 仅 `tests/test_layer4_market_structure.py`
- **风险：** LOW — 隔离在 `layer4_markets` 包内
