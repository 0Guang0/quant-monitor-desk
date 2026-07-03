# AUDIT.plan — R3-DCP-08

> **追溯：** `EXECUTION_INDEX.md` §5 · `research/00-EXECUTION-ENTRY.md`

## §0.1 Trace Authority Set

| 类别              | 文件                                                      | 用途                     |
| ----------------- | --------------------------------------------------------- | ------------------------ |
| 活卡              | `frozen/R3_DCP_08_LAYER4_MARKET_STRUCTURE.md`             | scope / AC               |
| ADR-033           | `docs/decisions/ADR-033-dcp08-layer4-us-eq-clean-read.md` | P0 US_EQ · registry 双轨 |
| Execute 入口      | `research/00-EXECUTION-ENTRY.md`                          | 路由 · §2 约束           |
| integration-audit | `research/integration-audit.md`                           | Plan 5d PASS_WITH_GAPS   |
| 包外              | `research/EXTERNAL-INDEX.md` §A                           | 开工必读                 |

## §1 覆写

- **任务：** Wave 4 R3-DCP-08 Layer4 US_EQ clean + registry hygiene
- **PASS 门槛：** 活卡 §5 全勾 · `test_layer4_us_equity_clean_e2e` GREEN · ACC 台账关账 · pytest 全绿

## §2 验证矩阵（摘要）

| 维  | 要点                                 |
| --- | ------------------------------------ |
| A1  | 活卡/ENTRY/ADR-033 一致              |
| A2  | clean read 非 staged；022 无回归     |
| A3  | 无 `参考项目` runtime import         |
| A4  | US_EQ breadth 从 Tier A clean        |
| A5  | mootdx dry-run 对齐；REQ2-EM 仍 open |
| A6  | eastmoney taxonomy notes             |
| A7  | sandbox 隔离                         |
| A8  | `uv run pytest -q`                   |

## §3 台账

- 关：`ACC-MOOTDX-DRYRUN-ROUTE-001` · `ACC-EASTMONEY-TAXONOMY-001`(部分) · `ACC-LAYER-E2E-LIVE-001` L4
- 不关：`R3-B2.75-REQ2-EM`
