# QMD 项目实施总路线图（模块轨道版）

> **版本：** 2026-07-04（三批法则 R4→R5→R6 · §0.1 合并 · M-DATA-03 关账）  
> **定位：** 根目录**唯一活规划** — 以 **51 个 Module ID** 为行；完成度以 **`MODULE_COMPLETION_RATING.md` Rating 列（Pass E）** 为准（代码+测试，非任务卡自述）。  
> **通俗解释：** 本文件回答「下一步做什么业务、关哪个模块、怎样算做完」；**新任务卡才是工单**；历史 Wave 叙事见 legacy / 归档。  
> **上一版备份：** `docs/archive/planning/PROJECT_IMPLEMENTATION_ROADMAP.legacy-20260629.md` · `R3H_PASS_EXECUTION_PLAN.archived-20260702.md`  
> **进度复核：** `master` @ 2026-07-04 — M-DATA-03 CLOSED；**下一入口 M-G1-03** — 见 MCR §0 · 本文 §3。  
> **重构：** §3 **模块闭环队列 v2** 已按用户 grill-gate @ 2026-07-02 生效；§3L 为历史 Wave 编排（只读）。

### 当前下一入口（v2 · 用户确认 @ 2026-07-02 · **M-DATA-03 关账 @ 2026-07-04**）

| 优先级 | 票 ID             | 业务一句话                                                     | 状态 / 开工前                                                        |
| ------ | ----------------- | -------------------------------------------------------------- | -------------------------------------------------------------------- |
| ~~P0~~ | ~~**M-DATA-03**~~ | —                                                              | **CLOSED** @ 2026-07-04 · R4 · ADR-034 · 只读 §3.1                   |
| **P0** | **M-G1-03**       | 五轴按设计完整落地（真链，非仅 seed）                          | **下一入口** · 依赖 M-DATA-03 **R4** clean 输入（隔离库证明）        |
| **P1** | **M-G2-FULL**     | Layer2 九组资产按 `layer2_cross_asset_sensor.md` 完整落地      | 单 **Plan→Execute** 流程内多 worktree/串行切片；**统一** A1–A8 Audit |
| **P1** | **M-G4-FULL**     | Layer4 各 `market_id` 按 `layer4_market_structure.md` 完整落地 | 同上；可与 G2/G5 **并行**（不同 graph 节点）                         |
| **P1** | **M-G5-FULL**     | Layer5 证据链按 `layer5_security_evidence.md` 完整落地         | 同上                                                                 |
| **P0** | **M-PASS-01**     | `PASS_ROUND4_REAL_DATA_READY`（硬门禁 **R4** · 见 §6.1）       | **末位**：G\* 达 R4 + 清单全绿（**≠ R6** · §6.1.3）                  |

活评级：`MODULE_COMPLETION_RATING.md` · 工程契约：`全局规则.txt` · 历史 Wave：§3L / `R3H_PASS_EXECUTION_PLAN.archived-20260702.md`

---

## 0. 定位与 SSOT 指针

| 用途                          | 文件                                                  |
| ----------------------------- | ----------------------------------------------------- |
| 完成度运营快照                | `MODULE_COMPLETION_RATING.md` §3                      |
| 机器索引                      | `specs/context/authority_graph.yaml` v2               |
| 项目地图                      | `docs/generated/project_map.generated.md`             |
| Tier A/B/C 落库逐源表（只读） | `R3H_PASS_EXECUTION_PLAN.archived-20260702.md` §2.1   |
| Round4 产品范围               | `BATCH_04_TASK_CARD_MANIFEST.md`                      |
| DataSync 五类 job / 写库      | 本文 **§5.1**                                         |
| Wave 0 `/to-issues` 范例      | `WAVE0_BATCH3V_TO_ISSUES_INDEX.md`                    |
| Round3 活轨 `/to-issues` 索引 | 本文 **§3.7** · `docs/implementation_tasks/README.md` |

### 0.1 用户裁决与规划约束（有效）

> **来源：** grill-gate @ 2026-07-02 · 与 `MODULE_COMPLETION_RATING.md` §1 · §1.2 **一致** · **三批法则**见 §1.2。

#### 0.1.1 完成度与证据（Pass E）

| 项               | 裁决                                                                                      |
| ---------------- | ----------------------------------------------------------------------------------------- |
| **PASS 判定**    | **真实代码 + 真实运行**；**禁止**任务 CLOSED、文档勾选、tmp DB seed 冒充                  |
| **Rating 依据**  | MCR **Rating 列**只信可执行代码 + pytest；子集竖切记 **Milestone**，不得抬升整模块 Rating |
| **模块「完成」** | 声明 scope **未达 R4** 不得称模块完成（R4 = 完整功能/机制真落地）                         |

#### 0.1.2 PASS 门禁 `PASS_ROUND4_REAL_DATA_READY`

| 项            | 裁决                                                                                            |
| ------------- | ----------------------------------------------------------------------------------------------- |
| **名称**      | 可继续叫 `PASS_ROUND4_REAL_DATA_READY` = **M-PASS-01**（§6.1）                                  |
| **过关**      | 清单逐项真绿 + 硬门禁模块 **MCR Rating ≥ R4**；无「R3 冒充 R4 / CLOSED 但 Rating 仍 R3」        |
| **PASS 档位** | **≠ R6** — PASS 只验 **R4 能力**；**R5/R6** 走三批法则 Batch 2/3 · 主收敛 **Batch05**（§6.1.3） |
| **旧 Wave**   | Wave 1–4 CLOSED **不自动算 PASS**；仅历史证据索引                                               |

