# QMD 项目实施总路线图（模块轨道版）

> **版本：** 2026-07-02（规划 SSOT 收敛；`R3H_PASS_EXECUTION_PLAN.md` **已归档**）  
> **定位：** 根目录**唯一活规划** — 以 **51 个 Module ID** 为行；完成度以 **`MODULE_COMPLETION_RATING.md` Pass E** 为准（代码+测试，非任务卡自述）。  
> **通俗解释：** 本文件回答「下一步做什么业务、关哪个模块、怎样算做完」；**新任务卡才是工单**；历史 Wave 叙事见 legacy / 归档。  
> **上一版备份：** `docs/archive/planning/PROJECT_IMPLEMENTATION_ROADMAP.legacy-20260629.md` · `R3H_PASS_EXECUTION_PLAN.archived-20260702.md`  
> **进度复核：** `git log` @ 2026-07-02 — 历史 Wave 1–4 代码已 merge；**模块 Rating 多数未达任务卡声称的 R4** — 见 `MODULE_COMPLETION_RATING.md` §0。  
> **重构：** §3 **模块闭环队列 v2** 已按用户 grill-gate @ 2026-07-02 生效；§3L 为历史 Wave 编排（只读）。

### 当前下一入口（v2 · 用户确认 @ 2026-07-02）

| 优先级 | 票 ID         | 业务一句话                                                     | 开工前                                                               |
| ------ | ------------- | -------------------------------------------------------------- | -------------------------------------------------------------------- |
| **P0** | **M-DATA-03** | 11 主源真网增量→写库→巡检（隔离库）                            | §0.3.3：先 grill-me 确认拿不到 KEY/付费资格的源 → ADR                |
| **P0** | **M-G1-03**   | 五轴按设计完整落地（真链，非仅 seed）                          | 依赖 M-DATA-03 至少宏观/行情 clean 输入就绪                          |
| **P1** | **M-G2-FULL** | Layer2 九组资产按 `layer2_cross_asset_sensor.md` 完整落地      | 单 **Plan→Execute** 流程内多 worktree/串行切片；**统一** A1–A8 Audit |
| **P1** | **M-G4-FULL** | Layer4 各 `market_id` 按 `layer4_market_structure.md` 完整落地 | 同上；可与 G2/G5 **并行**（不同 graph 节点）                         |
| **P1** | **M-G5-FULL** | Layer5 证据链按 `layer5_security_evidence.md` 完整落地         | 同上                                                                 |
| **P0** | **M-PASS-01** | `PASS_ROUND4_REAL_DATA_READY`（真实代码+真跑，见 §6.1）        | **末位**：前述阻塞模块 MCR Rating 诚实 + 清单全绿                    |

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

### 0.1 用户裁决（有效）

| 议题                   | 裁决                                                         |
| ---------------------- | ------------------------------------------------------------ |
| **PASS 判定**          | **真实代码 + 真实运行**（§0.3.1）；非任务 CLOSED / 文档勾选  |
| **模块 scope**         | 设计权威 **完整落地**；单流程多切片 + 统一 Audit（§0.3.2）   |
| **11 源真网**          | M-DATA-03 硬要求；无资格 → ADR+占位（§0.3.3）                |
| Round4 入口            | **`PASS_ROUND4_REAL_DATA_READY`** = **M-PASS-01**（§6.1 v2） |
| `web_search` 真 API    | **post-Round4** 独立模块（`R3H-WEB-SEARCH` / J5）            |
| 真网 live              | env-gated → Tier A/B/C（归档 §2.1；新票写入模块闭环 AC）     |
| 后端优先               | **Round3 闭合数据面 + 五轴 + 增量** 后再开 Round4 产品       |
| **Layer1 五轴（G12）** | **PASS 前必须 pytest 全绿**（非 Round4+ 可选项）             |
| R3-DCP 增量试点源      | **历史**；新票 **M-DATA-03** 覆盖 11 源真网（§0.3.3）        |

### 0.3 用户 grill-gate @ 2026-07-02（规划约束 · 有效）

#### 0.3.1 PASS 门禁 `PASS_ROUND4_REAL_DATA_READY`

