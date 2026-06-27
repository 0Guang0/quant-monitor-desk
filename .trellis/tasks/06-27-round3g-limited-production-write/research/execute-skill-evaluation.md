# Execute skill evaluation — R3G-03

Skills recorded in `execute-skill-reads.jsonl`:

- trellis-execute: Phase 0 boot; §9.0→9.8 RED/GREEN evidence in `research/execute-evidence/`
- test-driven-development: ApprovalContract/BeforeProof/RollbackPlan/PromoteRunner/AfterProof/PromoteCli tests before modules
- incremental-implementation: full `pytest -q` after each GREEN slice; Tier A+ at 9.8
- karpathy-guidelines: compose existing gates; three small modules + CLI extension
- testing-guidelines: five-field Chinese docstrings; block_if adversarial matrix covered
- ponytail: reuse mutation_proof + rehearsal_runner gate helpers; no third orchestrator
- gitnexus-impact-analysis: `research/gitnexus-execute-summary.md`; LOW/MEDIUM blast radius only

## Tier B note

Prod-path promote not executed — coordinator §6 approval YAML + explicit `--execute` required.
