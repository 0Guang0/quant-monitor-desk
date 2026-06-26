# Integration ledger — R3FR-05（六类）

| source                                 | category     | disposition      | master_anchor      | execute_extract    | for_ac_step |
| -------------------------------------- | ------------ | ---------------- | ------------------ | ------------------ | ----------- |
| R3FR_05 live + frozen                  | task_card    | frozen           | frozen §1–§9       | scope              | all         |
| design.md                              | architecture | inline §5–6      | frozen §5          | catalog model      | AC-1–4      |
| grill-me-session.md                    | decision     | pointer          | frozen §7          | 裁决摘要           | scope       |
| source_registry.yaml                   | contract     | must-read        | EXECUTION_INDEX §3 | 23+2 源            | AC-1        |
| source_capabilities.yaml               | contract     | must-read + edit | §3 / 9.2           | openbb stub        | AC-6        |
| provider_catalog.yaml                  | contract     | create           | §9.2               | SSOT               | AC-1        |
| source/capability/datasource contracts | contract     | edit 9.4         | §3                 | catalog path refs  | AC-7        |
| reference_adoption_guardrails.yaml     | rule         | must-read + edit | §3 / 9.5           | R3FR-05 test       | AC-5        |
| provider_catalog.py                    | wiring       | create           | §9.3               | loader→YAML        | AC-6        |
| BATCH_3FR_COORDINATOR_PLAYBOOK.md      | business     | must-read        | §3                 | registry file lock | 9.2         |
| GLOBAL\_\* + schema 009                | rule         | must-read        | §3                 | enums/TDD          | AC-2        |
| test_provider_catalog.py               | test         | create           | §2                 | primary gate       | AC-6        |
| loop_maintain.py --fix                 | wiring       | gate 9.6         | §2.1 B             | test_catalog       | AC-7        |