#### 0.1.3 模块落地、拆法与建模 scope

| 项       | 裁决                                                                                                        |
| -------- | ----------------------------------------------------------------------------------------------------------- |
| **范围** | 设计权威 **完整落地**（`docs/modules/`、`specs/contracts/`、`specs/layer*`）；**禁止** P0 子集却宣称 CLOSED |
| **G2**   | `layer2_cross_asset_sensor.md` §2 **九组**全覆盖                                                            |
| **G4**   | `layer4_market_structure.md` §2 各 `market_id` 按设计落地                                                   |
| **G5**   | `layer5_security_evidence.md` §2–3 第一阶段资产域 + 证据链完整落地                                          |
| **拆法** | **一模块成品 = 一 complex 票**；票内 `/to-issues` 竖切可并行 worktree · **一次** A1–A8 Audit                |
| **禁止** | 同一模块完整成品拆成多张独立 Plan/Audit/Repair 票（Wave/DCP 教训）                                          |
| **允许** | 票内分阶段 + **可选**单次对抗性 check；**不得**每阶段各走完整 8 维 Audit                                    |
| **关账** | MCR 对应模块 **Rating 必须跃迁**（或 ADR 收窄设计权威并同步文档）                                           |

#### 0.1.4 排期与路由

| 项                      | 裁决                                                 |
| ----------------------- | ---------------------------------------------------- |
| **后端优先**            | Round3 闭合数据面 + 五轴 + 增量后再开 Round4 产品    |
| **Layer1 五轴（G12）**  | PASS 前 `tests/test_layer1_*` 等 **pytest 全绿**     |
| **11 源真网**           | **已满足** — M-DATA-03 CLOSED @ 2026-07-04 · ADR-034 |
| **R3-DCP 试点**         | **历史**；由 M-DATA-03 承接                          |
| **Round4 入口**         | **M-PASS-01** 通过后 · `BATCH_04_*`                  |
| **`web_search` 真 API** | **post-Round4**（J5 · ADR）                          |
| **真网 live**           | env-gated Tier A/B/C；新票 AC 写入模块闭环           |

#### 0.1.5 关账证据（只读）

**M-DATA-03** CLOSED @ 2026-07-04 — Tier A 11/11 · Tier B 10/10 · B2/C3/D1/E1/E2/F0→**R4** — **ADR-034** · §3.1 · archived Trellis `m-data-03-tier-a-live/`。

### 0.2 已核实 canonical 入口

| 范围          | 文件夹 / 文件                                                                                                 |
| ------------- | ------------------------------------------------------------------------------------------------------------- |
| Batch 3V      | `BATCH_3V_VERIFIED_AUDIT_CLEANUP/` — **CLOSED**                                                               |
| Batch 3H PASS | `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/`（历史） |
| Round4        | `BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/`                                                                     |
| Round5        | `BATCH_05_VERIFIED_AUDIT_SECURITY_RELEASE/`                                                                   |

本文件与 canonical 任务卡冲突时：**修路线图或任务卡使之闭环**，不得用路线图压过活卡。

---

## 1. 全局完成度规则

### 1.1 评级量表（摘要）

完整定义：`MODULE_COMPLETION_RATING.md` §1 · §1.2。

| 级别   | 规划含义                                                                     |
| ------ | ---------------------------------------------------------------------------- |
| R0–R1  | 未开工 / 壳子                                                                |
| R2–R3  | 历史竖切 / staged fixture（**非**三批目标档；见 Milestone 列）               |
| **R4** | **Batch 1 目标** — 声明 scope **完整功能、机制真落地**（证明环境常为隔离库） |
| **R5** | **Batch 2 目标** — 运维、监控、使用/运行手册与生产 posture 收尾              |
| **R6** | **Batch 3 目标** — **完整商业可发布** · 真实生产跑通 + Batch05 manifest      |

### 1.2 三批法则（从零到商业真生产 · **至多三批**）

| 批          | Rating 目标 | 交付含义                                                                              |
| ----------- | ----------- | ------------------------------------------------------------------------------------- |
| **Batch 1** | **R4**      | 声明 scope **完整功能、机制真落地**（端到端真链 + 诚实测试；证明环境可为隔离库）      |
| **Batch 2** | **R5**      | **运维收尾** — 监控、告警、runbook、operator 使用/运行手册、生产 posture              |
| **Batch 3** | **R6**      | **完整商业真生产** — R4+R5 已闭合 · 回归全绿 · 无开放 blocker · Batch05 发布 manifest |

**通俗：** R4 能力落地后，**再两轮**（Batch 2→R5 · Batch 3→R6）即到商业可发布；**全程禁止第四批**凑发布。`批/3` 见 §2 · MCR §1.1。**I6、K2、K3** 随父模块，不单独占三批。

**历史模块：** Wave/DCP 已消耗的批次仍计入 `批/3` 上限；下一批须按上表 **追当前缺口档**（如在 R3 的模块下一批直追 **R4**，不得再开「R2 竖切批」）。

### 1.3 三批与评级对照

| 批  | Rating | 能否对外完整发布               |
| --- | ------ | ------------------------------ |
| 1   | R4     | 否 — 功能已落地，未运维/未发布 |
| 2   | R5     | 否 — 可运维，未商业真生产发布  |
| 3   | R6     | **是**                         |

