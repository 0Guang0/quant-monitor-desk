# M-DATA-03 会话交接 — 新 Agent 必读（Context Pack）

> **产出：** 2026-07-03 20:24 UTC+8 · **rev 4.4** · **关账切片 2/2 完成**（`task.json` → `review`，非 finish-work）  
> **保存路径：** `M-DATA-03-HANDOFF.md`（本文件）· 协调者细则另见 `M-DATA-03-EXECUTE-COORDINATOR-HANDOFF.md`  
> **全局规则 SSOT：** `c:\Users\Guang\Desktop\全局规则.txt` · **工程契约：** `.cursor/rules/project-global.mdc`

---

## 0. 是否建议新会话接手？

**是。** 理由：

| 因素         | 说明                                                                        |
| ------------ | --------------------------------------------------------------------------- |
| 上下文长度   | Execute + 合规 Audit + Repair + grill-me 多轮已超单会话有效注意力           |
| 决策已冻结   | 本文件 **§2.1 本批契约** 为业务 SSOT；§3–§5 为展开与证据，勿再 grill 已决项 |
| 未提交改动大 | `feature/m-data-03-tier-a-live` 上大量 modified/untracked（见 §8）          |
| 剩余工作独立 | F0 方向 B、空窗调查、二次幂等、CI 实跑、Tier B/C 三轨 — 适合干净上下文 TDD  |

**新会话第一句建议：**「Read `M-DATA-03-HANDOFF.md` §2.1 §2.3（T-01–T-18 总表），从 §9 **#0** 开始。」

---

## 1. Context Engineering — 加载顺序（勿一次灌整包 Plan）

按持久性从高到低加载；**单次任务聚焦 <2000 行**。

```
┌─────────────────────────────────────────┐
│ L1 规则：全局规则.txt · project-global.mdc │
│         AGENTS.md · ADR-034              │
├─────────────────────────────────────────┤
│ L2 本文件 §2.1 + §2.2 + §3–§7（契约 + 缺口 + 决策）│
├─────────────────────────────────────────┤
│ L3 任务路由（按需切片）                   │
│    00-EXECUTION-ENTRY.md                 │
│    plan-revision-r2.md §2（只读引用）     │
│    to-issues-slices.md（注意 §6 与 §5.2） │
├─────────────────────────────────────────┤
│ L4 实现触点（改哪读哪）                   │
│    tier_a_live_acceptance.py             │
│    data_health_profiles/__init__.py      │
│    live_tier_a_evidence_v1.yaml          │
│    tier-a-report.json（最新真网报告）     │
├─────────────────────────────────────────┤
│ L5 迭代：pytest 输出 · live-run.log      │
└─────────────────────────────────────────┘
```

**信任级别：** 源码/测试 = 可信 · Plan/ADR = 权威但实现以代码为准 · 旧 handoff（本文件 rev 前）= **已过期**

---

## 2. 任务快照（一句话 + 阶段）

