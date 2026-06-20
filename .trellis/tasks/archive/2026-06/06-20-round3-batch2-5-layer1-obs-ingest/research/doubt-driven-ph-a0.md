# Doubt-Driven Checklist — PH-A0 (Phase 0 DB/Contract Gate)

> F-A3-11 · doubt-driven-development · 2026-06-20

## CLAIM

Phase 0 proves ingestion chain DDL, contract wiring, and Layer1 boundary gates are satisfied **before** any read-only inventory or mutation phases — without requiring `ingestion.py`.

## CONTRACT (must hold)

- AC-P0-1: source context matrix + annex crosswalk complete
- AC-P0-2: schema/migration deviation classified (011 authoritative; schema.sql lag B2.5-O-02)
- AC-P0-3: datasource factory boundary; registry staged route for ENV-E1-DGS10
- AC-P0-4: Layer1 must not import `create_adapter`
- Phase 0 pytest block green; PH-A0 adversarial remediation closed

## Adversarial questions (answered)

| #   | Doubt                                           | Reconciliation                                                                         |
| --- | ----------------------------------------------- | -------------------------------------------------------------------------------------- |
| 1   | Is `schema.sql` falsely authoritative?          | **Yes risk** — classified B2.5-O-02; tests assert migration 011 columns                |
| 2   | Can silent fallback slip through route planner? | Gate tests copy contract `reject_if` + `test_noSilentFallbackCopied`                   |
| 3   | Is FRED live assumed?                           | **No** — B2.5-O-05; staged `macro_supplementary` only                                  |
| 4   | Does sync pipeline prove Layer1 write path?     | **No** — documented contrast; Layer1 uses validators + WriteManager directly (Phase 4) |
| 5   | Are deferred items hidden?                      | Listed in MASTER §8.1 + `AUDIT_DEFERRED_REGISTRY.md`                                   |
| 6   | Is factory boundary only import-checked?        | Remediated: `test_layer1Ingestion_phase0_datasourceServiceFactoryBoundaryEnforced`     |

## STOP condition

No P0/P1 open findings after `adversarial-audit-phase0-remediation.md`. PH-A0 signed in `research/audit-ph-a0-phase0-gate.md`.
