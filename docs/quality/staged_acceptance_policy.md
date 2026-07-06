# Staged Acceptance Policy

## 1. 目的

修复 QM-AUD-006 与 QM-AUD-020：不同阶段不能使用同一套验收命令，实施文档包也不能假装已经包含源码和测试结果。

## 2. 阶段化验收

| 阶段      | 适用任务                | 必跑命令                                                                                                                                                                                               |
| --------- | ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| docs-only | 文档索引、ADR、设计说明 | `uv sync --locked && uv run python scripts/check_doc_links.py`，若脚本尚未创建则必须先创建等价 markdown link check                                                                                     |
| scaffold  | 目录、配置、测试基线    | `uv sync --locked && uv run pytest -q tests/test_project_scaffold.py && uv run ruff check .`                                                                                                           |
| backend   | 后端模块                | `uv sync --locked && uv run pytest -q && uv run ruff check . && uv run python -m compileall backend scripts tests`                                                                                     |
| frontend  | 前端模块                | `uv sync --locked && uv run pytest -q tests/test_api_contracts.py && cd frontend && npm ci && npm audit --audit-level=high && npm run typecheck && npm run build`                                      |
| release   | 最终包                  | `uv sync --locked && uv run python scripts/validate_release_allowlist.py && uv run python scripts/validate_manifest.py`；若脚本尚未创建，release 任务必须先创建并运行等价 allowlist/manifest/hash 校验 |

## 3. 源码与证据声明

本包是实施文档包，不包含 `backend/`、`frontend/`、`tests/`、`scripts/` 的最终实现。执行角色完成实现后，必须把源码、锁文件和测试输出作为实现成果另行提交。

## 4. 证据最低集

- 代码 diff。
- 测试命令和完整输出。
- 依赖锁文件。
- `MANIFEST.json`。
- ResourceGuard 是否触发。
- 未完成项与用户待拍板点。

## 5. 用户决策补充

落实 D-01 与 D-10：

- Python 默认验收命令必须使用 `uv sync --locked` / `uv run`。
- 如果用户明确拒绝安装 uv，可使用 pip-tools 备用方案，但必须在执行报告中说明。
- 本 zip 是设计稿与执行计划包，不包含最终 `backend/`、`frontend/`、`tests/` 源码。
- 实现完成后的终审必须基于源码 Git commit、CI 结果、测试输出和锁文件，而不是把源码塞回设计包。

## 复审修复补充：阶段化验收命令

所有 implementation task 必须按任务类型执行阶段化验收，不得无差别套用旧统一验收命令。默认 Python 命令使用：

```bash
uv sync --locked
uv run ...
```

文档类任务执行链接、allowlist、manifest、contract consistency 检查；后端任务执行 `uv run` 目标测试 + ruff + compileall；前端任务执行 `npm ci && npm audit --audit-level=high && npm run typecheck && npm run build`，且不得使用 会吞掉失败结果的 shell 容错短路写法 掩盖 API contract 测试失败；release 任务必须执行 manifest exclude-self policy、allowlist 和 FINAL_AUDIT_REPORT 校验。
