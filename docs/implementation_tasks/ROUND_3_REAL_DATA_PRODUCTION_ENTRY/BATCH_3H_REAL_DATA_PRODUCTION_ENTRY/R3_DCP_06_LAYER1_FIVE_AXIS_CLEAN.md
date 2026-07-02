# R3-DCP-06 — Layer1 五轴真 clean 全绿（G12 PASS 硬门禁）

> **规划 ID：** R3-DCP-06  
> **Wave：** 4b · **并行按轴**（见 Trellis `to-issues-slices.md`）  
> **Trellis：** `.trellis/tasks/wave4-r3-dcp-06-five-axis-clean/` · Plan v4.1  
> **Module：** G1 Layer1 axes · K2 五轴 spec · K1 model input whitelist · A4 ResourceGuard  
> **评级：** G1/K2 `R3→R4`（PASS 硬门禁）  
> **前置：** R3-DCP-05 ✅ CLOSED @ `c2258363`（Tier A clean 增量输入）  
> **状态：** **Execute DONE** — 待 Audit（`feature/wave4-r3-dcp-06-five-axis-clean`）

---

## 1. Goal（人话）

五轴（环境、信用压力、风险偏好、流动性、情绪）现在主要靠 **staged fixture** 跑通 loader/引擎；这一轮要让每条轴至少有一条 **P0 锚点指标** 从 **DCP-05 写入的 Tier A clean 表**读数 → 算特征/解释 → pytest 全绿，**不再依赖 `staged_fixture_only` 作为唯一输入**。

---

## 2. 价值

- Wave 4 **PASS 硬门禁**（用户裁决：五轴必须在 `R3H-05-GATE` 之前全绿）
- 承接 `ACC-LAYER-E2E-LIVE-001` 的 **L1 子集**（全链 L3–L5 余量阶段外置至 DCP-07/08/10 + Wave 5）
- 解锁 `MODULE_COMPLETION_RATING` G1 R3→R4、K2 每轴 ≥1 真 clean 测

---

## 3. 约束

| 约束      | 要求                                                                                                  |
| --------- | ----------------------------------------------------------------------------------------------------- |
| 输入 SSOT | **Tier A clean**（`axis_observation` · `security_bar_1d` 等）；禁止用 staged fixture 冒充 PASS        |
| 金路径    | 读 clean → `AxisFeatureEngine` → `AxisInterpretationEngine` → snapshot/lineage（已有 Batch 2/2.5 桥） |
| 真网      | 默认 **replay/clean 种子**；live 须 env-gate + 隔离库（延续 DCP-05 政策）                             |
| Schema    | **无新 migration**（R3H-06 + 015 已封）；本票只扩读路径与测                                           |
| K1        | P0 FRED/CFTC/alpha 行 `readiness` 与 runtime 对齐；**不关** `B2.5-O-05` live primary                  |
| 参考项目  | Plan L1/L2/L3 **仅** `参考项目/**`；仓内 Layer1 = 承接，不进借鉴梯                                    |
| Registry  | 若动 `model_inputs` / capabilities → 主会话排队 merge                                                 |

---

## 4. 架构触点

```text
Tier A incremental (DCP-05) → clean tables
  axis_observation  ← fred / us_treasury / bis / world_bank / cftc_cot
  security_bar_1d   ← alpha_vantage (流动性 ponytail 锚点)
        ↓
Layer1CleanObservationReader (本票 S00)
        ↓
AxisFeatureEngine → AxisInterpretationEngine → snapshot lineage
        ↓
per-axis replay e2e pytest (S01–S05) + 五轴集成 smoke (S06)
```

**P0 每轴锚点（ADR-029）：**

| 轴            | indicator_id                 | clean 来源                                                               |
| ------------- | ---------------------------- | ------------------------------------------------------------------------ |
| ENVIRONMENT   | ENV-E1-DGS10                 | fred → `axis_observation`                                                |
| CREDIT_STRESS | CRD.CS1.BAA10Y               | fred → `axis_observation`                                                |
| RISK_APPETITE | RA.R1.VIXCLS_30D_IMPLIED_VOL | fred → `axis_observation`                                                |
| LIQUIDITY     | LIQ.B-I1.AMIHUD_ILLIQ        | alpha_vantage SPY → `security_bar_1d`（ponytail：非 spec tiingo 主路径） |
| SENTIMENT     | SEN-S1-COT_LF_NET            | cftc_cot → `axis_observation`                                            |

---

## 5. Acceptance criteria

- [x] `PROJECT_IMPLEMENTATION_ROADMAP.md` §3.5.1 五轴清单 **全部 [x]**
- [x] 五轴各 ≥1 replay e2e：**读 clean 非 fixture** → 特征/解释可断言
- [x] `tests/test_layer1_*` 或新增 `tests/test_layer1_*_clean_e2e.py` 全绿
- [x] ResourceGuard：五轴 smoke 路径 cap 证明（A4）
- [x] K1 `layer1_source_whitelist.yaml` P0 行与实现一致
- [x] `ACC-LAYER-E2E-LIVE-001` **L1 子集**关账；L3–L5 **阶段外置**登记（→ DCP-07/08/10 + R3H-05-GATE）
- [x] `research/reference-adoption-dcp06.md` 含参考项目 L1/L2/L3（非仓内）
- [x] Plan v4.1 包齐；`validate-plan-freeze` exit 0
- [x] `uv run pytest -q` exit 0（S06 主会话收尾复验 @ 2026-07-02）

---

## 6. 非目标

- FRED **live primary** 关账（`B2.5-O-05` → Wave 5 / `R3F-SH-06`）
- L2/L4/L5 全链 E2E（DCP-07/08/10）
- tiingo/FMP 流动性主路径（spec 原 primary；本票 ponytail 用 alpha_vantage bar）
- 五轴 **全部** YAML 指标一次落地（仅 P0 锚点/轴）
- 新 migration DDL

---

## 7. Trellis 入口

`.trellis/tasks/wave4-r3-dcp-06-five-axis-clean/research/00-EXECUTION-ENTRY.md`