| 项                 | 裁决                                                                                          |
| ------------------ | --------------------------------------------------------------------------------------------- |
| **名称**           | 可继续叫 `PASS_ROUND4_REAL_DATA_READY`                                                        |
| **过关定义**       | **M-PASS-01 清单逐项真绿** + **`MODULE_COMPLETION_RATING.md` 阻塞模块无「R3 假完成」**        |
| **判定依据**       | **真实代码 + 真实运行**（隔离库/受控 env）；**禁止**任务卡 CLOSED、文档勾选、tmp DB seed 冒充 |
| **与旧 Wave 关系** | Wave 1–4 CLOSED **不自动算 PASS**；仅作历史证据索引                                           |

#### 0.3.2 模块落地范围（G2 / G4 / 全体建模）

| 项       | 裁决                                                                                                                                                   |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **范围** | **设计权威完整落地** — `docs/modules/`、`specs/contracts/`、`specs/layer*` 等规定的**成品形态**即为交付标准，**禁止**「只做 P0 子集却宣称模块 CLOSED」 |
| **G2**   | `layer2_cross_asset_sensor.md` §2 **九组资产**全覆盖（非「多加一个 VIX」）                                                                             |
| **G4**   | `layer4_market_structure.md` §2 各 `market_id`（含 CN_A / US_EQ / HK_EQ …）按设计落地                                                                  |
| **G5**   | `layer5_security_evidence.md` §2–3 第一阶段资产域 + 证据链完整落地（非「单 mootdx 样本」）                                                             |
| **拆法** | **允许**在一个 **Plan→Execute 完整流程**内：多执行者 **并行 worktree** 或 **串行分批**，全部做完后 **统一 A1–A8 Audit**                                |
| **禁止** | 把**同一模块的完整成品**拆成多张独立「完整流程任务」（每张都 Plan/Audit/Repair）— 过去 Wave/DCP 教训                                                   |
| **允许** | 单流程内分阶段；阶段间可插 **单次对抗性审计 agent**；**不得**每阶段各走一遍完整 8 维 Audit                                                             |

#### 0.3.3 数据管道 M-DATA-03（11 源 Tier A）

| 项                 | 裁决                                                                                                   |
| ------------------ | ------------------------------------------------------------------------------------------------------ |
| **PASS 硬要求**    | **11/11** 源须 **逻辑完整实现**；能真网的必须 **真连网 → 增量 sync → 写 clean → 巡检通过**             |
| **验收环境**       | **隔离库**（`.audit-sandbox` / 专用 `DATA_ROOT`）；**禁止污染主库**、不可逆破坏                        |
| **拿不到资格的源** | **开工前** grill-me 与用户确认（API KEY、付费通道、地域限制等）→ **ADR** 登记「当前无法真网」          |
| **ADR 源仍须**     | replay/逻辑测绿 + **配置占位**（env/secret 槽位）；用户日后填入 KEY/开通资格后 **无需再开发** 即可真跑 |
| **不得**           | 无 ADR 的无限延后；无占位的「以后接真网」                                                              |

**Tier A 十一源（开工前资格核对用）：** `fred` `us_treasury` `sec_edgar` `cftc_cot` `bis` `world_bank` `alpha_vantage` `deribit` `baostock` `cninfo` `mootdx` — 资格矩阵在 **M-DATA-03 Plan 冻结前**产出 `research/tier-a-live-eligibility.md`。

#### 0.3.4 源资格确认（用户 @ 2026-07-02）

| 源组                                                            | 结论                                             |
| --------------------------------------------------------------- | ------------------------------------------------ |
| `fred`                                                          | **能** — `FRED_API_KEY` 可提供 → **须真网**      |
| `alpha_vantage`                                                 | **能** — API Key 可提供 → **须真网**             |
| `deribit`                                                       | **能** — **须真网**                              |
| `baostock` / `cninfo` / `mootdx`                                | **均能** — **须真网**                            |
| `us_treasury` / `sec_edgar` / `cftc_cot` / `bis` / `world_bank` | **同意**公开 API 默认无须 KEY → **五源均须真网** |

**ADR 例外（当前）：** **无** — M-DATA-03 按 **11/11 真网** 验收；Plan 冻结时写入 `research/tier-a-live-eligibility.md` 固化本表。

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

完整定义：`MODULE_COMPLETION_RATING.md` §1。

| 级别  | 规划含义                            |
| ----- | ----------------------------------- |
| R0–R1 | 未开工 / 壳子                       |
| R2    | 首批最小竖切（每模块 Batch 1 底线） |
| R3    | staged fixture 闭合                 |
| R4    | sandbox 真网 / 彩排                 |
| R5    | 有界生产入口                        |
| R6    | 完整生产稳定 — **Round5 发布确认**  |

### 1.2 三批法则

