# 通知与报告模块

> 权威定位：本文件定义日报、周报、数据质量报告、盘中提醒、人工确认清单、回测复盘报告与通知发送流程。它负责“报告结构、归档和发送”，不负责生成未经验证的市场观点。  
> 重要边界：提醒和报告不是交易信号，不输出买、卖、加仓、减仓、入场、出场等动作语义。

---

# 1. 模块目标

通知与报告模块回答：

```text
今天系统运行是否正常？
五层状态有什么值得关注的结构性变化？
哪些数据源失败、过期或冲突？
哪些证据链需要人工确认？
哪些盘中提醒已经触发、去重、冷却或发送失败？
哪些回测/复盘结论需要进一步验证？
```

报告不输出：

```text
买卖建议
仓位建议
收益承诺
未经证据链支持的结论
自动交易动作
```

---

# 2. 报告类型

| report_type              | 中文名         | 频率          | 说明                                   |
| ------------------------ | -------------- | ------------- | -------------------------------------- |
| `daily_market_report`    | 每日市场报告   | 每日盘后      | 五层状态、异常、事件、证据链摘要       |
| `weekly_review_report`   | 周度复盘报告   | 每周          | 状态变化、数据质量、市场结构复盘       |
| `data_quality_report`    | 数据质量报告   | 每日/任务后   | 数据源失败、冲突、滞后、缺失           |
| `manual_review_report`   | 人工确认清单   | 有需要时      | 严重冲突、Agent 输出失败、schema drift |
| `intraday_alert`         | 盘中提醒       | 盘中          | 只提醒异常事实，不给交易动作           |
| `ops_health_report`      | 运维健康报告   | 每日/每周     | 备份、磁盘、任务、API、Agent 状态      |
| `backtest_review_report` | 回测与复盘报告 | 用户触发/定期 | 规则触发历史表现、误报、证据复盘       |

---

# 3. 报告输入

报告只能使用结构化数据：

```text
axis_interpretation_snapshot
cross_asset_daily_snapshot
industry_chain_daily_snapshot
market_breadth_snapshot
market_sector_snapshot
security evidence_chain
data_quality_log
source_conflict
manual_review_queue
agent_run_log
ops_health_check_result
backtest_run_log
backtest_metric_snapshot
```

Agent 可以参与自然语言改写，但必须基于结构化 facts_used_json，输出必须通过 NoActionSemanticGuard。

---

# 4. 表结构

## 4.1 report_registry

```sql
CREATE TABLE IF NOT EXISTS report_registry (
    report_id           VARCHAR PRIMARY KEY,
    report_type         VARCHAR,
    report_date         DATE,
    title               TEXT,
    summary             TEXT,
    local_path          TEXT,
    status              VARCHAR,
    generated_by        VARCHAR,
    generated_at        TIMESTAMP,
    quality_flag        VARCHAR,
    needs_human_review  BOOLEAN
);
```

## 4.2 report_section

```sql
CREATE TABLE IF NOT EXISTS report_section (
    section_id          VARCHAR PRIMARY KEY,
    report_id           VARCHAR,
    section_order       INTEGER,
    section_type        VARCHAR,
    title               TEXT,
    content_markdown    TEXT,
    facts_used_json     JSON,
    quality_warnings_json JSON,
    created_at          TIMESTAMP
);
```

## 4.3 notification_log

```sql
CREATE TABLE IF NOT EXISTS notification_log (
    notification_id     VARCHAR PRIMARY KEY,
    alert_id            VARCHAR,
    report_id           VARCHAR,
    channel             VARCHAR,
    recipient           VARCHAR,
    status              VARCHAR,
    attempt_count       INTEGER,
    last_error_code     VARCHAR,
    sent_at             TIMESTAMP,
    created_at          TIMESTAMP
);
```

## 4.4 alert_event

```sql
CREATE TABLE IF NOT EXISTS alert_event (
    alert_id              VARCHAR PRIMARY KEY,
    alert_type            VARCHAR,
    severity              VARCHAR,
    source_layer          VARCHAR,
    target_id             VARCHAR,
    title                 TEXT,
    summary               TEXT,
    trigger_reason_code   VARCHAR,
    facts_used_json       JSON,
    evidence_ids_json     JSON,
    quality_flags_json    JSON,
    dedup_key             VARCHAR,
    cooldown_until        TIMESTAMP,
    status                VARCHAR,
    no_action_semantics   BOOLEAN,
    created_at            TIMESTAMP
);
```

