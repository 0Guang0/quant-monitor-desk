# Wave 3–4 — R3-DCP `/to-issues` 任务卡索引

> **格式：** `/to-issues` · tracer-bullet 垂直切片  
> **波次：** `R3H_PASS_EXECUTION_PLAN.md` §3 Wave 3（本 INDEX 先覆盖 3a–3c）  
> **并行：** **DCP-01（baostock）∥ DCP-02（fred）**；DCP-03 依赖 01/02 至少一轨  
> **协议：** **debt-lite**（Phase 8D slice plan + 用户 Plan 增强：调研 L1/L2/L3 先行）  
> **状态：** OPEN @ 2026-06-30 · 前置 Wave 1–2 **CLOSED**

---

## 0. Wave 级门控

| 项 | 内容 |
| --- | --- |
| **Wave 目标** | **baostock + fred** 走通「读库水位 → 只拉新增 → 写库 → 抽检」产品路径 |
| **前置** | R3H-10 · R3H-07 · R3H-08 · R3H-06 CLOSED ✅ |
| **Trellis** | 双轨 debt-lite：`wave3-r3-dcp-01-baostock` · `wave3-r3-dcp-02-fred` |
| **活卡** | `R3_DCP_01_BAOSTOCK_INCREMENTAL.md` · `R3_DCP_02_FRED_INCREMENTAL.md` |
| **协调目录** | `_tmp-wave3-dcp-parallel/` |
| **下游** | Wave 4 R3-DCP-05..10（Tier A 扩展 + 五轴） |

---

## 1. R3-DCP-01 · baostock 增量水位 + CLI

**规划 ID：** R3-DCP-01  
**Module：** D1 Sync orchestration · E1 `qmd data` CLI  
**分支：** `feature/wave3-r3-dcp-01-baostock`  
**Worktree：** `../quant-monitor-desk-wt-dcp01`

### What to build

从 clean 表读 `max(trade_date)` 作为 watermark，经 `DataSourceService` 金路径只拉新增 CN 日频 bar，经 `IncrementalJobRunner` 写隔离库；`qmd data sync`（或等价子命令）可重复跑且幂等。

### Acceptance criteria

- [ ] 读库算窗：`date_start = max(trade_date)+1`（或契约等价）有单测
- [ ] baostock 增量经 `datasource_service` + orchestrator，无 adapter bypass
- [ ] 默认写 **隔离** `QMD_DATA_ROOT`（非 canonical 主库）
- [ ] CLI dry-run / 真跑路径各有契约或 smoke 测
- [ ] `research/*-reference-adoption.md` 标注 L1/L2/L3
- [ ] `uv run pytest -q` 全绿（本轨相关 + 全库）

### Blocked by

Wave 2 CLOSED ✅ · R3H-06 clean schema ✅

### Vertical slices

| Slice | AC | 验证 |
| ----- | --- | ---- |
| P1 调研 + Plan | L1/L2/L3 借鉴报告 + `DEBT.plan.md` | 主会话 Plan 闸门 |
| P2 Plan-Audit | 对抗审计 0 遗留 | Plan 修复复验 |
| P3 watermark | 读 clean max(trade_date) | unit test |
| P4 incremental run | service + orchestrator 端到端 | integration test |
| P5 CLI | `qmd data` 子命令可演示 | CLI contract test |
| P6 Audit + Repair | A1–A8 + ledger 关账 | pytest 全绿 |

**活卡 SSOT：** `R3_DCP_01_BAOSTOCK_INCREMENTAL.md`

---

## 2. R3-DCP-02 · fred 宏观序列增量

**规划 ID：** R3-DCP-02  
**Module：** D1 · E1  
**分支：** `feature/wave3-r3-dcp-02-fred`  
**Worktree：** `../quant-monitor-desk-wt-dcp02`

### What to build

fred 宏观序列：读库水位 → 只拉新增观测 → 写 macro clean 域；与 baostock 共享 orchestration 契约但 **fred adapter/port 归本轨**。

### Acceptance criteria

- [ ] fred watermark 与序列 ID 绑定（非仅 trade_date 若契约要求 observation_date）
- [ ] env-gated live（`FRED_API_KEY`）+ replay 双路径
- [ ] 隔离库写；无 silent canonical 主库
- [ ] L1/L2/L3 调研报告齐
- [ ] `uv run pytest -q` 全绿

### Blocked by

同 DCP-01

### Vertical slices

同 DCP-01 结构；实现域为 `fred_port` + macro clean 表。

**活卡 SSOT：** `R3_DCP_02_FRED_INCREMENTAL.md`

---

## 3. R3-DCP-03 · 写后抽检（E2 + F0）

**规划 ID：** R3-DCP-03  
**Module：** E2 DB inspect · F0 health profile  
**依赖：** DCP-01 **或** DCP-02 至少一轨 Audit PASS  
**挂载策略：** 主会话在较快轨完成后决定（第三短轨或挂快轨）

### What to build

写后 `row count` / `max(trade_date)` / health profile smoke；`qmd db-inspect` 或等价 E2 路径绿。

### Acceptance criteria

- [ ] 增量写后可断言行数不重复膨胀（幂等）
- [ ] inspect smoke 对 baostock **或** fred 表有 profile
- [ ] 不阻塞 DCP-01/02 并行开工

---

## 4. Wave 3 Checklist（主会话）

```text
[ ] _tmp-wave3-dcp-parallel/ 协调目录 + agent-prompts
[ ] 双 worktree 就绪
[ ] 各轨 task.py create（debt-lite）
[ ] P1 双轨 Plan agent 并行派发
[ ] P2 Plan-Audit → P3 Plan-Repair（全修完）
[ ] P4 Execute（必读调研 + 源码）
[ ] P5 Audit A1–A8 各一 agent
[ ] P6 A9 + Repair + pytest 全绿
[ ] P7 主会话 registry 排队 merge
[ ] 更新 R3H_PASS_EXECUTION_PLAN §3.1 Wave 3 状态
```

---

## 5. 参考上游（Plan 必读追溯）

| 主题 | 路径 |
| ---- | ---- |
| Sync orchestrator | `docs/modules/data_sync_orchestrator.md` §13.4.2 |
| DataSourceService 金路径 | R3H-10 归档 `EXECUTION_INDEX.md` |
| baostock port | `backend/app/datasources/fetch_ports/baostock_port.py` |
| fred port | `backend/app/datasources/fetch_ports/fred_port.py` |
| R3G watermark 先例 | `.trellis/tasks/archive/2026-06/06-27-round3g-limited-production-write/` |
| 项目地图 | `docs/generated/project_map.generated.md` |
