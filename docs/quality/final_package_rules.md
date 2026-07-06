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

## 审计修复 v1.1 新增正式文件

以下文件属于正式文档包，最终清理不得删除：

```text
MIGRATION_MAP.md
specs/datasource_registry/source_registry.yaml
specs/contracts/runtime_versions.md
specs/contracts/snapshot_lineage_contract.yaml
specs/contracts/api_security_contract.yaml
specs/contracts/backtest_reproducibility_contract.yaml
specs/contracts/release_cleanup_allowlist.yaml
docs/ops/config_secret_policy.md
docs/ops/migration_recovery_policy.md
docs/ops/lock_and_concurrency_policy.md
docs/ops/idempotency_retry_dlq_policy.md
docs/ops/agent_security_policy.md
docs/ops/privacy_retention_policy.md
docs/ops/frontend_security_policy.md
docs/quality/staged_acceptance_policy.md
```

最终清理脚本必须读取 `specs/contracts/release_cleanup_allowlist.yaml` 并先 dry-run。

## 用户决策补充：过程材料与设计包边界

落实 D-07 与 D-10：

```text
每轮只长期保留任务卡 / 审计结论 / 决策记录 / 关键执行清单。
细碎 evidence、red/green log、临时截图、skill reads 应归档到 artifacts zip，不得长期堆在主仓库或最终设计包。
设计包保持轻量，只包含 docs/specs/tasks；实现源码和测试结果通过 Git commit + CI 结果终审。
```

## MANIFEST 自校验规则

`MANIFEST.json` 不得把自身作为普通文件条目记录 sha256，因为文件内容一旦写入自身 hash 就会改变，无法稳定校验。

最终发布脚本必须采用以下策略：

```text
MANIFEST.json 不出现在 files[] 中；
files[] 记录除 MANIFEST.json 以外全部正式文件的 path、size_bytes、sha256；
顶层记录 manifest_self_policy: exclude_self_from_file_hashes；
顶层记录 generated_at_utc、root_dir、file_count_excluding_manifest；
验收测试必须包含 test_manifestSelfHashPolicy_isVerifiable。
```

`FINAL_AUDIT_REPORT.md` 属于本设计包的正式交付文件，必须进入 allowlist、MANIFEST files[] 和最终 zip。
