<!-- FROZEN: Plan protocol v4 · do not edit · source: docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/R3FR_05_PROVIDER_CATALOG_OPENBB_REFERENCE.md · frozen_at: 2026-06-26T13:57:57Z -->

# R3FR-05 — Provider Catalog from OpenBB Architecture Reference

> **Batch:** Batch 3F-R — Mature Reference Adoption Refactor  
> **Module movement:** Provider metadata must move from ad hoc registry notes to a QMD-owned catalog contract informed by mature provider architecture.  
> **Execution posture:** contract/catalog only; no provider runtime copy; no live fetch.

---

## 1. Purpose

Create the provider catalog shape needed before Round 3G and Round4 provider-facing work. The catalog should use OpenBB as architecture reference only, not as copied runtime source.

This task must complete the catalog contract and all active/proposed source entries in one batch. Do not split provider catalog work into repeated tiny “add one field” tasks.

```yaml
reference_project:
  path: 参考项目/OpenBB/openbb_platform/providers/
  license: AGPL-3.0
  allowed_use: architecture_only
  qmd_target_files:
    - specs/datasource_registry/provider_catalog.yaml
  direct_copy_allowed: false
  rewrite_required:
    - no_openbb_runtime_source_copy
    - no_openbb_provider_class_copy
  forbidden_semantics:
    - copied_provider_fetcher_class
    - openbb_runtime_dependency
  attribution_required: false
```

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
specs/datasource_registry/source_registry.yaml
specs/datasource_registry/source_capabilities.yaml
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

---

## 7. Red Flags / grill 摘要（Plan 已关闭）

- 禁止接 `DataSourceService.fetch` 热路径
- registry 当前 **23** 源 + 本批补 **2** = **25** catalog 覆盖
- `qmd_target_files` SSOT = `specs/datasource_registry/provider_catalog.yaml`
- R3G 文档偶发 `production_default_allowed` 措辞；catalog canonical = `production_default_enabled`

---

## 8. 边界约束 / 停止条件

| #   | 条件                                                                   | 动作                           |
| --- | ---------------------------------------------------------------------- | ------------------------------ |
| 1   | 发现 `backend/**` 或 `scripts/**` import `参考项目/OpenBB/**` runtime  | 停止；删除 import，回 Plan     |
| 2   | catalog 将 proposed-disabled 源标为 `production_default_enabled: true` | 停止；修正 YAML                |
| 3   | `source_type` / `license_type` 与 schema CHECK 不一致                  | 停止；对齐 enum 后重跑测试     |
| 4   | 试图拆成多个「只加一个 provider 字段」PR                               | 停止；单批完成 §4 全条目       |
| 5   | AC 未全绿即请求 Audit / finish-work                                    | 停止；完成 §9.6 证据           |
| 6   | 与 R3FR-03 并发改 `source_registry.yaml` 未 rebase                     | 停止；按 playbook 合并顺序协调 |

---

## 9. 实现步骤

### 9.0 Boot

- Read `frozen/R3FR_05_PROVIDER_CATALOG_OPENBB_REFERENCE.md` + `EXECUTION_INDEX.md` + `implement.jsonl` 每行 + `context_pack.json`
- GitNexus `impact(load_provider_catalog)` → `research/gitnexus-execute-summary.md`（Execute 6.pre）

### 9.1 Catalog 结构测试 RED

| RED 命令                                                                       | GREEN 命令 | 证据                                   |
| ------------------------------------------------------------------------------ | ---------- | -------------------------------------- |
| `uv run pytest tests/test_provider_catalog.py -q`（ModuleNotFound / 收集失败） | 结构用例绿 | `execute-evidence/9.1-{red,green}.txt` |

### 9.2 全量 catalog YAML + registry/capability 缺口

| RED 命令                   | GREEN 命令                                                                          | 证据                                   |
| -------------------------- | ----------------------------------------------------------------------------------- | -------------------------------------- |
| registry/capability 覆盖红 | `uv run pytest tests/test_provider_catalog.py tests/test_source_capabilities.py -q` | `execute-evidence/9.2-{red,green}.txt` |

交付：`provider_catalog.yaml`（25 源）；`source_registry.yaml` 补 `qmt_xqshare`、`openbb_provider_reference`；`source_capabilities.yaml` 为 `openbb_provider_reference` 补 `proposed_disabled_source` stub。

`openbb_provider_reference` registry 最小行：

```yaml
- source_id: openbb_provider_reference
  source_name: OpenBB provider architecture reference (metadata only)
  source_type: aggregator
  license_type: public_web
  enabled_by_default: false
  trust_level: 0
  allowed_domains: []
  default_role: Validation
  validation_only: true
  requires_user_setup: false
  notes: Architecture-only placeholder; no runtime adapter.
```

### 9.3 只读 loader

| RED 命令      | GREEN 命令                                        | 证据                                   |
| ------------- | ------------------------------------------------- | -------------------------------------- |
| loader 测试红 | `uv run pytest tests/test_provider_catalog.py -q` | `execute-evidence/9.3-{red,green}.txt` |

### 9.4 契约交叉引用（必做）

| RED 命令                                | GREEN 命令                   | 证据                                   |
| --------------------------------------- | ---------------------------- | -------------------------------------- |
| `test_provider_catalog_contractRefs` 红 | contract + capability 测试绿 | `execute-evidence/9.4-{red,green}.txt` |

### 9.5 Guardrails closure

| RED 命令                               | GREEN 命令    | 证据                                   |
| -------------------------------------- | ------------- | -------------------------------------- |
| `test_r3fr05ProviderCatalogClosure` 红 | guardrails 绿 | `execute-evidence/9.5-{red,green}.txt` |

### 9.6 Merge gate

| GREEN 命令                                                                                                                      | 证据                                         |
| ------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| `uv run pytest tests/test_provider_catalog.py tests/test_source_capabilities.py tests/test_reference_adoption_guardrails.py -q` | `execute-evidence/9.6-green.txt`             |
| `uv run pytest -q`（全库）                                                                                                      | `execute-evidence/9.6-full-pytest-green.txt` |
| `uv run python scripts/loop_maintain.py --fix`                                                                                  | 同上                                         |
