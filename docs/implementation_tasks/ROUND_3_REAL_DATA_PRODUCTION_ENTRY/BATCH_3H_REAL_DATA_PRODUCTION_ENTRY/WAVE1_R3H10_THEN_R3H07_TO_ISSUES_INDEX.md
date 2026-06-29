# Wave 1 — R3H-10 → R3H-07 `/to-issues` 任务卡骨架（串行硬门禁）

> **格式：** `/to-issues` · tracer-bullet 垂直切片（非按层横切）  
> **波次定位：** `PROJECT_IMPLEMENTATION_ROADMAP.md` §3.2–§3.3 · `R3H_PASS_EXECUTION_PLAN.md` §3 Wave 1  
> **执行纪律：** **单主会话默认串行** — **必须先 CLOSED `R3H-10`，再开工 `R3H-07`**；禁止 Wave 1 内并行两轨（多 agent 须主会话显式批准）。  
> **模块轨：** 一轨一主 Module ID 评级一跳 — `R3H-10` → **C2**（+E4）`R3→R4`；`R3H-07` → **G4**（+C3 日历语义）`R3→R4`。  
> **状态：** Wave 1 **OPEN** @ 2026-06-29

---

## 0. Wave 级门控

| 项                   | 内容                                                                                                          |
| -------------------- | ------------------------------------------------------------------------------------------------------------- |
| **Wave 目标**        | DataSourceService 产品唯一入口；US 交易日历 L2 闭合 CAL-US                                                    |
| **串行顺序（写死）** | **`R3H-10` CLOSED** → 才允许 **`R3H-07` Plan/Execute**                                                        |
| **并行**             | **默认禁止** Wave 1 内 10∥07；Wave 2+ 另见 PASS 计划                                                          |
| **Wave Done**        | 两轨 Trellis Audit PASS + 全量 `uv run pytest -q` 绿 + `MODULE_COMPLETION_RATING` C2/G4 行可更新              |
| **下游**             | Wave 2 `R3H-08A–D`（24 源 live 产品化）                                                                       |
| **Trellis**          | R3H-10：**complex**；R3H-07：**complex**                                                                      |
| **活卡**             | `R3H_10_DATASOURCE_SERVICE_SSOT.md` · `R3H_07_US_TRADING_CALENDAR.md`                                         |
| **Trellis 切片**     | `.trellis/tasks/06-29-round3h-r3h10-datasource-service-ssot/research/00-EXECUTION-ENTRY.md`（Execute 总入口） |

### 0.1 为何必须先 10 后 07

```text
R3H-08 全源 live 产品化要求：Sync / CLI / 探针 一律经 DataSourceService
R3H-07 美股日历最终体现在：拉数窗口 + Layer4 市场结构
若 07 先做而 10 仍双轨 → 08 会重复改入口，陷入平铺微切片
```

---

## 1. R3H-10 · DataSourceService SSOT（`C2` + `E4`）

**规划 ID：** `R3H-10`  
**Module ID：** **C2**（主）· **E4**（staged/pilot 收敛）  
**评级移动：** `R3_STAGED_FIXTURE_CLOSED` → **`R4_SANDBOX_REAL_DATA_OR_REHEARSAL`**（产品路径 SSOT；非 R6）  
**闭合登记：** `STAGED-PILOT-SSOT` · `PROJECT_IMPLEMENTATION_ROADMAP.md` §5.0.1  
**Graph 节点：** `datasources` · `ops`（协调 merge，单轨拥有 C2 实现）

### What to build

生产拉数、route preview、sync plan、live/staged rehearsal **统一经 `DataSourceService`**；消除 sync/orchestrator、live pilot、interface probe 等对 fetch port 的 **绕过主路径**；`staged_pilot` / `--live-wire` 仅保留 **rehearsal** 语义，不得作为 Round4 前「产品 live」替身。

### Acceptance criteria

- [x] `STAGED-PILOT-SSOT` = **CLOSED**（registry / UNRESOLVED 无矛盾）
- [x] Sync orchestrator 金路径 fetch **仅** 经 `DataSourceService`（负向：直接 adapter 调用 RED；reconcile `adapter=` defer ADR-025）
- [x] `qmd data` route-preview / sync-plan **仅** 经 service boundary（`E1` 对齐）
- [x] Live pilot / interface probe：**rehearsal-only** 或显式委托 service；产品 live 留给 `R3H-08`
- [x] `tests/test_datasource_service.py` + 新增 bypass 负向测 **GREEN**
- [x] **禁止** 无测试证明即删 pilot 模块；**禁止** Round4 前用 pilot 脚本冒充 08 产品路径

### Blocked by

- **R3H-06** CLOSED ✅（schema / upsert）
- **Batch 3V** CLOSED ✅

### Vertical slices（SSOT）

Execute 入口：`.trellis/tasks/06-29-round3h-r3h10-datasource-service-ssot/research/00-EXECUTION-ENTRY.md`  
切片正文：`…/research/to-issues-slices.md`

### GitHub issue 骨架（整卡 1 票 · 推荐）

```markdown
## [R3H-10] DataSourceService SSOT — C2 R3→R4

**What to build:** 一张票闭合 STAGED-PILOT-SSOT：Sync、qmd data CLI、rehearsal 脚本全部经 DataSourceService；产品 live 双轨消除；bypass 负向测绿。

**Acceptance criteria:**

- [ ] S10-01..05 切片 RED→GREEN 证据齐全
- [ ] `tests/test_datasource_service.py` 与 bypass 测绿
- [ ] pilot/live 路径文档标明 rehearsal-only
- [ ] MODULE_COMPLETION_RATING **C2** 可更新为 R4 证据路径

**Blocked by:** R3H-06 CLOSED

**Out of scope:** R3H-08 真网 live；registry 主会话 CLOSED（本票只交 proposed delta）
```

