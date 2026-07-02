# Project Overview — R3-DCP-07 Layer2

> **GitNexus Phase 1a** · 2026-07-02

## Query

Layer2 cross-asset sensor: registry loader, snapshot builder, lineage, clean read gap.

## Scope

| 模块 | 路径 | 角色 |
|------|------|------|
| G2 Layer2 | `backend/app/layer2_sensors/**` | registry + snapshot + lineage（Batch 3 staged） |
| Tier A clean | `axis_observation`, `security_bar_1d` | DCP-05 写入 SSOT |
| Layer1 先例 | `backend/app/layer1_axes/clean_observation_reader.py` | DCP-06 clean 读模式（仓内承接，非 L 梯） |
| 测试契约 | `tests/test_layer2_sensor_loader.py` | staged fixture + lineage VR 绑定 |

## 执行流（现状）

```text
STAGED_REGISTRY_FIXTURE (YAML)
  → CrossAssetRegistryLoader (mode=staged_fixture_only)
  → CrossAssetObservation (source=staged_fixture)
  → CrossAssetSnapshotBuilder.build_daily_snapshots
  → Layer2LineageBuilder → Layer2SnapshotWriter
```

## DCP-07 目标流

```text
axis_observation (indicator_id=VIXCLS, DCP-05 fred clean)
  → Layer2CleanObservationReader [NEW]
  → CrossAssetObservation (source=fred_clean_replay)
  → CrossAssetSnapshotBuilder (existing contract)
  → lineage (source_fetch_id + content_hash)
```

## Findings

1. `sensor_loader.py` 硬编码 `staged_fixture_only` + `ALLOWED_PRIMARY_SOURCES = {staged_fixture}` — Execute 须扩 P0 clean replay 模式（ADR-032）。
2. `snapshot_builder.py` 调用 `assert_staged_source` — clean 路径需 parallel guard 或 reader 输出满足契约。
3. `CrossAssetSnapshotBuilder` GitNexus impact **LOW**（仅 `__init__.py` 导入）。
4. DCP-06 已证明 `VIXCLS` 在 `axis_observation` 可 replay；Layer2 复用种子模式，不新 fetch。

## Caveats

- 全量 staging→DQ→conflict pipeline 仍 defer（module doc §7 F-019-R02）。
- L2-HYG / security_bar_1d 为后续 Wave 候选，非本票 P0。
