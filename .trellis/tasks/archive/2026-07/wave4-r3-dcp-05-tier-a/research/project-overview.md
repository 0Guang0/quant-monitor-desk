# Project overview — R3-DCP-05 Plan context

> **Repo:** quant-monitor-desk · Wave 4 incremental extension

## 相关子系统

- **CLI:** `backend/app/cli/data_commands.py` — `qmd data sync`
- **Sync:** `backend/app/sync/` — watermark, orchestrator, runners
- **Ops incremental:** `backend/app/ops/fred_incremental_*.py` — macro 模板
- **Datasources:** `fetch_ports/*`, `product_live_ports.py`, `product_live_gate.py`
- **Schema:** `backend/app/db/migrations/013_*.sql` → **015 DCP-05**
- **Contracts:** ADR-028, `source_registry.yaml`, `clean_write_targets.py`

## 已完成上游

Wave 1–3 CLOSED；DCP-01 baostock + DCP-02 fred + DCP-03 inspect；R3H-08 live ports；R3H-10 SSOT。

## 本票新增

migration 015；11 源 incremental registry；baostock product live sync。
