# Migration, Rollback, and Recovery Policy

## 1. 目的

修复 QM-AUD-008，并落实用户拍板 D-06：第一版采用“破坏性变更用备份恢复，非破坏性变更可以无 down SQL”的策略。

## 2. 已拍板 rollback 策略（D-06）

```text
不要求每个 migration 都写 down SQL。
非破坏性 migration 可无 down SQL，但必须写 down_not_supported_reason。
破坏性 migration 必须先生成备份，失败时通过备份恢复。
完全不支持回滚/恢复的 migration 禁止进入 prod。
```

## 3. Migration 元数据基线

每个 migration 必须登记：

- `version`
- `name`
- `up_sql_path`
- `down_sql_path` 或 `down_not_supported_reason`
- `is_destructive`
- `sha256_checksum`
- `applied_at`
- `applied_by_tool_version`
- `pre_migration_backup_path`（破坏性变更必填）

## 4. 执行顺序

1. ResourceGuard 检查。
2. 获取 migration lock。
3. 判断是否破坏性变更。
4. 如果是破坏性变更，生成 schema-change 前备份。
5. 校验 checksum。
6. 执行 up migration。
7. 写入 `schema_version`。
8. 执行 smoke query。
9. 失败时 rollback；如无法 rollback，恢复 `pre_migration_backup_path` 并写 audit log。

## 5. 禁止事项

- 禁止直接在生产库手写 `ALTER TABLE` 而不登记 migration。
- 禁止无备份执行破坏性 schema change。
- 禁止改写旧 migration 文件；修正必须新增 migration。
- 禁止把“无 down SQL”当作“无需恢复方案”。

## 6. 测试要求

- `test_nonDestructiveMigration_mayDeclareNoDownReason`
- `test_destructiveMigration_requiresPreBackup`
- `test_applyMigration_recordsChecksum`
- `test_failedMigration_rollsBackOrRestoresBackup`
- `test_migrationLock_preventsConcurrentSchemaChange`
