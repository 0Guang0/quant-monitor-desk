# AUDIT.plan — R3-DCP-07

> **追溯：** `EXECUTION_INDEX.md` §5 · `research/00-EXECUTION-ENTRY.md`

## §0.1 Trace Authority Set

| 类别 | 文件 | 用途 |
|------|------|------|
| 活卡 | `frozen/R3_DCP_07_LAYER2_CROSS_ASSET.md` | scope / AC |
| ADR-032 | `docs/decisions/ADR-032-dcp07-layer2-vix-clean-read.md` | P0 锚点 |
| Execute 入口 | `research/00-EXECUTION-ENTRY.md` | 路由 · §2 约束 |
| integration-audit | `research/integration-audit.md` | Plan 5d GAP |
| 包外必读 | `research/EXTERNAL-INDEX.md` §A | 开工 SSOT |

## §1 覆写

- **任务：** Wave 4 R3-DCP-07 Layer2 单传感器真 clean
- **PASS 门槛：** L2-VIX clean e2e 非 fixture · lineage 可断言 · pytest 全绿

## §2 验证矩阵（摘要）

| 维 | 要点 |
|----|------|
| A1 | 活卡/ENTRY/ADR-032 一致 |
| A2 | ponytail 单传感器；staged 路径保留 |
| A3 | 无参考项目 runtime；no fallback |
| A4 | L2 clean e2e 可断言 |
| A5 | ACC-LAYER-E2E L2 子集；L3–L5 阶段外置 |
| A6 | G2 MODULE_COMPLETION（主会话） |
| A7 | tmp_path 隔离 |
| A8 | `uv run pytest -q` |

## §3 台账

- 关（部分）：`ACC-LAYER-E2E-LIVE-001` **L2 子集**
- 阶段外置：L3–L5 全链 · L2 余量资产 · `B2.5-O-05`
