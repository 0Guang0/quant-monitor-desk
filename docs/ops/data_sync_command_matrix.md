# Data Sync Command Matrix（Round2.6）

| 场景 | 命令形态 | 默认写入 | 必须检查 | 失败文档 |
|---|---|---:|---|---|
| 初始化 DB/registry | `qmd data init-basic --dry-run` | 否 | schema/migration/source_registry | `ERROR_CODE_GUIDE.md` |
| 预览路由 | `qmd data route-preview --domain ...` | 否 | SourceRoutePlan/capability/platform matrix | `incident_playbook.md#disabled-source` |
| 日线同步 | `qmd data sync --domain market_bar_1d --dry-run` | 否 | ResourceGuard/route/idempotency/fetch_log | `ERROR_CODE_GUIDE.md#schema-drift` |
| 公告索引 | `qmd data sync --domain announcement --since ... --dry-run` | 否 | capability/file registry/raw evidence | `ERROR_CODE_GUIDE.md#not-published-yet` |
| 健康检查 | `qmd data health --domain ...` | 否 | source_health/fetch_log | `ERROR_CODE_GUIDE.md#resource-guard-paused` |
| 生产等价 smoke | `python scripts/production_equivalent_smoke.py` | 临时/受控 | cleanup/resource guard/schema | `incident_playbook.md#production-equivalent-smoke` |

## 约束

- 设计阶段只定义命令矩阵，不新增 CLI 代码。
- 所有写路径必须有 dry-run 与可回滚边界。
- 所有失败必须输出 error code 与 docs anchor。