### 1.4 参考项目使用总规则（Batch04 引用 `roadmap §1.4`）

| 规则               | 说明                                                        |
| ------------------ | ----------------------------------------------------------- |
| 任务卡本地执行     | 参考路径、禁止能力、目标文件、测试写在任务卡内              |
| 覆盖地图不是工单   | `PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md` 只查漏       |
| 不复制危险 runtime | 禁止 `参考项目/**` runtime import；禁止 OpenBB AGPL runtime |
| 采纳阶梯 L1/L2/L3  | `reference_adoption_guardrails.yaml`                        |
| 不引入交易动作     | 禁止 order/broker/terminal 语义                             |
| 最多三批达 R6      | 同 §1.2                                                     |

### 1.5 Trellis 路由（v2）

| 类型                | 适用                                                                   |
| ------------------- | ---------------------------------------------------------------------- |
| **complex Trellis** | **§3 活票**（M-G\*-FULL、M-PASS-01）、Round4 B04；M-DATA-03 **CLOSED** |
| **debt-lite**       | Batch6 卫生、已 CLOSED 票的小修补（**不得**承接模块完整成品）          |
| Plan 冻结前         | 活票须 `/to-issues` 垂直切片（§3.6）；**一模块成品 = 一 complex 票**   |

### 1.6 并行与合并

- **worktree：** 一 agent 一 worktree；按 `authority_graph.yaml` **节点**划分。
- **registry 三件套**（`source_registry.yaml`、`source_capabilities.yaml`、`tests/test_catalog.yaml`）— **主会话排队 merge**。
- **schema DDL：** R3H-06 已封板；新 DDL → Batch6/B05 门禁。
- **改符号前** `impact()`；**提交前** `detect_changes()`。

### 1.7 完整流程任务规则

见 **§0.1.3**（一模块一 complex 票 · 票内竖切 · 统一 A1–A8 · 关账须 Rating 跃迁）。

### 1.8 模块 → 活票归属（一模块一完整流程）

> **规则：** 同一 **Module ID 的完整成品**只归属 **一张** §3 complex 票；票内可多批次（S01…Sn），**禁止**再开第二张完整流程票。  
> **子范围**（K2⊂G1、I8⊂I1）随父模块票闭合，不单独 freeze Plan。

| 活票           | 主模块（Rating 跃迁）                          | 同票闭合的关联模块             | 设计权威                                               |
| -------------- | ---------------------------------------------- | ------------------------------ | ------------------------------------------------------ |
| **M-DATA-03**  | **CLOSED** @ 2026-07-04 — C3,D1,E1,E2,F0,B2→R4 | —                              | ADR-034 · archived Trellis                             |
| **M-G1-03**    | G1 → R4                                        | K1, K2, A5                     | `layer1_global_regime_panel.md` · `specs/layer1_axes/` |
| **M-G2-FULL**  | G2 → R4                                        | —                              | `layer2_cross_asset_sensor.md` §2 九组                 |
| **M-G4-FULL**  | G4 → R4                                        | —                              | `layer4_market_structure.md` §2 各 market              |
| **M-G5-FULL**  | G5 → R4                                        | A3 provenance 绑真源           | `layer5_security_evidence.md` §2–3                     |
| **M-PASS-01**  | 门禁清单绿                                     | C1, C4, B3, G6, A3/A4 终态审计 | 本文 §6.1.1                                            |
| **Batch6**     | D2, D3, D4, H1, A6                             | 不挡 PASS                      | §5.2                                                   |
| **Round4 B04** | I1–I8, J2                                      | PASS 后                        | `BATCH_04_TASK_CARD_MANIFEST.md`                       |
| **Batch05**    | 全体 **Batch 3 → R6**                          | A1, A2, A7, E3, E6, J3         | §5.3                                                   |

**历史 CLOSED**（R3H-07/10、R3H-08、R3-DCP-\*）：只读证据，**不得**作为新开工路由；未达设计成品 scope 的竖切 → 记入 MCR **Milestone** 列，由上表活票承接余量。

---

## 2. 模块轨道总表（51 Module ID）

> 当前 Rx / 批/3 来自 `MODULE_COMPLETION_RATING.md` §3 @ Pass E。  
> **活票列：** 模块完整成品的 **唯一** 完整流程归属（§1.8）；历史 R3H/DCP ID 仅作 Milestone 证据。  
> **PASS 阻塞：** §6.1.1 #2–#5 未达 **R4** 的 G/K 模块，及 #7–#9 门禁未绿；**已达 R4 且清单项 ✅ 的不阻塞**（如 @ M-DATA-03 的 B2/C3/D1/E1/E2/F0）。

### 2.A Platform（A1–A7）

| ID  | 模块               | 当前 | 批/3 | PASS 阻塞 | 活票 / 归属                   |
| --- | ------------------ | ---- | ---- | --------- | ----------------------------- |
| A1  | Project scaffold   | R3   | 2/3  | —         | Batch05                       |
| A2  | DuckDB schema      | R3   | 2/3  | —         | Batch05                       |
| A3  | Storage / evidence | R3   | 2/3  | **是**    | **M-G5-FULL** + **M-PASS-01** |
| A4  | ResourceGuard      | R3   | 2/3  | **是**    | **M-G1-03** / **M-PASS-01**   |
| A5  | Snapshot lineage   | R3   | 2/3  | —         | **M-G1-03**                   |
| A6  | Spec migrator      | R1   | 0/3  | —         | Batch6                        |
| A7  | Platform matrix    | R2   | 1/3  | —         | Batch05                       |

