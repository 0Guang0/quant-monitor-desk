# Vertical slices — 022 (Plan 3.5 / to-issues)

| 序  | ID              | 交付物（完标准）                                   | 依赖           | AC              |
| --- | --------------- | -------------------------------------------------- | -------------- | --------------- |
| 1   | SLICE-BOOT      | implement.jsonl 全读 + ledger + 测试文件骨架       | 021 gate       | —               |
| 2   | SLICE-REGISTRY  | `market_registry` 种子行；`market_id` 唯一         | SLICE-BOOT     | AC-022-1        |
| 3   | SLICE-ADAPTER   | staged `MarketAdapter` + fixture bundle manifest   | SLICE-REGISTRY | AC-022-6        |
| 4   | SLICE-CAL-BREAD | calendar 行 + breadth snapshot 符合 contract         | SLICE-ADAPTER  | AC-022-2,3      |
| 5   | SLICE-LINEAGE   | `Layer4LineageBuilder` + source hashes             | SLICE-CAL-BREAD| AC-022-4        |
| 6   | SLICE-ASOF      | market snapshot build + no_future_data             | SLICE-LINEAGE  | AC-022-5        |
| 7   | SLICE-QUALITY   | 非交易日/quality_flag 规则                         | SLICE-ASOF     | AC-022-2,7      |
| 8   | SLICE-GATES     | Tier A + batch3 gate + 全库 pytest（一次）         | SLICE-QUALITY  | AC-022-8        |

→ 冻结为 MASTER §8.0–8.7
