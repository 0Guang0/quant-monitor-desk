# Agent 06 — 规范性、工程质量、架构设计审计报告

审计日期：2026-06-21。角色边界：只审计工程规范、架构边界、项目约定与可交付 gate。按用户要求只报告，不修复。

## 工具与 skill

| skill / 工具               | 用途                                | 命令或依据                                                                                     | 结果                                        |
| -------------------------- | ----------------------------------- | ---------------------------------------------------------------------------------------------- | ------------------------------------------- |
| codebase-design            | 深模块、接口、seam 与 locality 审查 | `DataSourceService`、Layer1 ingestion facade                                                   | 服务 seam 已存在，但 ingestion 文件过深过宽 |
| code-review-and-quality    | 工程 gate 与规范审查                | `pyproject.toml`、runtime contract、测试结果                                                   | pytest gate 失败，ruff 未执行               |
| module boundary pytest     | 架构边界测试                        | `pytest tests/test_module_boundaries.py -q --basetemp=.audit-sandbox/pytest-9agent-boundaries` | PASS，4 passed                              |
| registry / contract review | 工程约定一致性                      | `specs/contracts/runtime_versions.md`、registry                                                | `uv.lock` 约定疑似未满足                    |

## 验证摘要

- Module boundaries：PASS，4 passed。
- Source route planner：PASS，6 passed。
- Backend smoke：PASS，3 passed。
- 全量 pytest：FAIL，2 failures。
- `ruff check .`：未执行，CodexPro safe allowlist 拒绝。
- Frontend typecheck/test/build：PASS。

## 发现项

| ID       | 等级 | 问题                                       | 证据                                                                     | 影响                          | 状态      | 解决方案                                    |
| -------- | ---- | ------------------------------------------ | ------------------------------------------------------------------------ | ----------------------------- | --------- | ------------------------------------------- |
| A6-P1-01 | P1   | 工程 gate 不绿                             | 全量 pytest 2 failures                                                   | 不能判定工程质量 PASS         | NOT FIXED | 修复 evidence 测试并重跑全量 gate           |
| A6-P2-01 | P2   | runtime lockfile 合同疑似未满足            | `specs/contracts/runtime_versions.md` 要求 `uv.lock`；根目录 tree 未显示 | 环境复现性风险                | NOT FIXED | 提交 `uv.lock` 或修订合同                   |
| A6-P2-02 | P2   | lint/format gate 本轮未能执行              | safe allowlist 拒绝 `ruff check .`                                       | 工程规范验证不完整            | NOT FIXED | 在本机完整 shell 或 CI 跑 ruff check/format |
| A6-P2-03 | P2   | 架构边界测试虽绿，但 ingestion facade 过宽 | `ingestion.py` 包含 route、fetch、commit、evidence、format               | seam 深度不足，维护局部性下降 | NOT FIXED | 拆出 evidence 模块和 sandbox helper         |
| A6-P2-04 | P2   | 归档 audit report 仍含 pending 文案        | `audit.report.md` §3                                                     | 工程归档质量不足              | NOT FIXED | 补 final 摘要                               |
| A6-P3-01 | P3   | 未跟踪临时文件                             | `backend/app/storage/path_compat.py`                                     | 提交风险                      | NOT FIXED | 手动删除                                    |

## 评分与结论

总分：85/100。FAIL。达到 95 分的最小清单：pytest gate 绿；runtime lockfile 口径闭环；ruff gate 绿；拆分过宽 ingestion facade；清理未跟踪文件；补齐归档报告。
