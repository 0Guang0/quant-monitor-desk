# 数据验证、冲突治理、写入与并发模块（兼容索引）

> 状态：已在 P0 第一轮扩展中拆分为两个实现级模块。  
> 原 v1.6 内容没有删除，核心原则已分别迁移并扩展到下列文件：

```text
docs/modules/data_validation_and_conflict.md
docs/modules/write_manager.md
```

## 当前权威文件

| 主题 | 权威文件 |
|---|---|
| DataQualityValidator | `docs/modules/data_validation_and_conflict.md` |
| SourceConflictValidator | `docs/modules/data_validation_and_conflict.md` |
| ReconcileJob 冲突重抓 | `docs/modules/data_validation_and_conflict.md` |
| ValidationReport / data_quality_log / source_conflict | `docs/modules/data_validation_and_conflict.md` |
| DuckDBWriteManager | `docs/modules/write_manager.md` |
| 单写多读、事务、回滚、写入审计 | `docs/modules/write_manager.md` |

## 保留原则

```text
staging → validation → WriteManager → clean table
```

本文件仅作为兼容入口保留，避免旧链接失效；后续实现请引用拆分后的两个权威文件。
