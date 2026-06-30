# Execute 六项上下文闭合 — R3-DCP-01

| #   | 项           | 闭合内容                                                                                                                                  |
| --- | ------------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **目标**     | baostock CN 日频 bar 产品增量：读 `security_bar_1d` watermark → 只拉新 bar → 隔离库 upsert → `qmd data sync` 可重复跑                     |
| 2   | **价值**     | Wave 3 首个可复制增量试点；验证金路径不需 `--live-wire`；为 Wave 4 Tier A 扩展模板                                                        |
| 3   | **完成条件** | 活卡 §5：watermark 单测、E2E+幂等、CLI dry-run/真跑 smoke、`pytest -q` 绿、S06 registry 登记                                              |
| 4   | **边界**     | 仅 baostock；禁 `fred_port`/`orchestrator.py` 改；`QMD_DATA_ROOT` 隔离；无 migration；CN 日历 ponytail 用 calendar day                    |
| 5   | **架构触点** | 新建 `sync/watermark.py`；`runners.py` date→FetchRequest；`baostock_port` 窗过滤；`data_commands` baostock sync；`clean_write_targets` L1 |
| 6   | **终态**     | `qmd data sync --domain cn_equity_daily_bar` dry-run 输出 window；replay 真跑写 `security_bar_1d`；重复跑行数不变；主会话 merge + Audit   |