| 项                   | 值                                                                                       |
| -------------------- | ---------------------------------------------------------------------------------------- |
| 任务                 | M-DATA-03 — 11 源 Tier A **隔离沙箱**真网完整验收（Plan R2）                             |
| 目录                 | `.trellis/tasks/archive/2026-07/m-data-03-tier-a-live/`（archived）                      |
| 分支                 | `master`（PR [#32](https://github.com/0Guang0/quant-monitor-desk/pull/32) · `ff587020`） |
| `task.json` status   | **completed** · archived `2026-07` · finish-work @ 2026-07-04                            |
| Plan R2 Execute 切片 | R2.1–R2.6 **均已 [x]**（见 `EXECUTION_INDEX.md`）                                        |
| 合规 Audit           | 8 维独立 agent → 初 FAIL 14 条 → **Repair 14/14 已修复**（`REPAIR.plan.md` CLOSED）      |
| grill-me 扩批        | **7/7 AC 可勾选** — AC-4 按**公开仓库口径**关账（§2.1 AC-4 注）                          |
| 最新有效真网 run     | `.audit-sandbox/m-data-03/r2-live-20260703220000/` · run1+run2 exit 0 · 11/11 PASS       |
| **注意**             | 沙箱过关 **≠** 生产主库就绪（ADR-034 §Sandbox boundary）                                 |

---

## 2.1 本批契约（用户锁定 SSOT · **禁止修改、禁止再问**）

> 新 agent **先读本节**再读 §3 细节。  
> **本节完整性（rev 4+）：** 下表四块均已独立成段，不得再散落到 §3/§5 后误读为未定义。

| 块                                                       | 本节锚点             | 状态 |
| -------------------------------------------------------- | -------------------- | ---- |
| 本批交付（一件事）                                       | §2.1「本批交付」     | ✅   |
| 本批 AC 七条 + 阶段外置 0                                | §2.1「本批 AC」      | ✅   |
| 本批不做什么（绑定+关闭条件表）                          | §2.1「本批不做什么」 | ✅   |
| 8 项缺口 → 处置 → AC 映射                                | §2.1「8 项缺口」     | ✅   |
| F0 方向 B 三条业务理由                                   | §2.1「F0 方向 B」    | ✅   |
| 缺口 G-01–G-07 + 逐源评估 + AC 0/7 + §2.3 总表 T-01–T-18 | §2.2 · §2.3          | ✅   |

### 本批交付（一件事）

Tier A 把与「成品」不一致的 **8 项全部关账**，并 **按 Tier A 同款** 为 **Tier B、Tier C** 各建 live 验收轨（**三份报告、三个契约**），**沙箱边界**写进文档。

**全票核心核实目的（所有数据源体检的共同目标）：**  
在隔离沙箱内证明该源 **真网可用**、**入库形态符合** 设计文档 / 契约 / 规则 / 架构所定义的 **最终成品形态**，以便后续轮次放开生产主库时 **无需再改管道语义**（本批仍 **不写** 生产 `data/` 主库，见 ADR-034）。

### 本批 AC（7 条 · 可勾选关账）

| #     | 验收项                                                                                                                                                                                                         |
| ----- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1** | **bis / cninfo / sec_edgar**：按 §3.4 完成根因调查；**可修复则必须修复且有 clean 行**；结论写明 **是否可用** + 入库是否符合成品形态；仅 **§3.4.3 客观外部空窗** 可 `FAIL_EXTERNAL`+ADR，**禁止** 0 行静默 PASS |
| **2** | `to-issues` 每源 AC#2 与实现/契约对齐：`sync=COMPLETED` + `clean_rows≥1` 为过关默认；空响应仅 `FAIL_EXTERNAL`+证据化 ADR，**禁止**「合法空窗文档化 PASS」替代修根因                                            |
| **3** | Tier A **幂等**：同一 sandbox 连续两次 `--report` 均 exit 0；指纹/行数一致                                                                                                                                     |
| **4** | **CI 实跑**：`tier-a-live` `workflow_dispatch` 有日志/artifact（或等价全量复现说明）                                                                                                                           |

> **AC-4 公开仓库关账口径（用户 2026-07-04 · 路径 A · finish-work）**  
> 仓库 **PUBLIC** + D-03：**真网验收仅本地沙箱**（`.env.local` + `.audit-sandbox/m-data-03/`）。  
> **关账证据：** `r2-live-20260703220000` run1+run2 **11/11 PASS**。  
> **GitHub live CI 已删除（2026-07-04）：** `tier-a/b/c-live.yml`（含 `workflow_dispatch` 与每日 cron）。历史机制 run [28676746914](https://github.com/0Guang0/quant-monitor-desk/actions/runs/28676746914) 仅作归档。  
> **复跑：** `scripts/tier_a_live_acceptance.py --report … --data-root …`
> | **5** | **F0 全量**：av / baostock / mootdx 报告 **无** `staged-only … review only`（方向 B，§3.2） |
> | **6** | **沙箱边界**：MCR / ADR 写明 `.audit-sandbox/` ≠ 生产 `data/` |
> | **7** | **Tier B（10）+ Tier C（3）**：各 `live_tier_{b,c}_evidence_v1` + acceptance 脚本 + `--report` 绿 + 证据归档 |

**阶段外置配额：0**

### 本批不做什么

| 项                                            | 绑定                 | 关闭条件                          |
| --------------------------------------------- | -------------------- | --------------------------------- |
| 24 源一张 `tier_a` 总报告                     | 本批已否决           | 若要做需新 Plan 修订              |
| 写生产主库                                    | ADR-034              | 永远隔离 sandbox                  |
| Wave3 大杂烩脚本复活                          | 架构决策             | 用分轨契约替代                    |
| 三源 EMPTY_RESPONSE **阶段后置** / 口头 defer | 用户 2026-07-03 禁令 | 本批调查+修或 `FAIL_EXTERNAL`+ADR |

### 8 项缺口 → 处置对照

| 缺口              | 处置                                                          | 对应 AC    |
| ----------------- | ------------------------------------------------------------- | ---------- |
| 空响应仍 PASS     | §3.4 调查 → 可修必修+有行；仅站点客观不可用可 `FAIL_EXTERNAL` | AC-1、AC-2 |
| AC#2 字面不一致   | 与契约/实现统一；默认 `COMPLETED`+clean≥1                     | AC-2       |
| 仅沙箱            | MCR/ADR 文档化                                                | AC-6       |
| 未证二次幂等      | 同 sandbox 双跑对比                                           | AC-3       |
| CI 未实跑         | workflow_dispatch 机制 + 本地沙箱全量复现（公开仓库不放 key） | AC-4       |
| F0 staged-only    | 方向 B：live 独立 gate，退役 R3G 彩排 gate                    | AC-5       |
| Tier B/C 未覆盖   | 并行契约三轨                                                  | AC-7       |
| MCR 是 sandbox R4 | AC-6 + 汇报边界说明                                           | AC-6       |

### F0 方向 B（用户确认）

**选定方案：** live 验收走 **自己的 gate**（非 R3G 彩排 gate）；统一 Tier A live **完整体检**；**清理退役** live 路径上的 staged-only / `evaluate_rehearsal_closeout_gate` 依赖（方向 A 伪造 closeout JSON **已否决**）。

**三条业务理由（用户原文口径）：**

| #   | 理由         | 内容                                                                                                                                   |
| --- | ------------ | -------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **业务诚实** | 今天沙箱里行情 **确实抓到了、有 clean 行**（当前报告 **av=3 / baostock=2 / mootdx=2**），**不是假 PASS**；问题是体检档位未与宏观源统一 |
| 2   | **口径统一** | AC 要求「和宏观源一致」→ 应是 **`f0=PASS` 且无 staged-only 附注**，而不是去伪造 R3G 彩排材料                                           |
| 3   | **不夸大**   | 即使 F0 全绿，**仍不等于生产主库已上线**——由 **ADR-034 + MCR 沙箱边界**单独说明，**不靠** staged-only 小字来提醒                       |

**技术锚点（实现时只读）：** `data_health_profiles/__init__.py` · `data_health.py` L1039–1063 · `tier_a_live_acceptance.py` `_run_f0_data_health` · 细节 §3.2

---

## 2.2 核心目标对齐评估 · 缺口登记（下一会话必处理）

> **SSOT 报告：** `.audit-sandbox/m-data-03/r2-live-20260703220000/tier-a-report.json`  
> **逐源结案模板：** `research/archive/non-plan/execute/tier-a-per-source-production-readiness.md`  
> **三源空响应专项：** `research/archive/non-plan/execute/tier-a-empty-response-investigation.md`

### 方向判断（工程 vs 关账）

| 维度                             | 是否符合用户核心目标                     | 说明                                                            |
| -------------------------------- | ---------------------------------------- | --------------------------------------------------------------- |
| 建统一 live 验收流水线           | **符合**                                 | 真网→raw→clean→E2→F0→B2→manifest；为「核实成品形态」搭台        |
| 本批可宣称「核实完成、可开主库」 | **不符合**                               | 见下表；**0/11 源**可诚实宣称「成品形态已核实，下轮只等开主库」 |
| grill AC 七条                    | **7/7 可勾选**（AC-4 公开仓库口径 §2.1） | `task.json` → `review`                                          |

### 偏离预期 — 必须视为未完成（禁止当 PASS 宣传）

| ID       | 缺口                                                                        | 下一会话动作                                                        | 映射                      |
| -------- | --------------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------- | -------------------------------------------------------- |
| **G-01** | 验收门槛过低：`EMPTY_RESPONSE`+0 行仍 PASS                                  | 修 acceptance 守卫 + 三源调查/修或 `FAIL_EXTERNAL`                  | AC-1 · AC-2 · §9 #0 #2    | **✅** 守卫+调查+关账 run                                |
| **G-02** | 缺「成品形态」叙事：无逐源对照 `data_sources.md`/契约/F0/B2 结论文本        | 填 `tier-a-per-source-production-readiness.md`（11 源 §3.4.2 四问） | AC-1 · 全源               | **✅** 11 源四问已填                                     |
| **G-03** | 行情 F0 双标准：`staged-only` ≠ 成品档                                      | F0 方向 B 实现 + 复跑报告                                           | AC-5 · §9 #1              | **✅** 三行情 `f0=PASS` 无 staged-only                   |
| **G-04** | 证据过度乐观：`r2-tier-a-live-accept-evidence.md` 写「零缺口」、三源当 PASS | **已改诚实表述**；关账 run 已更新                                   | 本文 §7                   | **✅** rev 4 evidence md                                 |
| **G-05** | 生产前置未验：无二次幂等、无 CI 实跑、沙箱≠生产未入 ADR/MCR、B/C 未覆盖     | §9 #3–#7                                                            | AC-3 · AC-4 · AC-6 · AC-7 | **✅** · 幂等+B/C+ADR+AC-4（公开仓库口径）               |
| **G-06** | 任务未关：`in_progress`；grill AC **0/7**                                   | handoff 门禁 + `task.json` → `review`（**非** finish-work）         | §2.3 T-14/T-15            | **✅ 部分** · `review` · 7/7 AC                          |
| **G-07** | world_bank/deribit 仅 1 行 clean，证据偏薄                                  | 扩窗/复跑 + 四问（§2.3 T-05）                                       | G-02 · §9 #0c             | **✅** `r2-thicken-wb-deribit-20260703224024` wb=2 der=2 |

### 逐源业务评估（`r2-live-20260703192034` · 用户口径）

| 源                                | 能不能用？                 | 抓到了吗？入库像成品吗？           | 能否支撑「下轮可开主库」？                         | 下一会话          |
| --------------------------------- | -------------------------- | ---------------------------------- | -------------------------------------------------- | ----------------- |
| fred / us_treasury / cftc_cot     | **倾向可用**               | COMPLETED，clean 有行；F0/B2 绿    | **部分**：单次沙箱跑通；缺幂等、缺逐源成品对照说明 | 填四问 + 二次幂等 |
| world_bank / deribit              | **沙箱可用**               | 各 **2** 行 clean（G-07 加厚 run） | **弱→中**：双国家/双合约已证管道                   | 主库前 promote    |
| alpha_vantage / baostock / mootdx | **有数据，体检未达成品档** | 3/2/2 行 K 线                      | **否**：F0 仍 staged-only                          | AC-5 + 四问       |
| bis / cninfo / sec_edgar          | **未证实可用**             | EMPTY_RESPONSE，**0** 行 clean     | **否**：rev4 须调查→修到有位或 `FAIL_EXTERNAL`+ADR | §9 #0 最高优      |

**汇总结论（不得改写成 PASS 宣传）：**

- **11 源**在关账 sandbox（`r2-live-20260703220000`）双跑 **11/11 PASS**。
- **11 源**已填 `tier-a-per-source-production-readiness.md` 四问（沙箱 scope）。
- **0 源**可诚实宣称：**仅等放开生产主库**（须 R3G promote + posture）。

### AC 勾选现状（grill 七条）

| AC   | 状态                                                                                                                                                                  |
| ---- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| AC-1 | ✅ 三源调查+修 · investigation md · 关账 run                                                                                                                          |
| AC-2 | ✅ 守卫 + `test_cleanRowCount_*`                                                                                                                                      |
| AC-3 | ✅ 双跑 exit 0 · `r2-live-20260703220000`                                                                                                                             |
| AC-4 | ✅ 公开仓库口径：机制 [run 28676746914](https://github.com/0Guang0/quant-monitor-desk/actions/runs/28676746914) + 本地 `r2-live-20260703220000` 11/11（§2.1 AC-4 注） |
| AC-5 | ✅ 三行情 `f0=PASS`（无 staged-only）                                                                                                                                 |
| AC-6 | ✅ ADR-034 §Sandbox boundary + MCR                                                                                                                                    |
| AC-7 | ✅ Tier B/C 契约+报告 · **Tier B 增补：** stooq **路径二已接受**；CN 三源 **条件路径二**（`tier-b-network-path2-evidence.md`）                                        |

### 2.2.1 是否过度清理？— 并集核对说明

| 来源                                           | 是否仍须解决   | handoff 锚点                  | 风险                    |
| ---------------------------------------------- | -------------- | ----------------------------- | ----------------------- |
| 用户最初 **8 项缺口**                          | **是**         | §2.1「8 项缺口」· §3.1        | 无遗漏                  |
| grill **AC 1–7**                               | **7/7**        | §2.1 · §5 · §2.2 AC 表        | AC-4 公开仓库口径已关账 |
| 用户决策 **full_triple**（幂等+CI+F0）         | **是**         | AC-3 · AC-4 · AC-5 · §9 #3–#5 | AC-4 按路径 A 关账      |
| **并行契约三轨** Tier B/C 扩本批               | **是**         | AC-7 · §3.3 · §9 #6–#7        | 未砍范围                |
| **方向 B** 退役 R3G staged-only                | **是**         | G-03 · §3.2                   | 未删                    |
| rev4 **三源严格调查**（取代宽松 empty_window） | **是**         | §3.4 · G-01                   | **收紧**，非删除        |
| **新发现** G-01–G-06                           | **是**         | 本节 + §9                     | 见 §2.3 总表            |
| **新发现** 宏观/薄证据源未写四问               | **是**         | G-02 · G-07 · §9 #0b #0c      | 曾偏弱，已补 G-07       |
| Plan R2 机闸（pytest/管线）                    | **保留不重做** | §7「保留」                    | **≠** 成品关账          |

**诚实化修正（G-04）只改了措辞，未从待办删除任何用户已确认项。**

---

## 2.3 全部待解决事项总表（并集 · 下一会话关账前 **全部 ⬜→✅**）

> **规则：** 本表 = §2.1 八缺口 + grill AC-1–7 + G-01–G-07 + Plan R2 在**新口径下**须复验项。**禁止**因 evidence 诚实化或 Repair 14/14 而从表中删行。

| ID   | 事项（要解决什么）                                                           | 来源                           | 映射         | 状态                                                  |
| ---- | ---------------------------------------------------------------------------- | ------------------------------ | ------------ | ----------------------------------------------------- |
| T-01 | bis/cninfo/sec：根因调查（网络/代码/格式/窗）+ 可修必修 + 历史窗             | 原缺口#1 · rev4 · G-01         | AC-1 · §9#0  | ✅                                                    |
| T-02 | acceptance：**EMPTY_RESPONSE+0 clean 不得 PASS**                             | 原缺口#1 · G-01                | AC-2 · §9#2  | ✅                                                    |
| T-03 | `to-issues` AC#2 与契约/实现/报告对齐                                        | 原缺口#2 · G-01                | AC-2         | ✅                                                    |
| T-04 | **11 源** §3.4.2 四问 + 成品形态对照（`data_sources.md` 等）                 | 核心目标 · G-02                | AC-1 · §9#0b | ✅                                                    |
| T-05 | world_bank/deribit：**加厚证据**（扩窗/复跑，非 1 行即止）                   | 新发现 §2.2 逐源表 · **G-07**  | G-02 · §9#0c | ✅ `r2-thicken-wb-deribit-20260703224024`             |
| T-06 | fred/us_treasury/cftc_cot：四问 + 幂等前确认过关形态                         | 新发现 §2.2                    | T-04 · AC-3  | ✅                                                    |
| T-07 | av/baostock/mootdx：**F0 方向 B** 实现，无 staged-only                       | 原缺口#6 · full_triple · G-03  | AC-5 · §9#1  | ✅                                                    |
| T-08 | 同 sandbox **二次** `--report` 幂等指纹                                      | 原缺口#4 · full_triple · G-05a | AC-3 · §9#3  | ✅ `r2-live-20260703220000`                           |
| T-09 | CI **workflow_dispatch** 机制 + 本地 11/11 等价复现                          | 原缺口#5 · full_triple · G-05b | AC-4 · §9#4  | ✅ 路径 A：run 28676746914 + `r2-live-20260703220000` |
| T-10 | ADR-034 + **MCR** 写明沙箱≠生产；汇报边界                                    | 原缺口#3#8 · G-05c             | AC-6 · §9#5  | ✅                                                    |
| T-11 | Tier B：10 源 `live_tier_b_evidence_v1` + acceptance + dispatch + report     | 原缺口#7 · 并行契约            | AC-7 · §9#6  | ✅ `tier-b/closeout-20260703`                         |
| T-12 | Tier C：3 源 `live_tier_c_evidence_v1` + acceptance + report                 | 同上                           | AC-7 · §9#7  | ✅ `tier-c/closeout-20260703`                         |
| T-13 | evidence md **关账版**（含修后 live run，非仅机闸叙述）                      | G-04                           | §9#8         | ✅ rev 4                                              |
| T-14 | `uv run pytest -q` · `loop_maintain` · `validate-execute-handoff`            | Plan R2 · G-06                 | §9#8         | ✅ slice 2/2                                          |
| T-15 | grill AC **7/7 可勾选** + `task.json` → `review`（**非** finish-work）       | G-06                           | §9#9         | ✅ 7/7 · AC-4 路径 A                                  |
| T-16 | Plan R2 **#8** 在新守卫下 **11 源** live exit 0（或全 FAIL_EXTERNAL 有 ADR） | Plan §2                        | 复验 · §9#8  | ✅ `r2-live-20260703220000`                           |
| T-17 | Plan R2 **#9** MCR 诚实 **sandbox scope**（非生产就绪宣称）                  | Plan §2                        | T-10         | ✅                                                    |
| T-18 | 可选：改动面大时 **再 Audit**（A4/A5/A8 增量）                               | §6.1                           | 关账前评估   | ⏭ **跳过**（用户禁止本批再 Audit）                   |

**新缺口 G-07（补登）：** world_bank、deribit 仅 1 行 clean — 须复跑/扩窗证明管道与成品形态，**不得**仅凭单次 1 行宣称「可用」。

---

## 3. 用户锁定决策（grill-me 展开 · SSOT = **§2.1**）

### 3.1 八项「与成品不一致」缺口 — 处置口径

| #   | 缺口                                                     | 用户决策                                                                                                                                    | 严重度（业务）          |
| --- | -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------- |
| 1   | 空响应仍 PASS（bis/cninfo/sec · 0 行 clean）             | **§3.4 强制调查**；可修（网络/代码/格式/窗参数）**必须修且有行**；当前窗无数据则 **尝试过往历史窗**；仅客观外部不可用可 `FAIL_EXTERNAL`+ADR | 高                      |
| 2   | `to-issues` AC#2「COMPLETED + clean≥1」与 EMPTY_RESPONSE | **默认过关=有行**；空响应 **不得** 静默 PASS；与契约/报告字段对齐（§5 AC-2）                                                                | 中                      |
| 3   | 数据仅在 `.audit-sandbox/`，非生产 `data/`               | **沙箱边界文档化**（MCR/ADR 写明沙箱≠生产）；**不写主库**                                                                                   | 中                      |
| 4   | ADR-034 二次幂等未证                                     | **必须**：同一 sandbox **连续两次** `--report` 对比指纹                                                                                     | 中                      |
| 5   | CI 未在本机/GitHub 实跑                                  | **必须**：`tier-a-live` workflow **实跑证据**（dispatch 全量 11/11 或等价可核对 artifact）                                                  | 中                      |
| 6   | F0 行情源 staged-only                                    | **方向 B（已确认）** — 见 §3.2                                                                                                              | 中                      |
| 7   | Tier B/C 未覆盖                                          | **扩进本批**                                                                                                                                | 按范围预期 / 全产品缺口 |
| 8   | MCR 是 sandbox R4                                        | 与 #3 一并：**诚实边界**写入 MCR/汇报，不等于监控台生产就绪                                                                                 | —                       |

**阶段外置配额：0**（用户明确要求逐项解决，禁止隐形 defer）。

### 3.2 F0「非 staged-only」— 技术展开（业务理由见 **§2.1 F0 方向 B**）

| 概念               | 业务含义                                                                                                                                         |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| **今天现象**       | av/baostock/mootdx 的 `f0_health_status=PASS`，但 `failure_detail` 含 `staged-only profile; gate input sufficient for review only`               |
| **原因**           | `market_bar_p0` 仍调用 `evaluate_rehearsal_closeout_gate`，要求 Batch 2.75/R3G 的 `pilot_v2_closeout.json` 等；M-DATA-03 live 路径不产生这些文件 |
| **方向 B（锁定）** | Tier A **live 验收即完整 F0 关门**；与 fred 同级：报告仅 `f0=PASS`，**不得**再出现 `staged-only`                                                 |
| **实现要点**       | 改 `market_bar_p0` 和/或 `tier_a_live_acceptance`：**退役** live 路径对 R3G rehearsal closeout 的依赖；**勿**伪造 closeout JSON（方向 A 已否决） |
| **不等于**         | 允许写生产主库 — ADR-034 仍禁止；只是 **验收报告语义统一**                                                                                       |

**代码锚点：** `backend/app/ops/data_health_profiles/__init__.py` L276 `evaluate_rehearsal_closeout_gate` · `backend/app/ops/data_health.py` L1039–1063 · `tier_a_live_acceptance.py` `_run_f0_data_health`

### 3.3 Tier B/C 扩批形态（用户确认）

| 选项                                        | 结果                                                                                                                                              |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| 24 源塞进 `tier_a_live_acceptance` 一份报告 | **否决**                                                                                                                                          |
| **并行契约、三轨报告（采纳）**              | Tier A 先关 §5 缺口 → `live_tier_b_evidence_v1` + `tier_b_live_acceptance`（10 源）→ `live_tier_c_evidence_v1` + `tier_c_live_acceptance`（3 源） |
| 本批只做 A，B/C 另票                        | **否决**（用户选扩本批）                                                                                                                          |

**Tier 定义 SSOT：** `backend/app/datasources/live_tier_router.py`

- A=11（本票已有 acceptance）· B=10 · C=3
- B/C **尚无** `tier_*_live_incremental_dispatch` 同级能力（如 `akshare` 调 Tier A 增量会报错）

### 3.4 三源空响应（bis · cninfo · sec_edgar）— 调查与过关标准（用户 2026-07-03 收紧 · **rev 4**）

> **取代** 早期 grill「合法空窗可 PASS + `empty_window` 字段」的宽松口径。  
> **本批必须得出结论：该源到底能不能用、入库是否符合成品形态。**

#### 3.4.1 必须搞清楚的分类

对每一源单独建档（写入 `research/archive/non-plan/execute/tier-a-empty-response-investigation.md` 或同级证据）：

| 根因类别     | 典型表现                                 | 本批要求                                                               |
| ------------ | ---------------------------------------- | ---------------------------------------------------------------------- |
| **网络**     | 超时、TLS、代理、DNS、429/503            | 修配置/重试/限流；复跑直至有 raw **或** 证伪为站点级故障               |
| **代码**     | dispatch、normalizer、窗计算、EMPTY 误判 | **修代码**（TDD）；不得 acceptance 层吞掉                              |
| **格式**     | 上游 HTML/JSON/XML 变更、字段漂移        | 修 adapter/normalizer；对照契约与 `data_sources.md`                    |
| **窗/参数**  | 当前增量窗无新公告/系列                  | **扩窗抓取过往数据**（历史窗、symbol 列表、series id）；证明管道能入库 |
| **客观外部** | 站点长期宕机、官方停更、需付费且无 KEY   | 仅此类可 `FAIL_EXTERNAL` + **ADR**；报告 **诚实写明** 外部条件         |

#### 3.4.2 必须得出的结论（每源一段 · 给用户汇报用）

1. **是否可以用？**（是 / 否 / 有条件可用 — 条件写清）
2. **抓过来了吗？** raw 路径、条数、时间窗
3. **入库形态是否符合成品？** 对照：`docs/modules/data_sources.md` · `live_tier_a_evidence_v1.yaml` `source_bindings` · `data_quality_rules.yaml` · F0 profile · B2 `validate_table` · 相关 ADR
4. **后续放开生产主库还需什么？**（若无则写「管道语义已就绪，仅差 ADR-034 主库禁令解除」）

**有可修复根因时：本批过关形态 = `sync=COMPLETED` + `clean_rows ≥ 1` + F0/B2 非 FAIL。** 不得以 SKIP、静默 PASS、`empty_window` 字段 alone 过关。

#### 3.4.3 唯一允许「空响应仍过关」的情形

仅当调查 **证实** 下列 **客观外部** 条件（须附证据：HTTP 状态、官方公告、停更日期、付费墙无资格等）：

- 站点/服务 **挂了** 且非本仓可修
- 数据源 **不再更新**（官方停更）
- 本环境 **无合法访问资格** 且 eligibility 矩阵已登记 ADR

此时：`failure_class=FAIL_EXTERNAL`，`adr_ref` 指向契约 `authoritative_docs` 或新 ADR 行；**禁止** 标 `PASS` + 0 行。

**以下均不得视为过关，不得阶段后置：**

- 「今天刚好没公告」但未尝试历史窗
- 「测试窗太窄」但未扩窗复现
- 「以后再接 Tier B」
- 「EMPTY_RESPONSE 先绿着」

#### 3.4.4 调查动作清单（新会话执行顺序）

| 源          | 建议入口                            | 对照文档                                                         |
| ----------- | ----------------------------------- | ---------------------------------------------------------------- |
| `bis`       | `bis_incremental_*` · macro layer1  | `source_bindings` → `axis_observation` · `layer1_observation_p0` |
| `cninfo`    | `cninfo_incremental_*` · disclosure | `cn_announcement_clean` · `disclosure_p0`                        |
| `sec_edgar` | `sec_edgar_incremental_*`           | `us_disclosure_clean` · `disclosure_p0`                          |

每源至少保留：一次失败 run 日志、一次修后/扩窗后 run、raw 样例路径、clean 行样例、与 §3.4.2 四问对应的文字结论。

---

## 4. Plan R2 原始 AC（`plan-revision-r2.md` §2 · 用户锁定 · 只引用不篡改）

1. `live_tier_a_evidence_v1.yaml` 11 源闭合
2. 统一验收报告 JSON；`failure_class` 明确；无 SKIP
3. F0 四族 profile
4. B2 每源 `validate_table`
5. E2 `DbInspector.inspect()` 非 FAIL
6. dispatch 重构；mootdx matrix；无 bypass
7. CI nightly quick + manual 11/11 + failure artifact
8. `pytest -q` exit 0；11/11 live exit 0（或 FAIL_EXTERNAL 全 ADR）
9. MCR C3/D1/E1/E2/F0/B2 诚实 R4 **sandbox scope**
10. Execute 关账证据 `archive/non-plan/execute/r2-tier-a-live-accept-evidence.md`

> **状态：** §1–§10 Execute/Repair 声称已满足；**§5 grill 扩批 AC 是额外关账门槛**，未满足前不得对用户宣称「成品一致」。

---

## 5. grill-me 扩批 AC（**本批最终关账标准 · 禁止修改**）

> 与 §2.1 表一致；本节补 **通过证据** 路径。

| #        | 验收项                                                                                                   | 通过证据                                                                                        |
| -------- | -------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| **AC-1** | bis/cninfo/sec：**§3.4 调查结案**；可修必修 → `COMPLETED`+clean≥1；仅客观外部 → `FAIL_EXTERNAL`+ADR+证据 | `tier-a-empty-response-investigation.md` + 更新后 `tier-a-report.json` + 修后 live run          |
| **AC-2** | `to-issues` AC#2 与实现一致：默认 `COMPLETED`+clean≥1；**禁止** 0 行 PASS                                | `to-issues-slices.md` 脚注 + 契约/acceptance 测 + 报告字段                                      |
| **AC-3** | Tier A 幂等：同 sandbox 连续两次 `--report` exit 0；DB/行数/manifest 指纹一致                            | 两次 run 路径 + 对比表写入 `r2-tier-a-live-accept-evidence.md`                                  |
| **AC-4** | 本地沙箱全量真网可核对（公开仓库无 GitHub live CI）                                                      | `r2-live-20260703220000` 11/11 · `scripts/tier_a_live_acceptance.py` · tier-a/b/c workflow 已删 |
| **AC-5** | av/baostock/mootdx：`failure_detail` 仅 `f0=PASS`（与 fred 同形），**无** `staged-only`                  | 新 live run 报告 + 定向 pytest                                                                  |
| **AC-6** | 沙箱≠生产：MCR + ADR-034 增补（或 execute 证据 §边界）                                                   | 文档 diff + 用户可读摘要                                                                        |
| **AC-7** | Tier B（10）+ Tier C（3）：各自契约 + acceptance + `--report` 绿 + 证据归档                              | 新契约 YAML · 新脚本 · 新 sandbox run · 新 evidence md                                          |

**本批不做什么：** 见 **§2.1「本批不做什么」** 表（不在此重复，防漂移）。

---

## 5.2 真网报告快照

**详见 §2.2 逐源表。** 关账报告：`.audit-sandbox/m-data-03/r2-live-20260703220000/tier-a-report.json`  
**口径：** 双跑 11/11 PASS = 沙箱 pipeline 关账；**≠** 生产主库就绪。

---

## 6. 本轮任务最终要产出什么、证明什么、向用户汇报什么

### 6.1 最终产出物（文件/能力）

| 产出                | 路径/形态                                                                                             |
| ------------------- | ----------------------------------------------------------------------------------------------------- |
| Tier A 关账         | 更新 `r2-tier-a-live-accept-evidence.md`（含二次幂等、CI、F0、空窗）                                  |
| F0 方向 B 代码      | `data_health_profiles` / `tier_a_live_acceptance` + 测试                                              |
| 空窗语义 / 三源调查 | `tier-a-empty-response-investigation.md` + 11 源四问 md + 报告 JSON（**非** empty_window alone 过关） |
| 沙箱边界文档        | ADR-034 增补或 MCR 表注 + 用户可读一段                                                                |
| Tier B 轨           | `specs/contracts/live_tier_b_evidence_v1.yaml` · `tier_b_live_acceptance` · dispatch · 测试           |
| Tier C 轨           | `specs/contracts/live_tier_c_evidence_v1.yaml` · `tier_c_live_acceptance` · …                         |
| 机闸全绿            | `uv run pytest -q` exit 0 · `validate-repair-close` / `validate-execute-handoff` · `loop_maintain`    |
| 可选再 Audit        | 若改动面大：合规 8 维复验或增量 A4/A5/A8                                                              |
| Git                 | PR #32 已 merge `master`；AC-4 证据见 §2.1 注 + `r2-tier-a-live-accept-evidence.md` §CI               |

### 6.2 必须向用户证明的业务命题（不是写 PASS 就完）

汇报须用 **业务语言** 回答下列问题，每条带 **证据路径**：

1. **接通是否等于有数据？**
   - 默认 **是**（`COMPLETED`+clean≥1）。bis/cninfo/sec：**§3.4 四问结论** + 修后证据；仅客观外部失败可 ADR 化 **FAIL**，**禁止** 0 行 PASS。

2. **入库是否符合最终成品形态？**
   - 每源对照设计文档/契约/F0/B2；为 **后续放开生产主库** 做管道语义核实（本批仍不写主库）。

3. **真网链路是否完整？**
   - 抓取 → raw 落盘 → sync/clean → E2 → F0 → B2 → manifest/report；11 源同一验收层。

4. **跑两次会不会 duplicate/炸库？**
   - 同 sandbox 二次 `--report` 指纹对比（ADR-034 §Decision #4）。

5. **CI 会不会 nightly 假绿？**
   - GitHub（或等价）workflow_dispatch **实跑** 11/11 日志/artifact。

6. **行情源体检是否和宏观一样正式？**
   - 3 行情源报告 **无 staged-only**；旧 R3G gate 已从 live 路径退役说明。

7. **沙箱过关是否等于生产上线？**
   - **明确否**；MCR R4 = sandbox scope；主库未写。

8. **全产品 24 源进度？**
   - A 关账 + B 10 + C 3 各自报告绿；未覆盖部分 **零**（若 AC-7 未完成则诚实报缺口）。

### 6.3 用户汇报模板（关账时必填）

```markdown
## M-DATA-03 关账汇报

### 业务结论（3 句话以内）

- Tier A：…
- Tier B/C：…
- 生产主库：未写入（证据：…）

### AC 勾选（§5 七条 + Plan §2 十条）

- [ ] AC-1 …（证据：…）
- …

### 真网数据摘要表（11+10+3）

| 档 | 源 | 有数据/结论 | 成品形态符合 | 二次幂等 | F0 | 备注 |

### 已知边界（诚实）

- 沙箱路径：…
- MCR 不等于全功能监控台生产就绪：…

### 命令复现

（粘贴用户可复制的 2–3 条命令）
```

**禁止：** 仅报「Audit PASS / pytest 绿 / 11/11」而不附 §6.2 业务表。

---

## 7. 已完成工作（保留 · 勿推倒重来）

| 阶段                      | 状态    | 证据                           | 备注                              |
| ------------------------- | ------- | ------------------------------ | --------------------------------- |
| Plan R2 freeze            | ✅ 保留 | `plan.freeze.md`               |                                   |
| Execute R2.1–R2.6 切片    | ✅ 保留 | `EXECUTION_INDEX.md`           | 机制已建，**关账口径见 §2.2**     |
| 统一 acceptance pipeline  | ✅ 保留 | `tier_a_live_acceptance.py` 等 | **须修** G-01 守卫                |
| 合规 Audit → Repair 14/14 | ✅ 保留 | `audit-repair-ledger.md`       | 机闸/管线；**不等于**成品核实完成 |
| grill-me 决策             | ✅ 锁定 | §2.1                           |                                   |

### 已完成但须修正（下一会话第一件事含文档）

| 项                                          | 问题                          | 修正要求                                                            |
| ------------------------------------------- | ----------------------------- | ------------------------------------------------------------------- |
| `r2-tier-a-live-accept-evidence.md`         | G-04：「零缺口」、三源当 PASS | **已改**为 Plan R2 机闸 vs grill 关账分列；禁止再写「成品核实完成」 |
| `r2-live-20260703192034` 报告叙事           | 11/11 PASS 过度乐观           | 对外以 **§2.2 逐源表** 为准，不以 summary.passed alone 宣传         |
| `tier-a-per-source-production-readiness.md` | G-02                          | **已填** 11 源四问 · 锚定 `r2-live-20260703220000`                  |
| `tier-a-empty-response-investigation.md`    | G-01                          | **已填** bis/cninfo/sec 四问 · 无 replay 过关表述                   |
| MCR / ADR-034                               | G-05                          | 沙箱 R4 诚实口径 · sec_edgar 本环境 `FAIL_EXTERNAL`（SEC TLS 封锁） |

**勿重做：** 全量重写 dispatch/契约/首次 11 源 pipeline（除非调查证明根因在彼）。

---

## 8. Git / 工作区（2026-07-03 交接时）

```
分支：feature/m-data-03-tier-a-live
未提交：tier_a_live_acceptance.py · data_health_profiles · conftest · audit 报告全套 · REPAIR.plan.md 等
最近 commit：8aa87997 chore P4 handoff · 560bf07f AC#8 11/11 · 9f3c6405 raw evidence F0
```

**新会话第一件事：** `git status` 核对是否仍上述状态；改 symbol 前 **GitNexus `impact()`**。

---

## 9. 工作队列（严格顺序 · 过关即进下一项）

| 序     | 工作项                                                                                 | 依赖            | 验证                                                                                    |
| ------ | -------------------------------------------------------------------------------------- | --------------- | --------------------------------------------------------------------------------------- |
| **0**  | **G-01/G-02**：bis/cninfo/sec §3.4 调查 + 修或 `FAIL_EXTERNAL`；建/填 investigation md | 最高优          | **[x]** AC-1 · AC-2                                                                     |
| **0b** | **G-02 / T-04**：11 源 `tier-a-per-source-production-readiness.md` 四问                | 可与 #0 并行    | **[x]** 每源一节                                                                        |
| **0c** | **G-07 / T-05**：world_bank + deribit 扩窗/复跑加厚 clean 证据 + 四问                  | 可与 #0 并行    | **[x] wb=2 der=2** · `r2-thicken-wb-deribit-20260703224024`                             |
| **1**  | **G-03**：F0 方向 B                                                                    | 可与 #0 并行    | **[x]** AC-5                                                                            |
| **2**  | **G-01**：acceptance 守卫 — EMPTY_RESPONSE+0 clean **不得 PASS**                       | #0 根因或同步   | **[x]** 测 + 报告                                                                       |
| **3**  | **G-05a**：二次幂等双跑                                                                | Tier A 过关形态 | **[x]** AC-3 · `r2-live-20260703220000`                                                 |
| **4**  | **G-05b**：CI workflow_dispatch 机制 + 本地全量复现                                    | 稳定            | **[x]** AC-4 路径 A · run 28676746914 + `r2-live-20260703220000`                        |
| **5**  | **G-05c**：沙箱边界 ADR/MCR                                                            | 无              | **[x]** AC-6                                                                            |
| **6**  | **G-05d**：Tier B 10 源                                                                | 镜像 A          | **[x]** AC-7 · `tier-b-closeout` · **诚实口径：** 6 PASS + stooq 路径二 + CN 条件路径二 |
| **7**  | **G-05e**：Tier C 3 源                                                                 | #6 可并行       | **[x]** AC-7 · `tier-c-closeout`                                                        |
| **8**  | **G-04/G-06**：修正 evidence md · 全量 pytest · handoff 门禁                           | 全部 G          | **[x]** slice 2/2                                                                       |
| **9**  | `task.json` → `review`（**非** finish-work）/ commit                                   | T-01–T-17       | **[x]** 7/7 AC · AC-4 路径 A                                                            |

---

## 10. 权威路径索引（引用，不复述条文）

| 用途                         | 路径                                                                                  |
| ---------------------------- | ------------------------------------------------------------------------------------- |
| Execute 路由                 | `.trellis/tasks/archive/2026-07/m-data-03-tier-a-live/research/00-EXECUTION-ENTRY.md` |
| Plan R2 AC §2                | `research/plan-revision-r2.md`                                                        |
| 切片 AC                      | `research/to-issues-slices.md`                                                        |
| 证据契约 A                   | `specs/contracts/live_tier_a_evidence_v1.yaml`                                        |
| ADR 隔离验收                 | `docs/decisions/ADR-034-m-data-03-tier-a-live-acceptance.md`                          |
| 最新真网报告                 | `.audit-sandbox/m-data-03/r2-live-20260703220000/tier-a-report.json`                  |
| Execute 证据（Plan R2 机闸） | `research/archive/non-plan/execute/r2-tier-a-live-accept-evidence.md`                 |
| Tier B 网络路径二            | `research/archive/non-plan/execute/tier-b-network-path2-evidence.md`                  |
| 11 源成品核实                | `research/archive/non-plan/execute/tier-a-per-source-production-readiness.md`         |
| 三源空响应调查               | `research/archive/non-plan/execute/tier-a-empty-response-investigation.md`            |
| 缺口登记 SSOT                | 本文件 **§2.2–§2.3**（G-01–G-07 · T-01–T-18）                                         |
| Audit / Repair               | `audit.report.md` · `research/audit-repair-ledger.md` · `REPAIR.plan.md`              |
| CI workflow                  | **已删除** — 本地 `scripts/tier_*_live_acceptance.py`                                 |
| Tier 路由                    | `backend/app/datasources/live_tier_router.py`                                         |
| 协调者协议                   | `M-DATA-03-EXECUTE-COORDINATOR-HANDOFF.md`                                            |
| 全局规则                     | `c:\Users\Guang\Desktop\全局规则.txt`                                                 |

---

## 11. 新会话 Boot 命令（复制即用）

```bash
cd C:\Users\Guang\Desktop\quant-monitor-desk
git checkout feature/m-data-03-tier-a-live
git status -sb

# 读交接
# Read M-DATA-03-HANDOFF.md §2.1 §2.2 §9

# 开工前全量基线（改动前）
uv run pytest -q

# Tier A live 复现（勿写主库）
$env:QMD_ALLOW_LIVE_FETCH=1
$ts = Get-Date -Format "yyyyMMddHHmmss"
$sandbox = ".audit-sandbox/m-data-03/r2-live-$ts"
New-Item -ItemType Directory -Force -Path $sandbox | Out-Null
uv run python scripts/tier_a_live_acceptance.py --report "$sandbox/tier-a-report.json" --data-root $sandbox
```

---

## 12. Suggested Skills（新 Agent 应按需 Invoke）

| 顺序 | Skill                                                                          | 何时                                                                      |
| ---- | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------- |
| 1    | `.cursor/skills/trellis-execute/SKILL.md` + `reference.md`                     | Boot · 切片执行                                                           |
| 2    | `test-driven-development`（`.claude/skills/test-driven-development/SKILL.md`） | **每个**代码改动先 RED                                                    |
| 3    | `testing-guidelines`                                                           | 五字段 docstring                                                          |
| 4    | `karpathy-guidelines`                                                          | 代码风格                                                                  |
| 5    | `gitnexus-impact-analysis`                                                     | 改 `evaluate_rehearsal_closeout_gate` / acceptance 前 **必须** `impact()` |
| 6    | `grill-me`                                                                     | **仅** §3 未覆盖的新冲突；已锁定决策禁止重开                              |
| 7    | `incremental-implementation`                                                   | Tier B/C 大扩批时分批                                                     |
| 8    | `trellis-check` / Audit agents                                                 | 关账前对抗性复验                                                          |
| 9    | `agent-toolchain.md`                                                           | 工具路由歧义                                                              |

---

## 13. 风险与易错点

| 风险                                   | 缓解                                            |
| -------------------------------------- | ----------------------------------------------- |
| PowerShell `&&` / `$ts=` 语法错误      | 用 `;` 与 `$ts = Get-Date ...`                  |
| `QMD_ALLOW_LIVE_FETCH=1` 误跑 batch275 | `conftest.py` 已收窄 tier-a 路径；勿放宽        |
| 为绿改测试目的                         | 禁止；可改实现                                  |
| 伪造 R3G closeout JSON                 | 用户否决方向 A                                  |
| 三源 EMPTY 静默 PASS / 阶段后置        | §3.4 · 用户 rev4 禁令                           |
| 宣称生产就绪                           | MCR 仅 sandbox R4                               |
| 单次 live run 当幂等                   | 必须两次对比                                    |
| Tier B 工作量低估                      | 每源需 dispatch；镜像 A 模式，勿抄 Wave3 大杂烩 |

---

## 14. 会话历史

完整对话（含 Audit/Repair/grill-me）：  
`C:\Users\Guang\.cursor\projects\c-Users-Guang-Desktop-quant-monitor-desk/agent-transcripts/963e3d3f-6d9b-4824-8cc3-5fe3f1afe008/963e3d3f-6d9b-4824-8cc3-5fe3f1afe008.jsonl`

---

_End of handoff — **rev 4.8** · finish-work 2026-07-04 · 本地沙箱 only · GitHub live workflow 已删 · 7/7 AC。_
