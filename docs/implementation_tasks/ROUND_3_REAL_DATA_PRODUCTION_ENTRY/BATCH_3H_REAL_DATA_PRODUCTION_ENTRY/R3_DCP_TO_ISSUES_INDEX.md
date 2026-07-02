# Wave 3–4 — R3-DCP `/to-issues` 任务卡索引

> **格式：** `/to-issues` · tracer-bullet 垂直切片  
> **波次：** `R3H_PASS_EXECUTION_PLAN.md` §3 Wave 3（§1–§4）· **Wave 4**（§6）  
> **并行：** **DCP-01（baostock）∥ DCP-02（fred）**；DCP-03 依赖 01/02 至少一轨  
> **协议：** **debt-lite**（Phase 8D slice plan + 用户 Plan 增强：调研 L1/L2/L3 先行）  
> **状态：** Wave 3 **CLOSED** @ 2026-06-30 · Wave 4 **`R3-DCP-05` CLOSED** @ `c2258363` · 下一入口 **`R3-DCP-06..10`**

---

## 0. Wave 级门控

| 项            | 内容                                                                  |
| ------------- | --------------------------------------------------------------------- |
| **Wave 目标** | **baostock + fred** 走通「读库水位 → 只拉新增 → 写库 → 抽检」产品路径 |
| **前置**      | R3H-10 · R3H-07 · R3H-08 · R3H-06 CLOSED ✅                           |
| **Trellis**   | 双轨 debt-lite：`wave3-r3-dcp-01-baostock` · `wave3-r3-dcp-02-fred`   |
| **活卡**      | `R3_DCP_01_BAOSTOCK_INCREMENTAL.md` · `R3_DCP_02_FRED_INCREMENTAL.md` |
| **协调目录**  | `_tmp-wave3-dcp-parallel/`                                            |
| **下游**      | Wave 4 R3-DCP-05..10（Tier A 扩展 + 五轴）                            |

---

## 1. R3-DCP-01 · baostock 增量水位 + CLI

**规划 ID：** R3-DCP-01  
**Module：** D1 Sync orchestration · E1 `qmd data` CLI  
**状态：** ✅ **CLOSED** @ 2026-06-30 · merge `5dc71c0b`  
**分支：** `feature/wave3-r3-dcp-01-baostock`  
**Worktree：** `../quant-monitor-desk-wt-dcp01`

### What to build

从 clean 表读 `max(trade_date)` 作为 watermark，经 `DataSourceService` 金路径只拉新增 CN 日频 bar，经 `IncrementalJobRunner` 写隔离库；`qmd data sync`（或等价子命令）可重复跑且幂等。

### Acceptance criteria

- [x] 读库算窗：`date_start = max(trade_date)+1`（或契约等价）有单测
- [x] baostock 增量经 `datasource_service` + orchestrator，无 adapter bypass
- [x] 默认写 **隔离** `QMD_DATA_ROOT`（非 canonical 主库）
- [x] CLI dry-run / 真跑路径各有契约或 smoke 测
- [x] `research/*-reference-adoption.md` 标注 L1/L2/L3
- [x] `uv run pytest -q` 全绿（本轨相关 + 全库）

### Blocked by

Wave 2 CLOSED ✅ · R3H-06 clean schema ✅

### Vertical slices

| Slice              | AC                                 | 验证              |
| ------------------ | ---------------------------------- | ----------------- |
| P1 调研 + Plan     | L1/L2/L3 借鉴报告 + `DEBT.plan.md` | 主会话 Plan 闸门  |
| P2 Plan-Audit      | 对抗审计 0 遗留                    | Plan 修复复验     |
| P3 watermark       | 读 clean max(trade_date)           | unit test         |
| P4 incremental run | service + orchestrator 端到端      | integration test  |
| P5 CLI             | `qmd data` 子命令可演示            | CLI contract test |
| P6 Audit + Repair  | A1–A8 + ledger 关账                | pytest 全绿       |

**活卡 SSOT：** `R3_DCP_01_BAOSTOCK_INCREMENTAL.md`

---

## 2. R3-DCP-02 · fred 宏观序列增量

