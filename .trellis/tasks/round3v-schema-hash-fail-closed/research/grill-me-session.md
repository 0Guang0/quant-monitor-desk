# Grill-me session — B3V-DATA

- **Date**: 2026-06-25
- **Skill**: grill-me（Phase 3 三选一）

## Q1: 为什么 JSON 有 infer 而 CSV/Parquet 没有？

**A**: 历史 Round 2 Batch B 只实现了 JSON 键形状指纹；verified audit 发现结构化源可凭 `schema_hash=NULL` 绕过 drift gate。

## Q2: Gate 在 hash 为 NULL 时为何放行？

**A**: `_schema_hash_blocks_write` 把「无 hash」当作「无法比较」而非「不可写」— 与 `write_contract.yaml` `schema_hash_changed` 语义不一致。

## Q3: schemaless 源怎么处理？

**A**: 契约显式列出豁免（如纯二进制证据）；**本任务不修改** `source_registry.yaml`（registry 锁归主会话）。Execute 在契约 + gate 用 `file_type`/路径后缀判定 structured 集合 `{json,csv,parquet}`。

## Q4: 会不会全文件扫描？

**A**: 否。CSV 仅解析 header 行（字节上限，对齐 `resource_limits` 精神）；Parquet 用 DuckDB schema 探测或 port 预填 hash；损坏即 FAILED，不读全表。

## Q5: Registry 谁关？

**A**: B02-DATA-05 **不在 Execute**；本分支只交付代码+测试证据；主会话合并后闭合 `VR-DATA-001`。

## 结论

需求边界清晰；fail-closed 为硬约束；禁止为便利 weaken gate（B3V-AUD-05）。
