# R3FR-05 — Provider Catalog from OpenBB Architecture Reference

> **Batch:** Batch 3F-R — Mature Reference Adoption Refactor  
> **Module movement:** Provider metadata must move from ad hoc registry notes to a QMD-owned catalog contract informed by mature provider architecture.  
> **Execution posture:** contract/catalog only; no provider runtime copy; no live fetch.

---

## 1. Purpose

Create the provider catalog shape needed before Round 3G and Round4 provider-facing work. The catalog should use OpenBB as architecture reference only, not as copied runtime source.

This task must complete the catalog contract and all active/proposed source entries in one batch. Do not split provider catalog work into repeated tiny “add one field” tasks.

---

## 2. Reference source paths

Read architecture only:

```text
参考项目/OpenBB/openbb_platform/providers/
参考项目/OpenBB/openbb_platform/providers/fred/README.md
```

Useful architecture ideas:

- provider-per-package organization;
- provider README / metadata separation;
- optional provider extras;
- provider identity and external documentation links;
- provider-specific credential posture.

Forbidden:

- copying OpenBB runtime source;
- copying provider fetcher classes;
- adding OpenBB runtime dependency in Round 3F-R/Round 3G;
- using AGPL source as direct QMD runtime code.

---

## 3. Target files

Create/update:

```text
specs/datasource_registry/provider_catalog.yaml
backend/app/datasources/provider_catalog.py
specs/contracts/source_capability_contract.yaml
specs/contracts/datasource_service_contract.yaml
tests/test_provider_catalog.py
tests/test_reference_adoption_guardrails.py
```

If runtime `provider_catalog.py` is too early for this batch, at minimum create the YAML contract and tests that validate it. Do not leave this as prose only.

---

## 4. Required first catalog entries

The catalog must include every active or proposed source in `specs/datasource_registry/source_registry.yaml`. At minimum this includes the original sources plus the newly added proposed-disabled expansion set:

```text
qmt_xtdata
baostock
akshare
cninfo
yahoo_finance
tdx_pytdx
fred
us_treasury
sec_edgar
cftc_cot
bis
world_bank
deribit
coingecko
kalshi
polymarket
stooq
alpha_vantage
mootdx
eastmoney
sina_finance
ths_ifind
web_search
qmt_xqshare
openbb_provider_reference
```

Each entry must declare:

```yaml
provider_id: ""
source_ids: []
source_type: "" # must match schema CHECK values
license_type: "" # must match schema CHECK values
license_or_terms: ""
allowed_domains: []
enabled_by_default: true|false
status: active|sandbox_candidate|proposed_disabled_source
production_default_candidate: true|false
production_default_enabled: true|false
requires_user_authorization: true|false
requires_local_client: true|false
validation_only: true|false
max_default_symbols_or_series: 0
max_default_window_days: 0
reference_architecture: ""
runtime_source_copy_allowed: false
```

Use `production_default_candidate` vs `production_default_enabled` to avoid the current ambiguity where a planned primary source appears production-enabled before Round 3G admission.

---

## 5. Tests / gates

Required verification:

```bash
uv run pytest tests/test_provider_catalog.py tests/test_source_capabilities.py -q
uv run pytest tests/test_reference_adoption_guardrails.py -q
```

Tests must prove:

- every source registry provider candidate has catalog metadata, including proposed-disabled sources such as `us_treasury`, `sec_edgar`, `cftc_cot`, `bis`, `world_bank`, `deribit`, `coingecko`, `kalshi`, `polymarket`, `stooq`, `alpha_vantage`, `mootdx`, `eastmoney`, `sina_finance`, `ths_ifind`, and `web_search`;
- `source_type` and `license_type` values match the CHECK enums in `specs/schema/schema.sql` and migration 009;
- `openbb_provider_reference.runtime_source_copy_allowed == false`;
- `fred.requires_user_authorization == true` and enabled-by-default false;
- all newly added external sources remain `enabled_by_default == false` and `production_default_enabled == false` until adapter/auth/license/route/replay evidence exists;
- TDX/QMT/xqshare default enablement remains false;
- production candidate and production enabled are distinct fields;
- no OpenBB runtime source is imported/copied.

---

## 6. Done criteria

R3FR-05 is done when provider catalog metadata is machine-checkable and first candidate providers are represented without copying OpenBB runtime code or overstating production enablement.