**规划 ID：** R3-DCP-02  
**Module：** D1 · E1  
**状态：** ✅ **CLOSED** @ 2026-06-30 · merge `5d8d7b0f`  
**分支：** `feature/wave3-r3-dcp-02-fred`  
**Worktree：** `../quant-monitor-desk-wt-dcp02`

### What to build

fred 宏观序列：读库水位 → 只拉新增观测 → 写 macro clean 域；与 baostock 共享 orchestration 契约但 **fred adapter/port 归本轨**。

### Acceptance criteria

- [x] fred watermark 与序列 ID 绑定（非仅 trade_date 若契约要求 observation_date）
- [x] env-gated live（`FRED_API_KEY`）+ replay 双路径
- [x] 隔离库写；无 silent canonical 主库
- [x] L1/L2/L3 调研报告齐
- [x] `uv run pytest -q` 全绿

### Blocked by

同 DCP-01

### Vertical slices

同 DCP-01 结构；实现域为 `fred_port` + macro clean 表。

**活卡 SSOT：** `R3_DCP_02_FRED_INCREMENTAL.md`

---

## 3. R3-DCP-03 · 写后抽检（E2 + F0）

**规划 ID：** R3-DCP-03  
**Module：** E2 DB inspect · F0 health profile  
**状态：** ✅ **CLOSED** @ 2026-06-30 · merge `eff49343`  
**Trellis：** 归档 `06-30-wave3-r3-dcp-03-post-write-inspect`  
**活卡 SSOT：** `R3_DCP_03_POST_WRITE_INSPECT.md`  
**依赖：** DCP-01 **与** DCP-02 均已 CLOSED ✅  
**分支：** `feature/wave3-r3-dcp-03-post-write-inspect`（已 merge master）

### What to build

写后 `row count` / `max(trade_date)` / health profile smoke；`qmd db-inspect` 或等价 E2 路径绿。

### Acceptance criteria

- [x] 增量写后可断言行数不重复膨胀（幂等）— `DbInspector` 视角
- [x] inspect smoke 对 baostock 表 + `market_bar_p0` profile
- [x] `qmd_ops db-inspect` JSON smoke 绿
- [x] Plan：`reference-adoption-dcp03.md` + `DEBT.plan.md`
- [x] Audit + Repair 关账 → Wave 3 **CLOSED**

---

## 4. Wave 3 Checklist（主会话）

```text
[x] _tmp-wave3-dcp-parallel/ 协调目录 + agent-prompts
[x] 双 worktree 就绪
[x] 各轨 task.py create（debt-lite）
[x] P1 双轨 Plan agent 并行派发
[x] P2 Plan-Audit → P3 Plan-Repair（全修完）
[x] P4 Execute（必读调研 + 源码）
[x] P5 Audit A1–A8 各一 agent
[x] P6 A9 + Repair + pytest 全绿
[x] P7 主会话 registry 排队 merge
[x] 更新 R3H_PASS_EXECUTION_PLAN §3.1 Wave 3 状态（**CLOSED** @ 2026-06-30）
[x] R3-DCP-03 写后抽检 — merge `eff49343` · Audit/Repair PASS
```

**Wave 3 Done：** DCP-01/02/03 全闭合。**Wave 4 DCP-05 Done：** @ `c2258363` · 下一协调入口 **`R3-DCP-06`**（五轴 G12）。

---

## 6. Wave 4 开放项（live 验收承接 · 2026-07-02）

> **状态：** **`R3-DCP-05` ✅ CLOSED** @ `c2258363` · **`R3-DCP-06..10` 🔴 OPEN** · 见 `PROJECT_IMPLEMENTATION_ROADMAP.md` §3.5.2 · `待修复清单.md` §4 / §8  
> **Wave 4 prep 前置（2026-07-01）：** ~~`LIVE-PILOT-DB-001` · `LIVE-BAOSTOCK-SYNC-SILENT-001`~~ **已关** — `待修复清单.md` §1 · `RESOLVED_ISSUES_REGISTRY.md` §Wave 4 prep blockers resolved

### 6.1 R3-DCP-05 · Tier A 真网增量扩展 — **✅ CLOSED** @ `c2258363`

