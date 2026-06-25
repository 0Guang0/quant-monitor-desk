# R3FR-03 — TDX Provider Refactor from EasyXT Reference

> **Batch:** Batch 3F-R — Mature Reference Adoption Refactor  
> **Module movement:** TDX must move from ad hoc manual probe pieces to a QMD-owned disabled/raw-only provider port with explicit authorization and caps.  
> **Execution posture:** disabled by default; raw evidence only; no production clean write; no default live scan.

---

## 1. Purpose

Refactor existing TDX/pytdx probe code so provider lifecycle, connection attempts, request caps, error mapping, and raw evidence output are separated from probe orchestration. This must complete the disabled/raw-only provider shape in this batch; do not split it into repeated “add one host/add one status” tasks.

---

## 2. Reference source file

Read and adapt from:

```text
参考项目/EasyXT/easy_xt/realtime_data/providers/tdx_provider.py
```

Useful ideas:

- optional `pytdx` import handling;
- server list / host-port abstraction;
- connection lifecycle separation;
- retry/error classification;
- stock code normalization/parsing ideas;
- daily/index/security-list method separation.

---

## 3. Required rewrites

Do not copy EasyXT provider behavior wholesale. Rewrite as QMD-owned port code:

- no auto server scan by default;
- no default live enablement;
- no silent fallback to another source;
- no QMT/xqshare enablement;
- no trading/account semantics;
- all live attempts require explicit authorization object;
- every fetch must respect caps from capability/contract;
- raw output must be stored as evidence with content/schema hash;
- route status must remain `DISABLED_SOURCE`, `USER_AUTH_REQUIRED`, or raw-only pass until future authorization changes it.

---

## 4. Target QMD files

Create/update:

```text
backend/app/datasources/fetch_ports/tdx_pytdx_port.py
backend/app/datasources/normalizers/tdx.py
backend/app/datasources/adapters/tdx_pytdx.py
backend/app/ops/interface_probe_fetch_ports.py
backend/app/ops/tdx_manual_probe.py
specs/datasource_registry/source_registry.yaml
specs/datasource_registry/source_capabilities.yaml
tests/test_tdx_manual_probe.py
tests/test_tdx_live_manual_probe_authorization.py
tests/test_reference_adoption_guardrails.py
```

If the `fetch_ports/` or `normalizers/` package does not exist, create it with QMD-owned module boundaries.

---

## 5. Required operations and caps

Supported disabled/raw-only operations:

```text
security_list
cn_equity_daily_bar
cn_index_daily_bar
```

Default caps:

```yaml
security_list_max_rows: 20
equity_daily_bar_max_symbols: 3
index_daily_bar_max_symbols: 3
max_network_calls: 5
minute_bars_enabled: false
full_market_scan_enabled: false
```

Any larger scope requires a later task or ADR. Do not add another micro-batch for one more cap unless it moves the provider toward a complete stable form.

---

## 6. Tests / gates

Required verification:

```bash
uv run pytest tests/test_tdx_manual_probe.py tests/test_tdx_live_manual_probe_authorization.py -q
uv run pytest tests/test_reference_adoption_guardrails.py tests/test_source_capabilities.py -q
```

Tests must prove:

- missing `pytdx` returns disabled/source error, not crash;
- live path requires explicit authorization;
- default path is mocked/disabled raw-only;
- full-market/minute/default scan is rejected;
- source route/fetch result records disabled/user-auth status;
- no runtime import from `参考项目/**`;
- EasyXT auto-login/account/trading semantics are absent.

---

## 7. Done criteria

R3FR-03 is done when TDX has a complete disabled/raw-only QMD-owned provider port shape for the supported operations above. It must be strong enough for Round 3G audit to reason about TDX as excluded/disabled, not as a loose probe wrapper.
