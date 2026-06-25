# Batch 3G Hardening Rules

## 1. Task-card locality

Batch 3G uses one executable card per Task ID:

```text
R3G_01_SANDBOX_CLEAN_WRITE_REHEARSAL.md
R3G_02_PRE_PRODUCTION_ADVERSARIAL_AUDIT.md
R3G_03_LIMITED_PRODUCTION_CLEAN_WRITE.md
```

Reference-source decisions must be written in the task card that uses them. Do not move Batch 3G reference details into a separate inventory document.

## 2. Reference adoption boundaries

### EasyXT

Allowed only as scoped adaptation of data-quality ideas from:

```text
参考项目/EasyXT/data_manager/data_integrity_checker.py
参考项目/EasyXT/data_manager/smart_data_detector.py
```

Required rewrite before QMD use:

- remove runtime dependency on EasyXT files;
- remove path mutation patterns;
- remove default database path lookup;
- remove hardcoded table assumptions;
- replace interpolated query strings with QMD-owned bounded inputs;
- do not treat EasyXT holiday examples as authoritative exchange calendar.

### JQ2PTrade

Allowed only as scoped adaptation of frozen-data loading, report separation, and API-name deny-list ideas from:

```text
参考项目/JQ2PTrade/ptrade_local/engine/data_loader.py
参考项目/JQ2PTrade/ptrade_local/engine/report.py
参考项目/JQ2PTrade/api_mapping.json
```

Required rewrite before QMD use:

- remove default local database path;
- remove broad universe loading;
- preserve raw source symbol identity;
- replace console-only reporting with structured evidence;
- keep execution-style API names out of QMD Round 3G runtime.

### OpenBB

Allowed only as architecture reference from:

```text
参考项目/OpenBB/openbb_platform/providers/
参考项目/OpenBB/openbb_platform/providers/fred/README.md
```

Required rewrite before QMD use:

- no OpenBB runtime source copy;
- no OpenBB provider class copy;
- no OpenBB package dependency in Round 3G runtime;
- express provider metadata through QMD-owned registry/catalog files.

### TradingAgents / agents-for-openbb

No active use in Round 3G. Agent/UI references are future Round4 concerns. Batch 3G must enforce that write candidates are not created, expanded, approved, or triggered by an Agent path.

## 3. Source and write boundaries

- R3G-01 is sandbox-only.
- R3G-02 is audit-only.
- R3G-03 requires exact explicit user approval and before/after proof.
- No default live fetch.
- No full-market, full-history, or minute-bar scope.
- No QMT, TDX, xqshare, or Yahoo production-primary path.
- FRED remains disabled by default and requires authorization.
- `baostock`, `cninfo`, and authorized `fred` samples are the only first candidate families.

## 4. Required QMD gates

Any implementation must compose existing QMD gates:

- `DataSourceService`
- `SourceRoutePlanner`
- `ResourceGuard`
- `DbValidationGate`
- `WriteManager`
- QMD-owned data-health profiles from R3F-R

Bypassing those gates blocks the task.

## 5. Required tests

Every Batch 3G implementation PR must include or update tests proving:

- no runtime import from `参考项目/**`;
- no OpenBB runtime source copy;
- no JQ2PTrade disallowed API names in Round 3G runtime;
- no Agent-triggered write path;
- production path cannot be used by R3G-01/R3G-02;
- R3G-03 blocks without explicit approval, before proof, after proof, and rollback dry run.
