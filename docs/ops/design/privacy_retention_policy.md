# Privacy, Notification, Report Retention, and Masking Policy

## 1. 目的

修复 QM-AUD-016，并落实用户拍板 D-05：普通 raw、audit、report 默认保留 1 年并提供手动归档按钮/CLI；可信最终库不自动清理，异常 payload 依领域频率规则留存。

## 2. 状态机

报告状态：

```text
DRAFT -> READY_FOR_REVIEW -> APPROVED_TO_SEND -> SENT -> ARCHIVED
DRAFT -> FAILED
READY_FOR_REVIEW -> CANCELLED
```

通知状态：

```text
PENDING -> SENT
PENDING -> SUPPRESSED_BY_DEDUP
PENDING -> SUPPRESSED_BY_COOLDOWN
PENDING -> FAILED_RETRYABLE -> RETRYING -> SENT
PENDING -> FAILED_FINAL
```

## 3. 去重键

```text
dedup_key = hash(notification_type + severity + layer_id + subject_id + event_time_bucket + rule_version)
```

## 4. 隐私分级

| 级别            | 内容                        | 处理              |
| --------------- | --------------------------- | ----------------- |
| public_market   | 行情、指数、公告公开信息    | 可入报告          |
| internal_system | 本机路径、错误日志、任务 ID | 默认不外发        |
| sensitive_user  | 邮箱、token、账号、终端路径 | 必须 mask         |
| secret          | API key、cookie、password   | 禁止进入报告/通知 |

## 5. 已拍板留存策略（D-05）

第一版采用低空间策略：

```text
普通 raw 文件：默认保留 1 年
普通 audit log：默认保留 1 年
report snapshot：默认保留 1 年
notification_log：默认保留 1 年
可信最终库：不由本策略自动清理
被回补替代的异常 payload：按领域频率基线与最长计算窗口保留
secret-like error payload：不得保存原文
```

删除/清理前必须支持：

```text
手动归档按钮或 CLI
归档目录 manifest
归档 hash 校验
清理 dry-run
```

推荐 CLI：

```bash
qmd archive --kind raw --before 365d --dry-run       # 仅普通 raw
qmd archive --kind audit --before 365d --dry-run     # 仅普通 audit
qmd archive --kind reports --before 365d --dry-run
```

## 6. 测试要求

- `test_retentionPolicy_defaultsToOneYear`
- `test_archiveBeforeDelete_requiresDryRun`
- `test_secretLikePayload_isMaskedBeforePersist`
- `test_notificationDedupKey_isStable`

## 7. 用户决策补充

D-04 与 D-05 已拍板：

- 第一版默认通知渠道为前端 Notification Center。
- 邮件通知可以作为可选渠道，但必须用户显式配置。
- 不实现多 webhook 默认发送。
- 普通 raw/audit/report/notification 默认保留 1 年；可信最终库和异常 payload 适用各自留存规则。
- 必须提供手动归档按钮或 CLI，归档后再清理。

`qmd archive --before 365d` 必须先按数据类型拒绝可信最终库和不满足保留期的异常 payload；只有
主源验证写入、异常归档成功、审计索引完整后才允许清理。异常 payload 的具体期限和精简审计索引
规则以 `specs/contracts/design/source_provenance_quality_contract.yaml` 为准。
