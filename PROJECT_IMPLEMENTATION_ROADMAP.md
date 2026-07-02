# QMD 项目实施总路线图（模块轨道版）

> **版本：** 2026-06-29（模块轨道重写；用户裁决：五轴 PASS 前全绿）  
> **定位：** 根目录总施工图 — 以 **51 个 Module ID**（`MODULE_COMPLETION_RATING.md` §3）为行，串联评级、波次、任务卡与门禁。  
> **通俗解释：** 本文件回答「每个模块现在几级、还差几批、在哪一轮闭合」；**任务卡才是工单**，`PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md` 只是覆盖地图。  
> **上一版备份：** `PROJECT_IMPLEMENTATION_ROADMAP.legacy-20260629.md`（Wave 平铺叙事、§5.0.6 等仍可查）  
> **进度复核：** `git log` @ 2026-07-02 — Wave 1–3 **CLOSED**；Wave 4 **`R3-DCP-05` CLOSED** @ `c2258363` · **`R3-DCP-06` CLOSED** @ `6c6cdd73`；**`R3-DCP-07..10` OPEN**；活轨见 §3。

### 当前下一入口

| 优先级 | 任务                       | 模块  | 说明                                       |
| ------ | -------------------------- | ----- | ------------------------------------------ |
| P0     | **Wave 4** `R3-DCP-07..10` | G2–G5 | cross-asset / 市场结构 / backfill / 证据链 |

索引：`docs/implementation_tasks/.../R3_DCP_TO_ISSUES_INDEX.md` §3

---

## 0. 定位与 SSOT 指针

| 用途                             | 文件                                      |
| -------------------------------- | ----------------------------------------- |
| 完成度运营快照                   | `MODULE_COMPLETION_RATING.md` §3          |
| 机器索引                         | `specs/context/authority_graph.yaml` v2   |
| 项目地图                         | `docs/generated/project_map.generated.md` |
| Round3 PASS 协调（Tier / 24 源） | `R3H_PASS_EXECUTION_PLAN.md`              |
| Round4 产品范围                  | `BATCH_04_TASK_CARD_MANIFEST.md`          |
| DataSync 五类 job / 写库         | 本文 **§5.1**                             |
| Wave 0 `/to-issues` 范例         | `WAVE0_BATCH3V_TO_ISSUES_INDEX.md`        |
| Round3 活轨 `/to-issues` 索引    | 本文 **§3.6**（随波次开工增补）           |

### 0.1 用户裁决（有效）

| 议题                   | 裁决                                                      |
| ---------------------- | --------------------------------------------------------- |
| Round4 入口            | **`PASS_ROUND4_REAL_DATA_READY`**（非 WARN 主路径）       |
| `web_search` 真 API    | **post-Round4** 独立模块（`R3H-WEB-SEARCH` / J5）         |
| 真网 live              | env-gated → Tier A/B/C（`R3H_PASS_EXECUTION_PLAN.md` §2） |
| 后端优先               | **Round3 闭合数据面 + 五轴 + 增量** 后再开 Round4 产品    |
| **Layer1 五轴（G12）** | **PASS 前必须 pytest 全绿**（非 Round4+ 可选项）          |
| R3-DCP 增量试点源      | **baostock + fred**（见 §3.3 白话说明）                   |

### 0.2 已核实 canonical 入口

| 范围          | 文件夹 / 文件                                                         |
| ------------- | --------------------------------------------------------------------- |
| Batch 3V      | `BATCH_3V_VERIFIED_AUDIT_CLEANUP/` — **CLOSED**                       |
| Batch 3H PASS | `BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/` + `R3H_PASS_EXECUTION_PLAN.md` |
| Round4        | `BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/`                             |
| Round5        | `BATCH_05_VERIFIED_AUDIT_SECURITY_RELEASE/`                           |

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

### 1.5 Trellis / debt-lite 路由

| 类型                | 适用                                                                             |
| ------------------- | -------------------------------------------------------------------------------- |
| **complex Trellis** | R3H-08 四子轨、R3H-05-GATE、Round4 B04                                           |
| **debt-lite**       | R3-DCP 小项、Batch6 卫生                                                         |
| Plan 冻结前         | 须 `/to-issues` 垂直切片（`.trellis` + `WAVE0_BATCH3V_TO_ISSUES_INDEX.md` 格式） |

### 1.6 并行与合并

