# Data Sync Quick Reference（Round2.6）

本页是面向用户/运维的一页式数据同步入口。它不替代 implementation tasks；它把安全运行命令、dry-run、ResourceGuard、SourceRoutePlan 和错误排障放在一起。

## 推荐命令形态（设计稿）

```bash
qmd data init-basic --dry-run
qmd data route-preview --domain market_bar_1d --operation fetch_daily_bar
qmd data sync --domain market_bar_1d --start 2024-01-01 --end 2024-12-31 --dry-run
qmd data sync --domain announcement --since 2026-01-01 --dry-run
qmd data health --domain market_bar_1d
```

当前阶段这些是设计目标；现有脚本仍以 `scripts/init_db.py`、`scripts/sync_registry.py`、`scripts/production_equivalent_smoke.py` 为准。

## 安全规则

1. 所有可能写数据的命令必须支持 `--dry-run`。
2. fetch 前必须输出 `SourceRoutePlan`。
3. QMT / qmt_xqshare 不得被 CLI 自动启用。
4. 失败输出必须包含 `error_code` 与 `docs_anchor`。
5. ResourceGuard 暂停时不得绕过。

## 相关文档

- `docs/ops/ERROR_CODE_GUIDE.md`
- `docs/ops/incident_playbook.md`
- `specs/contracts/data_cli_contract.yaml`
- `specs/contracts/source_route_contract.yaml`
