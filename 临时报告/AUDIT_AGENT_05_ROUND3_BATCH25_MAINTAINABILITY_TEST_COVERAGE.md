# Agent 05 — 可维护性与测试覆盖审计报告

审计日期：2026-06-21。角色边界：只审计可维护性、测试覆盖与验证充分性。按用户要求只报告，不修复。

## 工具与 skill

| skill / 工具                  | 用途                           | 命令或依据                                                          | 结果                                     |
| ----------------------------- | ------------------------------ | ------------------------------------------------------------------- | ---------------------------------------- |
| test-driven-development       | 检查测试是否覆盖关键行为       | full / targeted / E2E pytest                                        | 关键 evidence 测试失败                   |
| code-review-and-quality       | 判断测试是否语义化、是否能维护 | `tests/test_layer1_observation_ingestion.py`、smoke、frontend tests | 后端测试多，前端薄                       |
| code-simplification           | 维护性与模块体量审查           | `ingestion.py`、evidence helper                                     | 大文件与重复 helper 增加维护成本         |
| coverage gate contract review | 校验覆盖率要求                 | `pyproject.toml` fail_under=85；full cov 未跑通                     | 因 pytest 失败，覆盖率 gate 不能最终确认 |

## 验证命令摘要

| 命令                                                                                                                                                                                                                                                              | 结果             |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------- |
| `pytest -q --basetemp=.audit-sandbox\pytest-9agent-current`                                                                                                                                                                                                       | FAIL，2 failures |
| `pytest tests/test_layer1_observation_ingestion.py::test_layer1Ingestion_phase3_taskEvidenceArtifacts tests/test_layer1_observation_ingestion.py::test_layer1Ingestion_phase4_taskEvidenceArtifacts -q --basetemp=.audit-sandbox/pytest-9agent-restored-targeted` | FAIL，2 failures |
| `pytest tests/test_layer1_ingestion_gates.py tests/test_layer1_observation_ingestion.py -q --basetemp=.audit-sandbox/pytest-9agent-layer1-e2e`                                                                                                                    | FAIL，2 failures |
| `pytest tests/test_raw_store.py -q --basetemp=.audit-sandbox/pytest-9agent-raw-store`                                                                                                                                                                             | PASS，15 passed  |
| `pytest tests/test_db_validation_gate.py -q --basetemp=.audit-sandbox/pytest-9agent-db-gate`                                                                                                                                                                      | PASS，10 passed  |
| `npm run test --prefix frontend`                                                                                                                                                                                                                                  | PASS，3 tests    |

## 发现项

| ID       | 等级 | 问题                                                | 证据                                            | 影响                         | 状态      | 解决方案                                                      |
| -------- | ---- | --------------------------------------------------- | ----------------------------------------------- | ---------------------------- | --------- | ------------------------------------------------------------- |
| A5-P1-01 | P1   | 关键后端测试失败，覆盖率 gate 无法作为 PASS 证据    | full pytest FAIL                                | 测试套件不能作为交付信号     | NOT FIXED | 修复 phase3/4 evidence 测试，再跑 full + cov                  |
| A5-P2-01 | P2   | 覆盖率命令未在失败状态下完成                        | `pyproject.toml` 要求 fail_under=85；全量先失败 | 无法证明当前覆盖率仍满足门槛 | NOT FIXED | full pytest 绿后跑 `pytest --cov=backend --cov-fail-under=85` |
| A5-P2-02 | P2   | 前端测试覆盖很薄                                    | Vitest 仅 3 tests                               | UI 改动的回归保护不足        | NOT FIXED | 增加页面、数据契约、错误态测试                                |
| A5-P2-03 | P2   | 大量 Batch2.5 evidence helper 集中在 `ingestion.py` | 文件约 1506 行                                  | 后续维护和定位成本高         | NOT FIXED | 拆分 evidence writer 与 ingestion service                     |
| A5-P3-01 | P3   | 未跟踪临时文件需清理                                | `backend/app/storage/path_compat.py`            | 增加维护噪音                 | NOT FIXED | 手动删除                                                      |

## 评分与结论

总分：84/100。FAIL。达到 95 分的最小清单：关键 pytest 绿；覆盖率 gate 绿；前端测试扩展；拆分过长 evidence helper；删除未跟踪临时文件。