**承接台账：** `ACC-BAOSTOCK-NO-LIVE` ✅ · `ACC-EASTMONEY-TAXONOMY-001` 部分（§4 仍 open）

- [x] `data_commands.sync_baostock_incremental`：`QMD_ALLOW_LIVE_FETCH=1` 时 `use_mock=False`（产品 live port）
- [x] 隔离库 `qmd data sync --no-dry-run` baostock 真网路径（sandbox + fail-closed；replay e2e 绿）
- [x] 其余 Tier A 主源 watermark 增量 + 11/11 clean upsert e2e（ADR-028 · migration 015）
- [x] `qmd data sync --source-id` 11 源 dry-run 可审计（S12 `tier_a_sync_router`）
- [ ] CN validation 口径：产品 `eastmoney_port` mock vs akshare `stock_zh_a_hist` 真网 — **DCP-05 S13 registry notes 已交付**；REQ2 硬约束仍 `R3-DCP-08` / Batch 6

### 6.2 R3-DCP-06 · 五轴全绿 + L1 子集（L3–L5 阶段外置）

**承接台账：** `ACC-LAYER-E2E-LIVE-001`

- [x] §3.5.1 五轴清单 **全部 [x]**（Tier A clean replay e2e）
- [x] **L1 子集：** 五轴 clean → feature → interpretation 非 `staged_fixture_only`（DCP-06 S07 repair）
- [ ] **L3–L5 全链：** 真网 → clean → L3 快照 → L4 结构 → L5 证据 — **阶段外置** → DCP-07/08/10 + Wave 5 `R3H-05-GATE`
- [ ] 下游 Wave 5 `R3H-05-GATE` 审计门（全链 PASS）

### 6.3 R3-DCP-09 · 有界 backfill + 连网 CI

**承接台账：** `WAVE3-ACC-OPT-01` · `ACC-LIVE-NETWORK-CI-001` · `ACC-LIVE-ACCEPT-NIGHTLY-001`

- [ ] `wave3_isolated_production_acceptance.py` `--quick` 或 nightly-only 全量
- [ ] CI nightly：`pytest --run-network` batch275 phase3 子集
- [ ] CI nightly：`scripts/wave3_live_production_acceptance.py` + findings 硬门禁

### 6.4 其余 Wave 4 活卡（路线图 §3.5.1）

- [ ] **R3-DCP-07** — cross-asset 传感器绑真市况源
- [ ] **R3-DCP-08** — 市场结构 + US 日历
- [ ] **R3-DCP-10** — G5 source_fetch_id / content_hash / schema_hash 绑真源

### 6.5 Wave 5 / Batch 6（live 验收登记 · 不挡 Wave 4 开工）

| 阶段                               | 承接项                                | 台账                            |
| ---------------------------------- | ------------------------------------- | ------------------------------- |
| Wave 5 `R3F-SH-06` / `R3H-05-GATE` | FRED live primary 关账                | `B2.5-O-05` §3                  |
| Batch 6 `R3F-LIN-01/02`            | L3/L4 lineage · L2 VR                 | §2 `ADV-R3X` · `R3Y-LINEAGE-VR` |
| Batch 6 `R3F-SH-07`                | akshare live hist（REQ2-EM 余量）     | `R3-PROMPT14-AKSHARE-VAL-01` §3 |
| 政策                               | akshare macro pilot `DISABLED_SOURCE` | `AKSHARE-MACRO-PILOT-POLICY` §3 |

---

## 7. 参考上游（Plan 必读追溯）

| 主题                     | 路径                                                                     |
| ------------------------ | ------------------------------------------------------------------------ |
| Sync orchestrator        | `docs/modules/data_sync_orchestrator.md` §13.4.2                         |
| DataSourceService 金路径 | R3H-10 归档 `EXECUTION_INDEX.md`                                         |
| baostock port            | `backend/app/datasources/fetch_ports/baostock_port.py`                   |
| fred port                | `backend/app/datasources/fetch_ports/fred_port.py`                       |
| R3G watermark 先例       | `.trellis/tasks/archive/2026-06/06-27-round3g-limited-production-write/` |
| 项目地图                 | `docs/generated/project_map.generated.md`                                |
