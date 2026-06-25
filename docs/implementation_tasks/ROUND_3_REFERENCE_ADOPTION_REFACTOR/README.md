# Round 3F-R — Reference Adoption Refactor

> **Canonical status:** post-3F / pre-3G planning package.  
> **Reason:** Batch 3F is complete and green, but several thin self-built modules now need controlled replacement or hardening using mature reference projects before sandbox clean-write rehearsal.  
> **Executable batch entrypoint:** `BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/README.md`.

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

1. `backend/app/ops/data_health.py` daily bar checks are too thin compared with EasyXT integrity checks.
2. `backend/app/cli/data_commands.py::health_check` still returns `not_implemented_phase_c`, even though Batch 3F has completed.
3. `backend/app/ops/interface_probe_fetch_ports.py::TdxPytdxProbeFetchPort` should not grow into a self-written TDX downloader; TDX connection/provider details should be adapted from EasyXT or another vetted pytdx provider while keeping QMD authorization and caps.
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
