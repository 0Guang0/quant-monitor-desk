# AUDIT.plan — R3-DCP-06

> **追溯：** `EXECUTION_INDEX.md` §5 · `research/00-EXECUTION-ENTRY.md`

## §0.1 Trace Authority Set

| 类别              | 文件                                                          | 用途           |
| ----------------- | ------------------------------------------------------------- | -------------- |
| 活卡              | `frozen/R3_DCP_06_LAYER1_FIVE_AXIS_CLEAN.md`                  | scope / AC     |
| ADR-029           | `docs/decisions/ADR-029-dcp06-layer1-five-axis-clean-read.md` | P0 锚点        |
| Execute 入口      | `research/00-EXECUTION-ENTRY.md`                              | 路由 · §2 约束 |
| integration-audit | `research/integration-audit.md`                               | Plan 5d GAP    |
| 包外必读          | `research/EXTERNAL-INDEX.md` §A                               | 开工 SSOT      |

## §1 覆写

- **任务：** Wave 4 R3-DCP-06 五轴真 clean + G12 PASS
- **PASS 门槛：** §3.5.1 全 [x] · 五轴 e2e 非 fixture · pytest 全绿

## §2 验证矩阵（摘要）

| 维  | 要点                                  |
| --- | ------------------------------------- |
| A1  | 活卡/ENTRY/ADR-029 一致               |
| A2  | ponytail 流动性；staged 桥保留        |
| A3  | 无参考项目 runtime；no fallback       |
| A4  | 五轴 clean e2e 可断言                 |
| A5  | ACC-LAYER-E2E L1 子集；L3–L5 阶段外置 |
| A6  | K1 whitelist（主会话）                |
| A7  | tmp_path 隔离                         |
| A8  | `uv run pytest -q`                    |

## §3 台账

- 关（部分）：`ACC-LAYER-E2E-LIVE-001` L1
- 阶段外置：L3–L5 全链 · tiingo 流动性 · `B2.5-O-05`
