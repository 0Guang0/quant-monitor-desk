# Plan Task Breakdown — R3-DCP-07

## Overview

Single-sensor Layer2 vertical slice: **L2-VIX** reads **VIXCLS** from Tier A `axis_observation`, produces snapshot + lineage, closes ACC-LAYER-E2E L2 subset.

## Architecture Decisions

| ID | Decision | Source |
|----|----------|--------|
| AD-1 | P0 = L2-VIX / VIXCLS / axis_observation | ADR-032 |
| AD-2 | No new migration | 活卡 §3 |
| AD-3 | Parallel staged + clean paths | DCP-06 staged 桥先例 |
| AD-4 | ACC L2 子集关账；L3–L5 阶段外置 | 待修复清单 §4 |
| AD-5 | Forbidden EasyXT fallback | reference-adoption-dcp07 |

## Task List

### S00 — Core clean reader

- **Description:** `Layer2CleanObservationReader` + registry mode for P0 clean replay
- **AC:** VIXCLS rows → `CrossAssetObservation[]`; missing clean → fail-closed
- **Verification:** `test_layer2CleanReader_*`
- **Dependencies:** ADR-028 macro clean schema
- **Files:** `backend/app/layer2_sensors/clean_observation_reader.py`（新）, `sensor_loader.py`, `observation.py`
- **Scope:** ~120 LOC

### S01 — VIX clean e2e

- **Description:** End-to-end snapshot + lineage from clean DB
- **AC:** lineage includes fetch ids/hashes; not staged_fixture_only
- **Verification:** `tests/test_layer2_vix_clean_e2e.py`
- **Dependencies:** S00
- **Files:** 新测 + 可能 `snapshot_builder.py` guard 分流
- **Scope:** ~80 LOC test + minimal prod

### S02 — Integration + ledger

- **Description:** Close ACC-LAYER-E2E L2 subset; G2 rating row
- **AC:** 待修复清单 + ROADMAP 登记；pytest 全绿
- **Verification:** `uv run pytest -q`
- **Dependencies:** S01
- **Files:** `docs/quality/待修复清单.md`, `MODULE_COMPLETION_RATING.md`（主会话）
- **Scope:** 文档 + 证据

## Checkpoints

1. S00 RED → GREEN
2. S01 RED → GREEN
3. S02 ledger + full pytest

## Risks

| Risk | Mitigation |
|------|------------|
| `assert_staged_source` blocks clean | ADR-032: reader tags `fred_clean_replay`; observation guard 分流 |
| Registry mode too broad | P0-only whitelist in loader |
| Double-count VIX vs Layer1 | registry `display_only=true` 不变 |

## Open Questions

- [x] P0 sensor choice → L2-VIX（ADR-032）
- [x] clean 表 → axis_observation（非 security_bar_1d）