---

# 5. 盘中提醒规则

盘中提醒只允许基于明确事实触发，分为 6 类。

| alert_type                      | 来源                                           | 触发示例                                      | 默认等级   |
| ------------------------------- | ---------------------------------------------- | --------------------------------------------- | ---------- |
| `data_quality_alert`            | DataQualityValidator / SourceConflictValidator | 主源失败、数据滞后、严重冲突、schema drift    | DATA_RISK  |
| `layer1_state_alert`            | Layer 1 五轴                                   | 极端水位、突变、历史不足、source switched     | WATCH/WARN |
| `layer2_cross_asset_alert`      | Layer 2 跨资产                                 | VIX、美元、铜、油、美债等 P0 资产出现异常变化 | WATCH/WARN |
| `layer3_anchor_alert`           | Layer 3 产业链                                 | P0 anchor 事件、P0 source 更新、跨链边触发    | WATCH/WARN |
| `layer4_market_structure_alert` | Layer 4 市场结构                               | 市场宽度突变、涨跌停异常、期权波动异常        | WATCH/WARN |
| `layer5_evidence_alert`         | Layer 5 证据链                                 | 公告、财报、事件、成交量/价格异常需要人工确认 | WATCH/WARN |

提醒等级：

```text
INFO：普通信息
WATCH：观察
WARN：异常
CRITICAL：严重异常
DATA_RISK：数据质量风险
OPS_RISK：系统资源/运行风险
```

硬规则：

```text
1. 只基于已通过 validation 的数据。
2. 只读取 snapshot / evidence / audit summary，不触发大范围回补。
3. 不输出交易动作。
4. 必须有 dedup_key，避免重复提醒。
5. 必须有 cooldown，避免连续轰炸。
6. 必须能展开 facts_used_json 和 evidence_ids。
7. 数据质量风险优先标为 DATA_RISK，不解释为市场风险。
8. ResourceGuard 处于 PAUSE / STOP_NON_CORE 时，只允许 OPS_RISK 与 DATA_RISK 提醒。
```

---

# 6. 去重、冷却与节流

## 6.1 dedup_key

建议格式：

```text
{alert_type}:{source_layer}:{target_id}:{trigger_reason_code}:{as_of_date}
```

相同 dedup_key 在同一个交易日内只保留一条主提醒，后续变化写入 `alert_event.facts_used_json` 或 `notification_log`。

## 6.2 cooldown

默认冷却：

| severity  | cooldown |
| --------- | -------: |
| INFO      |   4 小时 |
| WATCH     |   2 小时 |
| WARN      |   1 小时 |
| CRITICAL  |  15 分钟 |
| DATA_RISK |  30 分钟 |
| OPS_RISK  |  30 分钟 |

## 6.3 throttle

本机默认低打扰。默认本地通知节流仅适用于 `dashboard_notification`、`local_audit_log`、`console_summary` 与显式配置后的 optional `email`：

```text
每小时最多 10 条普通提醒
CRITICAL / DATA_RISK 不进入普通提醒上限，但仍要去重
webhook / desktop_notification / SMS / phone / bot / Slack / Discord / Telegram / 企业微信均默认禁用；未完成独立授权、配置和契约前，不实现发送逻辑，也不实现该禁用渠道的节流逻辑
```

必须补测试：`test_defaultNotificationThrottle_excludesDesktop`、`test_notificationModule_containsNoActiveDesktopThrottleWhenDisabled`。

---

# 7. 通知渠道

第一阶段默认渠道：

| channel                  | 默认 | 说明                              |
| ------------------------ | ---- | --------------------------------- |
| `dashboard_notification` | 开启 | 前端通知中心，必须实现            |
| `local_markdown`         | 开启 | 写入 reports / intraday 目录      |
| `local_html`             | 可选 | 便于浏览器打开                    |
| `local_audit_log`        | 开启 | 写 notification_log / alert_event |
| `console_summary`        | 开启 | CLI 运行时输出摘要                |

可选渠道：

