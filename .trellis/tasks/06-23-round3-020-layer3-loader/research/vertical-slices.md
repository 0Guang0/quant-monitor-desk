# Vertical slices — 020 (Plan 3.5 / to-issues)

| 序 | ID | 交付物（完标准） | 依赖 | AC |
| -- | -- | ---------------- | ---- | -- |
| 1 | SLICE-BOOT | implement.jsonl 全读 + ledger + 基线 pytest | gate | — |
| 2 | SLICE-MODELS | `models.py` typed entries + `IndustryChainLoadResult` | SLICE-BOOT | AC-020-1 |
| 3 | SLICE-LOADER | `loader.py` staged_fixture_only + 五文件解析 | SLICE-MODELS | AC-020-1,5 |
| 4 | SLICE-GRAPH | node/edge/cross-chain 引用校验 | SLICE-LOADER | AC-020-2 |
| 5 | SLICE-ANCHOR | event_only + P0 source_keys + anchor.node_id | SLICE-LOADER, SLICE-GRAPH | AC-020-3,4 |
| 6 | SLICE-GATES | Tier A + batch3 staged gate tests | SLICE-ANCHOR | AC-020-6 |

→ 冻结为 MASTER §8.0–8.6