### 2.B Write path（B1–B3）

| ID  | 模块                | 当前   | 批/3 | PASS 阻塞 | 活票 / 归属            |
| --- | ------------------- | ------ | ---- | --------- | ---------------------- |
| B1  | WriteManager + gate | R4     | 2/3  | —         | Batch05 manifest       |
| B2  | Data quality        | **R4** | 2/3  | —         | ✅ M-DATA-03 · Batch05 |
| B3  | Source conflict     | R2→R3  | 2/3  | **是**    | **M-PASS-01**          |

### 2.C Data sources（C1–C4, J5）

| ID  | 模块                | 当前   | 批/3 | PASS 阻塞 | 活票 / 归属                  |
| --- | ------------------- | ------ | ---- | --------- | ---------------------------- |
| C1  | Registry / route    | R3     | 2/3  | **是**    | **M-PASS-01**                |
| C2  | DataSourceService   | R4     | 2/3  | —         | 历史 CLOSED · M-PASS-01 审计 |
| C3  | Adapters / ports    | **R4** | 2/3  | —         | ✅ M-DATA-03 · Batch05       |
| C4  | Provider catalog    | R2     | 2/3  | **是**    | **M-PASS-01**                |
| J5  | web_search live API | R3     | 1/3  | —         | post-Round4 ADR              |

### 2.D Sync（D1–D4）

| ID  | 模块                 | 当前 | 批/3 | PASS 阻塞 | 活票 / 归属            |
| --- | -------------------- | ---- | ---- | --------- | ---------------------- |
| D1  | Sync orchestration   | R4   | 3/3  | —         | ✅ M-DATA-03 · Batch05 |
| D2  | Task idempotency     | R1   | 0/3  | —         | Batch6                 |
| D3  | Scheduler / cron     | R0   | 0/3  | —         | Round4 壳 / Batch6     |
| D4  | Source health writer | R2   | 1/3  | —         | Batch6                 |

### 2.E Ops（E1–E7, F0）

| ID  | 模块                | 当前 | 批/3    | PASS 阻塞 | 活票 / 归属            |
| --- | ------------------- | ---- | ------- | --------- | ---------------------- |
| E1  | `qmd data` CLI      | R4   | 2/3     | —         | ✅ M-DATA-03 · Batch05 |
| E2  | DB inspect          | R4   | 2/3     | —         | ✅ M-DATA-03 · Batch05 |
| E3  | Production gate     | R2   | 1/3     | —         | Batch05                |
| E4  | Live / staged pilot | R4   | 2/3     | **是**    | **M-PASS-01** 收敛     |
| E5  | Sandbox clean write | R5   | **3/3** | —         | 批次已满               |
| E6  | Backup / recovery   | R1   | 1/3     | —         | Batch05                |
| E7  | Ops report CLI      | R0   | 0/3     | —         | B04_04 / ADR           |
| F0  | Data health engine  | R4   | 2/3     | —         | ✅ M-DATA-03 · Batch05 |

### 2.F Modeling（G1–G6, K1–K3）

| ID  | 模块                  | 当前 | 批/3 | PASS 阻塞 | 活票 / 归属                 |
| --- | --------------------- | ---- | ---- | --------- | --------------------------- |
| G1  | Layer1 axes           | R3   | 2/3  | **是**    | **M-G1-03**                 |
| G2  | Layer2 sensors        | R3   | 2/3  | **是**    | **M-G2-FULL**               |
| G3  | Layer3 chains         | R3   | 1/3  | —         | Round4 初（非 PASS 硬门禁） |
| G4  | Layer4 markets        | R3   | 2/3  | **是**    | **M-G4-FULL**               |
| G5  | Layer5 evidence       | R2   | 2/3  | **是**    | **M-G5-FULL**               |
| G6  | Manual review         | R3   | 1/3  | **是**    | **M-PASS-01**               |
| K1  | Model input whitelist | R3   | 2/3  | **是**    | **M-G1-03**（G1 子范围）    |
| K2  | Layer1 五轴 spec      | R3   | 1/3  | **是**    | **M-G1-03**（G1 子范围）    |
| K3  | Layer3 registries     | R3   | 1/3  | —         | G3 子范围                   |

### 2.G–I 其余模块

| ID          | 模块              | 当前  | 批/3  | 闭合轮次 | PASS 阻塞 |
| ----------- | ----------------- | ----- | ----- | -------- | --------- |
| H1          | ETL / Parquet     | R1    | 1/3   | Batch6   | —         |
| I1          | FastAPI           | R1    | 0/3   | R4       | Round4 后 |
| I8          | Diagnostics API   | R1    | 0/3   | R4       | I1 子集   |
| I2          | Agent             | R0    | 0/3   | R4       | Round4 后 |
| I3          | Frontend          | R1    | 1/3   | R4       | Round4 后 |
| I4          | Notifications     | R0    | 0/3   | R4       | Round4 后 |
| I5–I7       | Backtest / review | R0–R1 | 0–1/3 | R4       | Round4 后 |
| J2          | No-action guard   | R1    | 1/3   | R4       | Round4 后 |
| J7          | Privacy           | R1    | 0/3   | R4       | Round4 后 |
| J1,J3,J4,J6 | Governance        | R1–R3 | 0–2/3 | R5       | —         |

