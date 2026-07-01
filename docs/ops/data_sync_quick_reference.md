# Data Sync Quick Reference（Round2.6）

本页是面向用户/运维的一页式数据同步入口。它不替代 implementation tasks；它把安全运行命令、dry-run、ResourceGuard、SourceRoutePlan 和错误排障放在一起。

## Tier A 增量 sync（R3-DCP-05 · ADR-028）

11 个 Tier A 源统一经 `--source-id` 路由；默认 **dry-run** 输出可审计 JSON（watermark / clean 表 / 窗参数）。

```bash
# 示例：dry-run 审计（不写库）
qmd data sync --source-id baostock --domain cn_equity_daily_bar --end 2024-06-30 --dry-run
qmd data sync --source-id fred --domain macro_series --dry-run
qmd data sync --source-id mootdx --domain cn_equity_daily_bar --end 2024-06-30 --dry-run

# 真跑须隔离 QMD_DATA_ROOT（.audit-sandbox）+ 源级 live gate；见 ADR-027
```

| source_id                                    | canonical domain       | clean 表                |
| -------------------------------------------- | ---------------------- | ----------------------- |
| baostock, mootdx                             | cn_equity_daily_bar    | security_bar_1d         |
| alpha_vantage                                | us_equity_daily_bar    | security_bar_1d         |
| fred, us_treasury, bis, world_bank, cftc_cot | 各 macro domain        | axis_observation        |
| cninfo                                       | cn_announcements       | cn_announcement_clean   |
| sec_edgar                                    | us_filings             | us_disclosure_clean     |
| deribit                                      | crypto_options_surface | crypto_derivative_clean |

SSOT：`backend/app/sync/incremental_source_registry.py` · `docs/decisions/ADR-028-dcp05-tier-a-clean-domain-extension.md`

### ACC-EASTMONEY-TAXONOMY-001（口径 SSOT · 不关 REQ2-EM）

- **问题：** `eastmoney_port` 产品 mock 与 akshare `stock_zh_a_hist`（`push2his.eastmoney.com`）真网口径并存。
- **本票边界：** DCP-05 仅登记文档/registry 注释；**不**关闭 `R3-B2.75-REQ2-EM` 硬约束。
- **运维读法：** validation 用 akshare/eastmoney 对照；产品 bar 增量主路径为 **baostock/mootdx**（`--source-id`）。
- 台账：`docs/quality/待修复清单.md` · Wave 4 `R3-DCP-05`/`08`

## 推荐命令形态（设计稿）

```bash
qmd data init-basic --dry-run
qmd data route-preview --domain market_bar_1d --operation fetch_daily_bar
qmd data sync --domain market_bar_1d --start 2024-01-01 --end 2024-12-31 --dry-run
qmd data sync --domain announcement --since 2026-01-01 --dry-run
qmd data health --domain market_bar_1d
```

当前阶段这些是设计目标；现有脚本仍以 `scripts/init_db.py`、`scripts/sync_registry.py`、`scripts/production_equivalent_smoke.py` 为准。

**已实现的 CI one-liner（R2-GAP-1）：**

```bash
uv run python scripts/init_db.py --sync-registry
```

**Perf budget 门禁（R3-B25-PERF-BUDGET-01）：**

```bash
uv run python scripts/ci_perf_budget_artifact.py
```

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