1. **Batch 1：** ≥ `R2_MINIMAL_VERTICAL_SLICE`
2. **Batch 2：** 主承诺范围（通常 R4–R5）
3. **Batch 3：** 硬化 / 回归 / 发布 gate

`批/3` 见 §2。**I6、K2、K3** 为父模块子范围，不单独占三批。

### 1.3 R6 两层判断

| 层             | 含义                      |
| -------------- | ------------------------- |
| 主能力完成轮次 | 模块核心在哪一轮落地      |
| R6 发布确认    | **Batch05** 统一 manifest |

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

| 类型                | 适用                                                                 |
| ------------------- | -------------------------------------------------------------------- |
| **complex Trellis** | **§3 活票**（M-DATA-03、M-G\*-FULL、M-PASS-01）、Round4 B04          |
| **debt-lite**       | Batch6 卫生、已 CLOSED 票的小修补（**不得**承接模块完整成品）        |
| Plan 冻结前         | 活票须 `/to-issues` 垂直切片（§3.6）；**一模块成品 = 一 complex 票** |

### 1.6 并行与合并

- **worktree：** 一 agent 一 worktree；按 `authority_graph.yaml` **节点**划分。
- **registry 三件套**（`source_registry.yaml`、`source_capabilities.yaml`、`tests/test_catalog.yaml`）— **主会话排队 merge**。
- **schema DDL：** R3H-06 已封板；新 DDL → Batch6/B05 门禁。
- **改符号前** `impact()`；**提交前** `detect_changes()`。

### 1.7 完整流程任务规则（用户裁决 @ 2026-07-02）

通俗说：**一个大模块要做满设计书，开「一张大单」；单子里可以多人、多阶段干活，最后统一验收。**

| 允许                                                           | 禁止                                                            |
| -------------------------------------------------------------- | --------------------------------------------------------------- |
| 一个 Trellis **complex** 票覆盖 **G2 全模块** 或 **G4 全模块** | 把 G2 拆成 DCP-07、DCP-07b、DCP-07c… 每张独立 Plan/Audit/Repair |
| 票内 `/to-issues` 竖切：S01…Sn 并行或串行                      | 每竖切单独 freeze 一张「完整流程任务」                          |
| 全部 Execute 完后 **一次** A1–A8                               | 每完成一个资产/市场就 full Audit                                |
| 阶段间 **可选** 单次对抗性审计（check agent）                  | 用阶段外置把「成品范围」削成 P0 子集且不写 ADR                  |

**关账时：** `MODULE_COMPLETION_RATING.md` 对应模块 **Rating 必须跃迁**（或 ADR 收窄设计权威并同步改文档）— 与 §0.3.1 一致。

### 1.8 模块 → 活票归属（一模块一完整流程）

> **规则：** 同一 **Module ID 的完整成品**只归属 **一张** §3 complex 票；票内可多批次（S01…Sn），**禁止**再开第二张完整流程票。  
> **子范围**（K2⊂G1、I8⊂I1）随父模块票闭合，不单独 freeze Plan。

| 活票           | 主模块（Rating 跃迁）      | 同票闭合的关联模块             | 设计权威                                               |
| -------------- | -------------------------- | ------------------------------ | ------------------------------------------------------ |
| **M-DATA-03**  | C3, D1, E1 → R4 真网 scope | E2, F0, B2 post-write          | Tier A §0.3.3 · archived §2.1                          |
| **M-G1-03**    | G1 → R4                    | K1, K2, A5                     | `layer1_global_regime_panel.md` · `specs/layer1_axes/` |
| **M-G2-FULL**  | G2 → R4                    | —                              | `layer2_cross_asset_sensor.md` §2 九组                 |
| **M-G4-FULL**  | G4 → R4                    | —                              | `layer4_market_structure.md` §2 各 market              |
| **M-G5-FULL**  | G5 → R4                    | A3 provenance 绑真源           | `layer5_security_evidence.md` §2–3                     |
| **M-PASS-01**  | 门禁清单绿                 | C1, C4, B3, G6, A3/A4 终态审计 | 本文 §6.1.1                                            |
| **Batch6**     | D2, D3, D4, H1, A6         | 不挡 PASS                      | §5.2                                                   |
| **Round4 B04** | I1–I8, J2                  | PASS 后                        | `BATCH_04_TASK_CARD_MANIFEST.md`                       |
| **Batch05**    | 全体 R6 确认               | A1, A2, A7, E3, E6, J3         | §5.3                                                   |

