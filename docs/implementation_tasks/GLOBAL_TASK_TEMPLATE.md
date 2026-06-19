# Global Task Template

每个 implementation task 必须按这个结构书写和执行。

## 1. 任务目标

一句话说明本任务要交付什么。

## 2. 预期结果

用户或系统能看到的结果。

## 3. 输入文件

必须读取的 docs / specs / contracts。

## 4. 相关代码文件

需要创建或修改的代码路径。

## 5. 现有模式 / 参考

应遵守的项目内已有设计。

## 6. 技术约束

语言、框架、依赖、schema、API、前端或 Agent 限制。

## 7. 资源约束

ResourceGuard 要求与低占用边界。

## 8. 边界约束

不得修改、不得破坏、不得引入的内容。

## 9. 实现步骤

5-10 个可执行步骤。

## 10. 测试要求

单元测试、集成测试、smoke test、fixture。

## 11. 验收命令
按任务类型选择阶段化验收命令，不得无差别套用 full pytest：

```bash
uv sync --locked
uv run pytest -q <targeted-tests>
uv run ruff check .
uv run python -m compileall backend scripts tests
```

前端任务还必须运行：

```bash
cd frontend && npm ci && npm audit --audit-level=high && npm run typecheck && npm run build
```

文档/发布规则任务运行文档链接、allowlist、manifest 校验，不强制运行尚未创建源码的 full test suite。

## 12. 完成标准

可验证的完成条件。

## 13. Red Flags

出现这些行为说明任务偏离，应停止并修正。

## 14. 输出要求

最终汇报必须包含改动文件、测试结果、未完成项、资源保护状态。

## 15. 审计修复新增强制项

所有 implementation task 还必须显式处理以下审计修复项：

1. **版本与锁文件**：读取 `specs/contracts/runtime_versions.md`，说明 Python/Node/npm/依赖锁文件策略。
2. **阶段化验收**：读取 `docs/quality/staged_acceptance_policy.md`，不得把所有任务都套用同一条验收命令；docs-only、backend、frontend、release 分层验收。
3. **回滚与恢复**：涉及数据库、文件写入、清理、发布的任务必须说明失败后如何 rollback/restore。
4. **幂等与重试**：涉及同步、通知、报告、回测、发布的任务必须定义幂等键、重试策略、死信或人工复核路径。
5. **安全与隐私**：涉及 API、Agent、通知、前端、配置的任务必须说明鉴权、脱敏、留存、提示注入或 XSS/CSP 边界。
6. **lineage / as-of**：涉及建模、快照、回测的任务必须写入 as-of、source hash、rule version、parameter hash。
7. **测试质量**：测试必须断言业务语义，不得只断言“不报错”。
