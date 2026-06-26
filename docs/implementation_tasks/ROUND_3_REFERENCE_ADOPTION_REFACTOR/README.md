# Round 3F-R — Reference Adoption Refactor

> **Canonical status:** **CLOSED** (Batch 3F-R complete @ R3FR-07). Next entry: Round 3G.  
> **Reason:** Batch 3F-R replaced or hardened thin wrappers (data health, CLI, TDX, provider catalog) with tested QMD-owned implementations.  
> **Historical entrypoint:** `BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/README.md` (manifest + redirect notes only).

---

## 1. Purpose

Round 3F-R is a mandatory refactor gate between Batch 3F and Round 3G.

Its job is not to redo the whole project. Its job is to prevent the next production-readiness phase from building on thin local wheels where mature reference implementations already exist.

The adoption model is:

```text
Keep QMD governance boundary
→ adapt mature reference modules behind QMD contracts
→ prove equivalence or improvement by tests
→ replace thin wrappers
→ then proceed to 3G sandbox clean-write rehearsal
```

Execution details for external references must live in the task card that uses the reference source. 3F-R must not create a central executable `reference_adoption_inventory.md`; any future inventory can only be a non-executable navigation index.

Current completion state belongs in `MODULE_COMPLETION_RATING.md` and planning/task files. Design docs, contracts, architecture docs, and rule definitions describe the full finished product shape.

The anti-overengineering rule applies here: each module must be planned to reach full production-stable scope in at most three implementation batches, and the first implementation batch must deliver a real minimum vertical slice rather than placeholders or one-field micro-slices.

---

## 2. Reference projects and allowed use

| Reference repo                       | Local path                    | License posture         | Use in 3F-R                                                                    | Direct source adaptation allowed?         |
| ------------------------------------ | ----------------------------- | ----------------------- | ------------------------------------------------------------------------------ | ----------------------------------------- |
| EasyXT                               | `参考项目/EasyXT/`            | MIT                     | data health rules, TDX pytdx provider shape, selected report/performance ideas | Yes, scoped and modified with attribution |
| JQ2PTrade                            | `参考项目/JQ2PTrade/`         | MIT per README          | API mapping, local DuckDB backtest lifecycle, report/data-loader shape         | Yes, scoped and modified with attribution |
| OpenBB                               | `参考项目/OpenBB/`            | AGPLv3                  | provider catalog / provider metadata architecture only                         | No source copy into QMD runtime           |
| agents-for-openbb                    | `参考项目/agents-for-openbb/` | MIT                     | future Round4 agent UI examples only                                           | Not in 3F-R runtime                       |
| TradingAgents / TradingAgents-astock | `参考项目/TradingAgents*`     | Verify before use       | future Round4 analysis graph / analyst taxonomy only                           | Not in 3F-R runtime                       |
| tdx-quant                            | `参考项目/tdx-quant/`         | Apache-2.0, Java/Spring | operations reference only                                                      | Not in QMD Python runtime                 |

---

## 3. What must be refactored in 3F-R

3F-R targets existing thin wheels that are already present after 3F:

1. ~~`backend/app/ops/data_health.py` daily bar checks~~ — **Done (R3FR-02):** `market_bar_p0` profile + shared OHLCV rules; evidence-path `check_daily_bars` remains a compatibility shim with redirect docstring.
2. ~~`backend/app/cli/data_commands.py::health_check` placeholder~~ — **Done (R3FR-06):** `qmd data health` delegates to `run_data_health_profile` read-only runtime.
3. ~~`TdxPytdxProbeFetchPort` self-written downloader risk~~ — **Done (R3FR-03):** thin delegate to `TdxPytdxFetchPort`; probe orchestration stays in `tdx_manual_probe`.
4. Round4 backtest task cards must stop implying a from-scratch backtest engine; they must explicitly adapt JQ2PTrade MiniPTrade local DuckDB lifecycle and selected EasyXT performance/report ideas.
5. Provider/plugin planning must stop being ad hoc; create a QMD provider catalog inspired by OpenBB provider metadata, without copying AGPL source.

---

## 4. What must be preserved

The following are not duplicate wheels and must not be removed:

- `SourceRegistry`
- `SourceCapabilityRegistry`
- `SourceRoutePlanner`
- `DataSourceService`
- `RawStore`
- `FileRegistry`
- `fetch_log`
- `WriteManager`
- `DbValidationGate`
- `ResourceGuard`
- source authorization gates
- no-mutation proof
- `source_fetch_id` / `content_hash` / `schema_hash` lineage semantics

These are QMD-specific governance boundaries. External repositories may supply data access and quality logic, but must not bypass this boundary.

---

## 5. Batch folder rule

From this point forward, unfinished executable work should be grouped by batch folder:

```text
docs/implementation_tasks/<ROUND_OR_THEME>/<BATCH_ID>/
```

Legacy loose task cards remain as historical input until they are rehomed or replaced by canonical batch-folder cards. Use redirects and index entries first, then retire obsolete loose cards only after CI proves all references were migrated.