**历史 CLOSED**（R3H-07/10、R3H-08、R3-DCP-\*）：只读证据，**不得**作为新开工路由；未达设计成品 scope 的竖切 → 记入 MCR **Milestone** 列，由上表活票承接余量。

---

## 2. 模块轨道总表（51 Module ID）

> 当前 Rx / 批/3 来自 `MODULE_COMPLETION_RATING.md` §3 @ Pass E。  
> **活票列：** 模块完整成品的 **唯一** 完整流程归属（§1.8）；历史 R3H/DCP ID 仅作 Milestone 证据。

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

| ID  | 模块                | 当前  | 批/3 | PASS 阻塞 | 活票 / 归属      |
| --- | ------------------- | ----- | ---- | --------- | ---------------- |
| B1  | WriteManager + gate | R4    | 2/3  | —         | Batch05 manifest |
| B2  | Data quality        | R3    | 2/3  | **是**    | **M-DATA-03**    |
| B3  | Source conflict     | R2→R3 | 2/3  | **是**    | **M-PASS-01**    |

### 2.C Data sources（C1–C4, J5）

| ID  | 模块                | 当前 | 批/3 | PASS 阻塞 | 活票 / 归属            |
| --- | ------------------- | ---- | ---- | --------- | ---------------------- |
| C1  | Registry / route    | R3   | 2/3  | **是**    | **M-PASS-01**          |
| C2  | DataSourceService   | R4   | 2/3  | **是**    | 历史 CLOSED；PASS 审计 |
| C3  | Adapters / ports    | R3   | 2/3  | **是**    | **M-DATA-03**          |
| C4  | Provider catalog    | R2   | 2/3  | **是**    | **M-PASS-01**          |
| J5  | web_search live API | R3   | 1/3  | —         | post-Round4 ADR        |

### 2.D Sync（D1–D4）

| ID  | 模块                 | 当前 | 批/3 | PASS 阻塞 | 活票 / 归属            |
| --- | -------------------- | ---- | ---- | --------- | ---------------------- |
| D1  | Sync orchestration   | R4   | 3/3  | **是**    | **M-DATA-03** 真网验收 |
| D2  | Task idempotency     | R1   | 0/3  | —         | Batch6                 |
| D3  | Scheduler / cron     | R0   | 0/3  | —         | Round4 壳 / Batch6     |
| D4  | Source health writer | R2   | 1/3  | —         | Batch6                 |

### 2.E Ops（E1–E7, F0）

| ID  | 模块                | 当前 | 批/3    | PASS 阻塞 | 活票 / 归属        |
| --- | ------------------- | ---- | ------- | --------- | ------------------ |
| E1  | `qmd data` CLI      | R4   | 2/3     | **是**    | **M-DATA-03**      |
| E2  | DB inspect          | R4   | 2/3     | **是**    | **M-DATA-03**      |
| E3  | Production gate     | R2   | 1/3     | —         | Batch05            |
| E4  | Live / staged pilot | R4   | 2/3     | **是**    | **M-PASS-01** 收敛 |
| E5  | Sandbox clean write | R5   | **3/3** | —         | 批次已满           |
| E6  | Backup / recovery   | R1   | 1/3     | —         | Batch05            |
| E7  | Ops report CLI      | R0   | 0/3     | —         | B04_04 / ADR       |
| F0  | Data health engine  | R4   | 2/3     | **是**    | **M-DATA-03**      |

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
> **用户裁决：** §0.3 — PASS = 真代码+真跑；模块 = 设计权威完整落地；11 源 = 真网硬要求（ADR 例外）。

### 3.0 队列总览

```text
M-DATA-03   11 源真网增量（隔离库验收）     ← 开工前 grill-me 源资格 → ADR
  ↓
M-G1-03     五轴完整落地（真链，非 seed）
  ↓
M-G2-FULL ∥ M-G4-FULL ∥ M-G5-FULL   各一张 complex 票；票内多切片；统一 A1–A8
  ↓
M-PASS-01   PASS_ROUND4_REAL_DATA_READY（§6.1 v2）
  ↓
Round4 B04-*  只读产品
```

