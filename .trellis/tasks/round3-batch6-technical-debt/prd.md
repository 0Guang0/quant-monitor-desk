# PRD — B3F-HYG Batch 3F.5 technical debt

## Goal

Close Batch6-owned hygiene/perf gaps without touching migration columns or live sources.

## Acceptance

1. Bounded smoke produces threshold-checked JSON artifact (`R3F-HYG-06`).
2. Ingestion PR-R2b `sandbox_bootstrap.py` wired; rollback plan documents R2b DONE (`R3F-HYG-07`).
3. Playbook §8.6 commands green on branch worktree.
4. Registry updates remain proposed delta for B3F-REG main-session merge.
