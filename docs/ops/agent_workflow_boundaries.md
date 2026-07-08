# Agent 工作流边界与信任模型

> 本文说明仓库中 `.cursor/` 的用途、入库策略，以及已退休工作流目录的清理口径。
> 适用读者：新贡献者、AI agent 操作者、安全审查。

---

## 1. 当前保留目录

| 目录             | 是否入库               | 用途                                        |
| ---------------- | ---------------------- | ------------------------------------------- |
| `.cursor/`       | 是（hooks、skills 等） | Cursor IDE 集成：hooks、项目级 skills/rules |
| `.cursor/hooks/` | 是                     | Session 启动时注入上下文（Python 脚本）     |

**结论：** `.cursor/` 仍是本地 IDE 集成目录；已删除的旧工作流目录不得作为活流程恢复。

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

## 3. 已退休工作流目录（SEC-3）

- 旧工作流目录已从活流程移除。
- 当前任务状态以 `PROJECT_IMPLEMENTATION_ROADMAP.md`、`MODULE_COMPLETION_RATING.md`、任务卡、模块文档和 contracts 为准。
- 新代码和测试不得新增对已删除工作流目录或脚本的依赖。

Agent 应优先读路线图、模块文档、contracts、rules 和当前任务卡，而非猜测未文档化的约定。

---

## 4. 干净检出与 Agent 协作

新 clone 后建议顺序（D-01：默认 `uv`；pip 仅备用，见 `specs/contracts/runtime_versions.md`）：

1. `uv sync --locked`（或备用：`pip install -e ".[dev]"`）
2. `uv run python scripts/init_db.py` — 创建 `data/duckdb` 等运行时目录（**pytest 不自动创建**）
3. `cd frontend && npm ci`
4. 复制 `.env.example` → `.env.local`；路径变量留空则使用仓库默认（见 `.env.example` 注释，D-03）

Agent 修改代码时：

- **不要**提交 `data/` 运行时产物
- **不要**在无 impact 分析时改 `backend/app/db/connection.py` 等核心模块（见根目录 `AGENTS.md` / GitNexus 规则）
- 文档入口变更后运行相关 `pytest` 选择器，例如 `tests/test_project_scaffold.py` 或 `tests/test_global_execution_rules.py`

---

## 5. 与历史任务的衔接

- 历史任务材料只作背景证据，不作当前执行入口。
- 若未来决定 workspace 不入库，应单独 PR 更新 `.gitignore` 并在此文件记录政策变更