| 票 ID         | 类型    | Module                | Rating 目标                      | 设计权威                                                   |
| ------------- | ------- | --------------------- | -------------------------------- | ---------------------------------------------------------- |
| **M-DATA-03** | complex | C3,D1,E1,E2,F0,B2     | C3/E1/D1 **R3→R4**（真网 scope） | `R3H_PASS_EXECUTION_PLAN.archived-20260702.md` §2.1 Tier A |
| **M-G1-03**   | complex | G1,K1,K2              | G1 **R3→R4**                     | `specs/layer1_axes/` · `layer1_axes.md`                    |
| **M-G2-FULL** | complex | G2                    | G2 **R3→R4**（九组）             | `docs/modules/layer2_cross_asset_sensor.md` §2             |
| **M-G4-FULL** | complex | G4                    | G4 **R3→R4**（各 market_id）     | `docs/modules/layer4_market_structure.md` §2               |
| **M-G5-FULL** | complex | G5, A3                | G5 **R2→R4**                     | `docs/modules/layer5_security_evidence.md` §2–3            |
| **M-PASS-01** | complex | C1,C4,B3,G6,E4 + 门禁 | 清单绿 + MCR 无假完成            | 本文 §6.1.1                                                |

### 3.1 M-DATA-03 — 11 源 Tier A 真网

| 项           | 内容                                                                    |
| ------------ | ----------------------------------------------------------------------- |
| **业务目标** | 每源：**真连网 → incremental sync → clean 写库 → inspect/health 绿**    |
| **开工前**   | grill-me → `research/tier-a-live-eligibility.md`（能真跑 / ADR 暂不能） |
| **ADR 源**   | 逻辑+占位+replay 测绿；**不得**缺实现                                   |
| **验收**     | 隔离 `DATA_ROOT` / `.audit-sandbox`；**零主库污染**                     |
| **切片建议** | S0 资格矩阵 · S1–S11 按源并行 worktree · Sn 统一 merge + 隔离验收脚本   |
| **禁止**     | 全 mock e2e 冒充 CLOSED；「3 真跑 + 8 replay SLA」作 PASS 主路径        |

**十一源：** `fred` `us_treasury` `sec_edgar` `cftc_cot` `bis` `world_bank` `alpha_vantage` `deribit` `baostock` `cninfo` `mootdx`

### 3.1.1 M-DATA-03 — Tier B live 外部边界（AC-7 增补 · 2026-07-04）

| 项                        | 内容                                                                                                      |
| ------------------------- | --------------------------------------------------------------------------------------------------------- |
| **证据 SSOT**             | `.trellis/tasks/m-data-03-tier-a-live/research/archive/non-plan/execute/tier-b-network-path2-evidence.md` |
| **stooq（路径二已接受）** | Stooq CSV 反爬 HTML；`FAIL_EXTERNAL`+ADR-034 · 台账 `M-DATA-03-STOOQ-EXTERNAL-001`                        |
| **CN 三源（条件路径二）** | `push2his.eastmoney.com` 间歇不可达；非 Clash 7897 误路由主因 · 台账 `M-DATA-03-TIERB-CN-HIST-001`        |
| **承接**                  | 关闭 stooq：替代源 / nightly 权威 PASS / 废弃 binding；关闭 CN：路径一复测或 baostock hist 链             |
| **禁止**                  | 用 exit 0 掩盖 `disposition=fail`；宣称 Tier B「10/10 真网 PASS」而 CN 三源未关账                         |

| 项          | 内容                                                                               |
| ----------- | ---------------------------------------------------------------------------------- |
| **范围**    | 五轴按 `restructured_axes_v1_1` **完整**指标与输入契约（非 L1 子集冒充全模块）     |
| **AC 底线** | 每轴：`sync→clean→指标引擎→pytest` **同库真链**（或 ADR 源 replay + 其余真网输入） |
| **依赖**    | M-DATA-03 宏观/行情 clean 就绪                                                     |
| **禁止**    | tmp DB seed 单独支撑 R4                                                            |

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

| 票        | 建议路径                                                                       |
| --------- | ------------------------------------------------------------------------------ |
| M-DATA-03 | `docs/implementation_tasks/M_DATA_03_TIER_A_LIVE/M_DATA_03_TO_ISSUES_INDEX.md` |
| M-G1-03   | `.../M_G1_03_TO_ISSUES_INDEX.md`                                               |
| M-G2-FULL | `.../M_G2_FULL_TO_ISSUES_INDEX.md`                                             |
| M-G4-FULL | `.../M_G4_FULL_TO_ISSUES_INDEX.md`                                             |
| M-G5-FULL | `.../M_G5_FULL_TO_ISSUES_INDEX.md`                                             |
| M-PASS-01 | `.../M_PASS_01_TO_ISSUES_INDEX.md`                                             |

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

