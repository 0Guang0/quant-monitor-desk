# ADR-011：有界 backfill 上限与 CI nightly

**状态：** 已接受  
**日期：** 2026-07-02  
**修订：** 2026-07-09 — 补正文；与 `performance_limits.md` §8 对齐

## 背景

`qmd data backfill` / `full-load` 不得无界拉取历史。成品权威在 `docs/ops/design/performance_limits.md` §8 与 `specs/contracts/design/runtime_flow_contract.yaml` `flows.backfill`。

## 决策

### 1. Backfill 日期窗口（交易日）

| 参数     | 值                     | 权威                            |
| -------- | ---------------------- | ------------------------------- |
| 默认上限 | **5 trading days**     | `performance_limits.md` §8 L250 |
| 硬顶     | **20 trading days**    | 同上                            |
| 计量单位 | **交易日**（非自然日） | ADR-007 交易日历 SSOT           |

- CLI 边界（`backfill_plan` / `full_load_plan`）负责按 `data_domain` 选用 CN/US 交易日历并校验窗宽。
- `plan_backfill_shards` 信任已裁剪的 `(date_start, date_end)` 交易日序列（S5 实现切片）。
- 超限须报错或 `--truncate-to-cap` 截断；不得静默扩窗。
- 磁盘剩余 < 20GB 时 backfill 暂停（`performance_limits.md` §10）。

### 2. 机器可读契约

`specs/contracts/bounded_backfill_cap.yaml` 为运行副本；数字须与 `performance_limits.md` §8 一致（S5 对齐切片负责 promote/直改）。

### 3. CI nightly（本 ADR 文件名后半段）

夜间 live 网络回归**不是** backfill 上限，而是独立流水线：

- **SSOT：** `docs/ops/nightly_ci.md`
- **工作流：** `.github/workflows/nightly.yml`（cron + `workflow_dispatch`）
- **隔离：** `QMD_DATA_ROOT=.audit-sandbox/nightly-*` + `QMD_ALLOW_LIVE_FETCH=1`
- PR CI（`.github/workflows/ci.yml`）**不**传 `--run-network`

## 后果

- backfill 默认行为与用户预期一致（5 交易日窗，非 31 自然日/片）。
- ADR-011 同时索引 backfill 上限与 nightly CI 入口，避免会话只搜文件名却不知道 nightly 文档在哪。

## 相关权威

| 主题            | 路径                                                |
| --------------- | --------------------------------------------------- |
| 性能上限 design | `docs/ops/design/performance_limits.md` §8          |
| 流程契约        | `specs/contracts/design/runtime_flow_contract.yaml` |
| 夜间 CI 操作    | `docs/ops/nightly_ci.md`                            |
| 运行 cap YAML   | `specs/contracts/bounded_backfill_cap.yaml`         |
