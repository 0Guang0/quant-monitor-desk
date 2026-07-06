# ADR-005：source_health_snapshot 模块边界

## 状态

已接受（2026-06-25）— 执行 R3F-SH-01

## 背景

`source_health_snapshot` 在 `MIGRATION_COVERAGE.md`（D2-P2-1）中标记为延后落地。Batch 01 / DH2 只读数据健康（`round3-readonly-data-health-v2`）**不得**创建该表。Batch 6 源健康需要独立写入器与隔离 pytest 路径；同时 **B3F-MIG** 独占 `backend/app/db/migrations/**` 中的正式 SQL。

## 决策

1. **DDL 位置：** `SourceHealthSnapshotWriter.ensure_schema()` 仅在**隔离测试库**中内嵌 `docs/modules/data_sources.md` §5.8 的表 DDL。生产环境迁移 SQL 仍由 **B3F-MIG** 锁定，本分支不抢先改 migrations。
2. **写入模块：** `backend/app/ops/source_health_writer.py` 是 Batch 6 持久化 snapshot 行的唯一入口。
3. **DH2 边界：** `backend/app/ops/data_health.py` 暴露 `DH2_FORBIDS_SNAPSHOT_DDL = True`；不得 import 写入器，不得发出 `CREATE TABLE source_health_snapshot`。
4. **汇总持久化：** `persist_readiness_rollup()` 放在 `source_health_writer.py`；调用方传入已打开的 DuckDB 连接（非 DH2 编排路径）。证据目录须含 `rollup_manifest.json`，缺失则 fail-closed 抛 `FileNotFoundError`。
5. **Registry 守卫（SH-07）：** `backend/app/ops/b3f_sh_registry_guard.py` 导出 `build_no_false_close_guard()` / `assert_sidecar_does_not_close_validation_rows()`。Sidecar 关账字典须保持 `R3-B2.75-REQ2-EM` 与 `R3-PROMPT14-AKSHARE-VAL-01` 为 **OPEN** — 仅由 pytest 接线（DH2 不得 import）。
6. **FRED live 路径：** `fred_live_primary.FRED_LIVE_AUTHORIZATION_DEFAULT` 指向归档 execute-evidence YAML（`docs/archive/trellis-evidence/round3-source-health-and-quality-runners/execute-evidence/fred_live_authorization_2026-06-25.yaml`）。

## 后果

- SH-01 的 pytest 可在本分支无 MIG 迁移文件时通过。
- SH-05 的 grep + 常量守卫防止 DH2 回退。
- MIG worktree 后续合并正式迁移 SQL；写入器内 DDL 字符串须与合并后的 migration 保持一致。
