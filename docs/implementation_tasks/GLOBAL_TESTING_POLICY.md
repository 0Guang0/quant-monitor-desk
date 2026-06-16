# Global Testing Policy

本测试策略来自项目约束与用户上传的测试规范。目标是让测试验证业务行为，而不是验证内部实现细节。

## 1. Mock 边界

允许 mock：

- 数据库连接。
- HTTP 调用。
- 文件系统 I/O。
- 消息队列。
- 第三方 API。
- 邮件、Webhook、桌面通知等外部通知渠道。

不应 mock：

- 纯计算逻辑。
- 条件分支。
- 状态判断函数。
- schema 校验逻辑。
- ResourceGuard 判断逻辑本身。

## 2. 断言要求

每个测试必须至少包含一个对业务语义有意义的断言，例如：

- 返回值是否等于业务预期。
- 状态是否发生正确变化。
- 持久化结果是否包含正确字段。
- 质量标记、错误码、warning 是否符合业务规则。

禁止把 `assertNotNull`、`assertDoesNotThrow` 作为唯一断言。

## 3. 不应断言的内容

除非顺序本身是业务约束，否则不要断言：

- private 方法是否被调用。
- private 方法被调用次数。
- 两个协作方法的内部调用顺序。
- 与业务结果无关的内部实现细节。

## 4. 必测场景

每个模块至少覆盖：

- 正常路径。
- 空值或缺失输入。
- 边界值。
- 异常路径。
- 资源限制路径。
- 数据质量失败路径。
- 不允许动作被拦截路径。

## 5. 测试命名

推荐：

```text
functionName_condition_expectedBehavior
```

例如：

```text
validate_sourceConflict_shouldCreateManualReviewQueue
resourceGuard_lowDisk_shouldPauseBackfill
```

## 6. 覆盖率策略

初期不追求机械 80% 覆盖率。优先覆盖：

- WriteManager。
- ResourceGuard。
- DataQualityValidator。
- SourceConflictValidator。
- Layer 1 / Layer 3 loader。
- Agent / Notification 的 No Action Semantics Guard。

每个 implementation task 必须写清本任务最低测试要求。