| channel                | 默认 | 说明                                 |
| ---------------------- | ---- | ------------------------------------ |
| `desktop_notification` | 延期 | D-13+ 重新拍板前不得实现真实发送逻辑 |
| `email`                | 关闭 | 用户配置 SMTP 后开启                 |
| `webhook`              | 延期 | D-13+ 重新拍板前不得实现真实发送逻辑 |

第一阶段不建议：

```text
短信
电话
自动下单接口
第三方群发机器人默认开启
```

通知失败不得影响数据写入主流程，只写 `notification_log`。

---

# 8. 通知消息结构

```json
{
  "notification_id": "...",
  "alert_id": "...",
  "severity": "WATCH",
  "source_layer": "Layer3",
  "target_id": "AI_COMPUTE",
  "title": "AI 算力链发生锚点异动",
  "summary": "NVIDIA / HBM / 服务器链条出现联动变化",
  "evidence_ids": ["..."],
  "quality_flags": [],
  "dedup_key": "layer3_anchor_alert:Layer3:AI_COMPUTE:P0_ANCHOR_EVENT:2026-06-14",
  "no_action_semantics": true,
  "created_at": "..."
}
```

---

# 9. 报告生成流程

```text
ReportJob 触发
    ↓
读取结构化快照和日志
    ↓
生成 report_context
    ↓
调用 Agent 生成解释段落，如果需要
    ↓
NoActionSemanticGuard 检查
    ↓
写 report_registry / report_section staging
    ↓
WriteManager 写 clean table
    ↓
渲染 Markdown / HTML
    ↓
写本地 reports 目录
    ↓
通知发送，如启用
```

---

# 10. 每日报告结构

建议章节：

```text
1. 今日摘要
2. 数据质量状态
3. Layer 1 五轴状态
4. Layer 2 跨资产传感器
5. Layer 3 产业链锚点
6. Layer 4 市场结构
7. Layer 5 个股/合约证据链
8. 盘中提醒回顾
9. 需要人工确认事项
10. 边界提醒：不构成交易建议
```

---

# 11. API 契约

```text
GET /api/reports/daily
GET /api/reports/{report_id}
GET /api/reports/{report_id}/sections
POST /api/reports/generate
GET /api/notifications
GET /api/notifications/{notification_id}
GET /api/notifications/logs
POST /api/notifications/{notification_id}/ack
POST /api/notifications/{notification_id}/mute
```

---

# 12. CLI 契约

```bash
python -m quant_monitor.reports.generate --type daily_market_report --date 2026-06-14
python -m quant_monitor.alerts.run_intraday_check --mode eco
python -m quant_monitor.notifications.send_pending --channel dashboard_notification
```

---

# 13. 验收测试

```text
盘中提醒必须有 dedup_key
盘中提醒必须有 cooldown_until
通知失败不得回滚 report_registry
所有报告必须有 no_action_semantics=true
Agent 报告段落触发禁用词时进入 manual_review
ResourceGuard PAUSE 时只允许 DATA_RISK / OPS_RISK 提醒
用户未启用 email 时不得发送外部通知；webhook/desktop/SMS/phone/bot 均延期到 D-13+，第一版不得实现真实发送逻辑
```

## 用户决策补充：通知渠道与留存

落实 D-04/D-05：

```text
默认通知渠道：前端 Notification Center。
可选渠道：email，由用户显式配置 SMTP 与收件人后启用。
禁止第一版默认启用：多 webhook、短信、电话、群机器人。
默认留存：notification/report 1 年。
清理前必须支持 archive/export。
```

如果实现角色需要新增 webhook、短信或机器人通知，必须作为 D-13+ 新决策交用户拍板。

## D-04 第一版通知渠道硬约束

第一版通知渠道只允许：

```text
默认：前端 Notification Center / dashboard_notification、local_markdown、local_audit_log、console_summary
可选：email（必须用户显式配置 SMTP 与收件人）
```

以下渠道全部延期到 D-13+ 再拍板，不得在第一版实现真实发送逻辑，也不得预留可误触发的 webhook 发送 skeleton：

```text
webhook、desktop_notification、SMS、phone_call、bot、Slack、Discord、Telegram、企业微信
```

如果执行角色认为必须新增外部通知渠道，必须先停止并请用户拍板。