---

## 3. 模块闭环队列 v2（生效 @ 2026-07-02）

> **取代：** 旧 Wave 1–5 水平切分（见 **§3L**）作为**新开工**路由；历史 CLOSED 票只读作证据。  
> **用户裁决：** §0.1 — PASS = 真代码+真跑 + 硬门禁 **R4**；**R5/R6** 走三批 Batch 2/3（§1.2 · §6.1.3）。

### 3.0 队列总览

```text
~~M-DATA-03~~  CLOSED @ 2026-07-04
  ↓
M-G1-03     五轴完整落地（真链，非 seed）  ← 下一入口
  ↓
M-G2-FULL ∥ M-G4-FULL ∥ M-G5-FULL
  ↓
M-PASS-01   PASS_ROUND4_REAL_DATA_READY
  ↓
Round4 B04-*
```

| 票 ID         | 类型    | Module                | Rating 目标                      | 设计权威                                        |
| ------------- | ------- | --------------------- | -------------------------------- | ----------------------------------------------- |
| **M-DATA-03** | complex | C3,D1,E1,E2,F0,B2     | **CLOSED** — **R4** @ 2026-07-04 | ADR-034 · §3.1 一行摘要                         |
| **M-G1-03**   | complex | G1,K1,K2              | G1 **R3→R4**                     | `specs/layer1_axes/` · `layer1_axes.md`         |
| **M-G2-FULL** | complex | G2                    | G2 **R3→R4**（九组）             | `docs/modules/layer2_cross_asset_sensor.md` §2  |
| **M-G4-FULL** | complex | G4                    | G4 **R3→R4**（各 market_id）     | `docs/modules/layer4_market_structure.md` §2    |
| **M-G5-FULL** | complex | G5, A3                | G5 **R2→R4**                     | `docs/modules/layer5_security_evidence.md` §2–3 |
| **M-PASS-01** | complex | C1,C4,B3,G6,E4 + 门禁 | 清单绿 + MCR 无 R3 冒充 R4       | 本文 §6.1.1                                     |

> **R5/R6：** 上表活票目标均为 **R4 能力落地**；运维收尾与商业发布 → **Batch05**（§1.2 · §6.1.3）。

### 3.1 M-DATA-03 — **CLOSED** @ 2026-07-04

**R4** 关账：Tier A 11/11 隔离库 live · Tier B 10/10 验收结论 · B2/C3/D1/E1/E2/F0→R4 — **ADR-034** · archived `.trellis/tasks/archive/2026-07/m-data-03-tier-a-live/` · 活卡 `M_DATA_03_TIER_A_LIVE/`（只读）。

### 3.2 M-G1-03 — 五轴完整落地（**下一入口** · **单票双阶段**）

| 项          | 内容                                                                                                                                                                      |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **结构**    | **票 B**：仍 `M-G1-03`；**Phase 1**（sync 解耦 + orchestrator 完整落地）→ **P1-GATE** → **Phase 2**（62 指标真链）                                                        |
| **Phase 1** | `data_sync_orchestrator.md` 完整（含 **FullLoad**、§13.6 调度、§13.7 CLI）+ `module_boundary_matrix.md` + 指标绑定 registry；详见 `M_G1_03_LAYER1_FULL/EXECUTION_PLAN.md` |
| **Phase 2** | **62 个 `indicator_id`** 各走 sync→clean→特征→解读 同库真链（spec README §指标全链路要求）                                                                                |
| **SSOT**    | `docs/implementation_tasks/M_G1_03_LAYER1_FULL/EXECUTION_PLAN.md`（唯一执行计划）                                                                                         |
| **依赖**    | M-DATA-03 **R4** clean 输入 ✅                                                                                                                                            |
| **禁止**    | P1 未过关做 62 指标；seed；每轴 1 代表；API/前端（Round4）                                                                                                                |

### 3.3 M-G2-FULL — Layer2 九组资产

| 项       | 内容                                                                    |
| -------- | ----------------------------------------------------------------------- |
| **范围** | `layer2_cross_asset_sensor.md` §2 **九组** sensors 全覆盖               |
| **流程** | **一张** complex 票 · 内部分 S01…S09（可并行 worktree）· **一次** A1–A8 |
| **AC**   | 每组至少一条真市况输入 → `axis_observation` 可断言                      |
| **禁止** | DCP-07 式「单 VIX 传感器」单独关 G2 模块                                |

### 3.4 M-G4-FULL — Layer4 多市场

| 项       | 内容                                                                     |
| -------- | ------------------------------------------------------------------------ |
| **范围** | `layer4_market_structure.md` §2 各 `market_id`（CN_A / US_EQ / HK_EQ …） |
| **流程** | 同 G2：单票多切片 · 统一 Audit                                           |
| **依赖** | M-DATA-03 对应行情源；Wave 1 US 日历（**已 CLOSED**）                    |

### 3.5 M-G5-FULL — Layer5 证据链

| 项       | 内容                                                                                        |
| -------- | ------------------------------------------------------------------------------------------- |
| **范围** | `layer5_security_evidence.md` 第一阶段资产域（股/ETF/期货/期权等）+ `evidence_chain` 可追溯 |
| **流程** | **一张** complex 票 · 多资产类切片 · **一次** A1–A8                                         |
| **AC**   | 至少一条 **真网 sync→clean→Layer5** 全链（非仅 mootdx 单样本）；provenance 字段可断言       |
| **禁止** | DCP-10 式「单 mootdx bar」单独关 G5 模块                                                    |

