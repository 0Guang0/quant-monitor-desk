# Grill-me Session — R3-DCP-02

> **日期：** 2026-06-30  
> **Plan agent：** wave3-r3-dcp-02-fred

---

## 状态：无未决（Plan 阶段可冻结）

Plan 阶段所需 scope / AC / 边界 / 架构触点均可从以下来源**确定性**推导，无需 block 用户：

| 议题 | 决议 | 依据 |
|------|------|------|
| Watermark 实体键 | per `series_id` → clean `indicator_id` | 活卡 §3 · INDEX §2 · `limited_production_entry._NON_TARGET_KEY_BY_TABLE` |
| Watermark 日期字段 | `publish_timestamp`（来自 evidence `observation_date`） | `rehearsal_loader.py` L341-354 · `source_capabilities.yaml` fred |
| 冷启动窗 | capped `MAX_WINDOW_DAYS`（120） | `fred_port.py` L30-31 |
| 金路径 | `DataSourceService` + `run_incremental` | 活卡 §3 · R3H-10/08 |
| 共享 watermark 模块 | 轨 A 拥有写权限；本轨只读或 `ops/fred_incremental_*` 局部 | `00-MAIN-SESSION-COORDINATOR.md` §4 · `BRANCH-DCP-02.md` |
| Live 授权 | `FRED_API_KEY` + `QMD_ALLOW_LIVE_FETCH` | 活卡 §3 · ADR-027 |
| Clean 表 | `axis_observation` / PK `observation_id` | `clean_write_targets.py` |
| CLI 旗标 | `--domain macro_series --source-id fred`（非 `--source`；对齐 `cli/main.py` sync 子命令现状） | `data_commands.sync_plan` L59-77 · DCP-01 轨 `--domain` 先例 |

---

## 协调项（非用户 Grill-me · 主会话跟踪）

| 项 | 说明 | Owner |
|----|------|-------|
| 轨 A watermark API 就绪时点 | Execute S02-01 前检查 `sync/watermark*.py`；无则走 ops 局部实现 | 主会话 + 轨 A |
| Registry fred 行 delta | 本轨可 proposed；merge 排队 | 主会话 P7 |

---

## 若 Execute 阶段需 Grill-me 的触发条件

- 轨 A 已 merge 的 watermark API 与 fred `indicator_id` 语义不兼容
- `axis_observation` 现有行 `indicator_id` 与 P0 `series_id` 不一致（需数据迁移 — 超出本票非目标）
- CLI 子命令形态与主会话/Product 方冲突（例如 `--source` vs `--data-domain`）

以上发生时 Execute agent 须 **对话提问用户**，不得自问自答写 session。
