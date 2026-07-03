# Plan Spec — R3-DCP-06 Layer1 Five-Axis Clean

## Problem

Layer1 tests prove loader/feature/interpretation on **staged fixtures**. PASS requires five axes consume **Tier A clean** inputs (roadmap §3.5.1).

## Users

- Wave 5 audit (`R3H-05-GATE`)
- Round4 modeling/product (after PASS)
- Ops: isolated replay e2e proves non-fixture path

## Functional Requirements

| ID   | Requirement                                                                             |
| ---- | --------------------------------------------------------------------------------------- |
| FR-1 | `Layer1CleanObservationReader` reads `axis_observation` by `indicator_id` + date window |
| FR-2 | Bar reader loads `security_bar_1d` for Amihud (LIQUIDITY P0)                            |
| FR-3 | Missing clean rows → fail-closed (no online fallback)                                   |
| FR-4 | Each axis: clean → `AxisFeatureEngine` → `AxisInterpretationEngine` → assertable output |
| FR-5 | ResourceGuard respected on compute path (A4)                                            |
| FR-6 | K1 P0 rows reflect `clean_replay_proven` (not production-live ready)                    |

## Non-Functional

| ID    | Requirement                      |
| ----- | -------------------------------- |
| NFR-1 | Tests use `tmp_path` isolated DB |
| NFR-2 | No migration DDL                 |
| NFR-3 | No runtime import `参考项目/**`  |

## Out of Scope

- FRED live primary (`B2.5-O-05`)
- L3–L5 full E2E chain
- tiingo liquidity primary
- All non-P0 indicators per axis YAML

## Acceptance Mapping

| Spec    | 活卡 §5  | 切片    |
| ------- | -------- | ------- |
| FR-1..3 | clean 读 | S00     |
| FR-4    | 五轴 e2e | S01–S05 |
| FR-5,6  | 集成     | S06     |