### 4.2 产品模块三批模板

| 模块  | Batch 1 →R2          | Batch 2                  | Batch 3       | 卡     |
| ----- | -------------------- | ------------------------ | ------------- | ------ |
| I1+I8 | 一个只读 endpoint    | diagnostics + pagination | auth 负测     | B04_01 |
| I2+J2 | 一个 allowed tool    | forbidden 拒绝           | no-action     | B04_02 |
| I3    | API-bound 单页       | 第二面板                 | contract      | B04_03 |
| I4    | event→log            | dedup/cooldown           | evidence refs | B04_04 |
| I5–I7 | loader+runner+report | metrics+API              | 再现性硬化    | B04_05 |

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
| Incremental   | **M-DATA-03** 11 源真网（隔离库）      | 24 源 cron 自动化余量 |
| Backfill      | 历史 DCP-09 有界分片 ✅；扩面归 Batch6 | broad backfill / CLI  |
| FullLoad      | **不要求 PASS**                        | D2-P1-1               |
| RevisionAudit | 不要求 PASS                            | D2-P1-1 产品          |
| Reconcile     | Round2 部分                            | D2-P2-2               |

#### 5.1.2 配套能力

| 能力                          | 闭合阶段                                  |
| ----------------------------- | ----------------------------------------- |
| watermark 读库算窗            | 历史 DCP-01/02 ✅；**M-DATA-03** 真网验收 |
| 写库 upsert_by_pk             | **R3H-06 CLOSED**                         |
| 任务级 idempotency_key        | Batch6                                    |
| `quant_monitor.sync` 生产 CLI | Batch6；Round4 D3 只包装                  |
| Sync production smoke         | Batch05                                   |

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

### 5.3 Round5 Batch05

| 卡     | 目标                                         |
| ------ | -------------------------------------------- |
| B05-01 | Security CI                                  |
| B05-02 | Integration / resource smoke                 |
| B05-03 | Release manifest — 全体 **R6** 或 limitation |

Round5 **不补功能**。

---

## 6. 门禁

### 6.1 Round3 → Round4（PASS 清单 · v2 @ 2026-07-02）

> **名称：** `PASS_ROUND4_REAL_DATA_READY`（不变）  
> **过关：** **M-PASS-01** 执行 + 下列清单在 **真实代码 + 真实运行** 下逐项绿（§0.3.1）。  
> **历史 Wave CLOSED** 仅作索引，**不自动满足**本清单。

#### 6.1.1 硬门禁（须真绿）

| #   | 项                  | 验收标准                                                                                                 |
| --- | ------------------- | -------------------------------------------------------------------------------------------------------- |
| 1   | **M-DATA-03**       | 11 源逻辑完整；非 ADR 源：**隔离库**真网 incremental→clean→inspect 绿；ADR 源：占位+replay 绿且 ADR 登记 |
| 2   | **M-G1-03**         | 五轴完整 scope；每轴真链或 ADR 允许的受控 replay+真网输入组合                                            |
| 3   | **M-G2-FULL**       | 九组资产按设计权威落地；G2 **R3→R4**（MCR）                                                              |
| 4   | **M-G4-FULL**       | 各 `market_id` 按设计落地；G4 **R3→R4**（MCR）                                                           |
| 5   | **M-G5-FULL**       | Layer5 设计 scope 落地；G5 **R2→R4**（MCR）                                                              |
| 6   | **G12 五轴 pytest** | `tests/test_layer1_*` 等 **GREEN**（不得仅 L1 子集冒充 PASS）                                            |
| 7   | **MCR 诚实**        | 阻塞模块无「任务 CLOSED 但 Rating 仍 R3 假完成」                                                         |
| 8   | **主库闸**          | `MAIN-DB-GATE` 绿；验收全程 **不污染主库**                                                               |
| 9   | **M-PASS-01 审计**  | registry / Layer 绑定终态（含原 R3H-05A..E + GATE，**单票内**）                                          |

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

- I1–I7、J2 各 ≥ R2 真实竖切（B04 验收）
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
7. 数据/建模验收是否在 **隔离库**（§0.3.3）？Round4 是否只读、是否绕过 DataSourceService？
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
- **活票 / PASS** 以本文 **§3 · §6.1.1 · §1.8** 为准；MCR **Required next movement** 列须指向 §3 活票，**禁止**再写 R3H-08 / DCP-07 等为下一完整流程。

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
