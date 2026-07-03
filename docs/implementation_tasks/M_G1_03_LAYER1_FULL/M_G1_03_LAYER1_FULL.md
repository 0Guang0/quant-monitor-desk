# M-G1-03 — Layer1 五轴完整落地（真链）

> **状态：OPEN · 下一入口**  
> **Module ID：** G1 → **R4** · 同票 K1, K2, A5  
> **依赖：** M-DATA-03 **CLOSED** @ 2026-07-04 — Tier A **R4** clean 输入（隔离库证明）  
> **设计权威：** `docs/modules/layer1_global_regime_panel.md` · `specs/layer1_axes/restructured_axes_v1_1/`  
> **活规划：** `PROJECT_IMPLEMENTATION_ROADMAP.md` §3.2 · §6.1.1 #2

---

## 1. 目的

在 **M-DATA-03 已闭合的 clean 输入**上，让五轴按 `restructured_axes_v1_1` **完整**指标与输入契约真落地：`sync→clean→指标引擎→pytest` **同库真链**（非 tmp DB seed 冒充 R4）。

## 2. 验收底线（AC）

| 项         | 标准                                                      |
| ---------- | --------------------------------------------------------- |
| **Rating** | G1 **MCR ≥ R4**；K1/K2 随父模块闭合                       |
| **五轴**   | 每轴至少一条可断言真链（或 ADR 源 replay + 其余真网输入） |
| **pytest** | `tests/test_layer1_*` 等 **GREEN**（§6.1.1 #6）           |
| **禁止**   | L1 子集冒充全模块；任务 CLOSED 但 Rating 仍 R3            |

## 3. Trellis / `/to-issues`

- **类型：** complex Trellis（§1.5）
- **竖切索引：** `M_G1_03_TO_ISSUES_INDEX.md`（Plan 冻结时增补）
- **Plan 冻结前：** 读路线图 §0.1.3 · §1.2 · `GLOBAL_*` 契约
