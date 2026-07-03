# ROUND 5 INTEGRATION RELEASE

本目录的当前 canonical execution package 是 `BATCH_05_VERIFIED_AUDIT_SECURITY_RELEASE/`。Loose `031`–`036` task files are historical inputs unless a Batch 05 card explicitly references them.

Round5 work must not implement product features that belong to Round 3G or Round4; it turns security, integration, resource, and release checks into gates. Missing Round3G/Round4 capability must block release or be listed in the manifest with owner and closure test, not become a new Round5 feature micro-slice.

执行前读取：

- `../GLOBAL_EXECUTION_RULES.md`
- `../GLOBAL_TESTING_POLICY.md`
- `../GLOBAL_RESOURCE_LIMITS.md`
- `../GLOBAL_TASK_TEMPLATE.md`

本目录文件不是临时文件，最终交付包应保留。不要删除 loose historical cards，除非已经完成路径引用审计并添加 redirect/pointer。