- **worktree：** 一 agent 一 worktree；按 `authority_graph.yaml` **节点**划分。
- **registry 三件套**（`source_registry.yaml`、`source_capabilities.yaml`、`tests/test_catalog.yaml`）— **主会话排队 merge**。
- **schema DDL：** R3H-06 已封板；新 DDL → Batch6/B05 门禁。
- **改符号前** `impact()`；**提交前** `detect_changes()`。

---

## 2. 模块轨道总表（51 Module ID）

> 当前 Rx / 批/3 来自 `MODULE_COMPLETION_RATING.md` §3 @ 2026-06-29。  
> **PASS 阻塞列：** 进 Round4 前须达标的模块（含 **G1+K2 五轴全绿**）。

### 2.A Platform（A1–A7）

| ID  | 模块               | 当前 | 批/3 | 闭合轮次 | PASS 阻塞 | 下一移动 / 任务                |
| --- | ------------------ | ---- | ---- | -------- | --------- | ------------------------------ |
| A1  | Project scaffold   | R3   | 2/3  | R5       | —         | Batch05                        |
| A2  | DuckDB schema      | R3   | 2/3  | R5       | —         | R3H-06 ✅；Batch05 drift       |
| A3  | Storage / evidence | R3   | 2/3  | R3→R5    | **是**    | R3H-08：每 READY 源 fetch 证据 |
| A4  | ResourceGuard      | R3   | 2/3  | R3→R5    | **是**    | R3H-08 全路径 cap              |
| A5  | Snapshot lineage   | R3   | 2/3  | R4→R5    | —         | G12 快照绑定时                 |
| A6  | Spec migrator      | R1   | 0/3  | Batch6   | —         | Batch6 或 ADR                  |
| A7  | Platform matrix    | R2   | 1/3  | R5       | —         | Batch05                        |

### 2.B Write path（B1–B3）

| ID  | 模块                | 当前  | 批/3 | PASS 阻塞 | 下一移动                   |
| --- | ------------------- | ----- | ---- | --------- | -------------------------- |
| B1  | WriteManager + gate | R4    | 2/3  | —         | R3H-06 ✅；R3H-08 主库路径 |
| B2  | Data quality        | R3    | 2/3  | **是**    | R3H-08 按源 profile        |
| B3  | Source conflict     | R2→R3 | 2/3  | **是**    | R3H-08 live outcome        |

### 2.C Data sources（C1–C4, J5）

| ID  | 模块                | 当前 | 批/3 | PASS 阻塞 | 下一移动                  |
| --- | ------------------- | ---- | ---- | --------- | ------------------------- |
| C1  | Registry / route    | R3   | 2/3  | **是**    | R3H-05：25 行终态         |
| C2  | DataSourceService   | R3   | 2/3  | **是**    | **R3H-10**                |
| C3  | Adapters / ports    | R3   | 2/3  | **是**    | R3H-01～04 ✅；**R3H-08** |
| C4  | Provider catalog    | R2   | 2/3  | **是**    | R3H-05 posture            |
| J5  | web_search live API | R3   | 1/3  | —         | **DEFERRED post-R4**      |

### 2.D Sync（D1–D4）

| ID  | 模块                 | 当前 | 批/3 | PASS 阻塞 | 下一移动                      |
| --- | -------------------- | ---- | ---- | --------- | ----------------------------- |
| D1  | Sync orchestration   | R3   | 2/3  | **是**    | R3-DCP watermark；R3H-08 demo |
| D2  | Task idempotency     | R1   | 0/3  | —         | Batch6（不挡 PASS）           |
| D3  | Scheduler / cron     | R0   | 0/3  | —         | Round4 壳调 CLI；矩阵 Batch6  |
| D4  | Source health writer | R2   | 1/3  | —         | Batch6 migration              |

### 2.E Ops（E1–E7, F0）

| ID  | 模块                | 当前 | 批/3    | PASS 阻塞 | 下一移动           |
| --- | ------------------- | ---- | ------- | --------- | ------------------ |
| E1  | `qmd data` CLI      | R3   | 2/3     | **是**    | R3-DCP incremental |
| E2  | DB inspect          | R3   | 2/3     | **是**    | R3-DCP 写后抽检    |
| E3  | Production gate     | R2   | 1/3     | —         | Batch05            |
| E4  | Live / staged pilot | R4   | 2/3     | **是**    | R3H-10 收敛        |
| E5  | Sandbox clean write | R5   | **3/3** | —         | **批次已满**       |
| E6  | Backup / recovery   | R1   | 1/3     | —         | Batch05            |
| E7  | Ops report CLI      | R0   | 0/3     | —         | B04_04 或 ADR      |
| F0  | Data health engine  | R3   | 2/3     | **是**    | R3H-08 admission   |

