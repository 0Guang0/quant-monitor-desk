# Execute Skill Evaluation — contract-gate

Cross-check against `research/execute-skill-reads.jsonl`.

| Skill | Required | Evidence |
|---|---|---|
| trellis-execute | boot | Phase 0 `execute-boot.md` |
| gitnexus-impact | boot | `gitnexus-execute-summary.md`, `context-closure.md` |
| test-driven-development | each §8 RED | `execute-evidence/*-red.txt` |
| testing-guidelines | each §8 GREEN | contract tests assert business semantics |
| karpathy-guidelines | GREEN | minimal test-only planner; no production service |
| incremental-implementation | post-step | full pytest per step (manifest-protocol pre-existing failures noted) |
| source-driven | YAML tests | tests load `specs/contracts` and registry YAML |

All handoff_required_skills from `execute-skill-paths.yaml` are present in execute-skill-reads.jsonl.
