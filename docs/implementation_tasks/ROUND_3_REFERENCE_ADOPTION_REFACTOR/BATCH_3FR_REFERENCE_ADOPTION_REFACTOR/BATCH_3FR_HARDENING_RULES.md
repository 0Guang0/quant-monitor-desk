# Batch 3F-R Hardening Rules

## 1. Preserve the green 3F baseline

Batch 3F-R starts from `integration/round3-batch3f` after Batch 3F integration is green. Do not weaken existing tests to make reference adoption pass.

If a reference-derived implementation conflicts with current tests, decide whether:

1. the reference implementation must be adapted to QMD; or
2. the old QMD test was overfitted and should be rewritten while preserving its original business purpose.

Never remove assertions merely because reference code behaves differently.

## 2. No runtime dependency on `参考项目/**`

The local reference repositories are source material, not runtime packages.

Forbidden:

```python
import sys
sys.path.insert(... "参考项目" ...)
from EasyXT ... import ...
from JQ2PTrade ... import ...
from OpenBB ... import ...
```

Allowed:

- copy/adapt licensed snippets into QMD-owned files with attribution when allowed
- write QMD-native wrappers inspired by reference code
- cite local reference paths in docs and task plans

## 3. License boundary

- EasyXT: MIT, scoped source adaptation allowed.
- JQ2PTrade: MIT per README, scoped source adaptation allowed.
- agents-for-openbb: MIT, future Round4 reference only.
- OpenBB main repo: AGPLv3, architecture reference only; no runtime source copy.
- tdx-quant: Apache-2.0 Java/Spring; no Python runtime copy.
- TradingAgents repos: future Round4 reference only; verify license before direct adaptation.

## 4. Trading and action boundary

Reference projects may contain trading APIs. QMD must not copy them into runtime.

Forbidden symbols include:

```text
order
order_target
order_value
order_target_value
cancel_order
buy
sell
auto_login
captcha_solver
terminal_control
```

If a reference file contains both useful and forbidden logic, extract only the useful non-trading parts and add tests proving forbidden symbols did not enter `backend/app/**`.

## 5. Source routing boundary

Reference data providers must not bypass:

```text
SourceRegistry
SourceCapabilityRegistry
SourceRoutePlanner
DataSourceService
ResourceGuard
RawStore
FileRegistry
fetch_log
```

No reference provider may write clean DB tables directly.

## 6. Data health boundary

EasyXT data health rules must be converted to QMD profile functions returning `DataHealthCheckResult` / `DataHealthReport`. They must not keep EasyXT's hardcoded DB/table assumptions.

Required rewrites:

- no hardcoded DuckDB path
- no hardcoded `stock_daily`
- no SQL string interpolation
- no `sys.path.insert`
- no live fetch
- no production DB mutation

## 7. TDX boundary

TDX remains disabled-by-default and validation/raw-only.

The provider refactor may adapt connection, server, and pytdx normalization logic, but it must not introduce:

- default live probe
- automatic full server scan
- production primary role
- full-market or full-history fetch
- minute-level default fetch
- silent fallback to Eastmoney/Sina/AkShare

## 8. Backtest boundary

Round4 backtest may adapt JQ2PTrade MiniPTrade lifecycle and EasyXT metrics/report ideas, but first QMD implementation must be review/event-study oriented.

Allowed:

- frozen DuckDB/evidence loader
- report builder
- metrics
- event windows
- analysis and human-review suggestions

Forbidden:

- executable user strategy code in first implementation
- broker connection
- automatic order generation
- direct position instruction

## 9. Cleanup boundary

Do not remove old wrappers until:

1. replacement tests exist;
2. old behavior is covered by new implementation;
3. no references in docs/tests still require the old symbol; and
4. roadmap/implementation task indexes point to the canonical new batch folder.

## 10. No central executable reference inventory

Executable reference-adoption details must stay local to the task card that uses the reference source. Batch 3F-R must not create or require `docs/architecture/reference_adoption_inventory.md` as another execution dependency.

Allowed:

- task cards list exact `参考项目/**` paths, allowed adaptations, required rewrites, target QMD files, and tests;
- `reference_adoption_guardrails.yaml` defines global policy and license posture;
- a future separate index may exist only as non-executable navigation.

Forbidden:

- execution agents must not chase a central inventory before implementing a task card;
- task cards must not point to an external inventory for their executable reference details;
- license or adaptation decisions must not be implicit.

## 11. Completion-rating boundary

`MODULE_COMPLETION_RATING.md` is the only current-state completion snapshot. Design docs, architecture docs, contracts, and rule definitions describe the full target product shape and must not be downgraded with current completion labels.

Planning files and task cards may reference completion ratings only to decide batch order, audit gaps, and expected rating movement.

## 12. Anti-overengineering closure rule

Each module must be planned to reach full production-stable scope in at most three implementation batches. This limit is about reaching full stable production, not only a minimal closure.

Reject or merge task slices that only add one metric, one flag, one registry note, one placeholder, or one narrow test without completing a meaningful supported behavior. The first implementation batch for a module must produce a true minimum vertical slice, and an already partially implemented module's next batch must close the main promised scope unless an ADR explicitly narrows that scope.