### 3.6 M-PASS-01 — Round3→Round4 门禁

见 **§6.1.1**。末位执行；**不得**在 §3 各活票未诚实关账前宣称 PASS。内含原 Wave5 `R3H-05A..E` + `R3H-05-GATE`（**单票**内切片，非独立完整流程）。

### 3.7 v2 `/to-issues` 索引（随 Plan 冻结增补）

| 票        | 建议路径                                                                                                      |
| --------- | ------------------------------------------------------------------------------------------------------------- |
| M-DATA-03 | `docs/implementation_tasks/M_DATA_03_TIER_A_LIVE/M_DATA_03_TO_ISSUES_INDEX.md`                                |
| M-G1-03   | `docs/implementation_tasks/M_G1_03_LAYER1_FULL/EXECUTION_PLAN.md` §7（索引指针 `M_G1_03_TO_ISSUES_INDEX.md`） |
| M-G2-FULL | `.../M_G2_FULL_TO_ISSUES_INDEX.md`                                                                            |
| M-G4-FULL | `.../M_G4_FULL_TO_ISSUES_INDEX.md`                                                                            |
| M-G5-FULL | `.../M_G5_FULL_TO_ISSUES_INDEX.md`                                                                            |
| M-PASS-01 | `.../M_PASS_01_TO_ISSUES_INDEX.md`                                                                            |

---

## 3L. 历史 Wave / DCP（只读 · 禁止新开工）

> **2026-07-02 起：** 不得再按 Wave 1–5 或 R3-DCP-07/08/10 **单独** freeze 完整流程任务。  
> CLOSED 证据与旧 `/to-issues` 索引 → **附录 C** · `R3_DCP_TO_ISSUES_INDEX.md`（只读）。

---

## 4. Round4 产品波次（I 组）

> **前置：** **M-PASS-01** / §6.1.1 `PASS_ROUND4_REAL_DATA_READY`  
> **SSOT：** `BATCH_04_TASK_CARD_MANIFEST.md`  
> **边界：** 只读 API / Agent / 前端 / 通知 / 回测；**禁止**新 fetch/sync 引擎、全历史灌库、五轴引擎重写。

### 4.1 执行顺序

```text
B04_01 API + I8 diagnostics — 最先
  ↓
并行：B04_02 Agent · B04_03 Frontend · B04_04 Notification · B04_05 Backtest
  ↓
可选：D3 调度壳 — cron 只调用 **M-DATA-03** 已验收的 CLI（无新 fetch）
```

### 4.2 产品模块三批模板（对齐 §1.2）

| 模块  | Batch 1 →**R4**      | Batch 2 →**R5**          | Batch 3 →**R6** | 卡     |
| ----- | -------------------- | ------------------------ | --------------- | ------ |
| I1+I8 | 一个只读 endpoint    | diagnostics + pagination | auth 负测       | B04_01 |
| I2+J2 | 一个 allowed tool    | forbidden 拒绝           | no-action       | B04_02 |
| I3    | API-bound 单页       | 第二面板                 | contract        | B04_03 |
| I4    | event→log            | dedup/cooldown           | evidence refs   | B04_04 |
| I5–I7 | loader+runner+report | metrics+API              | 再现性硬化      | B04_05 |

### 4.3 Round4 明确排除

- 新 Incremental/Backfill **引擎**（消费 Round3 入口）
- FullLoad、RevisionAudit 产品、任务级幂等 store
- **五轴指标引擎**（**M-G1-03** 闭合后 Round4 只读暴露）
- `web_search` 真 API（J5）

---

## 5. Round5 / Batch6 还债包

### 5.1 DataSync 五类 job 与写库索引

#### 5.1.1 五类 Sync Job

| Job           | PASS 前（活票）                        | Batch6 / Round5       |
| ------------- | -------------------------------------- | --------------------- |
| Incremental   | **✅ Tier A R4** @ M-DATA-03 CLOSED    | 24 源 cron 自动化余量 |
| Backfill      | 历史 DCP-09 有界分片 ✅；扩面归 Batch6 | broad backfill / CLI  |
| FullLoad      | **不要求 PASS**                        | D2-P1-1               |
| RevisionAudit | 不要求 PASS                            | D2-P1-1 产品          |
| Reconcile     | Round2 部分                            | D2-P2-2               |

#### 5.1.2 配套能力

| 能力                          | 闭合阶段                      |
| ----------------------------- | ----------------------------- |
| watermark 读库算窗            | ✅ M-DATA-03 · 历史 DCP-01/02 |
| 写库 upsert_by_pk             | **R3H-06 CLOSED**             |
| 任务级 idempotency_key        | Batch6                        |
| `quant_monitor.sync` 生产 CLI | Batch6；Round4 D3 只包装      |
| Sync production smoke         | Batch05                       |

#### 5.1.3 写库两道闸

```text
staging → [B2 质检] → [B3 冲突] → B1 upsert_by_pk → clean
```

任务级重复下载 ≠ 写库幂等（前者 Batch6）。

**下游 SSOT：** `data_sync_orchestrator.md` · `write_manager.md` · `idempotency_retry_dlq_policy.md` · legacy 路线图 §5.0.6。

### 5.2 Batch6 默认项（不挡 PASS / Round4）

