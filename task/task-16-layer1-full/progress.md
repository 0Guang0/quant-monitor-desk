# task-02-layer1-full · Progress（活文档）

> **更新：** 2026-07-10 晚 · **§7 迁入** · F-01/F-03 **复核重开**  
> **P1-GATE：** **未绿** — F-01 · F-03 · F-06–F-09 · F-13–F-16 · **F-18–F-23**（见 `findings.md` §1 · §7）  
> **硬前置：** 🟢 **task-01.5 已绿，可开工 Slice 0-N**（2026-07-10 · [`task-01.5-task-02phase1前置阻塞`](task-01.5-task-02phase1前置阻塞/task_plan.md) Phase F ✅）  
> **Phase 2（62 指标）：** **未开工**（P1-GATE 阻塞）

---

## 1. 总览

| 维度 | 状态 | 说明 |
|------|------|------|
| 四条命令 source-route-db 接缝 | 🟢 已接入 | `data_commands` → `source_route_db_cli_acceptance.py`（**待 Slice 0-N 正名**） |
| 验收信封形状统一 | 🟢 | F-04 · `data_cli_contract.yaml` |
| baostock 本机真网全链 | 🟢 | F-10 · sync 21 行 + 完整 observability |
| backfill / full-load 真网（baostock） | 🟢 | 无 crash；PASS（幂等时 rows_written 可为 0） |
| scheduler `weekly_backfill` | 🟢 | live backfill child 可 PASS |
| scheduler `daily_close` 整单 | 🔴 | fred + revision_audit 拉红（诚实 FAIL） |
| fred scheduler 路径 | 🔴 | F-07 · F-14 · binding 路径 DISABLED_SOURCE |
| macro_series 域策略 | 🟡 | F-15 · **决议 A** · 待 Slice 1-P 改 registry |
| 运营启用清单 SSOT | 🔴 | F-16 · 待 Slice 1-E |
| revision_audit / data_quality | 🔴 | F-08/F-09 · minimal stub |
| `uv run pytest -q` | 🟢 | 复验日全绿（含 phase1 acceptance 子集） |

图例：🟢 达标 / 🔴 阻塞 P1-GATE / 🟡 部分

---

## 2. 切片进度

| 切片 | 状态 | 证据 |
|------|------|------|
| P1-CLI-WIRING · fetch_port 正式接线 | 🔴 复核重开 | F-01 · task-01.5 FIND-B-01 迁入 §7 |
| P1-ENVELOPE · 四命令验收信封 | ✅ 完成 | `test_qmd_data_*_acceptance.py` · `test_data_cli_contract.py` · F-04 本机复验 |
| P1-OBS · observability 回填 | 🔴 复核重开 | F-03 · task-01.5 FIND-B-02 迁入 §7 |
| P1-LIVE-HONESTY · live/replay 政策 | ✅ 完成 | ADR-015/016 · `test_matrix_live_evidence_honesty.py` |
| P1-BAOSTOCK-LIVE · 本机真网 | ✅ 完成 | F-10 · 2026-07-09 无 replay patch 跑通 |
| P1-SCHED-WEEKLY · weekly_backfill live | ✅ 完成 | `test_sync_scheduler_acceptance.py` · 本机 child backfill |
| P1-NAMING · 接缝模块正名 | ⏳ 待做 | Slice 0-N · `phase1_acceptance` → `source_route_db_cli_acceptance` |
| P1-ENABLE-LEDGER · Tier A 按源启用台账 | ⏳ 待做 | Slice 1-E · F-16 |
| P1-MACRO-LIVE · macro_series 域落地 | ⏳ 待做 | Slice 1-P · F-15 · **OQ-P1-Q6=A 已决** |
| P1-SCHED-FRED · daily_close fred | ⏳ 待做 | F-07 · F-14 · 依赖 0-N |
| P1-SCHED-2a0 · quality child 小票接线 | ⏳ 待做 | 共用 seam |
| P1-SCHED-R1 · revision_audit 接缝 | ⏳ 待做 | F-08 · macro/fred |
| P1-SCHED-R2 · revision diff + log 表+ndjson | ⏳ 待做 | F-08 · AD-9 双写 P1 必做 |
| P1-SCHED-R3 · revision → BackfillJob | ⏳ 待做 | F-08 · 设计 §13.4.4-5 |
| P1-SCHED-R4 · 标记 feature/snapshot 重算 | ⏳ 待做 | F-08 · 设计 §13.4.4-6 · **新增** |
| P1-SCHED-DQ · data_quality baostock | ⏳ 待做 | F-09 · daily_close 必含 |
| P1-GATE-CLOSE · pytest 全绿 + ledger | ⏳ 待做 | 依赖上两项决策 |

---

## 3. 八步金路径（产品视角）

```text
① 选路 → ② 真网抓取 → ③ 原始+fetch_log → ④ staging
→ ⑤ 质检 → ⑥ 冲突检查 → ⑦ 写 clean → ⑧ 验收小票+下游读
```

| 环节 | 机制 | baostock 本机 | scheduler daily_close | 备注 |
|------|------|---------------|----------------------|------|
| ①–⑧ | 有 | sync 全填 | baostock child ✅ | 隔离验收库，非主库 |
| ①–⑧ | 有 | backfill/full-load ✅ | fred child ❌ F-07 | |
| 审计类 job | stub | — | revision_audit ❌ F-08 | 非 ①–⑧ 成品 |

---

## 4. 与 M-DATA-03 / 多源关系

- **不是「只做了 baostock」**：M-DATA-03 @ 2026-07-04 已关；22 源矩阵、Tier A 适配器在 **隔离库** 有 live/replay 证据（`findings.md` F-12）。
- **Phase 1 正式四命令金路径**：当前 **baostock 本机验证最完整**；fred 单命令 sync 可走矩阵路径（须 `FRED_API_KEY`），scheduler 仍缝（F-07）。

---

## 5. 下一步（建议顺序）

1. **实现：** Slice 0-N → **1-E ∥ 1-P ∥ 2a-0** → Slice 1 → 2a-R1→R2→R3 ∥ 2a-Q（见 `task_plan.md` AD-6/7/10/11）
2. **复验：** Slice 3 `daily_close` 四 job 整 profile（宏观语义依赖 1-P）
3. **关账：** Slice 4 · ledger + pytest

---

## 6. 变更日志

| 日期 | 变更 |
|------|------|
| 2026-07-10 | **task-01.5 §9.2 迁入 §7**：F-01/F-03 复核重开；F-18–F-23 新建；AUD-DOUBT-12 本票关账 |
| 2026-07-10 | **task-01.5 已绿**：前置阻塞票 Phase F 关账；可开工 Slice 0-N |
| 2026-07-09 | 初版：合并过期 Findings.txt 结论；录入 F-04–F-13 复验；标 P1-GATE 未绿 |
| 2026-07-09 | OQ 关闭：data_quality=baostock；revision_audit=P1 修订 diff；拆 2a-0/R1/R2/R3/Q |
| 2026-07-09 | findings §6 路由/启用：增 Slice 1-E/1-P · AD-10/11 · F-14–F-16 入 P1-GATE 阻塞项 |
| 2026-07-09 | **OQ-P1-Q6 = A**：macro_series 纳入 daily_close production-live（AD-11） |
| 2026-07-09 | **AC-CLOSE**：每切片 AC 增回读对齐 + `note.md` 计划外记账（§每切片关账 AC） |
