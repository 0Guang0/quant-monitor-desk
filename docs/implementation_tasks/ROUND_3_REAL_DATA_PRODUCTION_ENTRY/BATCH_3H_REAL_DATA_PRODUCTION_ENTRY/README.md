# Batch 3H — Real Data Production Entry（模块轨 PASS 收口）

> **Batch:** Round 3H Real Data Production Entry  
> **总施工图：** 根目录 `PROJECT_IMPLEMENTATION_ROADMAP.md`（模块轨道版）  
> **PASS 协调索引：** `R3H_PASS_EXECUTION_PLAN.md`  
> **批次状态：** Wave 1–3 **CLOSED** @ 2026-06-30（`git log` @ `893e6e2b`）  
> **当前下一执行入口（写死）：** **Wave 4** `R3-DCP-05..10` — 见 `PROJECT_IMPLEMENTATION_ROADMAP.md` §3.5 · `R3_DCP_TO_ISSUES_INDEX.md`（Wave 3 已索引；Wave 4 活卡 **Plan 阶段待建**）  
> **参考采纳索引：** `R3H_REFERENCE_ADOPTION_INDEX.md`  
> **Purpose:** Round4 产品化之前，闭合数据面、增量运维、**五轴 Layer1（PASS 前全绿）** 与生产接入审计；**不是** Round4 API/前端工作。

---

## 1. 执行纪律（反平铺）

| 规则                | 说明                                                              |
| ------------------- | ----------------------------------------------------------------- |
| **模块轨**          | 一活卡 = 一主 **Module ID** + 明确 **评级一跳**（如 D1：`R3→R4`） |
| **Wave = 依赖门禁** | 不是「每个模块挖一点」；Wave 内按 INDEX **竖切** 关账             |
| **Wave 4 依赖**     | Wave 2 数据入库 + Wave 3 增量模板可复制                           |
| **地图不是工单**    | `PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md` 只查漏             |
| **三批法则**        | `MODULE_COMPLETION_RATING.md` §2 — 禁止 registry 单行微切片       |

---

## 2. Round3 PASS 波次（活轨）

```text
[✅] 历史：3F-R · 3G · Batch 3V · R3H-01～04 · R3H-06
  ↓
[✅] Wave 1  R3H-10 → R3H-07（串行）
  ↓
[✅] Wave 2  R3H-08A / 08B / 08C / 08D（24 源 live）
  ↓
[✅] Wave 3  R3-DCP-01..03（baostock+fred 增量 + 写后抽检）
  ↓
Wave 4  R3-DCP-05..10（Tier A 增量扩展 + 五轴全绿 + L2/L4 最小）  ← 当前
  ↓
Wave 5  R3H-05A..E → R3H-05-GATE（PASS）
  ↓
Round4  BATCH_04（须 PASS_ROUND4_REAL_DATA_READY）
```

| Wave  | 规划 ID           | 主模块          | `/to-issues` INDEX                                   | 状态       |
| ----- | ----------------- | --------------- | ---------------------------------------------------- | ---------- |
| —     | R3H-01～04        | C3, …           | 各活卡                                               | **CLOSED** |
| —     | R3H-06            | B1, A2          | `R3H_06_CLEAN_SCHEMA.md`                             | **CLOSED** |
| 1     | R3H-10 → R3H-07   | C2, E4 → G4     | `WAVE1_R3H10_THEN_R3H07_TO_ISSUES_INDEX.md`          | **CLOSED** |
| 2     | R3H-08A–D         | C3, A3, B\*, G6 | `R3H_PASS_EXECUTION_PLAN.md` §4                      | **CLOSED** |
| 3     | R3-DCP-01..03     | D1, E1, E2, F0  | `R3_DCP_TO_ISSUES_INDEX.md` §1–3                     | **CLOSED** |
| **4** | **R3-DCP-05..10** | **D1, G1, K2…** | `R3_DCP_TO_ISSUES_INDEX.md` §4+（**Plan 待建**）     | **OPEN**   |
| 5     | R3H-05 + GATE     | 全表            | `R3H_05_LAYER_BINDING_AND_PRODUCTION_ENTRY_AUDIT.md` | **OPEN**   |

---

## 3. 任务卡清单

### 3.1 已 CLOSED（历史，勿作当前入口）

