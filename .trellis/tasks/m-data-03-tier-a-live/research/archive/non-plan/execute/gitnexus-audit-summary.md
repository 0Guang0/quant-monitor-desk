# GitNexus Audit Summary — M-DATA-03（7.pre）

> **⚠️ R1 切片名作废：** 只读参考。R2 冲击面见 `research/gitnexus-summary.md` · 切片 `S-R2-*`。

> **日期：** 2026-07-02 · A9 Boot 7.pre · 派发 A1–A8 前  
> **分支：** `feature/m-data-03-tier-a-live` vs `master`  
> **任务：** `.trellis/tasks/m-data-03-tier-a-live/` · Plan v4.1

## 变更面（工作区 · M-DATA-03 整轮）

### 生产代码（新增/修改）

| 路径                                                  | 说明                         |
| ----------------------------------------------------- | ---------------------------- |
| `backend/app/ops/tier_a_live_acceptance.py`           | S00-INFRA + S-ACCEPT harness |
| `backend/app/ops/tier_a_live_incremental_dispatch.py` | S-ACCEPT 11 源 live 调度     |
| `backend/app/datasources/fetch_ports/deribit_port.py` | live `mark_iv` 补齐          |
| `scripts/tier_a_live_acceptance.py`                   | CLI exit 0/1/2               |

### 测试（live e2e + harness）

- `tests/test_tier_a_live_harness.py` · `tests/test_tier_a_live_dispatch.py`
- `tests/*_incremental_support.py`（fred/baostock/macro/sec/deribit/cninfo/av/mootdx）
- `tests/test_*_incremental_e2e.py`（11 源 `@pytest.mark.network`）
- `tests/conftest.py`（`isolated_live_data_root` · dotenv boot）

### 文档 / Trellis

- `docs/decisions/ADR-034-*.md` · `docs/implementation_tasks/M_DATA_03_TIER_A_LIVE/`
- `.trellis/tasks/m-data-03-tier-a-live/**`（ENTRY · slices · execute evidence · accept evidence）

## 审计焦点符号（各维优先）

| 符号/区域                                                     | 用途              |
| ------------------------------------------------------------- | ----------------- |
| `tier_a_live_acceptance` / `tier_a_live_incremental_dispatch` | S-ACCEPT 金路径   |
| `product_live_gate` · `QMD_ALLOW_LIVE_FETCH`                  | ADR-027 live 闸   |
| `isolated_live_data_root` · `assert_isolated_live_data_root`  | ADR-034 隔离      |
| `run_*_incremental`（11 源 ops）                              | DCP-05 仓内复用   |
| `deribit_port._book_summary_mark_iv`                          | Market agent 修复 |
| `DbInspector.inspect`                                         | E2 inspect 冒烟   |

## 建议各维 GitNexus

- **A1/A5:** `context(tier_a_live_acceptance)` · `impact(run_tier_a_live_incremental)`
- **A3:** grep `参考项目` runtime import · `.env` / KEY 边界
- **A7:** `DATA_ROOT` 隔离 · `ensure_isolated_db` registry sync
- **A8:** 11 源 network e2e vs `to-issues-slices.md` 建议测试

## 独立复验锚点（A5/A8）

```bash
uv run pytest -q
uv run pytest tests/test_tier_a_live_harness.py -q
QMD_ALLOW_LIVE_FETCH=1 uv run python scripts/tier_a_live_acceptance.py --data-root .audit-sandbox/m-data-03/audit-a5
```
