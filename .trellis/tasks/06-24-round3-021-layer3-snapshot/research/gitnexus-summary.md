# GitNexus summary — 021 Layer3 snapshot builder (Plan 1b)

## 符号与流程

| 符号                              | 路径                                             | 说明                                   |
| --------------------------------- | ------------------------------------------------ | -------------------------------------- |
| `IndustryChainLoader`             | `backend/app/layer3_chains/loader.py`            | 020 前置；staged bundle → typed result |
| `CrossAssetSnapshotBuilder`       | `backend/app/layer2_sensors/snapshot_builder.py` | 模式参考：as_of + lineage              |
| `Layer2LineageBuilder`            | `backend/app/layer2_sensors/lineage.py`          | lineage envelope 构建                  |
| `SnapshotLineageBuilder` / kernel | `backend/app/core/snapshot_lineage.py`           | 共享 required_fields 校验              |

## 影响面（Plan 预估）

- **新建：** `snapshot_builder.py`（+ 可选 `lineage.py`）
- **扩展：** `models.py` snapshot 类型
- **无现有 upstream caller** — 仅 tests 直接调用
- **风险：** LOW — 隔离在 `layer3_chains` 包内

## 建议 Execute 顺序

1. models → 2. lineage → 3. builder core → 4. as_of → 5. event_only → 6. gates

## 禁止触碰

- `layer2_sensors/**` 生产修改（只读参考）
- `snapshot_lineage_contract.yaml` 写
- 三 registry 文档