| Task ID    | Active card / Trellis               | 状态                |
| ---------- | ----------------------------------- | ------------------- |
| R3H-01～04 | `R3H_0*_*.md`                       | CLOSED @ 2026-06-28 |
| R3H-06     | `R3H_06_CLEAN_SCHEMA.md`            | CLOSED @ 2026-06-29 |
| R3H-10     | `R3H_10_DATASOURCE_SERVICE_SSOT.md` | CLOSED @ 2026-06-29 |
| R3H-07     | `R3H_07_US_TRADING_CALENDAR.md`     | CLOSED @ 2026-06-29 |
| R3H-08A–D  | live productization（四 Tier 轨）   | CLOSED @ 2026-06-29 |
| R3-DCP-01  | `R3_DCP_01_BAOSTOCK_INCREMENTAL.md` | CLOSED @ `5dc71c0b` |
| R3-DCP-02  | `R3_DCP_02_FRED_INCREMENTAL.md`     | CLOSED @ `5d8d7b0f` |
| R3-DCP-03  | `R3_DCP_03_POST_WRITE_INSPECT.md`   | CLOSED @ `eff49343` |

### 3.2 活轨（按 Wave 顺序）

| Task ID       | Active card / 规划                                   | Wave | Module     | 评级移动  | 状态 |
| ------------- | ---------------------------------------------------- | ---- | ---------- | --------- | ---- |
| R3-DCP-05     | Tier A 增量扩展（活卡 **待建**）                     | 4    | D1, E1     | R4        | OPEN |
| **R3-DCP-06** | **五轴 G12 全绿**（活卡 **待建**）                   | 4    | **G1, K2** | **R3→R4** | OPEN |
| R3-DCP-07     | Layer2 最小竖切（活卡 **待建**）                     | 4    | G2         | R3→R4     | OPEN |
| R3-DCP-08     | Layer4 + US 日历（活卡 **待建**）                    | 4    | G4         | R3→R4     | OPEN |
| R3-DCP-09     | 有界 backfill（活卡 **待建**）                       | 4    | D1         | R4        | OPEN |
| R3-DCP-10     | Layer5 真源绑定（活卡 **待建**）                     | 4    | G5, A3     | R2→R3     | OPEN |
| R3H-05        | `R3H_05_LAYER_BINDING_AND_PRODUCTION_ENTRY_AUDIT.md` | 5    | 全表       | GATE only | OPEN |

**R3H-05 不是当前 Execute 入口** — 仅 Wave 5 审计；不得在 Wave 4 完成前单独 PASS。

---

## 4. 用户裁决（Round4 前有效）

| 议题              | 裁决                                                 |
| ----------------- | ---------------------------------------------------- |
| Round4 入口       | `PASS_ROUND4_REAL_DATA_READY`                        |
| web_search 真 API | post-Round4（`R3H-WEB-SEARCH`）                      |
| 24 源 live        | Wave 2 env-gated → Tier A/B/C ✅                     |
| 五轴 G12          | **Wave 4 R3-DCP-06** — PASS 前 pytest 全绿（硬门禁） |
| 增量试点源        | baostock + fred（Wave 3）✅                          |

---

## 5. Batch-level gates（Batch 3H CLOSED 当且仅当）

1. Wave 1–5 全部 **CLOSED** + `R3H-05-GATE` = **PASS**。
2. `MODULE_COMPLETION_RATING.md` PASS 阻塞模块达标（含 **G1 五轴 @ R3-DCP-06**）。
3. 每 READY 源：live 证据 + 正确 Tier（`R3H_PASS_EXECUTION_PLAN.md` §2.1）。
4. Round4 manifest 可开工；**不在此批次做** I 组 API/前端。

**当前进度：** 1/5 波次组 CLOSED（Wave 1–3 ✅）；Wave 4–5 🔴。

---

## 6. Forbidden scope

- 不做全市场 / 全历史 / 默认分钟线全量。
- 不把 prediction market 写 clean factual 表。
- 不让 `web_search` 真 API 在本批次冒充 READY。
- 不让 Agent 触发写入。
- 禁止「只改 registry 一行」冒充模块完成。
- Wave 4 五轴不得 WARN 收窄为「三轴先 PASS」。

---

## 7. 关联文件

```text
PROJECT_IMPLEMENTATION_ROADMAP.md
MODULE_COMPLETION_RATING.md
BATCH_3H_TASK_CARD_MANIFEST.md
BATCH_3H_COORDINATOR_PLAYBOOK.md
R3H_PASS_EXECUTION_PLAN.md
WAVE1_R3H10_THEN_R3H07_TO_ISSUES_INDEX.md
R3_DCP_TO_ISSUES_INDEX.md
R3G_MASS_REHEARSAL_OPEN_GAPS.md
```
