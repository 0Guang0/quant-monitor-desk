# Batch 3H — Real Data Production Entry（模块轨 PASS 收口）

> **Batch:** Round 3H Real Data Production Entry  
> **总施工图：** 根目录 `PROJECT_IMPLEMENTATION_ROADMAP.md`（模块轨道版）  
> **PASS 协调索引：** `R3H_PASS_EXECUTION_PLAN.md`  
> **批次状态：** R3H-01～04、R3H-06、Batch 3V — **CLOSED** @ 2026-06-29  
> **当前下一执行入口（写死）：** **`R3H-10` → `R3H-07` 串行** — 见 `WAVE1_R3H10_THEN_R3H07_TO_ISSUES_INDEX.md`  
> **参考采纳索引：** `R3H_REFERENCE_ADOPTION_INDEX.md`  
> **Purpose:** Round4 产品化之前，闭合数据面、增量运维、**五轴 Layer1（PASS 前全绿）** 与生产接入审计；**不是** Round4 API/前端工作。

---

## 1. 执行纪律（反平铺）

| 规则                | 说明                                                              |
| ------------------- | ----------------------------------------------------------------- |
| **模块轨**          | 一活卡 = 一主 **Module ID** + 明确 **评级一跳**（如 C2：`R3→R4`） |
| **Wave = 依赖门禁** | 不是「每个模块挖一点」；Wave 内按 INDEX **竖切** 关账             |
| **Wave 1 串行**     | **R3H-10 CLOSED 后** 才允许 R3H-07                                |
| **地图不是工单**    | `PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md` 只查漏             |
| **三批法则**        | `MODULE_COMPLETION_RATING.md` §2 — 禁止 registry 单行微切片       |

---

## 2. Round3 PASS 波次（活轨）

```text
[✅] 历史：3F-R · 3G · Batch 3V · R3H-01～04 · R3H-06
  ↓
Wave 1  R3H-10 → R3H-07（串行）           ← 当前
  ↓
Wave 2  R3H-08A / 08B / 08C / 08D（24 源 live）
  ↓
Wave 3  R3-DCP-01..03（baostock+fred 增量 + 写后抽检）
  ↓
Wave 4  R3-DCP-05..10（Tier A 增量扩展 + 五轴全绿 + L2/L4 最小）
  ↓
Wave 5  R3H-05A..E → R3H-05-GATE（PASS）
  ↓
Round4  BATCH_04（须 PASS_ROUND4_REAL_DATA_READY）
```

| Wave  | 规划 ID             | 主模块          | `/to-issues` INDEX                                   |
| ----- | ------------------- | --------------- | ---------------------------------------------------- |
| —     | R3H-01～04          | C3, …           | 各活卡（**CLOSED**）                                 |
| —     | R3H-06              | B1, A2          | `R3H_06_CLEAN_SCHEMA.md`（**CLOSED**）               |
| **1** | **R3H-10 → R3H-07** | **C2, E4 → G4** | **`WAVE1_R3H10_THEN_R3H07_TO_ISSUES_INDEX.md`**      |
| 2     | R3H-08A–D           | C3, A3, B\*, G6 | 待建 `WAVE2_R3H08_TO_ISSUES_INDEX.md`                |
| 3–4   | R3-DCP-\*           | D1, E1, G1, …   | 待建 `R3_DCP_TO_ISSUES_INDEX.md`                     |
| 5     | R3H-05 + GATE       | 全表            | `R3H_05_LAYER_BINDING_AND_PRODUCTION_ENTRY_AUDIT.md` |

---

## 3. 任务卡清单

### 3.1 已 CLOSED（历史，勿作当前入口）

| Task ID | Active card                                      | 状态                    |
| ------- | ------------------------------------------------ | ----------------------- |
| R3H-01  | `R3H_01_OFFICIAL_MACRO_DISCLOSURE_ADAPTERS.md`   | CLOSED @ 2026-06-28     |
| R3H-02  | `R3H_02_MARKET_DATA_ADAPTERS.md`                 | CLOSED；CAL-US → R3H-07 |
| R3H-03  | `R3H_03_CN_MARKET_ADAPTERS.md`                   | CLOSED；CN 日历 Q12     |
| R3H-04  | `R3H_04_PREDICTION_AND_WEB_EVIDENCE_ADAPTERS.md` | CLOSED；web_search mock |
| R3H-06  | `R3H_06_CLEAN_SCHEMA.md`                         | CLOSED @ 2026-06-29     |

### 3.2 活轨（按 Wave 顺序）

| Task ID    | Active card                                          | Wave | Module    | 评级移动    |
| ---------- | ---------------------------------------------------- | ---- | --------- | ----------- |
| **R3H-10** | `R3H_10_DATASOURCE_SERVICE_SSOT.md`（**待建**）      | 1    | C2, E4    | R3→R4       |
| **R3H-07** | `R3H_07_US_TRADING_CALENDAR.md`（**待建**）          | 1    | G4, C3    | R3→R4       |
| R3H-08A–D  | 待建                                                 | 2    | C3, A3, … | R3→R4       |
| R3-DCP-\*  | PASS 计划 §4                                         | 3–4  | D1, G1, … | 见路线图 §3 |
| R3H-05     | `R3H_05_LAYER_BINDING_AND_PRODUCTION_ENTRY_AUDIT.md` | 5    | 全表      | GATE only   |

**R3H-05 不是当前 Execute 入口** — 仅 Wave 5 审计；不得在 Wave 1–4 前单独 PASS。

---

## 4. 用户裁决（Round4 前有效）

| 议题              | 裁决                            |
| ----------------- | ------------------------------- |
| Round4 入口       | `PASS_ROUND4_REAL_DATA_READY`   |
| web_search 真 API | post-Round4（`R3H-WEB-SEARCH`） |
| 24 源 live        | Wave 2 env-gated → Tier A/B/C   |
| 五轴 G12          | **Wave 4 PASS 前 pytest 全绿**  |
| 增量试点源        | baostock + fred（Wave 3）       |

---

## 5. Batch-level gates（Batch 3H CLOSED 当且仅当）

1. Wave 1–5 全部 **CLOSED** + `R3H-05-GATE` = **PASS**。
2. `MODULE_COMPLETION_RATING.md` PASS 阻塞模块达标（含 **G1 五轴**）。
3. 每 READY 源：live 证据 + 正确 Tier（`R3H_PASS_EXECUTION_PLAN.md` §2.1）。
4. Round4 manifest 可开工；**不在此批次做** I 组 API/前端。

---

## 6. Forbidden scope

- 不做全市场 / 全历史 / 默认分钟线全量。
- 不把 prediction market 写 clean factual 表。
- 不让 `web_search` 真 API 在本批次冒充 READY。
- 不让 Agent 触发写入。
- Wave 1 **禁止** R3H-07 与 R3H-10 并行（除非主会话多 agent 显式调度）。
- 禁止「只改 registry 一行」冒充模块完成。

---

## 7. 关联文件

```text
PROJECT_IMPLEMENTATION_ROADMAP.md
MODULE_COMPLETION_RATING.md
BATCH_3H_TASK_CARD_MANIFEST.md
BATCH_3H_COORDINATOR_PLAYBOOK.md
R3H_PASS_EXECUTION_PLAN.md
WAVE1_R3H10_THEN_R3H07_TO_ISSUES_INDEX.md
R3G_MASS_REHEARSAL_OPEN_GAPS.md
```
