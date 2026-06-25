# Vertical Slices — Phase 3.5 /to-issues（冻结）

> 工单 ID = R3F-SH-01..07；Execute 不得水平吞并多切片（`BATCH_3F_COORDINATOR_PLAYBOOK` §2.7）

| ID        | 标题                     | 建设内容                                                                                                                | 验收标准                                                         | 依赖                      | 证据输出                                                     | 测试计划                                   |
| --------- | ------------------------ | ----------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- | ------------------------- | ------------------------------------------------------------ | ------------------------------------------ |
| R3F-SH-01 | Snapshot schema + writer | `source_health_snapshot` 表语义 ADR、writer 模块、isolated DB pytest；**migration SQL 等 B3F-MIG 合并或主会话书面协调** | RED: 无 writer/无 insert；GREEN: isolated migration test PASS    | Boot                      | `execute-evidence/sh-01-snapshot-writer-green.txt`；ADR 草案 | `tests/test_source_health_snapshot.py`     |
| R3F-SH-02 | Revision audit runner    | `DataSyncOrchestrator.run_revision_audit` 最小可运行实现                                                                | RED: `DeferredJobTypeError`；GREEN: job result PASS              | SH-01（只读表契约）       | `sh-02-revision-audit-green.txt`                             | `tests/test_b3f_quality_runners.py`        |
| R3F-SH-03 | Data quality runner      | `run_data_quality` 最小可运行实现                                                                                       | RED: defer；GREEN: job pytest PASS                               | SH-02 模式                | `sh-03-data-quality-green.txt`                               | `tests/test_b3f_quality_runners.py`        |
| R3F-SH-04 | Readiness rollup persist | 将 DH2 rollup 结果写入 snapshot writer（非 DH2 只读路径）                                                               | RED: 无 persist API；GREEN: rollup→snapshot 行                   | SH-01 writer              | `sh-04-rollup-persist-green.txt`                             | `tests/test_source_health_snapshot.py`     |
| R3F-SH-05 | DH2 boundary guard       | `VR-DATAHEALTH-001`：Batch01/DH2 不得 `CREATE TABLE source_health_snapshot`                                             | RED: DH2 import writer；GREEN: 边界测试 PASS                     | DH2 基线只读              | `sh-05-dh2-boundary-green.txt`                               | `tests/test_ops_data_health.py`            |
| R3F-SH-06 | FRED live primary        | 引用 `fred_live_authorization_2026-06-25.yaml`；FRED-only sandbox live + closeout                                       | RED: 无 YAML 可 live；GREEN: sandbox evidence + no prod mutation | SH-03 + **用户授权 YAML** | `fred_live_fetch_evidence.json` · 授权 YAML                  | `tests/test_fred_live_primary_closeout.py` |
| R3F-SH-07 | Hard-constraint tracking | `R3-B2.75-REQ2-EM` / AkShare 不得 sidecar 误关闭                                                                        | RED: 假关闭路径；GREEN: registry guard PASS                      | SH-06 隔离                | `sh-07-no-false-close-green.txt`                             | `tests/test_b3f_sh_hard_constraints.py`    |

## R3F-SH-01 / B3F-MIG 协调说明

| 项                                               | B3F-SH 可先写        | 须等 B3F-MIG 或主会话 |
| ------------------------------------------------ | -------------------- | --------------------- |
| ADR（表语义、writer 边界）                       | ✅                   | —                     |
| Writer 实现 + isolated pytest                    | ✅（test DB 自建表） | —                     |
| `backend/app/db/migrations/*.sql` 落库 migration | ❌                   | ✅ 合并或书面协调     |
| `MIGRATION_COVERAGE.md` 行更新                   | 草案 PR              | 主会话或 MIG 合并     |

## FRED live 授权（SH-06 必读）

- YAML: `.trellis/tasks/round3-source-health-and-quality-runners/execute-evidence/fred_live_authorization_2026-06-25.yaml`
- MD: `docs/quality/batch3f_fred_live_pilot_authorization_2026-06-25.md`
- Caps: DGS10 默认；≤100 rows；≤10 calls；sandbox only；`allow_production_clean_write: false`
