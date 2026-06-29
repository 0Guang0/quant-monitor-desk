# R3H-07 执行入口 — 路由地图（Execute SSOT）

> **角色：** 本任务 **唯一 Execute 读入口**  
> **任务目录：** `.trellis/tasks/06-29-round3h-r3h07-us-trading-calendar/`  
> **活卡：** `EXTERNAL-INDEX.md` → `R3H_07_US_TRADING_CALENDAR.md`  
> **协议：** Plan v4.1

---

## 1. 任务目的 · 价值 · 完成条件

| 维度         | 内容                                                             |
| ------------ | ---------------------------------------------------------------- |
| **目的**     | 闭合 **CAL-US**：US 源 + Layer4 使用 **交易日历** SSOT           |
| **价值**     | C3 拉数窗与 G4 市场结构共用权威；消除自然日 `calendar_days` 窗   |
| **评级**     | `R3_STAGED_FIXTURE_CLOSED` → `R4_SANDBOX_REAL_DATA_OR_REHEARSAL` |
| **完成条件** | S07-BOOT..CLOSE 全绿 · `CAL-US` CLOSED · 全量 pytest · CN 回归绿 |
| **不在范围** | R3H-08 live · 新 migration · crypto `calendar_days`              |

**前置：** R3H-10 CLOSED @ `227e0734`（C2 金路径）

---

## 2. 约束 · 规则 · Wave 承接

| 类别         | 约束                             | 详述                            |
| ------------ | -------------------------------- | ------------------------------- |
| **ADR**      | US 日历 SSOT                     | **ADR-026**                     |
| **ADR**      | Sync fail-closed                 | **ADR-025**（R3H-10；本卡不改） |
| **CN**       | `cn_trading_calendar` 不得回退   | R3H-03 Q12                      |
| **SSOT**     | 假日仅 `us_trading_calendar.py`  | `to-issues-slices.md`           |
| **禁止**     | 万年历无 cap · per-source 假日表 | INDEX §2                        |
| **GitNexus** | 改 ports/layer4 前 `impact`      | `AGENTS.md`                     |

### Wave 2 承接表（R3H-10 阶段外置 · 本卡不 silent bypass）

| 项                                                | 绑定          | 说明                            |
| ------------------------------------------------- | ------------- | ------------------------------- |
| `run_reconcile` + `datasource_service=` 金路径    | **R3H-08A–D** | ADR-025 §Reconcile defer        |
| `interface_probe.build_route_matrix` 不经 service | **R3H-08C**   | probe/CLI 路由统一              |
| 双 guard 合并                                     | tech-debt     | adapter vs service 语义分离保留 |

台账：`.trellis/tasks/archive/2026-06/06-29-round3h-r3h10-datasource-service-ssot/research/audit-repair-ledger.md` §Wave 2

---

## 3. 验证命令

```bash
uv run pytest -q
uv run pytest -q tests/test_market_data_adapters.py tests/test_layer4_market_structure.py
uv run pytest -q tests/test_cn_market_adapters.py -k calendar
```

证据：`execute-evidence/9.x-red.txt` → `9.x-green.txt`

---

## 4. ADR 索引

| ADR                                                                                        | 标题                            | 绑定切片       |
| ------------------------------------------------------------------------------------------ | ------------------------------- | -------------- |
| [ADR-026](../../../../docs/decisions/ADR-026-r3h07-us-trading-calendar-ssot.md)            | US equity trading calendar SSOT | **S07-01..04** |
| [ADR-025](../../../../docs/decisions/ADR-025-r3h10-sync-fail-closed-datasource-service.md) | Sync fail-closed（前置）        | 只读           |

---

## 5. 执行包阅读规则

### 5.1 文件地图

| 文件                          | Skill                       | 摘要          |
| ----------------------------- | --------------------------- | ------------- |
| `00-EXECUTION-ENTRY.md`       | trellis-plan 5e             | 本路由        |
| `EXTERNAL-INDEX.md`           | trellis-plan 5e             | 包外 §A/B/C   |
| `to-issues-slices.md`         | to-issues                   | 垂直切片 · AC |
| `calendar-baseline-matrix.md` | to-issues 扩展              | CAL-US 基线   |
| `plan-spec-gap.md`            | spec-driven-development     | Spec 六要素   |
| `plan-task-sizing.md`         | planning-and-task-breakdown | 规模 · CP     |
| `plan-context-pack.md`        | context-engineering         | 情境路由      |
| `plan-doubt-review.md`        | doubt-driven-development    | 对抗审查      |
| `reference-adoption-r3h07.md` | trellis-research            | 参考采纳      |
| `project-overview.md`         | gitnexus 1a                 | 架构现状      |
| `gitnexus-summary.md`         | gitnexus 1b                 | impact 摘要   |
| `original-plan-trace.md`      | trellis-plan                | AC 映射       |
| `plan-consolidation.md`       | trellis-plan 5e             | 分流对照      |
| `integration-audit.md`        | Plan 5d                     | 对抗审计      |

### 5.2 切片开工前必读

每一次 S07-xx（含 BOOT）开工前 **必须已 Read 全文**：

#### A. `research/` 包内（§5.1 除 `plan-boot.md` 外全部）

#### B. `EXTERNAL-INDEX.md` §A 全部

#### C. 当前切片节

`to-issues-slices.md` 对应 §

```text
开工检查：
[ ] research/ 登记文件已读
[ ] EXTERNAL-INDEX §A 已读
[ ] 当前 S07-xx § 已读
→ 然后才允许 RED
```

### 5.3 执行阶段情境路由

| 情境                      | 路由                                                                   |
| ------------------------- | ---------------------------------------------------------------------- |
| 新建/改 US 假日表         | **ADR-026** · `cn_trading_calendar.py` 镜像 · `us_trading_calendar.py` |
| 改 yahoo/stooq/AV port    | §C ports · `calendar-baseline-matrix.md` · `to-issues-slices.md` §4    |
| 改 evidence `window_kind` | `market_data.py` · `test_market_data_adapters.py`                      |
| 改 Layer4 US_EQ           | `market_structure.py` · `test_layer4_market_structure.py`              |
| 验证 service 窗口语义     | `service.py` · `test_datasource_service.py` · R3H-10 ENTRY             |
| CN 回归失败               | **停止** — 不得为 US 改 `cn_trading_calendar`                          |
| Wave 2 reconcile/probe    | §2 Wave 2 承接表 — **不** 本卡范围                                     |

---

## 6. Wave 级活卡（不迁入 research）

见 `EXTERNAL-INDEX.md` §A1–A2 · `R3H_07_US_TRADING_CALENDAR.md`

## D. 机器路由

权威数据在 **`context_pack.json`**（本任务根目录）。 由 `context_router.py --task` 写入；本段不重复列举。