### 2.F Modeling（G1–G6, K1–K3）

| ID  | 模块                  | 当前 | 批/3 | PASS 阻塞 | 下一移动                                     |
| --- | --------------------- | ---- | ---- | --------- | -------------------------------------------- |
| G1  | Layer1 axes           | R3   | 2/3  | **是**    | **R3-DCP-06 CLOSED** @ `6c6cdd73`（L1 子集） |
| G2  | Layer2 sensors        | R3   | 2/3  | **是**    | R3-DCP-07 最小竖切                           |
| G3  | Layer3 chains         | R3   | 1/3  | —         | Round4 初（非 PASS 硬门禁）                  |
| G4  | Layer4 markets        | R3   | 1/3  | **是**    | **R3H-07** + R3-DCP-08                       |
| G5  | Layer5 evidence       | R2   | 2/3  | **是**    | R3-DCP-10 + R3H-05                           |
| G6  | Manual review         | R2   | 1/3  | **是**    | R3H-08D                                      |
| K1  | Model input whitelist | R3   | 1/3  | **是**    | 五轴消费行对齐                               |
| K2  | Layer1 五轴 spec      | R3   | 1/3  | **是**    | **G1 子范围；五轴各至少 1 测**               |
| K3  | Layer3 registries     | R3   | 1/3  | —         | G3 子范围                                    |

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

## 3. Round3 闭合波次（模块轨 + `/to-issues`）

> **格式：** 对齐 `WAVE0_BATCH3V_TO_ISSUES_INDEX.md` — 每波 **Wave 目标 / 并行 / merge / Done / 下游**；任务用 **tracer-bullet 垂直切片**，非按层横切。  
> **策略：** 先后端（数据 + 建模 + 审计），Round4 只做只读产品。

### 3.0 总览

```text
[✅] 历史：Round0–2 · 3F-R · 3G · 3V · R3H-01～04 · R3H-06
  ↓
Wave 1  地基（R3H-07 ∥ R3H-10）                    2 任务 · 并行
  ↓
Wave 2  24 源真网产品化（R3H-08A/B/C/D）             4 任务 · 并行
  ↓
Wave 3  增量试点（baostock + fred + 写后抽检）       3 任务 · 部分并行
  ↓
Wave 4  后端加厚（五轴全绿 + 增量扩展 + L2/L4 最小）  6 任务 · 部分并行
  ↓
Wave 5  PASS 审计（R3H-05A..E ∥ → GATE 串行）        6 任务
  ↓
Round4  B04-01 先 · 产品只读
```

### 3.1 白话：baostock + fred「试点」≠ 只做俩源

| 层次                   | 做什么                                     | 哪些源                                   | 哪一波                        |
| ---------------------- | ------------------------------------------ | ---------------------------------------- | ----------------------------- |
| **真网 live 产品化**   | 真网拉 → 质检 → 写对库（A/B/C）            | **24 个 READY 源**（web_search 仅 mock） | **Wave 2**                    |
| **日常增量 watermark** | 读库最后一天 → 只拉新增 → CLI 可重复跑     | 先 **baostock + fred**，再扩 Tier A      | **Wave 3 → 4**                |
| **五轴指标 G12**       | 五轴都从 **真 clean** 算出指标 + pytest 绿 | 依赖 Wave 2–4 数据                       | **Wave 4**（**PASS 硬门禁**） |

### 3.2 Wave 1 — 地基

| 项            | 内容                                                                                     |
| ------------- | ---------------------------------------------------------------------------------------- |
| **Wave 目标** | US 交易日历 + DataSourceService 唯一入口                                                 |
| **并行**      | R3H-07 与 R3H-10 **可同时 Execute**（不同 graph 节点：`layer4_markets` / `datasources`） |
| **串行**      | 阻塞 Wave 2 全轨开工（尤其 08B 日历语义）                                                |
| **Wave Done** | 两轨 pytest 绿 + audit 零遗留                                                            |
| **下游**      | Wave 2 R3H-08                                                                            |

| #   | 规划 ID    | 模块   | Trellis | 交付要点                                         |
| --- | ---------- | ------ | ------- | ------------------------------------------------ |
| 1a  | **R3H-07** | G4, C3 | complex | US TradingCalendar L2；关闭 CAL-US               |
| 1b  | **R3H-10** | C2, E4 | complex | API/Sync/Agent **不得 bypass** DataSourceService |

