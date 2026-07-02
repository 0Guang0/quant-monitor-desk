# Execute reference read evidence — R3-DCP-09

> Plan D5 / `reference-adoption-dcp09.md` L28 — RED 前实读摘要（Repair 补盘）

## §D OpenBB fetcher（architecture_only）

- 路径：`参考项目/OpenBB/openbb_platform/core/openbb_core/provider/abstract/fetcher.py`
- 实读结论：抽象 Fetcher 定义 `fetch_data` 契约；**未** runtime import 进本仓。

## §D EasyXT unified_data_interface（forbidden）

- 路径：`参考项目/EasyXT/data_manager/unified_data_interface.py` L172–244
- 实读结论：统一数据接口为参考树；本票金路径为 `DataSourceService` + orchestrator，**禁止**复制。

## 负向声明

- `backend/` · `scripts/` **无** `参考项目` import / sys.path 渗入（Audit A3 rg 0 命中）。
