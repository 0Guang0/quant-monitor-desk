# 最终交付包规则

最终统一 zip 必须是可直接交给 Claude Code / Codex 执行实施的工程文档包。

## 必须保留

```text
README.md
MIGRATION_MAP.md
MANIFEST.json
FINAL_AUDIT_REPORT.md

docs/architecture/
docs/modules/
docs/api/
docs/ops/
docs/adr/
docs/quality/
docs/implementation_tasks/

specs/
```

## 不得保留

```text
source_packages/ 原始 zip
docs/archive/ 旧版归档文件
临时 round progress report
一次性 self-check 文件
task_plan.md / findings.md / progress.md
scratch / tmp / draft 文件
重复旧 zip
未被 README / MANIFEST / 模块文档引用的中间产物
```

## 兼容索引规则

允许保留兼容索引文件，但必须明确标注“不作为权威实现文件”，并指向当前权威模块文件。

当前允许的兼容索引：

```text
docs/modules/data_validation_write_concurrency.md
docs/modules/fastapi_and_frontend.md
```

## 本机资源约束

本机资源限制文件属于正式实现约束，必须保留：

```text
docs/ops/performance_limits.md
specs/contracts/resource_limits.yaml
docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md
```
