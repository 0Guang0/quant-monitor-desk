# Agent 工作流边界与信任模型

> 本文说明仓库中 `.cursor/`、`.trellis/` 的用途、入库策略，以及 Cursor hooks 的信任边界。  
> 适用读者：新贡献者、AI agent 操作者、安全审查。

---

## 1. 为何这些目录在仓库里

| 目录 | 是否入库 | 用途 |
|------|----------|------|
| `.trellis/` | 是（spec、tasks、scripts） | Trellis 任务编排、编码规范、工作流脚本 |
| `.trellis/workspace/` | 视项目政策 | 开发者会话日志；可能含过程性记录 |
| `.cursor/` | 是（hooks、skills 等） | Cursor IDE 集成：hooks、项目级 skills/rules |
| `.cursor/hooks/` | 是 | Session 启动时注入上下文（Python 脚本） |

**结论：** 上述目录**有意**纳入版本控制，以支持 Trellis 多阶段任务与 Cursor agent 协作。这不是误提交的运行时垃圾；请勿在 Repair 中批量删除。

---

## 2. Cursor hooks 信任边界（SEC-2）

`.cursor/hooks/` 下的 Python 脚本在 **Cursor 本地会话** 中由 IDE 触发，例如：

- `session-start.py` — 会话开始时注入项目上下文
- `inject-subagent-context.py` — 子 agent 派发前注入任务上下文
- `inject-shell-session-context.py` — shell 会话上下文

**威胁模型：**

- 脚本仅在本机、已信任的开发环境中运行；**不会**随 FastAPI 后端或前端 bundle 部署到生产。
- 贡献者应审查 hook 变更，与审查应用代码同等对待。
- 不要在 hook 中硬编码密钥；敏感值走 `.env`（已 gitignore）。

**CI：** GitHub Actions **不**执行 `.cursor/hooks/`；后端/前端构建路径与 hooks 隔离。

---

## 3. Trellis 任务与 workspace（SEC-3）

- **权威任务状态：** `.trellis/tasks/<slug>/`（PRD、plan、jsonl 上下文）
- **编码规范：** `.trellis/spec/` — agent 写代码前应读取对应 package/layer 指南
- **workspace 日志：** `.trellis/workspace/` 可能含对话摘要或调试笔记；是否 ignore 由项目政策决定，当前多数 task 元数据入库以便跨会话恢复

Agent 应优先读 `.trellis/tasks/` 与 `.trellis/spec/`，而非猜测未文档化的约定。

---

## 4. Clean checkout 与 agent 协作

新 clone 后建议顺序：

1. `pip install -e ".[dev]"`
2. `python scripts/init_db.py` — 创建 `data/duckdb` 等运行时目录（**pytest 不自动创建**）
3. `cd frontend && npm ci`
4. 复制 `.env.example` → `.env`；路径变量留空则使用仓库默认（见 `.env.example` 注释）

Agent 修改代码时：

- **不要**提交 `data/` 运行时产物
- **不要**在无 impact 分析时改 `backend/app/db/connection.py` 等核心模块（见根目录 `AGENTS.md` / GitNexus 规则）
- 文档链接变更后运行 `python scripts/check_doc_links.py`

---

## 5. 与 Round 2+ 的衔接

- P1-5 / P2-4 结论：**文档化边界**，而非移除 `.cursor`/`.trellis`
- 若未来决定 workspace 不入库，应单独 PR 更新 `.gitignore` 并在此文件记录政策变更
