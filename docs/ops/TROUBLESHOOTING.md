# Troubleshooting

本页是用户/运维排障入口。具体错误码见 `ERROR_CODE_GUIDE.md`，场景化处理见 `incident_playbook.md`。

## 常见问题

### 数据源显示 disabled

1. 查看 SourceRoutePlan。
2. 确认 source 是否 `enabled_by_default=false`。
3. QMT / Yahoo / qmt_xqshare 默认禁用是安全设计，不是 bug。
4. 不得修改代码绕过 disabled gate。

### ResourceGuard 暂停

1. 缩小日期范围或 universe。
2. 清理可销毁缓存。
3. 使用 backfill shard。
4. 不得关闭 ResourceGuard。

### Schema drift

1. 不写 clean 表。
2. 保存 raw evidence 与 fetch_log。
3. 更新 adapter schema mapping 与 capability contract。
4. 增加 regression test。

### DuckDB locked

1. 等待 writer 完成。
2. 确认没有多进程 writer。
3. 若是测试残留，清理临时 DB。

### 前端无法解释数据来源

1. 检查 route_status / source_used / quality_flags。
2. 若缺 SourceRoutePlan，说明仍在旧路径，需要收敛到 DataSourceService 正式入口。

## 相关文件

- `docs/ops/ERROR_CODE_GUIDE.md`
- `docs/ops/incident_playbook.md`
- `docs/ops/data_sync_quick_reference.md`
