# R3-DCP-07 — `/to-issues` 垂直切片

> **SSOT：** 切片 AC 仅本文件 · Plan v4.1  
> **依赖：** R3-DCP-05/06 CLOSED · ADR-032

---

## 垂直切片规则

1. 单片 tracer-bullet：单 P0 传感器 `L2-VIX`；可独立 pytest 绿。
2. RED → GREEN 证据：`research/execute-evidence/sNN-red.txt` → `sNN-green.txt`
3. 共享 `layer2_sensors` 读路径：**S00 独占 merge 后** S01 只追加 e2e。
4. Registry / K1：若动 `cross_asset_registry` 或 capabilities → 主会话 merge。

---

## 依赖图

```text
S00 (Layer2CleanObservationReader + registry P0 mode + no-fallback guard)
  → S01 (L2-VIX VIXCLS clean e2e: snapshot + lineage)
  → S02 (ACC-LAYER-E2E-LIVE-001 L2 子集 + G2 评级证据 + 全量 pytest)
```

---

## 切片总表

| Slice | What to build | Acceptance criteria | Blocked by | 测试 / 证据 |
|-------|---------------|---------------------|------------|-------------|
| **S00-CORE-READER** | `Layer2CleanObservationReader` 读 `axis_observation`（VIXCLS）→ `CrossAssetObservation`；registry P0 `production_clean_replay` mode | clean 有种子 → 返回观测序列；无 EasyXT 式 fallback | — | `test_layer2CleanReader_*`（Execute 新建） |
| **S01-VIX-CLEAN-E2E** | L2-VIX 从 clean 建 daily snapshot + lineage | 非 `staged_fixture_only`；`source_fetch_id` + content_hash 可断言；对齐 `test_layer2Snapshot_lineageIncludesFetchIdsAndHashes` 契约 | S00 | `test_layer2_vix_clean_e2e.py`（Execute 新建） |
| **S02-INTEGRATION** | 台账 L2 子集关账；MODULE_COMPLETION_RATING G2 行证据 | `ACC-LAYER-E2E-LIVE-001` L2 部分 [x]；L3–L5 阶段外置登记；`uv run pytest -q` 绿 | S01 | repair ledger + 全量 pytest |

---

## P0 锚点（ADR-032）

| 字段 | 值 |
|------|-----|
| asset_id | `L2-VIX` |
| instrument_id (registry) | `FRED:VIXCLS` |
| clean table | `axis_observation` |
| indicator_id | `VIXCLS` |
| source domain | `macro_series` / fred incremental (DCP-05) |

---

## Issue 骨架

```markdown
### [S01] L2-VIX clean read e2e

**What:** read axis_observation VIXCLS → CrossAssetSnapshotBuilder → lineage per ADR-032
**AC:** replay seed in tmp_path DB; source != staged_fixture; pytest green
**Blocked by:** S00
**Verify:** tests/test_layer2_vix_clean_e2e.py
```
