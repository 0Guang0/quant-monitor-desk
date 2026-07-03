# AUDIT.plan — R3-DCP-09

> **追溯：** `EXECUTION_INDEX.md` §5 · `research/00-EXECUTION-ENTRY.md`

## §0.1 Trace Authority Set

| 类别              | 文件                                                            | 用途                   |
| ----------------- | --------------------------------------------------------------- | ---------------------- |
| 活卡              | `frozen/R3_DCP_09_BOUNDED_BACKFILL_CI.md` · EXTERNAL-INDEX §A   | scope / AC / §3 约束   |
| ADR-030           | `docs/decisions/ADR-030-bounded-backfill-cap-and-ci-nightly.md` | cap + nightly 矩阵     |
| Execute 入口      | `research/00-EXECUTION-ENTRY.md`                                | 路由地图 · §2 约束     |
| 执行索引          | `EXECUTION_INDEX.md`                                            | 切片血缘 · manifest    |
| integration-audit | `research/integration-audit.md`                                 | Plan 期对抗 · GAP 路由 |
| 包外必读          | `research/EXTERNAL-INDEX.md` §A                                 | 开工必读 SSOT 超集     |

---

## §1 覆写

- **任务：** Wave 4 R3-DCP-09 有界 backfill + CI nightly
- **PASS 门槛：** 活卡 §5 全勾 · cap CLI e2e 绿 · nightly 可复现 · 台账四 ID 关账

## §2 验证矩阵（摘要）

| 维  | 要点                                     |
| --- | ---------------------------------------- |
| A1  | 活卡/ENTRY/ADR-030 一致                  |
| A2  | `bounded_backfill_cap.yaml` + planner    |
| A3  | 无 `参考项目` runtime import             |
| A4  | backfill replay e2e 写 clean（隔离库）   |
| A5  | nightly `--run-network` 子集；PR 仍 skip |
| A6  | workflow + ops 文档双轨                  |
| A7  | 主库零污染（验收 fingerprint）           |
| A8  | `uv run pytest -q`                       |

## §3 台账

- 关：`WAVE3-ACC-OPT-01` · `ACC-LIVE-NETWORK-CI-001` · `ACC-LIVE-ACCEPT-NIGHTLY-001` · `LIVE-NETWORK-GATE-001`
