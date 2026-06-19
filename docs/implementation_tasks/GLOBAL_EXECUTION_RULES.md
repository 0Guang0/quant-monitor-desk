# Global Execution Rules

## 1. 执行边界

所有 implementation task 必须遵守：

- 不做无关重构，不做 drive-by refactor。
- 不引入未经任务文件允许的新框架或大型依赖。
- 不破坏 `Primary / Validation / FallbackPolicy` 数据源口径。
- 不恢复旧的 `Primary / Shadow / Emergency` 命名。
- 不破坏 `Layer 3` 是“全球产业链资金震动锚点层”的定义。
- 不让 `Layer 3` 重复保存 `Layer 5` 的全量历史行情。
- 不让 Agent 自由 SQL、自由联网、直接写库或输出交易动作。
- 不让前端页面设计、排版、视觉风格被写死。前端正式实现前必须提醒用户亲自确认 UI、信息层级、布局和交互方式。
- 不绕过 `DuckDBWriteManager` 写 clean table。
- 不在本机默认模式下执行高内存、高 CPU、大磁盘扫描任务。

## 2. 执行流程

每个任务按以下流程执行：

1. 读取全局规则文件。
2. 读取当前任务文件。
3. 读取任务文件列出的输入文档、spec、contract。
4. 先写测试或 smoke test 约束，再实现。
5. 运行任务文件指定的验收命令。
6. 汇报改动文件、测试结果、未完成项、资源保护是否触发。

## 3. 用户确认点

以下情况必须停止并请用户确认：

- 需要改变核心架构或技术栈。
- 需要新增大型依赖或外部服务。
- 需要改变前端页面最终布局、风格、信息层级。
- 需要提高 ResourceGuard 限制。
- 需要执行全量回补、全历史审计或大范围扫描。
- 需要真实账户、真实 API key、真实交易账户或付费服务。

## 4. 完成报告格式

每个任务完成后，AI 必须报告：

- 改动文件清单。
- 新增文件清单。
- 删除文件清单。
- 执行的测试命令。
- 测试结果。
- ResourceGuard 是否触发。
- 是否有未完成项或需要用户确认的点。

## 5. 用户已拍板全局决策

执行所有任务时必须遵守 D-01 至 D-12：

- Python 默认使用 `uv.lock`，命令使用 `uv sync` / `uv run`。
- API dev 可关闭鉴权但仅 loopback；prod 必须 Bearer token。
- Secret 第一版使用 `.env.local`，只提交 `.env.example`，CI 必须 secret scan。
- 通知默认前端 Notification Center，邮件可选，不启用多 webhook。
- raw/audit/report 默认留存 1 年，并提供手动归档。
- 破坏性 migration 用备份恢复，非破坏性 migration 可无 down SQL。
- Trellis/Cursor 每轮只长期保留 MASTER/AUDIT/DECISIONS，细碎 evidence 归档。
- 前端正式实现前必须提醒用户确认 UI 信息架构。
- 完整标准化字段仅 Layer 1 使用。
- 设计包只放 docs/specs/tasks，源码和测试结果以 Git commit + CI 终审。
- QMT 第一版默认禁用，用户确认授权后再启用。
- Agent 只读固定来源与用户手动导入文本，禁止自由联网搜索。

## 决策标签补充

- D-03：Secret 第一版使用 `.env.local`；只提交 `.env.example`；必须配置 `.gitignore`、prod 启动检查与 secret scan。