**`/to-issues` 切片（规划）：** 每轨 Plan 冻结前产出 `research/to-issues-slices.md`（S0 BOOT → Sn MERGE）。

### 3.3 Wave 2 — 24 源真网产品化（PASS 核心）

| 项            | 内容                                                                         |
| ------------- | ---------------------------------------------------------------------------- |
| **Wave 目标** | 凡 READY 源：env-gated live → 正确 Tier（`R3H_PASS_EXECUTION_PLAN.md` §2.1） |
| **并行**      | 08A / 08B / 08C / 08D **四 worktree**                                        |
| **依赖**      | Wave 1 Done；**R3H-06** schema ✅                                            |
| **禁止**      | `--live-wire` 运维脚本冒充产品路径；pilot 数据 silent merge 主库             |
| **Wave Done** | 四轨 CLOSED + 全量 pytest 绿                                                 |
| **下游**      | Wave 3、4                                                                    |

| #   | 规划 ID     | Tier | 源组（摘要）              | 模块           |
| --- | ----------- | ---- | ------------------------- | -------------- |
| 2a  | **R3H-08A** | A    | baostock, cninfo, mootdx… | C3, A3, B1, E1 |
| 2b  | **R3H-08B** | B    | yahoo, akshare, stooq…    | C3, B2, B3     |
| 2c  | **R3H-08C** | A    | fred + 宏观五源           | C3, A3         |
| 2d  | **R3H-08D** | C    | kalshi, polymarket        | C3, G6         |

**唯一延后：** `web_search` **真 API** → post-Round4（mock/replay 本波闭合）。

### 3.4 Wave 3 — 增量试点（R3-DCP）

| 项            | 内容                                                                  |
| ------------- | --------------------------------------------------------------------- |
| **Wave 目标** | **baostock + fred** 走通「读库水位 → 只拉新增 → 写库 → 抽检」产品路径 |
| **并行**      | DCP-01（baostock）∥ DCP-02（fred）；DCP-03 依赖 01/02 至少一轨        |
| **协议**      | **debt-lite**（`.trellis` Phase 8D slice plan）                       |
| **Wave Done** | `qmd data`/sync 可重复跑试点增量；E2 inspect smoke 绿                 |
| **下游**      | Wave 4 扩展 + 五轴                                                    |

| #   | 规划 ID       | 模块   | 交付                                                                           |
| --- | ------------- | ------ | ------------------------------------------------------------------------------ |
| 3a  | **R3-DCP-01** | D1, E1 | baostock：watermark + incremental CLI · **✅ CLOSED** @ `5dc71c0b`             |
| 3b  | **R3-DCP-02** | D1, E1 | fred：宏观序列增量 · **✅ CLOSED** @ `5d8d7b0f` · P7 `bb3ce99c`                |
| 3c  | **R3-DCP-03** | E2, F0 | 写后 row count / max(trade_date) / health profile · **✅ CLOSED** @ `eff49343` |

### 3.5 Wave 4 — 后端加厚（含五轴 PASS 硬门禁）

| 项            | 内容                                                                                        |
| ------------- | ------------------------------------------------------------------------------------------- |
| **Wave 目标** | Tier A 增量扩展 + **G12 五轴 pytest 全绿** + L2/L4 最小竖切 + G5 绑真源                     |
| **用户裁决**  | **五轴必须在 R3H-05-GATE 之前全绿** — 不得 WARN 收窄为「三轴先 PASS」                       |
| **并行**      | DCP-05 按源并行；DCP-06 五轴可五 worktree（同 `layer1_axes` 需文件锁协调）；DCP-07 ∥ DCP-08 |
| **依赖**      | Wave 2 数据入库；Wave 3 试点逻辑可复制                                                      |
| **Wave Done** | 见 §3.5.1 五轴验收清单 **全部 [x]**                                                         |
| **下游**      | Wave 5 审计                                                                                 |

#### 3.5.1 G12 五轴 PASS 验收清单（硬门禁）

五轴 ID 以 `specs/layer1_axes/restructured_axes_v1_1/` 为准（K2）。每轴至少：

- [x] 从 **Tier A clean**（非 staged fixture）读取输入
- [x] 指标引擎产出可断言快照/序列
- [x] 专属 pytest **GREEN**（`tests/test_layer1_*` 或本轴新增测）
- [x] ResourceGuard / 有界窗口遵守 `resource_limits.yaml`
- [x] `MODULE_COMPLETION_RATING` **G1: R3→R4**，**K2** 行与轴一一对应

