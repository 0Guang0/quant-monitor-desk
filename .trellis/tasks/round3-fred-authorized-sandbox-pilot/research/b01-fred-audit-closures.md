# B01-FRED Audit closure registry (A1 zero遗留)

> Task-local SSOT for optional/deferred slice outcomes. Registry 三件套 delta remains coordinator merge Track A #3.

| ID | Item | Owner | Phase | Closure test | Audit status |
| --- | --- | --- | --- | --- | --- |
| FRED-07 | Authorized live FRED fetch (opt-in) | B01-FRED Execute | opt-in when `FRED_API_KEY` + `execute-evidence/authorization.yaml` | `test_fred07_liveFetch_closureClosedSkipOptIn_withoutApiKey` · `test_fredLiveFetch_authorized_respectsCaps` | **CLOSED-SKIP-OPT-IN** — no `FRED_API_KEY` in default/CI audit env; mocked + FAIL_AUTH paths green |
| B2.5-O-05 | Live FRED `primary_source` for `ENV-E1-DGS10` vs staged `macro_supplementary` | Batch 6 coordinator · R3E FRED-only sandbox evidence | **RE-DEFERRED** — live FRED primary closure (not Batch 2.75 Request 3) | `test_b250o05_reDeferred_closureRowClosed` · `tests/test_fred_staged_semantics.py` · `execute-evidence/fred_pilot_closeout.json` | **CLOSED** — FRED-only sandbox evidence recorded; debt stays DEFERRED until Batch 6 live primary |
| AA-FRED-A8-01 | Evidence health `MALFORMED_*` / `MISSING_ROWS` 分支无独立 pytest | B01-FRED Repair | Audit Repair | `test_fredEvidenceHealth_malformedBranches_failExplicitly` | **CLOSED** — mutation 测绑四码 |
| AA-FRED-A8-02 | §5.2 S3 缺 manifest 字段 → FAIL_SCHEMA 无直接 mutation 测 | — | — | `run_failure_scenario("schema")` · A4-DOUBT-01/03 | **CLOSED** — Audit A4 已闭合 |
| AA-FRED-A8-03 | §8.5 `ruff check backend/app/datasources backend/app/ops` 91 存量违规 | Repo hygiene coordinator | Batch 01 Track A hygiene wave | `repair-evidence/AA-FRED-A8-03_ruff_repo_hygiene_redefer.md` · FRED-scoped `ruff check backend/app/ops/fred_*.py tests/test_fred_*.py` 绿 | **CLOSED-repo-hygiene** — 非 FRED 引入；窄化 ruff 已绿；全库 91 项 re-defer |

## FRED-07 skip rationale

- `authorization.yaml` present (coordinator 2026-06-24).
- Live pytest uses `@pytest.mark.skipif(not os.environ.get("FRED_API_KEY"), ...)`.
- Without key: slice closed as opt-in skip; not OPEN.

## B2.5-O-05 re-defer rationale

- `fred_pilot_closeout.json`: `b2_5_o_05_decision=FRED_SANDBOX_EVIDENCE_RECORDED`, `b2_5_o_05_closed=false`.
- Macro/akshare cannot close (`macro_supplementary_cannot_close=true`).
- Full live FRED primary closure deferred to Batch 6 with explicit closure tests above.
