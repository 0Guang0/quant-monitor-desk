# Adversarial Audit — Agent 2 (Security, Tests, Runtime, Gates)

> Lens: Security boundaries · test gaps · runtime · operational risks  
> Date: 2026-06-20 · READ-ONLY original audit  
> **Remediation:** `research/adversarial-audit-phase2-remediation.md` (all A2-01..A2-28 CLOSED/WAIVED)

## Executive verdict (original)

**CONDITIONAL** — five P1 issues; Phase 3 not audit-ready without remediation.

## Findings (original → closure)

| ID    | Sev | Summary                       | Closure                                 |
| ----- | --- | ----------------------------- | --------------------------------------- |
| A2-01 | P1  | DB baseline misalignment      | CLOSED                                  |
| A2-02 | P1  | ResourceGuard not enforced    | CLOSED — raises                         |
| A2-03 | P1  | Fixture absent                | CLOSED                                  |
| A2-04 | P1  | Phase 3 tests missing         | CLOSED — §8.4 scope; prerequisites done |
| A2-05 | P1  | Live akshare risk             | CLOSED — fixture-only design constraint |
| A2-06 | P2  | HITL classification           | CLOSED                                  |
| A2-07 | P2  | Stale registry                | CLOSED                                  |
| A2-08 | P2  | Thin GREEN evidence           | CLOSED                                  |
| A2-09 | P2  | NOT_ON_ALLOWLIST / USER_AUTH  | CLOSED                                  |
| A2-10 | P2  | Prerequisite block            | CLOSED                                  |
| A2-11 | P2  | Private API                   | CLOSED                                  |
| A2-12 | P2  | db_capture_strategy           | CLOSED                                  |
| A2-13 | P2  | SyncValidationPipeline parity | CLOSED — Phase 4 note                   |
| A2-14 | P2  | No DB hash in P2 proof        | CLOSED                                  |
| A2-15 | P2  | Guard checked not enforced    | CLOSED — audit updated                  |
| A2-16 | P2  | staged_acceptance not read    | CLOSED — §8.4 boot mandate              |
| A2-17 | P2  | unit unitless                 | CLOSED — pct from fixture               |
| A2-18 | P2  | deferred test drift           | CLOSED                                  |
| A2-19 | P3  | Sandbox parity test           | CLOSED                                  |
| A2-20 | P3  | Conflict path                 | CLOSED — note in JSON                   |
| A2-21 | P3  | as_of vs fixture              | CLOSED                                  |
| A2-22 | P3  | Memo circularity              | CLOSED                                  |
| A2-23 | P2  | AC-TRACE-1 open               | CLOSED — documented                     |
| A2-24 | P3  | Eco window                    | WAIVED — §8.4 tests                     |
| A2-25 | P3  | Same-session audit            | CLOSED — remediation regen              |
| A2-26 | P2  | file_registry_factory risk    | CLOSED — handoff constraint             |
| A2-27 | P3  | Static scan scope             | CLOSED                                  |
| A2-28 | P3  | Absolute paths in evidence    | CLOSED — relative paths                 |