| #   | 规划 ID       | 模块   | 交付                                                                                            |
| --- | ------------- | ------ | ----------------------------------------------------------------------------------------------- |
| 4a  | **R3-DCP-05** | D1, E1 | 增量 watermark 扩展至 **全部 Tier A 主源** · **✅ CLOSED** @ `c2258363`                         |
| 4b  | **R3-DCP-06** | G1, K2 | **五轴全绿（G12）** — PASS 阻塞项 · **✅ CLOSED** @ `6c6cdd73`（L1 子集；L3–L5 → DCP-07/08/10） |
| 4c  | **R3-DCP-07** | G2     | 一条 cross-asset 传感器绑真市况源                                                               |
| 4d  | **R3-DCP-08** | G4     | 市场结构 + Wave 1 US 日历                                                                       |
| 4e  | **R3-DCP-09** | D1     | 有界 backfill（cap 分片；**非**无上限 FullLoad）· **✅ CLOSED** @ `feature/wave4-r3-dcp-09-backfill-ci` |
| 4f  | **R3-DCP-10** | G5, A3 | source_fetch_id / content_hash / schema_hash 绑真源                                             |

**仍归 Batch6（不挡 PASS）：** D2 任务级幂等、无 cap FullLoad、24 源 production cron 矩阵、H1 Parquet、D4 migration。

#### 3.5.2 Live 生产验收承接（2026-07-01 · Wave 4+ 路由）

> **证据：** `scripts/wave3_live_production_acceptance.py` · `待修复清单.md` §8  
> **须先闭环（非 Wave 4 规划）：** ~~§2.5 `LIVE-PILOT-DB-001` · `LIVE-BAOSTOCK-SYNC-SILENT-001`~~ **已关 2026-07-01**（见 `待修复清单.md` §1）

| 规划 ID / 活卡                 | 承接的 live 验收缺口                                                                                                                         | 台账 ID                                                                        |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| **R3-DCP-05**                  | ~~baostock 真网 + Tier A 全源增量~~ **✅ CLOSED** @ `c2258363`；东财口径 **部分**（registry notes，REQ2 仍 §4）                              | `ACC-BAOSTOCK-NO-LIVE` ✅ · `ACC-EASTMONEY-TAXONOMY-001` 部分                  |
| **R3-DCP-05**（ponytail 承接） | mootdx dry-run `selected_source_id` 与生产路由不一致；runtime `validation_only` 提升待 registry reconcile                                    | `ACC-MOOTDX-DRYRUN-ROUTE-001` · 关账条件见 `待修复清单.md` §4                  |
| **R3-DCP-06**                  | **L1 五轴 clean replay 子集**（G12 硬门禁；非 L1–L5 full `production_live` 全链）                                                            | `ACC-LAYER-E2E-LIVE-001`（L1 ✅ · L3–L5 → DCP-07/08/10 + R3H-05-GATE）         |
| **R3-DCP-09**                  | 有界 backfill；**连网验收 CI**：`--run-network` batch275 子集 + `wave3_live_production_acceptance.py` nightly；`WAVE3-ACC-OPT-01` quick 分层 · **✅ CLOSED** | `ACC-LIVE-NETWORK-CI-001` ✅ · `ACC-LIVE-ACCEPT-NIGHTLY-001` ✅ · `WAVE3-ACC-OPT-01` ✅ · `LIVE-NETWORK-GATE-001` ✅ |
| **R3-DCP-09**（Repair 阶段外置） | akshare eastmoney 本地审计网络 / ponytail dedup / quick perf gate / registry 硬化                                                          | `ACC-LIVE-NETWORK-AKSHARE-ENV` open · ledger 阶段外置行                                                                              |
| **R3-DCP-10**                  | G5 绑真源（content_hash / schema_hash）— 与 live 全链同一 Wave 4 波次                                                                        | `ACC-LAYER-E2E-LIVE-001`（G5 子集）                                            |
| **Wave 5 `R3H-05-GATE`**       | Layer 绑定终态审计；`PASS_ROUND4_REAL_DATA_READY`                                                                                            | `ACC-LAYER-E2E-LIVE-001`（审计门）                                             |
| **Batch 6 `R3F-LIN-01/02`**    | L3/L4 lineage · L2 VR binding 全量持久化                                                                                                     | `ADV-R3X-LINEAGE-001` · `R3Y-LINEAGE-VR-001`                                   |
| **Batch 6 `R3F-SH-06`**        | FRED **live primary** 关账（≠ DCP-02 增量 live）                                                                                             | `B2.5-O-05` §3 硬约束                                                          |
| **政策（非修复）**             | akshare `macro_supplementary` pilot 第 3 路 `DISABLED_SOURCE`                                                                                | `AKSHARE-MACRO-PILOT-POLICY` §3                                                |

