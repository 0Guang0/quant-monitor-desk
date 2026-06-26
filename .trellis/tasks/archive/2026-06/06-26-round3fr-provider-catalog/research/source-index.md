# Source index — R3FR-05

## B. Manifest

| path                                           | manifest   | status  |
| ---------------------------------------------- | ---------- | ------- |
| R3FR_05_PROVIDER_CATALOG_OPENBB_REFERENCE.md   | required   | frozen  |
| BATCH_3FR_COORDINATOR_PLAYBOOK.md              | must-read  | execute |
| GLOBAL_EXECUTION_RULES.md                      | must-read  | execute |
| GLOBAL_TESTING_POLICY.md                       | must-read  | execute |
| GLOBAL_RESOURCE_LIMITS.md                      | must-read  | execute |
| source_registry.yaml                           | must-read  | execute |
| source_capabilities.yaml                       | must-read  | execute |
| source/capability/datasource_service contracts | must-read  | both    |
| reference_adoption_guardrails.yaml             | must-read  | both    |
| schema.sql + 009 migration                     | must-read  | both    |
| ROUND3_BATCH_IMPLEMENTATION_MAP.md             | audit-only | audit   |
| docs/generated/project_map.generated.json      | audit-only | audit   |
| MIGRATION_MAP.md                               | audit-only | audit   |

## C. 索引完整

索引完整（对抗性审计修复后）

## D. 机器路由

权威数据在 **`context_pack.json`**（本任务根目录）。 由 `context_router.py --task` 写入；本段不重复列举。
