# Audit Repair Evidence — R3H-02（零遗留）

**日期：** 2026-06-28 · **任务：** `06-28-06-28-round3h-r3h02-market-data`

## 验证门

```text
uv run pytest -q                          → exit_code: 0
uv run python scripts/loop_maintain.py    → OK: loop maintain
uv run python scripts/check_test_catalog.py → OK: 116 modules
validate-execute-handoff                  → passed
node .gitnexus/run.cjs analyze            → 见 research/gitnexus-audit-summary.md
```

## A1 / A5 / A8 — 合并门与证据

| ID         | 状态   | 证据                                                                                                                                                                 |
| ---------- | ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| R3H02-R-01 | CLOSED | `tests/test_catalog.yaml` 登记 `test_market_data_adapters.py` / `test_crypto_market_adapters.py`；`check_test_catalog.py` CURATED + `git add` 防 pytest restore 回滚 |
| R3H02-R-02 | CLOSED | `execute-evidence/9.8-full.txt` 真实 pytest + loop 输出                                                                                                              |
| R3H02-R-03 | CLOSED | canonical `execute-evidence/` 与 `research/execute-evidence/` 9.6–9.8 路径对齐                                                                                       |
| R3H02-R-04 | CLOSED | `node .gitnexus/run.cjs analyze`；`research/gitnexus-audit-summary.md` 更新                                                                                          |
| R3H02-R-05 | CLOSED | `adapters/__init__.py` `create_fetch_port_for_source` → `yahoo_finance_port`；`test_yahooAdapter_createFetchPort_boundaryUsesReplayPort`                             |

## A4 / A8 — 对抗测试与契约

| ID         | 状态   | 证据                                                                                                                                          |
| ---------- | ------ | --------------------------------------------------------------------------------------------------------------------------------------------- |
| R3H02-R-10 | CLOSED | `test_r3h02_validationOnlySource_blockedAsPrimaryWhenForced`（yahoo/stooq）；`test_coingecko_validationOnlySource_blockedAsPrimaryWhenForced` |
| R3H02-R-11 | CLOSED | stooq/yahoo/coingecko `test_*_capOverflow_*`                                                                                                  |
| R3H02-R-12 | CLOSED | `test_alpha_vantage_port_capOverflow_blocksOverMaxSymbols`                                                                                    |
| R3H02-R-13 | CLOSED | `test_alpha_vantage_port_windowSpan_blocksOverMaxWindowDays`；`test_stooq_port_windowSpan_blocksOverMaxWindowDays`                            |
| R3H02-R-14 | CLOSED | yahoo `us_option_chain` 移出 `allowed_domains`；capabilities notes defer 至 alpha_vantage                                                     |
| R3H02-R-15 | CLOSED | `test_r3h02_capabilityFields_matchPortOutput`；`test_r3h02_cryptoCapabilityFields_matchPortOutput`                                            |
| R3H02-R-16 | CLOSED | `test_r3h02_marketCaps_matchRegistry`；`test_r3h02_cryptoCaps_matchRegistry`                                                                  |
| R3H02-R-17 | CLOSED | `test_r3h02_marketPort_unknownInstrument_rejectsWhitelist`；crypto unknown asset/instrument 测                                                |
| R3H02-R-18 | CLOSED | `contract_coverage.yaml` `SOURCE_ROUTE_READY_REQUIRED` / `SOURCE_CAPABILITY` `negative_required: true`                                        |
| R3H02-R-19 | CLOSED | `9.8-full.txt` 含 `test_r3h_source_final_decisions` + validation slice                                                                        |
| R3H02-R-21 | CLOSED | `test_alpha_vantage_port_optionChain_capOverflow_blocksOverMaxStrikes`                                                                        |
| R3H02-R-22 | CLOSED | `test_evidence_contract_replayFixture_*` + `window_kind == calendar_days`                                                                     |
| R3H02-R-23 | CLOSED | `test_alpha_vantage_port_route_disabledWhenSourceUnauthorized`                                                                                |
| R3H02-R-24 | CLOSED | `test_layer_smoke_cryptoReplay_layer4MarketStructurePreview`                                                                                  |
| R3H02-R-25 | CLOSED | `test_yahoo_port_route_readyWhenSourceAndDomainEnabled`                                                                                       |
| R3H02-R-26 | CLOSED | `evidence_index.json` execute/audit 索引已填                                                                                                  |
| R3H02-R-27 | CLOSED | canonical `9.1-green.txt` … `9.5-green.txt` 含 `exit_code: 0` 摘要                                                                            |

## A3 — Registry

| ID         | 状态   | 证据                                                                                                                                            |
| ---------- | ------ | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| R3H02-R-20 | CLOSED | validation-only 源移出 `domain_roles.validation` 禁用槽；`crypto_spot_market` primary→`alpha_vantage`；`global_asset_reference`→`yahoo_finance` |

## A2 — Ponytail debt

| ID         | 状态   | 证据                                                                                                       |
| ---------- | ------ | ---------------------------------------------------------------------------------------------------------- |
| R3H02-R-30 | CLOSED | `write_crypto_market_evidence_bundle` + `test_evidence_contract_writeReadRoundTrip_fixturePreservesFields` |
| R3H02-R-31 | CLOSED | `evidence_bundle.bundle_layer5_provenance()` 三处复用                                                      |
| R3H02-R-32 | CLOSED | yahoo 删 `MAX_OPTION_STRIKES`；AV/stooq/yahoo `reject_window_span_over_cap` 接线                           |
| R3H02-R-33 | CLOSED | `tests/conftest_layer_smoke.py` `assert_layer5_factual_source_record`                                      |
| R3H02-R-34 | CLOSED | AV replay 合并至 `test_evidence_contract_replayFixture_tradeDateCanonical`                                 |

## A6 / A7

| ID         | 状态           | 证据                                                                     |
| ---------- | -------------- | ------------------------------------------------------------------------ |
| R3H02-R-40 | CLOSED-by-test | R-11 cap 负例覆盖                                                        |
| R3H02-R-41 | CLOSED         | `alpha_vantage_port.py` live 路径 `ponytail:` DSS ResourceGuard 指针     |
| R3H02-R-50 | CLOSED         | `9.8-full.txt` PromoteRunner `refusesCanonicalProductionDbPath` 通过记录 |

**闭合计数：27 / 27 · 开放项：0**