### 3.6 Wave 5 — PASS 审计

| 项            | 内容                                                |
| ------------- | --------------------------------------------------- |
| **Wave 目标** | `PASS_ROUND4_REAL_DATA_READY`                       |
| **并行**      | R3H-05A..E 五片 **可并行**                          |
| **串行**      | **R3H-05-GATE 必须最后**                            |
| **Wave Done** | §6.1 清单全满足 + `round3h_*_audit.md` 25 行 CLOSED |

| #     | 规划 ID         | 范围                                           |
| ----- | --------------- | ---------------------------------------------- |
| 5a–5e | **R3H-05A..E**  | registry / Layer / adopt / orphan / limitation |
| 5f    | **R3H-05-GATE** | 合并裁决 → **PASS**                            |

### 3.7 Round3 状态看板（2026-06-30）

| 波次                                              | 状态                                                 |
| ------------------------------------------------- | ---------------------------------------------------- |
| 历史 + Wave 0（3V）+ R3H-01～04 + R3H-06          | ✅ CLOSED                                            |
| Wave 1（R3H-07, R3H-10）                          | ✅ CLOSED @ 2026-06-29                               |
| Wave 2（R3H-08A–D）                               | ✅ CLOSED @ 2026-06-29                               |
| Wave 3（R3-DCP-01..03）                           | ✅ **CLOSED** @ 2026-06-30（`eff49343` 收尾 DCP-03） |
| Wave 4（**R3-DCP-05/06** ✅ · **R3-DCP-07..10**） | 🔴 OPEN（DCP-05 @ `c2258363` · DCP-06 @ `6c6cdd73`） |
| Wave 5（R3H-05 + GATE）                           | 🔴 OPEN                                              |

### 3.7.1 Wave 3 隔离生产验收（2026-07-01）

> **报告 SSOT：** `WAVE3_PRODUCTION_ACCEPTANCE_REPORT.md`（隔离库 · 主库零污染）  
> **脚本：** `scripts/wave3_isolated_production_acceptance.py`  
> **证据：** 可重跑 `uv run python scripts/wave3_isolated_production_acceptance.py` → `.audit-sandbox/wave3-acceptance-<run_id>/`（gitignore）；参考跑 11/11 PASS  
> **承接（可选优化）：** `WAVE3-ACC-OPT-01` — 验收 quick profile · 见 `待修复清单.md` §4  
> **Live 连网验收（2026-07-01）：** `scripts/wave3_live_production_acceptance.py`（入库 @ `93b2c82`）· 承接路由见 §3.5.2 · `待修复清单.md` §8  
> **Wave 4 前须先闭环：** `待修复清单.md` §2.5 — **已清空 2026-07-01**（`LIVE-PILOT-DB-001` · `LIVE-BAOSTOCK-SYNC-SILENT-001` 见 §1）
> **结论摘要：** Wave 1–3 **隔离/机制验收通过**；Wave 4 prep **§1 共 30 项**经 pytest 复验已关；**§2.5 阻断项已关**；**G12 五轴 L1 子集** @ `6c6cdd73` ✅；**正式 PASS** 仍待 Wave 4 `R3-DCP-07..10` + Wave 5 `R3H-05-GATE`。

### 3.7.2 台账复验摘要（2026-07-01 @ `93b2c82`）

| 类别       | 数量 | 核实方式                                     | 结论                                                                     |
| ---------- | ---- | -------------------------------------------- | ------------------------------------------------------------------------ |
| §1 已关闭  | 30   | 定向 pytest + 代码路径                       | **维持已关**（含 `LIVE-PILOT-DB-001` · `LIVE-BAOSTOCK-SYNC-SILENT-001`） |
| §2.5 阻断  | 0    | `--run-network` + baostock CliFailure 测     | **已关 2026-07-01**                                                      |
| §4 Wave 4+ | 6    | 读码：无 `--quick`/nightly/真网 product sync | **仍 OPEN** — 合法延后至 DCP-05/06/09                                    |
| §3 硬约束  | 5    | 政策/registry                                | **刻意 DEFERRED** — 不得误关                                             |

