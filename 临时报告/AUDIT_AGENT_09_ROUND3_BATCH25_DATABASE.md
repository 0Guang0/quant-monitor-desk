# Agent 09 — 数据库深挖审计报告

审计日期：2026-06-21。角色边界：只审计当前数据库、迁移、schema 契约、写入证据链与原始设计一致性。按用户要求只报告，不修复。

## 工具与 skill

| skill / 工具                    | 用途                                   | 命令或依据                                                                                         | 结果                                    |
| ------------------------------- | -------------------------------------- | -------------------------------------------------------------------------------------------------- | --------------------------------------- |
| DB validation gate tests        | 数据库 validation gate 验证            | `pytest tests/test_db_validation_gate.py -q --basetemp=.audit-sandbox/pytest-9agent-db-gate`       | PASS，10 passed                         |
| raw store / file_registry tests | raw evidence 与 file registry 基础行为 | `pytest tests/test_raw_store.py -q --basetemp=.audit-sandbox/pytest-9agent-raw-store`              | PASS，15 passed                         |
| schema / registry review        | migration 与 schema 设计一致性         | `docs/AUDIT_DEFERRED_REGISTRY.md`、`specs/schema/schema.sql`、migration 011                        | 存在已登记 schema lag 与 CHECK deferred |
| 生产等价 gate                   | 不写真实 DB 的替代验证                 | `pytest tests/test_batch25_production_data_gate.py -q --basetemp=.audit-sandbox/pytest-9agent-b25` | PASS，4 passed                          |

## 验证摘要

| 命令                                                                                               | 结果             |
| -------------------------------------------------------------------------------------------------- | ---------------- |
| `pytest tests/test_db_validation_gate.py -q --basetemp=.audit-sandbox/pytest-9agent-db-gate`       | PASS，10 passed  |
| `pytest tests/test_raw_store.py -q --basetemp=.audit-sandbox/pytest-9agent-raw-store`              | PASS，15 passed  |
| `pytest tests/test_batch25_production_data_gate.py -q --basetemp=.audit-sandbox/pytest-9agent-b25` | PASS，4 passed   |
| `pytest tests/test_layer1_observation_ingestion.py::...phase3... ...phase4...`                     | FAIL，2 failures |
| full pytest                                                                                        | FAIL，2 failures |

## 发现项

| ID       | 等级 | 问题                                                 | 证据                                                 | 影响                                               | 状态      | 解决方案                                                          |
| -------- | ---- | ---------------------------------------------------- | ---------------------------------------------------- | -------------------------------------------------- | --------- | ----------------------------------------------------------------- |
| A9-P1-01 | P1   | Phase3/Phase4 DB 证据链当前失败                      | phase3 `file_registry_delta` 为 0；phase4 fetch 失败 | file_registry/fetch/clean write 证据链不能完整证明 | NOT FIXED | 修复 raw evidence 路径稳定性；重跑 targeted、DB gate、full pytest |
| A9-P2-01 | P2   | `specs/schema/schema.sql` 未同步 `axis_*` runtime 表 | registry B2.5-O-02                                   | schema 与迁移口径不一致                            | DEFERRED  | 同步 schema.sql 或在 docs 中明确 migration 011 为 runtime SSOT    |
| A9-P2-02 | P2   | 部分 DB CHECK 仍 deferred                            | A9-P1-01、A9-P2-01、A9-P2-02、B2.5-O-03              | DB 层防线不完整                                    | DEFERRED  | migration 008/012 增加 CHECK 或 ADR 接受 app-layer                |
| A9-P2-03 | P2   | 外部真实源 DB 写入未试点                             | R3-B2.75-01 DEFERRED                                 | 真实源 shape 与 DB evidence 仍未验证               | DEFERRED  | Batch2.75 在 sandbox 中做 raw-only 和可回滚验证                   |
| A9-P3-01 | P3   | 未跟踪临时文件                                       | `backend/app/storage/path_compat.py`                 | 不应进入提交                                       | NOT FIXED | 手动删除                                                          |

## 数据库一致性结论

底层 `DbValidationGate` 与 `RawStore/FileRegistry` 基础测试通过，说明基础 DB 写入守门仍可用。但 Batch2.5 任务级 evidence path 失败，使当前数据库证据链不能达到 95 分。另有 schema.sql 滞后、CHECK deferred 与外部真实源试点未执行等已登记风险。

## 评分与结论

总分：80/100。FAIL。达到 95 分的最小清单：修复 phase3/phase4 evidence DB 证据链；同步 schema/migration 口径；关闭或明确重登记 CHECK deferred；完成 Batch2.75 DB 边界验证；删除未跟踪临时文件。
