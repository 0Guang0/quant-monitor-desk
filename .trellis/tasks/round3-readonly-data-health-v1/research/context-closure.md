# Context closure — C-20 read-only data health v1

## Upstream wiring

- `staged_pilot.py` — `RAW_MANIFEST_JSON`, `STAGING_MANIFEST_JSON` manifest 常量
- `db_inspector.py` — `InspectReport` 只读模式参考
- `validators/data_quality.py` — rule_id 语义 SSOT（内联最小检查，不复制整表扫描）
- v2 evidence 根：`.trellis/tasks/archive/2026-06/06-24-round3-real-data-staged-pilot-v2/execute-evidence/`

## Deferred (unchanged)

- Batch6 完整 `qmd data health` 平台
- `source_health_snapshot` clean 表
- DuckDB full domain scan
- registry 三件套 — Wave C merge 后主会话
- `layer4_markets/**` — 022 分支
- `staged_evidence.py` — β-2 分支
- production-live / REQ2-EM unblock

## Slice boundary

- staged-only；`production_db_mutated: false` + `source_fetch_performed: false` 硬编码
- allowed：`data_health*.py` + `test_ops_data_health.py` + fixtures
- 无 production DB 写、无 live fetch
