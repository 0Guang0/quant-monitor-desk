# Runtime Versions and Dependency Lock Policy

## 1. 目的

本文件修复审计项 QM-AUD-005，并落实用户拍板 D-01：Python 依赖默认使用 `uv.lock` 锁定，确保 Claude Code / Codex、本机和 CI 在同一套依赖版本上执行。

## 2. 第一版推荐版本

| 组件                      | 推荐基线                   | 说明                                         |
| ------------------------- | -------------------------- | -------------------------------------------- |
| Python                    | `>=3.11,<3.13`             | 优先 3.11/3.12；避免使用低版本缺失的类型能力 |
| Node.js                   | `>=20,<23`                 | 适配 Vite/React/TypeScript 当前生态          |
| npm                       | `>=10`                     | 支持稳定 `npm audit --audit-level` 门禁      |
| DuckDB Python             | 固定到 `uv.lock`           | 不在任务文档硬编码补丁号，由锁文件记录       |
| FastAPI / Pydantic        | 固定到 `uv.lock`           | Pydantic v2 作为实现前提                     |
| React / Vite / TypeScript | 固定到 `package-lock.json` | 前端必须提交 lock 文件                       |

## 3. 已拍板锁文件规则（D-01）

用户已拍板：第一版采用 `uv.lock` 作为 Python 主锁文件。

```text
默认：uv.lock
备用：requirements.lock / pip-tools，仅在用户明确不想安装 uv 时使用
不采用：poetry.lock，第一版不引入 Poetry 项目管理结构
```

执行要求：

- `uv.lock` 必须提交到 Git。
- `pyproject.toml` 与 `uv.lock` 必须同步更新。
- 实现任务默认使用 `uv sync` / `uv run`。
- Claude Code / Codex 不得擅自改用 Poetry。
- 如果临时使用 pip-tools 备用方案，必须同步生成 `requirements.lock` 并在报告中说明原因。

## 4. 默认验收命令

```bash
uv --version
uv sync
uv run python --version
uv run pytest -q
uv run ruff check .
uv run python -m compileall backend scripts tests

cd frontend
node --version
npm --version
npm ci
npm audit --audit-level=high
npm run typecheck
npm run build
```

## 5. CI 规则

CI 必须基于锁文件安装依赖：

```text
Python: uv sync --locked
Frontend: npm ci
```

如 CI 使用 pip 备用安装，必须显式说明这是兼容路径，不得替代 `uv.lock` 主路径。
