# Plan Spec — R3-DCP-07 Layer2 Cross-Asset Clean

## Objective

Prove **one** P0 cross-asset sensor reads Tier A clean and produces assertable snapshot + lineage (G2 R3→R4).

## Tech Stack

- Python 3.11+ · DuckDB · pytest · existing `layer2_sensors` package
- Clean SSOT: `axis_observation` (DCP-05 fred)

## Commands

```bash
uv run pytest tests/test_layer2_sensor_loader.py -q
uv run pytest tests/test_layer2_vix_clean_e2e.py -q   # Execute 新建
uv run pytest -q
uv run python scripts/loop_maintain.py
```

## Project Structure

```text
backend/app/layer2_sensors/
  clean_observation_reader.py   # NEW (S00)
  sensor_loader.py              # P0 mode extend
  snapshot_builder.py             # minimal guard if needed
tests/
  test_layer2_vix_clean_e2e.py  # NEW (S01)
```

## Code Style

- ponytail：最小 diff；复用 DCP-06 `Layer1CleanObservationReader` 模式
- TDD：RED → GREEN per slice
- 五字段 docstring on new `test_*`

## Testing Strategy

| Layer | Approach |
|-------|----------|
| S00 | Unit: reader maps VIXCLS rows → observations |
| S01 | E2E: tmp_path DB + fred replay seed → snapshot + lineage |
| S02 | Full `pytest -q` |

## Boundaries

**In:** L2-VIX only · axis_observation · replay default  
**Out:** L2 全资产矩阵 · L3–L5 E2E · FRED live primary · new migration

## ASSUMPTIONS

1. DCP-05 fred incremental e2e seed pattern is reusable for VIXCLS.
2. `CrossAssetSnapshotBuilder` contract unchanged except input source tag.
3. Registry YAML fixture remains for non-P0 assets in existing tests.

## Success Criteria

| ID | Criterion |
|----|-----------|
| SC-1 | `test_layer2_vix_clean_e2e` GREEN |
| SC-2 | lineage fetch ids + hashes present |
| SC-3 | ACC-LAYER-E2E L2 subset closed (S02) |
| SC-4 | `validate-plan-freeze` exit 0 (Plan) |

## Open Questions

- [x] Replay vs live → replay satisfies 活卡 §3
