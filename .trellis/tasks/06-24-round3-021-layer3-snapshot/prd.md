# Round 3 021: Layer3 snapshot builder

## Goal

从 `020` loader 输出 + staged Layer5 bar fixture 生成 `industry_chain_daily_snapshot` 行、Layer5 映射视图、contract-scoped lineage envelope；staged-only。

## Requirements

- 复用 `layer2_sensors/snapshot_builder.py` + `core/snapshot_lineage.py` 模式
- 证明 `as_of` / `no_future_data` / `event_only` 边界
- 登记 `ADV-R3X-LINEAGE-001` / `R3Y-LINEAGE-VR-001` defer 边界（§3.2）
- 禁止 live L5 fetch、production DB、三 registry 写

## Acceptance Criteria

- [ ] AC-021-1：loader + staged L5 → snapshot 行
- [ ] AC-021-2：lineage 含 source hashes
- [ ] AC-021-3：拒绝未来观测
- [ ] AC-021-4：event_only 无价量
- [ ] AC-021-5：Layer5 mapping view
- [ ] AC-021-6：staged-only L5 源
- [ ] AC-021-7：Tier A exit 0

## Notes

- 全量 L3/L4 lineage → defer `022`/Batch 5
- registry VR 行 → separate hygiene slice
- Execute 前须用户批准 Plan freeze
