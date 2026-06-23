# Vertical slices — 021 (Plan 3.5 / to-issues)

| 序  | ID            | 交付物（完标准）                              | 依赖              | AC           |
| --- | ------------- | --------------------------------------------- | ----------------- | ------------ |
| 1   | SLICE-BOOT    | implement.jsonl 全读 + ledger + 基线 pytest   | 020 gate          | —            |
| 2   | SLICE-MODELS  | snapshot/mapping/lineage dataclasses          | SLICE-BOOT        | AC-021-1     |
| 3   | SLICE-LINEAGE | `Layer3LineageBuilder` + source hashes        | SLICE-MODELS      | AC-021-2     |
| 4   | SLICE-BUILD   | builder core + L5 fixture join + mapping view | SLICE-LINEAGE     | AC-021-1,5,6 |
| 5   | SLICE-ASOF    | no_future_data guard                          | SLICE-BUILD       | AC-021-3     |
| 6   | SLICE-EVENT   | event_only skip price                         | SLICE-BUILD       | AC-021-4     |
| 7   | SLICE-GATES   | Tier A + batch3 staged gate tests             | SLICE-ASOF, EVENT | AC-021-7     |

→ 冻结为 MASTER §8.0–8.6
