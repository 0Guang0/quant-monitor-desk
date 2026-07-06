# Agent 工具路由（场景 · 全员必读）

> **路径：** 仓库根 `agent-toolchain.md`

## GitNexus MCP（按场景）

| 场景                       | 用                                                                | 不用               |
| -------------------------- | ----------------------------------------------------------------- | ------------------ |
| 不熟模块、找入口           | `query` + skill `gitnexus-exploring`                              | 全库盲 grep        |
| **改函数/类前**            | MCP `impact()` + `gitnexus-impact-analysis`                       | 直接改             |
| 提交前看改动面             | MCP `detect_changes()`                                            | 只看 git diff 肉眼 |
| 测试红、栈对不上、回归不明 | `systematic-debugging` → `diagnosing-bugs` → `gitnexus-debugging` | 反复猜改           |
| rename / 拆模块 / 提取     | MCP `rename` + `gitnexus-refactoring`                             | find-replace       |
| 不知道 MCP 参数            | `gitnexus-guide`                                                  | 乱试工具           |

## 文档导航

| 场景                     | 先读                                                 |
| ------------------------ | ---------------------------------------------------- |
| 不熟仓库 / 模块在哪      | `openwiki/quickstart.md`（init 后）                  |
| 契约 / schema / registry | `specs/contracts/`、`specs/`\*\*                     |
| 模块设计 / 活规划        | `docs/modules/`、`PROJECT_IMPLEMENTATION_ROADMAP.md` |
| 领域术语                 | `CONTEXT.md`（有则读）、`docs/adr/`                  |

**优先级：** `specs/docs` + ADR > OpenWiki > 其他叙述文档。

## grill-gate（澄清）

scope / AC / 边界说不清 → Read `.claude/skills/grill-me/SKILL.md` → **对话里问用户** → 收到回复后再写码。

禁止：猜意图、自问自答、未问就写「用户认为…」。

## 实现规范

| 场景           | 用                                           |
| -------------- | -------------------------------------------- |
| 先写失败测试   | `/test-driven-development`                   |
| 代码与测试风格 | `karpathy-guidelines` + `testing-guidelines` |
| 工程契约全程   | `.cursor/rules/project-global.mdc`           |

## 条件 skill（触发才 Read）

| Skill                               | 触发                                         |
| ----------------------------------- | -------------------------------------------- |
| `systematic-debugging`              | RED 意外 PASS · GREEN 仍 FAIL · 同错 ≥2 轮   |
| `diagnosing-bugs`                   | systematic 后仍卡住                          |
| `gitnexus-debugging`                | 调用栈仍不明                                 |
| `source-driven-development`         | 外部 API/契约/SDK · `specs/contracts` 新字段 |
| `deprecation-and-migration`         | deprecate/remove/migrate/双轨 · 破坏性 API   |
| `observability-and-instrumentation` | ops/写路径/pipeline · AC 要 log/metric/trace |

## 验证

- 正式改动：`uv run pytest -q` 全绿（exit 0）
