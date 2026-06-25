# Plan Boot — B3V-DATA schema_hash fail-closed

- **日期**: 2026-06-25
- **Playbook**: `BATCH_3V_COORDINATOR_PLAYBOOK.md` §3.1 + §3.3 + §4
- **Manifest**: `B3V-C02` · branch `fix/round3v-schema-hash-fail-closed`
- **Worktree**: `../quant-monitor-desk-wt-b3v-data`

## 用户目标

关闭 `VR-DATA-001`：结构化抓取（JSON/CSV/Parquet）在 `SUCCESS` 且 `row_count > 0` 时，不得在无可信 `schema_hash` 的情况下进入 clean-write 校验链；ValidationGate 对缺失 hash 必须 fail-closed。

## 依赖与前置

- Batch 3V 协调包已冻结；post Batch 01 `master` 基线。
- 与 B3V-STOR（RawStore）可并行；ValidationGate 测试归属本分支独占（Playbook §2.5）。
- **Registry 闭合（B02-DATA-05）不在本 Plan Execute 范围** — 主会话批处理 `UNRESOLVED`/`RESOLVED`。

## AC 草稿

| ID | 验收 |
|----|------|
| AC-DATA-01 | 契约写明结构化 SUCCESS 必须带 `schema_hash`（schemaless 显式豁免） |
| AC-DATA-02 | CSV/Parquet 有界 schema 推导或 port 提供 hash |
| AC-DATA-03 | ValidationGate：结构化源 current/baseline hash 缺失 → `ValidationRejected` |
| AC-DATA-04 | 损坏 CSV/Parquet → `FAILED`/`SCHEMA_DRIFT`，不可 clean-write |
| AC-DATA-05 | 既有 schema_hash 漂移仍触发 `ValidationRejected`（回归） |

## 当前代码缺口（GitNexus + 源码）

1. `skeleton_base._infer_schema_hash`：`file_type != "json"` 直接返回 `None`（CSV/Parquet 无 hash）。
2. `DbValidationGate._schema_hash_blocks_write`：`current_row[0] is None` 或 `baseline_row[0] is None` 时返回 `False`（fail-open）。
3. 测试：JSON infer 有覆盖；CSV/Parquet 缺失 hash 与 gate fail-closed 无负向用例。

## 约束摘要

- **禁止**：全文件扫描、production clean write、db-inspect/RawStore/sync/registry/layer5 改动。
- **允许**：`validation_gate.py`、`skeleton_base.py` schema 路径、`data_adapter_contract.md` schema 段、相关 tests。

## 原计划已读

- [x] `B02_02_schema_hash_fail_closed.md` 全文
- [x] `BATCH_3V_COORDINATOR_PLAYBOOK.md` §3.1 + §3.3 + §4
- [x] GLOBAL×3 + `BATCH_3V_HARDENING_RULES.md`

## Phase P0 complete

- [x] 当前 Round batch map：`ROUND_3_VERIFIED_AUDIT_CLEANUP` README + `BATCH_3V_TASK_CARD_MANIFEST.md`
- [x] GLOBAL×3 + `BATCH_3V_HARDENING_RULES.md` 已摘要
- [x] 任务卡 `B02_02_schema_hash_fail_closed.md` 已读
- [x] GitNexus query/context/impact 已完成
- [x] `research/source-index.md` 待填 → 冻结前索引完整
