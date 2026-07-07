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
- 不把 degraded/fallback/validation-only 数据伪装成正常 Primary 数据。
- 不把 mock、replay、staged fixture 或 dry-run 结果冒充 live 成品验收。
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
- 需要改变 `Primary / Validation / FallbackPolicy`、clean 写入等级、fallback 降级语义或生产等价验收边界。

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
- 过程材料长期只保留任务卡、审计结论、决策记录；细碎 evidence 归档或删除。
- 前端正式实现前必须提醒用户确认 UI 信息架构。
- 完整标准化字段仅 Layer 1 使用。
- 设计包只放 docs/specs/tasks，源码和测试结果以 Git commit + CI 终审。
- QMT 第一版默认禁用，用户确认授权后再启用。
- Agent 只读固定来源与用户手动导入文本，禁止自由联网搜索。

## 参考项目采纳红线

允许吸收 JQ2PTrade、EasyXT、ptqmt-site 的 mapping-first、低耦合、local-only disclosure 和诊断工具入口思路，但禁止直接采纳以下能力：

- 真实交易、自动下单、order/order_target/order_value 等 API。
- QMT 自动登录、验证码识别、终端控制或远程端口自动探测。
- silent fallback 或无 SourceRoutePlan 的源切换。
- 未带 `source_used`、`source_role`、`source_switched`、`quality_flags` 的降级 clean 写入。
- 任意执行用户策略代码、`compile/exec`、无限制 import、外部网络访问。
- 未经用户确认新增重型依赖；真实源/QMT/xqshare 依赖必须为 optional extras。
