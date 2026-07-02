# AUDIT.plan — M-DATA-03

> **追溯：** `EXECUTION_INDEX.md` §5 · `research/00-EXECUTION-ENTRY.md`

## §0.1 Trace Authority Set

| 类别              | 文件                                                           | 用途                   |
| ----------------- | -------------------------------------------------------------- | ---------------------- |
| 活卡              | `frozen/M_DATA_03_TIER_A_LIVE.md` · EXTERNAL-INDEX §A 包外路径 | scope / AC / §3 约束   |
| ADR-034           | `docs/decisions/ADR-034-m-data-03-tier-a-live-acceptance.md`   | live 验收 · 隔离库     |
| Execute 入口      | `research/00-EXECUTION-ENTRY.md`                               | 路由地图 · §2 约束     |
| 执行索引          | `EXECUTION_INDEX.md`                                           | 切片血缘 · manifest    |
| integration-audit | `research/integration-audit.md`                                | Plan 期对抗 · GAP 路由 |
| 包外必读          | `research/EXTERNAL-INDEX.md` §A                                | 开工必读 SSOT 超集     |

---

## §1 覆写

- **任务：** M-DATA-03 — 11 源隔离库真网 incremental→clean→inspect；模块 C3/D1/E1/E2/F0/B2 → R4
- **PASS 门槛：** 活卡 §5 全勾 · 11/11 live 绿 · `tier_a_live_acceptance.py` exit 0 · pytest 全绿 · 零主库污染

## §2 验证矩阵（摘要）

| 维  | 要点                                             |
| --- | ------------------------------------------------ |
| A1  | 活卡/ENTRY/ADR-034/plan-spec 一致                |
| A2  | DCP-05 clean 矩阵不变；无新 migration            |
| A3  | 无 `参考项目` runtime import；借鉴梯仅评参考项目 |
| A4  | 11 源 live e2e（`-m network`）隔离库写 clean     |
| A5  | `QMD_ALLOW_LIVE_FETCH` + `gate_live_fetch_port`  |
| A6  | registry 三件套（S-MERGE 主会话）                |
| A7  | `DATA_ROOT` 隔离；负向测：主库路径 / 无 env 闸   |
| A8  | `uv run pytest -q`                               |

## §3 台账

- 前置：`wave4-r3-dcp-05-tier-a` replay 逻辑已交付
- Plan GAP → Execute：`test_tier_a_live_harness.py` 完整实现 · `tier_a_live_acceptance.py` · **11 源** live 变体
