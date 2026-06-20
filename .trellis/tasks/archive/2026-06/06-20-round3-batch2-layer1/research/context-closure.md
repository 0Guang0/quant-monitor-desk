# L2 Context Closure — Round 3 Batch 2 Layer 1

> E16: MASTER §4/§6 touchpoints · impact(upstream)

## §4 code map touchpoints

| Symbol / path          | impact risk | Upstream (d=1)                | Closure                                  |
| ---------------------- | ----------- | ----------------------------- | ---------------------------------------- |
| `apply_migrations`     | LOW         | `init_db.main`, test fixtures | Migration 011 additive; idempotent       |
| `WriteManager`         | LOW         | sync pipeline, test helpers   | §8.5 thin wrapper; no WM API change      |
| `DbValidationGate`     | LOW         | WriteManager, tests           | Consume `validation_report_id` only      |
| `ResourceGuard.check`  | LOW         | sync/orchestrator jobs        | §8.3 hook in new `AxisFeatureEngine`     |
| `DataQualityValidator` | LOW         | sync validation path          | Read `rule_version` / fetch lineage §8.5 |
| `ConnectionManager`    | LOW         | init_db, WM, gates            | Standard reader/writer pools             |

## §6 contract touchpoints

| Contract                         | Consumer (new)                   | Risk                      |
| -------------------------------- | -------------------------------- | ------------------------- |
| `layer1_axis_contract.yaml`      | `AxisSpecLoader`, interpretation | LOW — read-only parse     |
| `snapshot_lineage_contract.yaml` | `SnapshotLineageBuilder`         | LOW — new table + builder |
| `resource_limits.yaml`           | `AxisFeatureEngine`              | LOW — eco profile check   |
| `write_contract.yaml` (implicit) | snapshot writer §8.5             | LOW — existing WM path    |

## Out-of-closure (explicit defer)

- `backend/app/layer2_sensors/**` — Batch 3
- `backend/app/api/**` — Round 4
- Migration 008 CHECK — Batch 6
- `DataSyncOrchestrator` live fetch — fixture observations only

## Conclusion

All planned edits are **LOW** upstream risk for §8.1 migration. Proceed with TDD vertical slices §8.1→8.5.