---

### 3.8 `/to-issues` 索引文件（随开工增补）

| 波次     | 建议路径（主会话创建）                                               |
| -------- | -------------------------------------------------------------------- |
| Wave 1   | `docs/implementation_tasks/.../WAVE1_R3H07_R3H10_TO_ISSUES_INDEX.md` |
| Wave 2   | `.../WAVE2_R3H08_TO_ISSUES_INDEX.md`                                 |
| Wave 3–4 | `.../R3_DCP_TO_ISSUES_INDEX.md` ✅ @ 2026-06-30                      |
| Wave 5   | `R3H_05_LAYER_BINDING_AND_PRODUCTION_ENTRY_AUDIT.md` + slices        |

每 INDEX 须含：Wave 门控表、What to build、Acceptance criteria、Blocked by、Vertical slices 表、Issue 骨架（复制 GitHub）。

---

## 4. Round4 产品波次（I 组）

> **前置：** §6.1 `PASS_ROUND4_REAL_DATA_READY`（**含五轴全绿**）  
> **SSOT：** `BATCH_04_TASK_CARD_MANIFEST.md`  
> **边界：** 只读 API / Agent / 前端 / 通知 / 回测；**禁止**新 fetch/sync 引擎、全历史灌库、五轴引擎重写。

### 4.1 执行顺序

```text
B04_01 API + I8 diagnostics — 最先
  ↓
并行：B04_02 Agent · B04_03 Frontend · B04_04 Notification · B04_05 Backtest
  ↓
可选：D3 调度壳 — cron 只调用 §3 已闭合 CLI（无新 fetch）
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
- **五轴指标引擎**（Round3 已闭合；Round4 只读暴露）
- `web_search` 真 API（J5）

---

## 5. Round5 / Batch6 还债包

### 5.1 DataSync 五类 job 与写库索引

#### 5.1.1 五类 Sync Job

| Job           | Round3 要求                                       | Batch6 / Round5           |
| ------------- | ------------------------------------------------- | ------------------------- |
| Incremental   | Wave 3 试点 + Wave 4 扩 Tier A；**PASS 须可演示** | 全源 watermark 自动化余量 |
| Backfill      | Wave 4 有界分片（DCP-09）                         | broad backfill / CLI      |
| FullLoad      | **不要求 PASS**                                   | D2-P1-1                   |
| RevisionAudit | 不要求 PASS                                       | D2-P1-1 产品              |
| Reconcile     | Round2 部分                                       | D2-P2-2                   |

#### 5.1.2 配套能力

| 能力                          | 闭合阶段                 |
| ----------------------------- | ------------------------ |
| watermark 读库算窗            | Wave 3–4（试点→Tier A）  |
| 写库 upsert_by_pk             | **R3H-06 CLOSED**        |
| 任务级 idempotency_key        | Batch6                   |
| `quant_monitor.sync` 生产 CLI | Batch6；Round4 D3 只包装 |
| Sync production smoke         | Batch05                  |

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

### 6.1 Round3 → Round4（PASS 清单）

1. Batch 3V + R3H-06 + R3H-01～04 — **CLOSED** ✅
2. Wave 1–2：R3H-07、R3H-10、R3H-08A–D — **CLOSED**
3. Wave 3：R3-DCP-01..03 — **CLOSED**（baostock + fred 增量产品路径）
4. Wave 4：**R3-DCP-05** ✅ @ `c2258363`；**R3-DCP-06** ✅ @ `6c6cdd73`（五轴 clean e2e + §3.5.1 L1 子集）；**R3-DCP-07..10** — **OPEN**
5. **G12 五轴 L1 子集：** §3.5.1 清单 **全部满足** @ `6c6cdd73` — **硬门禁已关**
6. R3H-05-GATE → **`PASS_ROUND4_REAL_DATA_READY`**
7. 24 源 env-gated live→正确 Tier；`web_search` 真 API = **DEFERRED_POST_ROUND4** + 单 ADR
8. `MAIN-DB-GATE` 绿；Layer1–5 smoke 绿（**G12 五轴算在 Layer1**）

**不要求：** R6、Batch6 全集、24 源全自动 cron、G3 链全真网。

### 6.2 Round4 → Round5

- I1–I7、J2 各 ≥ R2 真实竖切（B04 验收）
- 只读 / no-action / 无 free SQL / 无写接口

### 6.3 Round5 → Release

- B05 三连过；manifest 无隐藏 blocker

---

## 7. 旧 Wave / 批次 → 模块 ID 映射

| 旧轨          | 状态   | 主要模块     | 新波次                  |
| ------------- | ------ | ------------ | ----------------------- |
| Batch 3F-R    | CLOSED | J1,F0,C4,E1  | 历史                    |
| Batch 3G      | CLOSED | B1,E5        | 历史                    |
| Batch 3V      | CLOSED | A3,B1,G5,C1… | 历史 (= 旧 Wave 0)      |
| R3H-01～04    | CLOSED | C3,A3,G\*    | 历史                    |
| R3H-06        | CLOSED | B1,A2        | 历史 (= 旧 Wave 1)      |
| R3H-07        | CLOSED | G4,C3        | **Wave 1** @ 2026-06-29 |
| R3H-10        | CLOSED | C2,E4        | **Wave 1** @ 2026-06-29 |
| R3H-08A–D     | CLOSED | C3,A3,B\*,G6 | **Wave 2** @ 2026-06-29 |
| R3-DCP-01..03 | CLOSED | D1,E1,E2,F0  | **Wave 3** @ 2026-06-30 |
| R3-DCP-05     | CLOSED | D1,E1        | **Wave 4** @ `c2258363` |
| R3-DCP-06     | CLOSED | G1,K2        | **Wave 4** @ `6c6cdd73` |
| R3-DCP-07..10 | OPEN   | G2,G4,G5,D1  | **Wave 4**              |
| R3H-05 + GATE | OPEN   | 全表         | **Wave 5**              |
| B04-\*        | 未开工 | I1–I8,J2,J7  | Round4                  |
| B05-\*        | 未开工 | J3,A1…       | Round5                  |
| Batch6        | 未开工 | D2,D3,D4,H1  | §5.2                    |

---

## 8. 全局施工顺序（模块视角）

```text
历史底座（Round0–2 · 3F-R · 3G · 3V · R3H-01～04 · R3H-06）
  ↓
