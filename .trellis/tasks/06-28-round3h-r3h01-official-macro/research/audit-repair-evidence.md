# Audit Repair Evidence — R3H-01（零遗留）

**日期：** 2026-06-28 · **分支：** `feature/round3h-r3h01-official-macro`  
**验证：** 全部 manifest ID → CLOSED

## 验证命令输出

```text
# 全库 pytest
uv run pytest -q
→ exit 0 (2026-06-28 repair pass)

# loop maintain
uv run python scripts/loop_maintain.py
→ OK: loop maintain

# execute handoff
uv run python .trellis/scripts/task.py validate-execute-handoff .trellis/tasks/06-28-round3h-r3h01-official-macro
→ Execute handoff validation passed
```

## A4 P1–P3

| ID    | 状态             | 证据                                                                                                 |
| ----- | ---------------- | ---------------------------------------------------------------------------------------------------- |
| P1-01 | CLOSED           | `observation_fields`/`bundle_fields` YAML；`test_r3h01_capabilityFields_matchPortOutput`             |
| P1-02 | CLOSED           | `test_cftc/bis/world_bank_port_capOverflow_*`                                                        |
| P1-03 | CLOSED           | `test_fred_port_capOverflow_blocksOverMaxSeries`                                                     |
| P1-04 | CLOSED           | `test_fred_port_liveWithoutApiKey` + `test_secEdgar_port_identityHeader` → `USER_AUTH_REQUIRED` only |
| P1-05 | CLOSED           | `read_fred_evidence_bundle` fail-closed；`test_fred_evidence_read_corruptBundle_missingHash_raises`  |
| P1-06 | CLOSED           | `test_r3h01_officialMacroRoute_disabledByDefault` 参数化六源完整断言                                 |
| P2-01 | CLOSED           | `test_r3h01_officialMacroCaps_matchRegistry`                                                         |
| P2-02 | CLOSED           | `reject_over_cap` 非正数消息；`test_fred_port_capOverflow_rejectsNonPositiveMaxRows`                 |
| P2-03 | CLOSED           | yield 行 `source_used`；`_normalize_yield_curve_row`                                                 |
| P2-04 | CLOSED           | 删除 per-port route DISABLED 重复；保留 `test_source_route_planner` 参数化                           |
| P2-05 | CLOSED           | `contract_coverage.yaml` SOURCE_CAPABILITY `negative_required: true`                                 |
| P3-01 | CLOSED           | `test_fred_port_windowStart_respectsMaxWindowDays`                                                   |
| P3-02 | CLOSED           | `len(bundle["observations"]) >= 1`                                                                   |
| P3-03 | CLOSED-by-design | `ops/fred_fetch_ports.py` thin re-export 保留                                                        |

## A8 G-01–G-11

| ID        | 状态   | 证据                                                                                       |
| --------- | ------ | ------------------------------------------------------------------------------------------ |
| G-01      | CLOSED | `test_layer_smoke_missingContentHash_raises`                                               |
| G-02–G-04 | CLOSED | 合并 P1-02 cap 测                                                                          |
| G-05      | CLOSED | 合并 P1-03/P3-01                                                                           |
| G-06      | CLOSED | `test_r3h01_officialMacroRoute_readyWhenSourceEnabled` ×3                                  |
| G-07      | CLOSED | `test_secEdgar_port_route_form4_*` + `test_bis_port_route_creditGap_*` + credit_gap replay |
| G-08      | CLOSED | `finalize_bundle` → `schema_hash`/`fetch_log`；`test_fred_port_emitsSchemaHashAndFetchLog` |
| G-09      | CLOSED | replay fixture 常量断言（fred-replay-dgs10 等）                                            |
| G-10      | CLOSED | 合并 P1-06                                                                                 |
| G-11      | CLOSED | `test_bootSkeleton_testModuleLoads` 检查模块 docstring                                     |

## A2 Ponytail

| 项                    | 状态   | 证据                                                                  |
| --------------------- | ------ | --------------------------------------------------------------------- |
| 共享 helper           | CLOSED | `normalizers/evidence_bundle.py` `finalize_bundle`/`reject_over_cap`  |
| read_bis_credit_gap   | CLOSED | 已删除；`credit_gap_replay_bundle.json` + `_read_observations_bundle` |
| 泛型 reader           | CLOSED | `_read_observations_bundle` 统一五域 read                             |
| SecEdgarLiveFetchPort | CLOSED | factory 层 identity gate + `FAILED` use mock                          |
| bis MAX_SERIES        | CLOSED | 已删未用常量                                                          |
| live_evidence_bridge  | CLOSED | 直接 import normalizer；删重复 wrapper                                |

## A3 / A5 / A6 / A1

| 项                   | 状态   | 证据                                                               |
| -------------------- | ------ | ------------------------------------------------------------------ |
| SEC 弱 UA            | CLOSED | `test_secEdgar_port_weakUserAgent_blocksLive`                      |
| PROJECT_ROOT jail    | CLOSED | `test_liveEvidenceBridge_resolveRawPath_rejectsOutsideProjectRoot` |
| execute 9.5–9.8 加厚 | CLOSED | `execute-evidence/9.5-green.txt` … `9.8-full.txt` 更新             |
| FRED pilot 分层      | CLOSED | `test_fred_liveCap_pilotAuthLayerDocumented` + fred_port 注释      |
| GitNexus analyze     | CLOSED | `research/gitnexus-audit-summary.md` 笔记（repair 后索引）         |
