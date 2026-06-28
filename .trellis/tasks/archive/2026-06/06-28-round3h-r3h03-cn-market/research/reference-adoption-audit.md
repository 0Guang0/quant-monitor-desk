# R3H-03 参考项目采纳审计（主会话 · 2026-06-28）

> **触发：** 用户要求 Execute 前确认未「从零造轮子」；须遵守 `reference_adoption_guardrails.yaml` L1/L2/L3 阶梯。  
> **纠正：** Plan Agent 错误写入「仓库无 `参考项目/` 树 / Execute 不读外部路径」。`参考项目/` **存在**（`.gitignore` 本地-only），Execute **必须 Read** 活卡列出的参考文件后再定 L1/L2/L3。

## 活卡列出的参考路径（归档用，禁止 runtime import）

| 参考路径 | License | 阶梯 | QMD 目标 | 动作 |
|----------|---------|------|----------|------|
| `参考项目/EasyXT/easy_xt/realtime_data/providers/tdx_provider.py` | MIT | **L2 已完成** | `fetch_ports/tdx_pytdx_port.py`, `normalizers/tdx.py` | R3FR-03 已拷改；R3H-03 **扩展** mootdx，勿重写 lifecycle |
| `参考项目/EasyXT/data_manager/smart_data_detector.py` | — | **L2 待完成** | `ops/data_health_profiles/calendar_gap_rules.py` 或新 `cn_trading_calendar.py` | 用户 Gate：**完整 G2/G17**；拷 `TradingCalendar` 节假日逻辑 → QMD 日历源；去掉 `sys.path`/硬编码 DB |
| `参考项目/EasyXT/data_manager/data_integrity_checker.py` | — | **L2 待完成** | `ops/data_health_profiles/cn_market.py` | 拷 OHLCV 完整性检查语义 → `DataHealthCheckResult`；禁止 pandas/duckdb 直写主库 |
| `backend/app/ops/staged_pilot_fetch_ports.py` | QMD | **L2 部分** | `fetch_ports/baostock_port.py`, `cninfo_port.py` | 已经 `cn_market` normalizer 迁 staged 形状；**补** MIT/QMD attribution 与字段映射对照 |
| 各 `backend/app/datasources/adapters/*.py` skeleton | QMD | **L2** | 对应 `fetch_ports/*` | 读 skeleton 再写 port，非 L3 自研 |
| eastmoney/sina/akshare 无 EasyXT 一一对应 | — | **L3** | 各 validation port | mock/replay + registry 终态即可 |

## 当前 Execute 偏差（须 Repair）

1. **`cn_market.py` calendar profile** — 仅 weekday proxy（`calendar_gap_rules.calendar_authority=false`）；**不符合**用户 Q12「完整闭合 G2/G17」。
2. **多数新 port docstring 写 L2 但无 attribution** — 须补「拷改自 staged_pilot / EasyXT / skeleton」或改标 L3 并记录理由。
3. **cninfo PDF live（用户 Q13）** — 尚未接 capped PDF 下载路径。
4. **INDEX §4 错误结论** — 已废止「不读参考项目」；§3 须列三份 EasyXT 文件为 must-read。

## Execute 铁律（主会话追加）

1. 实现任何模块前：**Read** 上表参考路径（本地 `参考项目/`，只读）。
2. 文件头注释：`MIT attribution` 或 `L2 migrate from staged_pilot` 或 `L3 greenfield: <reason>`。
3. **禁止** `import` / `sys.path` / 运行时读 `参考项目/**`。
4. 参考树删除后代码须独立可运行。

## 闸门

- `tests/test_reference_adoption_guardrails.py` 相关 R3H-03 段（若 INDEX 登记）须绿。
- A3：`rg 参考项目 backend/app` → 0。
