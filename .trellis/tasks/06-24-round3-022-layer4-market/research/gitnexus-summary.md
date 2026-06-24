# GitNexus summary — 022 Layer4 market structure (Plan 1b)

## 符号与流程

| 符号                         | 路径                                              | 说明                                |
| ---------------------------- | ------------------------------------------------- | ----------------------------------- |
| `IndustryChainSnapshotBuilder` | `backend/app/layer3_chains/snapshot_builder.py` | 021 上游；lineage + as_of 模式      |
| `Layer3LineageBuilder`       | `backend/app/layer3_chains/lineage.py`            | layer3 lineage envelope             |
| `CrossAssetSnapshotBuilder`  | `backend/app/layer2_sensors/snapshot_builder.py`  | L2 snapshot 模式参考                |
| `Layer2LineageBuilder`       | `backend/app/layer2_sensors/lineage.py`           | lineage 构建参考                    |
| snapshot lineage kernel      | `backend/app/core/snapshot_lineage.py`            | 共享 required_fields 校验           |
| `DuckDBWriteManager`         | `backend/app/db/write_manager.py`                 | clean 写路径（若触及 DB，只读对照） |

## 影响面（Plan 预估）

- **新建：** `backend/app/layer4_markets/market_structure.py`
- **无现有 upstream caller** — 仅 tests 直接调用
- **风险：** LOW — 隔离在 `layer4_markets` 包内；与 C-20/α-3/β-2 无文件冲突

## 建议 Execute 顺序

1. registry/models → 2. staged adapter fixture → 3. calendar/breadth → 4. lineage → 5. snapshot build + as_of → 6. quality rules → 7. gates

## 禁止触碰

- `backend/app/ops/staged_pilot.py`、`mutation_proof.py`、`storage/staged_evidence.py`
- `snapshot_lineage_contract.yaml` 写
- 三 registry 文档
- `layer5_evidence/**` 生产扩展（只读 foundation 参考）