| 模块 | 内容                            |
| ---- | ------------------------------- |
| D2   | idempotency_key store           |
| D3   | FullLoad + cron 矩阵            |
| D4   | source_health 生产 migration    |
| H1   | sync→Parquet                    |
| A6   | spec migrator                   |
| G3   | Layer3 全真网（若 Round4 未做） |

### 5.3 Round5 Batch05（三批法则 **Batch 3** · 全体 **R6** 收敛）

| 卡     | 目标                                           |
| ------ | ---------------------------------------------- |
| B05-01 | Security CI                                    |
| B05-02 | Integration / resource smoke（**商业真生产**） |
| B05-03 | Release manifest — 全体 **R6** 或 limitation   |

Round5 **不补功能**。

---

## 6. 门禁

### 6.1 Round3 → Round4（PASS 清单 · v2 @ 2026-07-02）

> **名称：** `PASS_ROUND4_REAL_DATA_READY`（不变）  
> **过关：** **M-PASS-01** 执行 + 下列清单在 **真实代码 + 真实运行** 下逐项绿（§0.1.2）。**PASS = 硬门禁 R4 · ≠ R6**（§6.1.3 · §1.2 Batch 3）。  
> **历史 Wave CLOSED** 仅作索引，**不自动满足**本清单。

#### 6.1.1 硬门禁（须真绿）

| #   | 项                  | 验收标准                                                                                                        |
| --- | ------------------- | --------------------------------------------------------------------------------------------------------------- |
| 1   | **M-DATA-03** ✅    | **CLOSED** @ 2026-07-04 — Tier A R4 · ADR-034（§3.1 一行摘要）                                                  |
| 2   | **M-G1-03**         | G1/K1/K2 **MCR Rating ≥ R4**；**62 指标身份** 各走 sync→clean→指标→解读 同库真链（spec README §指标全链路要求） |
| 3   | **M-G2-FULL**       | G2 **MCR Rating ≥ R4** — 九组资产按设计权威落地                                                                 |
| 4   | **M-G4-FULL**       | G4 **MCR Rating ≥ R4** — 各 `market_id` 按设计落地                                                              |
| 5   | **M-G5-FULL**       | G5 **MCR Rating ≥ R4** — Layer5 设计 scope 落地                                                                 |
| 6   | **G12 五轴 pytest** | `tests/test_layer1_*` 等 **GREEN**（不得仅 L1 子集冒充 PASS）                                                   |
| 7   | **MCR 诚实**        | 硬门禁模块无「R3 冒充 R4」或「任务 CLOSED 但 Rating 仍 R3」                                                     |
| 8   | **主库闸**          | `MAIN-DB-GATE` 绿；验收全程 **不污染主库**                                                                      |
| 9   | **M-PASS-01 审计**  | registry / Layer 绑定终态（含原 R3H-05A..E + GATE，**单票内**）                                                 |

#### 6.1.2 历史已 CLOSED（证据索引 · 非充分条件）

1. Batch 3V + R3H-06 + R3H-01～04 ✅
2. Wave 1–2：R3H-07、R3H-10、R3H-08A–D ✅
3. Wave 3：R3-DCP-01..03 ✅
4. Wave 4 子集里程碑：R3-DCP-05/06/09 ✅；DCP-07/08/10 代码 merge **≠** 模块成品 → **M-G2/G4/G5-FULL** 承接
5. `web_search` 真 API → **DEFERRED post-Round4**（单 ADR）

#### 6.1.3 不要求（不变）

R6、Batch6 全集、24 源全自动 cron、G3 链全真网。

#### 6.1.4 旧版清单（§6.1 legacy · 2026-06-30 前）

<details>
<summary>点击展开 — 仅供对照历史文档，不再作开工 SSOT</summary>

1. Batch 3V + R3H-06 + R3H-01～04 — **CLOSED** ✅
2. Wave 1–2 — **CLOSED** ✅
3. Wave 3 — **CLOSED** ✅
4. Wave 4：DCP-05/06 ✅；DCP-07..10 OPEN
5. G12 L1 子集 @ `6c6cdd73`
6. R3H-05-GATE
7. 24 源 env-gated Tier
8. MAIN-DB-GATE + Layer smoke

</details>

### 6.2 Round4 → Round5

- I1–I7、J2 各达 **Batch 1 → R4**（B04 验收；运维/发布走 Batch 2/3 · Batch05）
- 只读 / no-action / 无 free SQL / 无写接口

### 6.3 Round5 → Release

- B05 三连过；manifest 无隐藏 blocker

---

## 7. 历史批次 → 活票承接（只读索引）

| 旧轨                  | 状态     | 主要模块      | **v2 活票承接**（完整成品）                  |
| --------------------- | -------- | ------------- | -------------------------------------------- |
| Batch 3V · R3H-01～06 | CLOSED   | 底座          | 证据 only                                    |
| R3H-07 · R3H-10       | CLOSED   | G4 日历, C2   | **M-G4-FULL** 余量                           |
| R3H-08A–D             | CLOSED   | C3 24源 live  | **M-DATA-03** 真网验收余量                   |
| R3-DCP-01..03         | CLOSED   | D1,E1,E2      | **M-DATA-03**                                |
| R3-DCP-05/06/09       | CLOSED   | D1,G1,D1      | Milestone only → **M-DATA-03** / **M-G1-03** |
| R3-DCP-07/08/10       | CLOSED\* | G2,G4,G5 子集 | **M-G2/G4/G5-FULL**（\*子集≠模块关账）       |
| R3H-05 + GATE         | —        | 全表审计      | **M-PASS-01**（单票，禁止独立 Wave5 流程）   |
| B04-\*                | 未开工   | I 组          | Round4（PASS 后）                            |
| B05-\* · Batch6       | 未开工   | 发布/还债     | §5.2–5.3                                     |

