# Agent 09 — 数据库一致性、缺口、漏洞与风险审计

## 1. 独立角色边界

本 agent 只审计当前数据库、schema、migration、DB inspect、写入边界、数据证据链与原始设计文档一致性。不评价代码简化、前端或性能，除非影响 DB 风险。

## 2. 生产/生产等价边界

未直接连接或修改真实生产 DB。按 018B/policy，生产 live pilot 必须显式授权并禁止 production clean DB mutation。本 agent 采用只读/隔离生产等价验证：DB/schema pytest、Batch2.5 production data gate、ops DB inspector tests、read-only evidence 文档核对。残余风险：未验证真实生产 DB 中的 live vendor 行与真实 source shape。

## 3. 使用的有效 skill / 工具

| 名称                           | 用途                                            | 执行命令或依据                                                                                        | 结果                                              |
| ------------------------------ | ----------------------------------------------- | ----------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| security-and-hardening skill   | DB 写入边界、路径、外部数据校验                 | 已加载；检查 WriteManager/raw_store/validation gate 相关测试                                          | 未见直接生产写绕过，仍有 DB CHECK 缺口            |
| documentation-and-adrs skill   | DB 决策与 deferred registry 一致性              | 已加载；核对 ADR-001/002、registry、migration plan                                                    | 已知 deferred 记录完整，但仍未修复                |
| CodexPro search/read           | 比对 `specs/schema/schema.sql` 与 migration 011 | `search schema.sql axis_observation`; read `011_layer1_tables.sql`; read `AUDIT_DEFERRED_REGISTRY.md` | 确认 schema.sql drift 与 migration authority 差异 |
| pytest DB/schema suites        | DB contract/migration/inspector 验证            | `pytest tests/test_ops_db_inspector.py ... -q`                                                        | exit 0，1 skip                                    |
| pytest write/validation suites | 写入、验证、冲突门禁                            | `pytest tests/test_write_manager.py ... -q`                                                           | exit 0                                            |

## 4. 执行命令与结果

| 命令                                                                                                                                                  | 结果                                   |
| ----------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------- |
| `pytest tests/test_ops_db_inspector.py tests/test_duckdb_connection.py tests/test_schema_contract.py tests/test_schema_migration.py -q`               | exit 0；含 1 skip                      |
| `pytest tests/test_write_manager.py tests/test_data_quality_validator.py tests/test_source_conflict_validator.py tests/test_db_validation_gate.py -q` | exit 0                                 |
| `pytest tests/test_production_live_pilot_policy.py tests/test_batch25_production_data_gate.py -q`                                                     | exit 0；11 tests passed                |
| `pytest -q`                                                                                                                                           | exit 0；589 collected；1 skip observed |

## 5. 数据库证据

- `backend/app/db/migrations/011_layer1_tables.sql` 已创建 `axis_observation`、`axis_feature_snapshot`、`axis_interpretation_snapshot`、`axis_snapshot_lineage` 等 Layer1 表。
- `specs/schema/schema.sql` 搜索 `axis_observation` 无命中，证实 schema contract lag。
- `AUDIT_DEFERRED_REGISTRY.md` 明确保留 `B2.5-O-02`、`B2.5-O-03`、`B2.5-O-06` DB/schema 相关 deferred。
- `final_registry_update.md` 说明 Batch2.5 clean write scope 为 staged single-point，并非 production live DB readiness。

## 6. P0/P1/P2/P3

### P0

无。当前测试未显示 DB 初始化、连接、迁移、写入门禁全局失败。

### P1

| ID        | 问题                                                                 | 证据                                                       | 影响                                               | 当前阶段可修复?             | 修复状态 | 解决方案                                                                             |
| --------- | -------------------------------------------------------------------- | ---------------------------------------------------------- | -------------------------------------------------- | --------------------------- | -------- | ------------------------------------------------------------------------------------ |
| A09-P1-01 | `specs/schema/schema.sql` 与实际 migration 011 不一致                | schema.sql 无 axis 表；migration 011 有 axis 表；B2.5-O-02 | 高：设计/contract 与实际 DB 不一致，会误导后续实施 | 是，但用户禁止文档/代码变更 | 未修复   | 同步 schema.sql 或将 migration 011 声明为权威并补 contract test/ADR                  |
| A09-P1-02 | `axis_observation` 缺少 DB CHECK timestamp ordering                  | migration 011 table definition 无 CHECK；B2.5-O-03         | 高：DB 层不能独立阻止未来数据/时间顺序错误         | 是                          | 未修复   | migration 012 添加 CHECK，或正式 ADR 说明 app validator 为唯一边界并加 DB/app matrix |
| A09-P1-03 | Batch2.75 live pilot 未执行，DB 未验证真实 live 行/真实 source shape | R3-B2.75-01 DEFERRED                                       | 高：DB clean/staged 证据不能代表生产 live 数据     | 否，需授权与独立执行        | 未修复   | Batch2.75 raw-only/sandbox clean pilot，保留 before/after DB inspect delta           |

### P2

| ID        | 问题                                                | 证据                                        | 影响                                                | 当前阶段可修复?         | 修复状态 | 解决方案                                                  |
| --------- | --------------------------------------------------- | ------------------------------------------- | --------------------------------------------------- | ----------------------- | -------- | --------------------------------------------------------- |
| A09-P2-01 | Migration 008 broad CHECK closeout deferred         | B2.5-O-06 / A9-P1-01                        | 中：DB CHECK 覆盖不完整                             | 是但本轮禁止变更        | 未修复   | 执行 migration 008/后续 migration contract tests          |
| A09-P2-02 | 生产 DB row mutation 只通过测试与 evidence 间接证明 | production policy tests + Batch2.5 evidence | 中：未做真实 DB checksum/read-only before-after run | 否；需授权/隔离 DB copy | 未修复   | 对生产 DB 副本执行 read-only baseline + after delta proof |

### P3

| ID        | 问题                                                    | 影响 | 解决方案                                |
| --------- | ------------------------------------------------------- | ---- | --------------------------------------- |
| A09-P3-01 | DB inspect / data-root 产物较多，release 前需清理或归档 | 低   | 使用 final_package_rules 明确保留或清理 |

## 7. 评分

**84 / 100 — FAIL**

扣分依据：schema.sql drift -5；axis_observation DB CHECK 缺口 -4；live DB pilot 未执行 -4；migration 008 CHECK deferred -2；DB before/after checksum 未重跑 -1。

## 8. 达到 95+ 的最小修复清单

1. 同步 `specs/schema/schema.sql` 与 migration 011。
2. 为 `axis_observation` 增加 DB CHECK 或正式记录 app-validator-only 边界并补测试。
3. 完成 migration 008/后续 CHECK closeout。
4. 执行 Batch2.75 sandbox/live DB inspect before-after proof。
5. 全量重跑 DB/schema/write/validation tests。

## 9. 结论

本维度 **FAIL**。当前 DB 能支撑 staged Batch2.5 路径，但与原始 schema contract、DB CHECK、live production evidence 之间仍有不可忽略缺口。
