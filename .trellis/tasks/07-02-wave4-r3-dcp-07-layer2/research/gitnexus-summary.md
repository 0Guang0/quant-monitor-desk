# GitNexus Summary — R3-DCP-07

> **GitNexus Phase 1b** · 2026-07-02

## Impact: `CrossAssetSnapshotBuilder`

| 字段               | 值                                         |
| ------------------ | ------------------------------------------ |
| direction          | upstream                                   |
| risk               | **LOW**                                    |
| direct callers     | 1 (`layer2_sensors/__init__.py` re-export) |
| processes affected | 0                                          |

**结论：** 新增 clean reader + e2e 测为主；改 `snapshot_builder` 仅限解除 staged-only guard（若有），blast radius 低。

## Impact: `CrossAssetRegistryLoader`（计划）

| 字段    | 预期                                                  |
| ------- | ----------------------------------------------------- |
| risk    | LOW–MEDIUM                                            |
| callers | tests + future CLI                                    |
| 变更    | P0 资产 `primary_source` / mode 白名单扩 clean replay |

Execute 前须对实际修改 symbol 再跑 `impact()`。

## 相关执行流

- `proc_258_write_daily_snapshot` — `Layer2SnapshotWriter.write_daily_snapshot`
- `proc_30_write_lineage` — lineage VR 绑定
- 测试锚点：`test_crossAssetSnapshotBuilder_buildsDailySnapshotWithLineage`

## 建议 touch 顺序

1. `clean_observation_reader.py`（新，layer2 包内）
2. `sensor_loader.py`（P0 mode 扩展）
3. `observation.py`（staged assert 分流）
4. `tests/test_layer2_vix_clean_e2e.py`（新）

## Caveats

GitNexus 索引可能滞后；提交前 `detect_changes({scope: "compare", base_ref: "master"})`。
