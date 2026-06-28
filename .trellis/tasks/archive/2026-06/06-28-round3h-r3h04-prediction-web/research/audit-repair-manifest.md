# Audit Repair Manifest — R3H-04

**状态：** **38 / 38 CLOSED** · BLOCKING **0** · NON-BLOCKING **0**

| ID | 来源 | 优先级 | 状态 | 修复摘要 |
|----|------|--------|------|----------|
| R3H04-AR-001 | A5-O1/A1-01 | P0 | CLOSED | `execute-evidence/9.8-full-pytest.txt` 刷新，exit 0 |
| R3H04-AR-002 | A1-02/A5-O2 | P1 | CLOSED | `9.8-green.txt` 含 pytest 摘要 + handoff |
| R3H04-AR-003 | A1-04/A8-G9 | P1 | CLOSED | `path_jail_support` 修复 layer3/4/official_macro 路径测 |
| R3H04-AR-004 | A4-O1/G2 | P1 | CLOSED | `test_polymarket_port_capOverflow_blocksOverMaxMarkets` |
| R3H04-AR-005 | A4-O2/G2 | P1 | CLOSED | kalshi/polymarket window cap 负例测 |
| R3H04-AR-006 | A4-O3/G2 | P1 | CLOSED | `test_web_search_port_capOverflow_blocksOverMaxQueries` |
| R3H04-AR-007 | A4-O4/G4 | P1 | CLOSED | `test_r3h04_polymarketEventMarketRoute_validationOnlyPrimaryBlocked` |
| R3H04-AR-008 | A4-O5/A4-DOUBT-03 | P1 | CLOSED | `resolution_source` https?:// 校验；poly live 去 description fallback |
| R3H04-AR-009 | A4-O6 | P1 | CLOSED | 对抗 fixtures + read 路径 pytest |
| R3H04-AR-010 | G1/A8 | P1 | CLOSED | A8 `-k` 含 `r3h` 覆盖 `test_r3h_source_final_decisions` |
| R3H04-AR-011 | G3 | P2 | CLOSED | `test_no_clean_write_polymarketPortOutput_hasNoCleanWriteTarget` |
| R3H04-AR-012 | G5/A1-03/A3-PRED-ORCH | P2 | CLOSED | `test_predictionMarket_dataSourceService_fetch_portIntegration` |
| R3H04-AR-013 | G6 | P2 | CLOSED | layer smoke provenance 字段断言 |
| R3H04-AR-014 | G7/A4-DOUBT-05 | P2 | CLOSED | live gate `pytest.raises(PredictionMarketLiveSmokeError)` |
| R3H04-AR-015 | A2-06 | P3 | CLOSED | `_FORBIDDEN_FIELDS` import `FORBIDDEN_RESOLUTION_FIELDS` SSOT |
| R3H04-AR-016 | A2-01 | P2 | CLOSED | 删 `probability_signal_bundle_preview` |
| R3H04-AR-017 | A2-02/03 | P2 | CLOSED | `prediction_market_port_common.build_probability_market_fetch_payload` |
| R3H04-AR-018 | A2-04 | P2 | CLOSED | `run_prediction_market_live_smoke` 合并 runner |
| R3H04-AR-019 | A2-05 | P3 | CLOSED | `enable_source_route` → `tests/service_path_support.py` |
| R3H04-AR-020 | A2 ponytail | P2 | CLOSED | live `read_bounded_http_body` + ponytail 注释 |
| R3H04-AR-021 | A5-O3/A7 | P2 | CLOSED | `.audit-sandbox/round3h/*_live_smoke_evidence.json` |
| R3H04-AR-022 | A7-O1 | P2 | CLOSED | `tests/fixtures/prediction_market_live_authorization.template.yaml` |
| R3H04-AR-023 | A3-WEB-YAML-PRIMARY | P2 | CLOSED | registry notes 对齐 validation_only 运行时语义 |
| R3H04-AR-024 | A1-06/O5 | P3 | CLOSED | `original-plan-trace.md` AC-SCOPE 更新 |
| R3H04-AR-025 | A1-05/A5-O4/A8-G8 | P3 | CLOSED | `research/gitnexus-audit-summary.md` |
| R3H04-AR-026 | A3-PRED-ORCH-GAP | P2 | CLOSED | DSS integration + clean-write 负例测保留 |
| R3H04-AR-027 | A3-GITNEXUS-STALE | INFO | CLOSED | GitNexus analyze 记录 |
| R3H04-AR-028 | A3-POLY-LIVE-NOKEY | P3 | CLOSED | env gate + response size cap（A6-NB-1） |
| R3H04-AR-029 | A4-DOUBT-01 | NB | CLOSED | poly cap pytest（AR-004） |
| R3H04-AR-030 | A4-DOUBT-02 | NB | CLOSED | window cap 仅 start+end 非空 — 设计一致，已测 |
| R3H04-AR-031 | A4-DOUBT-04 | NB | CLOSED | 对抗 staging fixture pytest |
| R3H04-AR-032 | A4-O7 | — | CLOSED | 流程项（uncommitted → repair 会话） |
| R3H04-AR-033 | A6-NB-1 | NB | CLOSED | `MAX_LIVE_RESPONSE_BYTES` cap |
| R3H04-AR-034 | A6-NB-2 | NB | CLOSED | 邻接项，非本轨 hot path |
| R3H04-AR-035 | A7-O2 | P3 | CLOSED | port cap 符合 frozen §2.8#5 |
| R3H04-AR-036 | A7-O3 | P3 | CLOSED | GitNexus 摘要（AR-025） |
| R3H04-AR-037 | A2 建议 ponytail | — | CLOSED | 双 port 隔离天花板注释于 common 模块 |
| R3H04-AR-038 | A1 建议项 | P2–P3 | CLOSED | 见 AR-001–025 |
