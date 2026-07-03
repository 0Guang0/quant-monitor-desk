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
- [x] 真网 11/11 `--report`：**11/11 PASS** · exit 0（AC#8 闭合）

## 命令

```bash
uv run pytest -q
QMD_ALLOW_LIVE_FETCH=1 DATA_ROOT=.audit-sandbox/m-data-03/<run> \
  uv run python scripts/tier_a_live_acceptance.py --report <path>/tier-a-report.json --data-root <path>
```

## Live log（2026-07-03 · 真网 · AC#8 闭合）

| Run        | Sandbox                                               | Exit  | Notes                                                                                                                                 |
| ---------- | ----------------------------------------------------- | ----- | ------------------------------------------------------------------------------------------------------------------------------------- |
| fred 单源  | `.audit-sandbox/m-data-03/r2-p3-fred-fix-*`           | **0** | sync=COMPLETED · F0=PASS · B2=PASSED · raw 已落盘                                                                                     |
| full 11/11 | `.audit-sandbox/m-data-03/r2-ac8-full-20260703165723` | **0** | **11/11 PASS**（alpha_vantage · baostock · bis · cftc_cot · cninfo · deribit · fred · mootdx · sec_edgar · us_treasury · world_bank） |
| 复验       | `.audit-sandbox/m-data-03/r2-ac8-verify-*`            | **0** | post-fix 全绿复验 + `uv run pytest -q` exit 0                                                                                         |

**PASS 源（2026-07-03 AC#8）：** 全部 11 源  
**FAIL_FIXABLE 源：** 无

**根因修复（AC#8）：**

1. staging adapter：`EMPTY_RESPONSE` 前仍 `persist_incremental_fetch_payload`（macro · cninfo · sec_edgar）
2. product-live replay：`replay_rows_caught_up_fallback`（近期窗 + stale fixture；倒置窗/历史窗不回填）
3. `layer1_observation_p0`：接受 `report_date` · `policy_rate` · COT 合约字段
4. CN bar replay fixture 补至 ≥2 bars（F0 `INSUFFICIENT_HISTORY`）

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
