# R3-DCP-09 参考项目采纳调研（L1/L2/L3）

> **任务：** `.trellis/tasks/07-02-wave4-r3-dcp-09-backfill-ci/`  
> **日期：** 2026-07-02  
> **SSOT：** `specs/contracts/reference_adoption_guardrails.yaml`

---

## 0. 铁律

1. **L1/L2/L3 只评 `参考项目/**`**；仓内 `BackfillShardRunner`/`plan_backfill_shards` 记「仓内承接」。
2. 禁止 runtime import / sys.path / 软链参考树。
3. OpenBB = **architecture_only**（AGPL）。
4. EasyXT `unified_data_interface` silent fallback = **forbidden**。

---

## 1. 三等级总表（仅参考项目）

| 参考路径                                                  | 等级                            | 采纳 / 禁止                                  | QMD 目标                                            |
| --------------------------------------------------------- | ------------------------------- | -------------------------------------------- | --------------------------------------------------- |
| `参考项目/OpenBB/.../fetcher.py` L36–85                   | **architecture_only → L3 对齐** | transform_query / extract / transform 三阶段 | backfill 每 shard = 一次 bounded `FetchRequest` 窗  |
| `参考项目/OpenBB/.../provider` date window 分片概念       | **L3 概念**                     | 大日期范围拆成可恢复 task                    | 对齐 `plan_backfill_shards` + `SHARD_COMPLETE` 断点 |
| `参考项目/EasyXT/.../auto_data_updater.py` L149–178       | **L2 概念**                     | 单标的日期窗 `start_date`/`end_date`         | CLI `--start`/`--end`；禁止 DataManager 线程调度    |
| `参考项目/EasyXT/.../unified_data_interface.py` L172–244  | **forbidden**                   | DuckDB 不全 → QMT 在线回退                   | backfill 路径不得 silent 换源                       |
| `参考项目/EasyXT/.../auto_data_updater.py` L31–32, L87–97 | **forbidden**                   | sys.path + DataManager                       | 负向：禁止进入 sync                                 |

> **注：** 参考树路径与 DCP-05 一致；Plan 期按 guardrails 与活卡 §3 登记。Execute RED 前须实读对应行号并落盘 `execute-reference-read-evidence-dcp09.md`。

---

## 2. OpenBB Fetcher — 分片 / 日期窗（architecture_only → L3）

**概念对齐（非拷贝类）：**

```text
CLI params (--start, --end, --max-shards)
  → transform_query 等价：plan_backfill_shards + cap truncate
  → extract_data 等价：DataSourceService.fetch per shard
  → transform_data 等价：validation + clean write
```

**不拷贝：** `Fetcher` 泛型类、OpenBB provider registry。

---

## 3. EasyXT — forbidden silent fallback

backfill 与 incremental 共用 production fail-closed：

- 本地缺口 **不得** 触发在线 QMT/备用源
- 失败须 `CliFailure` / `FAILED_RETRYABLE` + 可审计 event

---

## 4. 仓内承接（非参考 L 梯）

| 组件                  | 路径                                      | DCP-09 用法         |
| --------------------- | ----------------------------------------- | ------------------- |
| Shard planner         | `sync/jobs.py:plan_backfill_shards`       | 31 天/片 eco cap    |
| Runner                | `sync/runners.py:BackfillShardRunner`     | 金路径执行          |
| Orchestrator          | `sync/orchestrator.py:run_backfill`       | CLI 调用目标        |
| Smoke shard benchmark | `production_equivalent_smoke.py`          | cap 回归门禁        |
| Tier A service path   | DCP-05 `build_*_incremental_service` 模式 | 首域 baostock pilot |

---

## 5. Execute 必读参考（RED 前）

| 文件                                                                            | 行号    | 目的           |
| ------------------------------------------------------------------------------- | ------- | -------------- |
| `参考项目/OpenBB/openbb_platform/core/openbb_core/provider/abstract/fetcher.py` | 36–85   | 三阶段窗提取   |
| `参考项目/EasyXT/data_manager/unified_data_interface.py`                        | 172–244 | forbidden 对照 |