---

## 8. 全局施工顺序（模块视角）

```text
历史底座（Round0–2 · 3V · R3H-01～06 · Wave 1–4 子集 CLOSED）
  ↓
§3 模块闭环队列 v2（M-DATA-03 → M-G1 → M-G2∥G4∥G5 → M-PASS-01）
  ↓
Round4 Batch04 — 只读产品（API 先）
  ↓
Batch6 还债（不挡 Round4 开工）
  ↓
Round5 Batch05 — R6 / limitation 发布裁判
```

| 阶段   | 业务目标                | 硬门禁          |
| ------ | ----------------------- | --------------- |
| Round3 | 数据真网 + 建模完整落地 | PASS **§6.1.1** |
| Round4 | 用户可见只读产品        | B04 验收        |
| Round5 | 安全 / 集成 / manifest  | 无隐藏 blocker  |

---

## 9. 执行者开工检查清单（v2）

1. 是否 **§3 活票**之一？同一模块完整成品 **不得**另开第二张 complex 票（§1.7–§1.8）。
2. 任务卡是否标明 **Module ID** + **Rating 跃迁**（或写明 milestone-only）？
3. Plan 冻结前 **`/to-issues`** 垂直切片（§3.7）？票内多切片 **统一** A1–A8。
4. 并行是否撞 registry 三件套或同节点文件锁？
5. 是否 **complex Trellis**（§3 活票）？**禁止**用 debt-lite 承接 G/C/D/E 模块完整成品。
6. 改符号前 `impact()`；提交前 `detect_changes()`；触达 backend/docs/specs 跑 `loop_maintain.py`。
7. 数据/建模验收是否在 **隔离库**（§0.1.5）？Round4 是否只读、是否绕过 DataSourceService？
8. PASS 前是否核对 **§6.1.1** 全表 + MCR 无假完成？
9. Sync job / 写库闸是否先读 **§5.1**？

---

## 10. 发布终态

Round5 后仅两类状态：`R6_FULL_PRODUCTION_STABLE` 或 `ADR_DISABLED_OUT_OF_SCOPE` / release limitation。

不允许：「差不多」「registry 有了就算完成」「Round5 顺手补管道」「三轴先 PASS 五轴后补」「DCP-07 关 G2」「再开 Wave 5 独立完整流程」。

---

## 附录 A. 历史叙事索引

Wave 平铺细节、3F-R/3G 任务卡路径、原 §5.0.6 完整表格 → **`docs/archive/planning/PROJECT_IMPLEMENTATION_ROADMAP.legacy-20260629.md`**。

## 附录 B. 与 `MODULE_COMPLETION_RATING.md` 对齐

- 51 ID 与 `authority_graph.yaml` v2 `rating_index` **无冲突**。
- **活票 / PASS** 以本文 **§3 · §6.1.1 · §1.8** 为准；MCR **活票 / 归属** 列须指向 §3 活票，**禁止**再写 R3H-08 / DCP-07 等为下一完整流程。

## 附录 C. 历史 CLOSED 证据（只读 · 非开工 SSOT）

| 旧 ID         | 状态   | 模块子集     | Milestone 要点           | v2 承接                 |
| ------------- | ------ | ------------ | ------------------------ | ----------------------- |
| R3H-07/10     | CLOSED | G4 日历, C2  | US 日历 · bypass 守卫    | M-G4-FULL / M-PASS-01   |
| R3H-08A–D     | CLOSED | C3,A3,B\*,G6 | 24 源 env-gated live     | M-DATA-03 真网余量      |
| R3-DCP-01..03 | CLOSED | D1,E1,E2,F0  | baostock+fred 增量试点   | M-DATA-03               |
| R3-DCP-05     | CLOSED | D1,E1,C3     | 11 源 replay incremental | M-DATA-03 **真网**      |
| R3-DCP-06     | CLOSED | G1,K2        | L1 五轴 P0 clean read    | **M-G1-03 完整**        |
| R3-DCP-07     | CLOSED | G2           | **仅** L2-VIX            | **M-G2-FULL 九组**      |
| R3-DCP-08     | CLOSED | G4           | **仅** US_EQ             | **M-G4-FULL 全 market** |
| R3-DCP-09     | CLOSED | D1           | 有界 backfill + CI       | Batch6 扩面             |
| R3-DCP-10     | CLOSED | G5,A3        | **仅** mootdx provenance | **M-G5-FULL**           |
| R3H-05A..E    | —      | 全表         | 审计切片                 | **M-PASS-01 单票内**    |

**旧 `/to-issues` 索引：** `R3_DCP_TO_ISSUES_INDEX.md` · `WAVE0_BATCH3V_TO_ISSUES_INDEX.md`（格式范例仍有效；**路由**须改 §3.7 活票路径）。

**隔离验收脚本（仍可复跑）：** `scripts/wave3_isolated_production_acceptance.py` · `scripts/wave3_live_production_acceptance.py` · 报告 `docs/quality/acceptance/WAVE3_PRODUCTION_ACCEPTANCE_REPORT.md`。