---

## 2. R3H-07 · US Trading Calendar L2（`G4` + `C3`）

**规划 ID：** `R3H-07`  
**Module ID：** **G4**（主）· **C3**（US 源拉数窗语义）  
**评级移动：** `R3_STAGED_FIXTURE_CLOSED` → **`R4_SANDBOX_REAL_DATA_OR_REHEARSAL`**  
**闭合登记：** `CAL-US` · `R3H-02` 追溯余量  
**Graph 节点：** `layer4_markets` · `datasources`（日历语义）

### What to build

为 **US/全球股市源**（`yahoo_finance`、`stooq`、`alpha_vantage` 等）建立 **交易日历 SSOT（L2）**；拉数窗口使用 **trading sessions**，不再默认自然日 `calendar_days`；Layer4 `market_structure` 对 US 市场使用同一日历权威。

### Acceptance criteria

- [ ] `CAL-US` = **CLOSED**
- [ ] US 源 window_kind / orchestrator 计划使用交易日历（非纯自然日）
- [ ] `tests/test_layer4_market_structure.py` + 日历专项测 **GREEN**
- [ ] CN 日历（R3H-03 Q12）**不被破坏**
- [ ] **禁止** 全市场万年历无 cap 扫描；**禁止** 与 R3H-06 DDL 冲突（本轨 **无新 migration**，除非 debt-lite ADR）

### Blocked by

- **`R3H-10` CLOSED**（硬门禁 — 日历窗口经 service 暴露）

### Vertical slices

| 序  | ID        | 垂直切片         | 交付物                              | 依赖      | Step                |
| --- | --------- | ---------------- | ----------------------------------- | --------- | ------------------- |
| 0   | S07-BOOT  | 基线 CAL-US 缺口 | 列出现状自然日窗源 + 测试 RED       | S10-CLOSE | `9.0-red.txt`       |
| 1   | S07-01    | 日历 SSOT 数据面 | US trading calendar 行集（有界）    | BOOT      | `9.1-red/green.txt` |
| 2   | S07-02    | C3 拉数窗接线    | market 源 fetch plan 用 trading day | S07-01    | `9.2-red/green.txt` |
| 3   | S07-03    | G4 loader 绑定   | layer4 非交易日拒绝 / 交易日通过    | S07-01    | `9.3-red/green.txt` |
| 4   | S07-04    | 负向：假日不拉   | 美股假日窗 RED→GREEN                | S07-02,03 | `9.4-red/green.txt` |
| 5   | S07-CLOSE | 审计 + registry  | `CAL-US` CLOSED；G4 `R3→R4`         | S07-04    | Audit PASS          |

### GitHub issue 骨架

```markdown
## [R3H-07] US Trading Calendar L2 — G4 R3→R4

**What to build:** 闭合 CAL-US：US 源与 Layer4 使用统一交易日历；自然日窗消除；假日负向测绿。

**Acceptance criteria:**

- [ ] S07-01..04 切片证据齐全
- [ ] yahoo/stooq/alpha_vantage 窗口语义经 service 可验证
- [ ] CN `cn_trading_calendar` 回归绿

**Blocked by:** R3H-10 CLOSED

**Out of scope:** R3H-08 live 产品化；新 clean DDL
```

---

## 3. Wave 1 协调 Checklist（主会话）

```text
[ ] 本 INDEX + PASS 计划 §3 Wave 1 已 commit
[x] 开工 R3H-10：Trellis Plan 冻结 validate-plan-freeze exit 0
[x] R3H-10 Execute：S10-BOOT..CLOSE 逐切片 RED→GREEN
[x] R3H-10 Audit PASS → merge master → 更新 C2/E4 rating 证据（audit.report.md @ 2026-06-29）
[x] 显式门控：R3H-10 CLOSED 证据落盘 — 允许 R3H-07 Plan/Execute
[ ] 开工 R3H-07：blocked-by R3H-10 写入 Plan
[ ] R3H-07 Execute → Audit PASS → merge
[ ] Wave 1 Done：记入 R3H_PASS_EXECUTION_PLAN §3 状态表
[ ] 下游：Wave 2 建议串行 08C→08A→08B→08D（单 agent）或 4 worktree（多 agent）
```

---

## 4. 与模块轨道 / PASS 路径关系

```text
[✅] 历史：3V · R3H-01～04 · R3H-06
  ↓
Wave 1（本文）R3H-10 → R3H-07 串行
  ↓
Wave 2  R3H-08A–D
  ↓
Wave 3  R3-DCP-01..03（baostock+fred 增量）
  ↓
Wave 4  R3-DCP-05..10（五轴全绿 PASS 硬门禁）
  ↓
Wave 5  R3H-05 + GATE
  ↓
Round4  B04-01
```

**Wave 1 明确不做：** 24 源 env-gated live（Wave 2）；增量 watermark（Wave 3）；五轴 G12（Wave 4）；`web_search` 真 API。

---

## 5. 粒度 quiz（2026-06-29 裁决）

| 项                | 裁决                               |
| ----------------- | ---------------------------------- |
| Wave 1 并行 10∥07 | **否** — 单主会话 **串行**         |
| R3H-10 issue 数   | **1 票**（S10-01..05 为票内 Step） |
| R3H-07 issue 数   | **1 票**（blocked by R3H-10）      |
| 下一执行入口      | **`R3H-10` only** until CLOSED     |
