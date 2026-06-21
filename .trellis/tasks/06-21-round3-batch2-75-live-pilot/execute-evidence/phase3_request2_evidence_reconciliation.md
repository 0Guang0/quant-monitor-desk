# Phase 3 — Request 2 Evidence Reconciliation

> **Generated:** 2026-06-21 (Execute continuation)  
> **Task:** `06-21-round3-batch2-75-live-pilot`  
> **Authority:** `eastmoney_stock_zh_a_hist_verdict.md` + `batch275_user_authorization_2026-06-21.md` Request 2

## 1. Original Request 2 semantics (approved)

| Field           | Approved value                                          |
| --------------- | ------------------------------------------------------- |
| `source_id`     | `akshare`                                               |
| `data_domain`   | `cn_equity_daily_bar`                                   |
| `operation`     | `fetch_daily_bar_validation`                            |
| AkShare API     | `stock_zh_a_hist`                                       |
| Vendor endpoint | `https://push2his.eastmoney.com/api/qt/stock/kline/get` |
| Symbol          | `sh.600519`                                             |
| Window          | recent 5 trading days                                   |
| `max_rows`      | `10`                                                    |

Request 2 is **validation-only** and must **not** be promoted to Primary.

## 2. Endpoint verdict authority

`execute-evidence/eastmoney_stock_zh_a_hist_verdict.md` is the **sole authority** for whether the original Request 2 endpoint is reachable in the current pilot environment.

**Verdict (2026-06-21):** `stock_zh_a_hist` / `push2his.eastmoney.com` is **不可用** (HTTPS connection failures at TCP/TLS layer across direct, proxy, and IPv4-pin probes).

## 3. Classification of existing Phase 3 raw evidence

| Artifact                                               | Classification                  | Notes                                                                                             |
| ------------------------------------------------------ | ------------------------------- | ------------------------------------------------------------------------------------------------- |
| `phase3_raw_micro_fetch_evidence.json` → `pilot-req-2` | **Preserved — not deleted**     | Fetch envelope shows `status=SUCCESS` at orchestration layer                                      |
| Sandbox raw file `…/c94dc92f….json`                    | **Sidecar / candidate only**    | `vendor_api=stock_zh_a_daily`; Sina host `finance.sina.com.cn`                                    |
| `8.5b-green.txt`                                       | **Historical execute evidence** | Records Phase 3 run before endpoint semantic reconciliation; not reinterpreted as Request 2 GREEN |

The sidecar raw file proves Sina `stock_zh_a_daily` returned rows in this environment. That is **not** equivalent to original Eastmoney hist success.

## 4. Sidecar evidence must not close Request 2

- Sina `stock_zh_a_daily` evidence **must not** close original Request 2.
- Sina sidecar evidence **must not** support `PILOT_PASS_RAW_ONLY` (which requires all three requests under original approved semantics).
- Sidecar rows may be cited only as **candidate / informational** signal for future `018C_tdx_pytdx_low_cost_probe.md` work.

## 5. Rerun of original `stock_zh_a_hist` path (2026-06-21)

Current pilot fetch port (`backend/app/ops/live_pilot_fetch_ports.py`) has been restored to call `ak.stock_zh_a_hist` (not `stock_zh_a_daily`).

Bounded rerun probe (same symbol/window class, authorization gates unchanged):

```
uv run python -c "import akshare as ak; ak.stock_zh_a_hist(symbol='600519', ...)"
→ FAIL: ProxyError / push2his.eastmoney.com unreachable
```

**Conclusion:** Original endpoint remains **unavailable**. Request 2 closeout = **source/endpoint failure** (`SOURCE_ENDPOINT_FAILURE`), not validation failure on sidecar structure.

## 6. Evidence retention policy

| Action                                   | Policy                          |
| ---------------------------------------- | ------------------------------- |
| Delete Phase 3 JSON                      | **Forbidden**                   |
| Rewrite raw sidecar file                 | **Forbidden**                   |
| Re-label sidecar in closeout             | **Required** — `candidate_only` |
| Mix TDX / xqshare / QMT / DB-GPT runtime | **Forbidden** in Batch 2.75     |

## 7. Batch 2.75 boundary

Future low-cost probe work (`tdx_pytdx`, AkShare Sina candidate evaluation) belongs to:

`docs/implementation_tasks/ROUND_3_MODELING_LAYERS/018C_tdx_pytdx_low_cost_probe.md`

—not this Batch 2.75 closeout.

## 8. Reconciliation outcome

| Question                            | Answer                                                         |
| ----------------------------------- | -------------------------------------------------------------- |
| Original Request 2 endpoint passed? | **No** — unavailable                                           |
| Sidecar Sina evidence present?      | **Yes** — classified sidecar only                              |
| Supports `PILOT_PASS_RAW_ONLY`?     | **No**                                                         |
| Recommended pilot outcome           | `PILOT_FAIL_SOURCE` (partial success on Request 1 + Request 3) |
