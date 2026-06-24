## Proposed closures (coordinator merge only)

| ID | Proposed status | Evidence | Residual / re-defer |
| --- | --- | --- | --- |
| R3-B6-021-O-01 | RESOLVED | LIN-S1 `test_layer3Snapshot_malformedBarElement_rejects` + `snapshot_builder._bar_for_trade_date` | — |
| R3-B6-021-O-02 | RESOLVED | LIN-S2 `test_layer3Snapshot_deterministicRebuild_sameInputsSameHash` full tuple | — |
| R3Y-LINEAGE-VR-001 | RESOLVED (staged WM path) | LIN-S4 VR binding + DB lineage column tests | production `fetch_log` E2E defer |
| ADV-R3X-LINEAGE-001 | **PARTIAL** | LIN-S3 contract-scoped pytest green | 全量 DB 写回 **re-defer → B01-023**（见 `lin01-partial-closure-scope.md`） |
| R3Y-TEST-DEPTH-001 | PARTIAL | LIN-S5 `research/test-depth-report.md` | 非 lineage 项仍 OPEN / wont-fix |