Round3 Wave 1–5（§3）— 数据 · 增量 · 五轴 · PASS
  ↓
Round4 Batch04 — 只读产品（API 先）
  ↓
Batch6 还债（不挡 Round4 开工）
  ↓
Round5 Batch05 — R6 / limitation 发布裁判
```

| 阶段   | 业务目标                | 硬门禁         |
| ------ | ----------------------- | -------------- |
| Round3 | 后端管道 + **五轴全绿** | PASS §6.1      |
| Round4 | 用户可见只读产品        | B04 验收       |
| Round5 | 安全 / 集成 / manifest  | 无隐藏 blocker |

---

## 9. 执行者开工检查清单

1. 任务卡是否标明 **Module ID** + 评级移动（如 `G1: R3→R4`）？
2. 是否从 canonical batch folder 开工？
3. Plan 冻结前是否 **`/to-issues`** 垂直切片（§3.8）？
4. 并行是否撞 registry 三件套或同节点文件锁？
5. R3H-08 / R3H-05-GATE 是否 **complex Trellis**？R3-DCP 是否 **debt-lite slice**？
6. 改符号前 `impact()`；提交前 `detect_changes()`；触达 backend/docs/specs 跑 `loop_maintain.py`。
7. Round4 是否只读、是否绕过 DataSourceService？
8. PASS 前是否核对 **§3.5.1 五轴清单**？
9. FullLoad / watermark / 幂等是否先读 **§5.1**？

---

## 10. 发布终态

Round5 后仅两类状态：`R6_FULL_PRODUCTION_STABLE` 或 `ADR_DISABLED_OUT_OF_SCOPE` / release limitation。

不允许：「差不多」「registry 有了就算完成」「Round5 顺手补管道」「三轴先 PASS 五轴后补」。

---

## 附录 A. 历史叙事索引

Wave 平铺细节、3F-R/3G 任务卡路径、§9 数据源表、原 §5.0.6 完整表格 → **`PROJECT_IMPLEMENTATION_ROADMAP.legacy-20260629.md`**。

## 附录 B. 与 `MODULE_COMPLETION_RATING.md` 对齐说明

- 51 ID 与 `authority_graph.yaml` v2 `rating_index` **无冲突**。
- **G12 / 五轴 PASS 门禁**以本文 §3.5.1、§6.1 为准；若 rating 文件仍写「G12 Round4+ 非 PASS」，以**本路线图用户裁决**覆盖规划语义（rating 表可在下一 reconcile 同步 `Required next movement` 列）。
