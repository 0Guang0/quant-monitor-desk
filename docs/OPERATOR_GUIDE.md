# Operator Guide

## 1. 常用入口

- 初始化与验证：`docs/ops/verification_commands.md`
- 数据同步速查：`docs/ops/data_sync_quick_reference.md`
- 错误排障：`docs/ops/ERROR_CODE_GUIDE.md`
- 场景手册：`docs/ops/incident_playbook.md`

## 2. 安全运行原则

1. 先 dry-run，再写入。
2. 先 route-preview，再 fetch。
3. 遇到 disabled source，不要手工绕过代码。
4. 遇到 ResourceGuard 暂停，缩小范围或分片。
5. 生产等价验证只使用临时 DB、fixture-scale 数据或只读/脱敏快照。

## 3. QMT / xqshare

QMT 本地源和 qmt_xqshare 远程源默认禁用。启用前必须用户确认授权、配置路径或 env，并接受安全边界。
