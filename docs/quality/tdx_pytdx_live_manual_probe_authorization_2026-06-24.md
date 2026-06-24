# TDX Live Manual Probe Authorization — 2026-06-24

authorized_session_id: b01-tdx-live-2026-06-24

我授权执行 Round 3 018C TDX 实时手工探测（tdx_pytdx live manual probe），
任务卡：docs/implementation_tasks/ROUND_3_MODELING_LAYERS/018C_tdx_pytdx_low_cost_probe.md，
执行计划：.trellis/tasks/06-22-round3-018c-live-manual-probe-plan/live_manual_probe_plan.md，
本清单：.trellis/tasks/06-22-round3-018c-live-manual-probe-plan/authorization_checklist.md，
授权文件：docs/quality/tdx_pytdx_live_manual_probe_authorization_2026-06-24.md。
仅允许下列 operation 列表中的项；禁止生产库写入；禁止将 tdx_pytdx 提升为 Primary；
禁止用本探测结论关闭 Eastmoney stock_zh_a_hist / Request 2（R3-B2.75-REQ2-EM）。

I authorize the Round 3 018C tdx_pytdx live manual probe scoped to
docs/quality/tdx_pytdx_live_manual_probe_authorization_2026-06-24.md only.
Execute plan: `.trellis/tasks/06-22-round3-018c-live-manual-probe-plan/live_manual_probe_plan.md`.
This probe does not close Eastmoney stock_zh_a_hist / R3-B2.75-REQ2-EM.

**Approved by:** project owner  
**Approved on:** 2026-06-24  
**Policy:** `docs/quality/production_live_pilot_policy.md`  
**Gate:** `backend/app/ops/tdx_live_manual_probe_gate.py`

## Per-request declaration (§4)

| # | probe_id | source_id | data_domain | operation | symbol / market | window | max_rows |
| - | -------- | --------- | ----------- | --------- | --------------- | ------ | -------- |
| 1 | probe-tdx-security-list | tdx_pytdx | security_list | fetch_security_list | sh | max_rows=20 per market | 20 |
| 2 | probe-tdx-equity-daily | tdx_pytdx | cn_equity_daily_bar | fetch_daily_bar | sh.600519 | recent 5 trading days | 10 |
| 3 | probe-tdx-index-daily | tdx_pytdx | cn_index_daily_bar | fetch_index_daily_bar | 000001.SH | recent 5 trading days | 10 |

**Caps (018C wins):** 5 trading days · equity/index max_rows=10 · security list max_rows=20 · max 5 network calls · total rows ≤ 40.

## TDX 行情主机

> **BLK-TDX-04：** 下列 `host` / `port` 须由用户在执行 live 探针前填写。占位值不能用于实际网络连接。

| host | port | provided_by | provided_on | reachability_note | reference_only_default | user_attestation |
| ---- | ---- | ----------- | ----------- | ----------------- | ---------------------- | ---------------- |
| __USER_FILL_HOST__ | 0 | project owner | 2026-06-24 | **待用户填写可达 TDX HQ 主机与端口** | false | bounded read-only probe OK once host confirmed |

## Global controls

| Control | Value |
| ------- | ----- |
| raw_only | true |
| write_target | sandbox |
| allow_clean_write | false |
| allow_production_clean_write | false |
