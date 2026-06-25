# 垂直切片 — B3V-DATA (/to-issues)

| 序 | ID | 交付物 | 依赖 | AC | 允许文件 |
|----|-----|--------|------|-----|----------|
| 1 | DATA-01 | `data_adapter_contract.md` 结构化 schema_hash 规则 + schemaless 豁免句 | — | AC-DATA-01 | 契约 md |
| 2 | DATA-02 | `_infer_schema_hash` CSV/Parquet 有界推导；`_fetch_impl` 无 hash 不 SUCCESS | DATA-01 | AC-DATA-02, AC-DATA-04 | `skeleton_base.py`, adapter tests |
| 3 | DATA-03 | `DbValidationGate` 缺失 current/baseline hash fail-closed | DATA-01 | AC-DATA-03, AC-DATA-05 | `validation_gate.py`, gate tests |
| 4 | DATA-04 | 损坏 CSV/Parquet 负向：FAILED/SCHEMA_DRIFT，gate 不可写 | DATA-02 | AC-DATA-04 | adapter + gate tests |

**不在切片内**: B02-DATA-05 registry — 主会话。

## 工单要点

### DATA-01
- SUCCESS + row_count>0 + file_type∈{json,csv,parquet} ⇒ schema_hash 非空
- schemaless：契约列举豁免类型；registry 字段后续由主会话补

### DATA-02
- CSV: stdlib `csv` 解析首行（max 64KiB 前缀）
- Parquet: DuckDB `DESCRIBE SELECT * FROM read_parquet(?) LIMIT 0` 列名指纹（临时文件/bytes）
- 损坏：infer 失败 → adapter 返回 FAILED 或 SCHEMA_DRIFT（非 SUCCESS+null hash）

### DATA-03
- `_schema_hash_blocks_write`: 结构化 fetch（由 file_registry.file_type 或 path 后缀判定）且 current hash NULL → True
- baseline NULL 且存在历史 structured 期望 → block（首写可文档化例外：无 baseline 时仅要求 current 非空）
- 保留 `manual_patch`/`schema_migration` 豁免

### DATA-04
- 负向测试：corrupt bytes → 非 clean-write eligible
