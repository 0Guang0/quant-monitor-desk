# Round 3 External Reference Landing Tasks

This directory contains original task cards for landing external-project reference ideas into QMD without losing Round/Batch ownership, source links, planning inputs, execution boundaries, or merge gates.

These files do not import or vendor external code by themselves. They convert external references into QMD-governed work items.

| Task card                                 | Round / Batch                             | Branch type                                                       | Can run in parallel?        | Purpose                                                                                        |
| ----------------------------------------- | ----------------------------------------- | ----------------------------------------------------------------- | --------------------------- | ---------------------------------------------------------------------------------------------- |
| `R3D_018C_low_cost_source_probe.md`       | Round 3 / Batch 2.75 follow-up / Phase 8D | `debt/r3b275-018c-low-cost-probe`                                 | Yes, with staged-only `019` | Low-cost `tdx_pytdx` and AkShare Sina sidecar probe.                                           |
| `R3D_ops_db_data_health_reference.md`     | Round 3 / Batch 1 and Batch 6             | `debt/r3-ops-inspect-data-health-references` or Batch 6 sub-batch | Yes, docs/ops-only first    | Land EasyXT/JQ2PTrade/ptqmt-site references into QMD ops/db-inspect/data-health/report design. |
| `R4D_readonly_sql_assistant_reference.md` | Round 4 candidate, not Round 3 execution  | future `research/r4-readonly-sql-assistant`                       | No Round 3 branch           | Land DB-GPT/DB-GPT-Hub as future read-only SQL/reporting research only.                        |

Planning rule: every plan that uses one of these cards must also read `ROUND3_BATCH_IMPLEMENTATION_MAP.md`, `.trellis/spec/guides/round3-repair-debt-worktree-plan.md`, and `.trellis/spec/guides/complex-task-planning-protocol.md` Phase 8D.
