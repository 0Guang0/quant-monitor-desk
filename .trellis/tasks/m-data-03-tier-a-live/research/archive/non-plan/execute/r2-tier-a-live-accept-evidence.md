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
- [ ] 本地 11/11 live `--report` exit 0（见 **Live log** — F0 真网仍 FAIL_FIXABLE）

## 命令

```bash
uv run pytest -q
QMD_ALLOW_LIVE_FETCH=1 DATA_ROOT=.audit-sandbox/m-data-03/<run> \
  uv run python scripts/tier_a_live_acceptance.py --report <path>/tier-a-report.json --data-root <path>
```

## Live log（2026-07-03 · 真网）

| Run        | Sandbox                                             | Exit  | Notes                                                                                                                                                             |
| ---------- | --------------------------------------------------- | ----- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| full 11/11 | `.audit-sandbox/m-data-03/r2-accept-close-20260703` | **1** | `tier_a_live_acceptance_failure_*.json` 已写出；E2 均非 FAIL（alpha_vantage WARN）；F0 11/11 FAIL（多数 `no raw evidence`；bar 源 empty bars / clean-write gate） |
| quick      | `.audit-sandbox/m-data-03/r2-quick-20260703`        | **1** | fred COMPLETED 但无 raw 落盘；baostock EMPTY_RESPONSE                                                                                                             |

**结论：** R2 验收层（report · manifest · failure_artifact · E2 接线 · B2 接线）已闭合；**全绿 live exit 0** 依赖 vendor 真数据 + raw 落盘/F0 后续修复，由 CI secrets + nightly 回归承接。

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
