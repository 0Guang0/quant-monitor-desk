# 数据同步快速参考

本页是面向用户/运维的一页式数据同步入口。它不替代 implementation tasks；它把安全运行命令、dry-run、ResourceGuard、SourceRoutePlan 和错误排障放在一起。

## Tier A 增量同步

11 个 Tier A 源统一经 `--source-id` 路由；默认 **dry-run** 输出可审计 JSON（watermark / clean 表 / 窗口参数）。

```bash
# 示例：dry-run 审计（不写库）
qmd data sync --source-id baostock --domain cn_equity_daily_bar --end 2024-06-30 --dry-run
qmd data sync --source-id fred --domain macro_series --dry-run
qmd data sync --source-id mootdx --domain cn_equity_daily_bar --end 2024-06-30 --dry-run

# 真跑须隔离 QMD_DATA_ROOT（.audit-sandbox/source-route-db）+ 源级 live gate；见 ADR-015
```

| source_id                                    | 规范 domain            | clean 表                |
| -------------------------------------------- | ---------------------- | ----------------------- |
| baostock, mootdx                             | cn_equity_daily_bar    | security_bar_1d         |
| alpha_vantage                                | us_equity_daily_bar    | security_bar_1d         |
| fred, us_treasury, bis, world_bank, cftc_cot | 各 macro domain        | axis_observation        |
| cninfo                                       | cn_announcements       | cn_announcement_clean   |
| sec_edgar                                    | us_filings             | us_disclosure_clean     |
| deribit                                      | crypto_options_surface | crypto_derivative_clean |

SSOT：`backend/app/sync/incremental_source_registry.py` · `docs/decisions/ADR-009-clean-write-targets-migration-015.md`

### ACC-EASTMONEY-TAXONOMY-001（口径 SSOT · 不关 REQ2-EM）

- **问题：** `eastmoney_port` 产品 mock 与 akshare `stock_zh_a_hist`（`push2his.eastmoney.com`）真网口径并存。
- **本票边界：** DCP-08 登记 registry proposed delta + 本文档；**不**关闭 `R3-B2.75-REQ2-EM` 硬约束。
- **运维读法：** validation 用 akshare/eastmoney 对照；产品 bar 增量主路径为 **baostock/mootdx**（`--source-id`）。
- **产品 bar 路径：** `cn_equity_daily_bar` 默认 primary=baostock；显式 `--source-id mootdx` 为 effective primary（ADR-014 双轨语义）。
- **eastmoney 域：** bar 历史仅作 validation；`sector_board` / `capital_flow` 为独立 domain，勿与 bar hist 分类混用。
- 台账：`docs/quality/待修复清单.md`

## 推荐命令形态

```bash
qmd data init-basic --dry-run
qmd data route-preview --domain market_bar_1d --operation fetch_daily_bar
qmd data sync --domain market_bar_1d --start 2024-01-01 --end 2024-12-31 --dry-run
qmd data sync --domain announcement --since 2026-01-01 --dry-run
qmd data health --domain market_bar_1d
```

这些命令形态是产品接口目标。若实现尚未覆盖，验收报告必须标记 `implementation_mode=not_implemented`，不得用脚本替代品冒充产品 CLI 完成。

**CI 单行命令：**

```bash
uv run python scripts/init_db.py --sync-registry
```

**性能预算门禁：**

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
