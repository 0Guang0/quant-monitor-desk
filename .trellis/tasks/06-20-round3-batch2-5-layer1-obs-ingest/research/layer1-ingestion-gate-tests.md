# Layer 1 Ingestion Gate Tests (Phase 0 Execute)

> Plan 5b · 018A §8 Phase 0

## 8.1 Phase 0 — 既有测试集（须全绿）

```bash
uv run pytest tests/test_schema_migration.py tests/test_schema_contract.py -q
uv run pytest tests/test_source_capabilities.py tests/test_source_route_planner.py tests/test_datasource_service.py tests/test_data_cli_contract.py -q
uv run pytest tests/test_ops_db_inspector.py -q
uv run pytest tests/test_layer1_axis_loader.py tests/test_layer1_interpretation.py -q
uv run pytest tests/test_sync_orchestrator.py tests/test_sync_jobs.py tests/test_vendor_fetch_e2e.py -q
```

## 8.1 新增（若缺失则 RED）

| 测试名                                                             | 语义                                                      |
| ------------------------------------------------------------------ | --------------------------------------------------------- |
| `test_layer1Ingestion_phase0_schemaSql_vs_migration011_axisTables` | migration 011 含 `axis_observation`；记录 schema.sql 滞后 |
| `test_layer1_axes_doesNotImportCreateAdapter`                      | 静态：layer1_axes 无 `create_adapter` import              |
| `test_sourceRegistry_roles_forbidShadowEmergency`                  | Primary/Validation/FallbackPolicy only                    |

## 证据

- `execute-evidence/phase0_test_output.txt`
- `execute-evidence/phase0_source_context_matrix.md`
- `execute-evidence/phase0_db_contract_gate.md`
