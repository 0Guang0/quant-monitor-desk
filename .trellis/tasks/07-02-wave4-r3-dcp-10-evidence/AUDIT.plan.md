# AUDIT.plan — R3-DCP-10

> **追溯：** `EXECUTION_INDEX.md` §5 · `research/00-EXECUTION-ENTRY.md`

## §0.1 Trace Authority Set

| 类别 | 文件 | 用途 |
| --- | --- | --- |
| 活卡 | `frozen/R3_DCP_10_LAYER5_EVIDENCE_BINDING.md` | scope / AC |
| ADR-031 | `docs/decisions/ADR-031-dcp10-layer5-evidence-provenance-binding.md` | P0 + mapping |
| Execute 入口 | `research/00-EXECUTION-ENTRY.md` | 路由 |
| integration-audit | `research/integration-audit.md` | Plan 5d GAP |
| 包外必读 | `research/EXTERNAL-INDEX.md` §A | 开工 SSOT |

## §1 覆写

- **任务：** Wave 4 R3-DCP-10 Layer5 绑真源 G5 子集
- **PASS 门槛：** provenance e2e 绿 · 三哈希对齐 bundle · pytest 全绿

## §2 验证矩阵（摘要）

| 维 | 要点 |
| --- | --- |
| A1 | 活卡/ENTRY/ADR-031 一致 |
| A2 | ponytail；不扩 scope |
| A3 | 无参考 runtime；WriteManager 金路径 |
| A4 | mootdx bar clean e2e 可断言 provenance |
| A5 | ACC G5 子集；全链阶段外置 |
| A6 | K1 layer5 plan 对齐（可选 note） |
| A7 | tmp_path 隔离 |
| A8 | `uv run pytest -q` |

## §3 台账

- 关（部分）：`ACC-LAYER-E2E-LIVE-001` **G5 子集**
- 阶段外置：L1–L4 已关/他票 · L3–L5 全链 · Wave 5 GATE
