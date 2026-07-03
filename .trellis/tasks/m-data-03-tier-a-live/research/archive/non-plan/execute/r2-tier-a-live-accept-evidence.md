# R2 Tier A Live Acceptance Evidence

> **日期：** 2026-07-03  
> **分支：** `feature/m-data-03-tier-a-live`  
> **契约：** `specs/contracts/live_tier_a_evidence_v1.yaml` · ADR-034

## 验收清单

- [x] `live_tier_a_evidence_v1` 11/11 manifest（`test_reportRun_writesElevenManifests`）
- [x] acceptance report JSON 11 rows + contract 顶层字段（`test_acceptanceReport_hasContractTopLevelFields`）
- [x] E2 inspect 非 FAIL（mock 增量：`test_reportRun_e2InspectNonFailForElevenSources`）
- [x] B2 `b2_validation_status` 接线（`test_reportRun_setsB2ValidationStatusForElevenSources`）
- [x] `failure_artifact` 写出（`test_reportRun_writesFailureArtifactOnFixableFail` + live run 见下）
- [x] CI workflow：`.github/workflows/tier-a-live.yml`（nightly `--quick` + `workflow_dispatch`）
- [x] `uv run pytest -q` exit 0
- [x] staging adapter raw 落盘 → F0 可发现（`test_macroStagingPersist_writesRawDiscoverableByF0`）
- [x] 真网 11/11 `--report`：**5/11 PASS** · exit 1（6× `FAIL_FIXABLE` F0/vendor；见 Live log）

## 命令

```bash
uv run pytest -q
QMD_ALLOW_LIVE_FETCH=1 DATA_ROOT=.audit-sandbox/m-data-03/<run> \
  uv run python scripts/tier_a_live_acceptance.py --report <path>/tier-a-report.json --data-root <path>
```

## Live log（2026-07-03 · 真网 · post raw-persist fix）

| Run        | Sandbox                                              | Exit  | Notes                                                                                                                                                                                      |
| ---------- | ---------------------------------------------------- | ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| fred 单源  | `.audit-sandbox/m-data-03/r2-p3-fred-fix-*`          | **0** | sync=COMPLETED · F0=PASS · B2=PASSED · raw 已落盘                                                                                                                                          |
| full 11/11 | `.audit-sandbox/m-data-03/r2-p3-full-20260703163139` | **1** | 5 PASS（fred · us_treasury · world_bank · deribit · alpha_vantage）· 6 FAIL_FIXABLE（baostock/mootdx F0 gate · bis/cninfo/sec_edgar 无新 raw · cftc_cot F0 FAIL）· failure_artifact 已写出 |

**PASS 源（2026-07-03 run）：** fred · us_treasury · world_bank · deribit · alpha_vantage  
**FAIL_FIXABLE 源：** baostock · mootdx · bis · cftc_cot · cninfo · sec_edgar（F0 健康门 / vendor EMPTY_RESPONSE / 证据形状）

**根因修复（本批）：** incremental staging adapter 旁路 `RawStore.save` → `persist_incremental_fetch_payload`；fred live `data_root=raw/fred` 对齐其它源。

## MCR（R4 sandbox scope）

| Module | Rating   |
| ------ | -------- |
| C3     | R4       |
| D1     | R4       |
| E1     | R4       |
| E2     | R4       |
| F0     | R4（窄） |
| B2     | R4       |

## CI

- Workflow: `.github/workflows/tier-a-live.yml`
- Schedule: `0 7 * * *` → `--quick`（fred + baostock）
- `workflow_dispatch` → 全量 11/11（`quick: false`）
- On failure: upload `tier_a_live_acceptance_failure_*.json` + `tier-a-report.json`
