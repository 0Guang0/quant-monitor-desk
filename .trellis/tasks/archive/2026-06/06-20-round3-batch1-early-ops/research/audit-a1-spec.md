# A1 audit-spec — §3.1

**Verdict:** PASS_WITH_FINDINGS

## Frozen DOUBT (spec scope?)

**CLAIM:** Round 3 Batch 1 `db-inspect` implementation is Phase A only, matches `ops_db_inspect_contract.yaml` + `db_inspect_cli.md` §5–11, and introduces no 017/migration/network/QMT enablement leakage.

**CONTRACT:** `specs/contracts/ops_db_inspect_contract.yaml`, `docs/ops/db_inspect_cli.md` (Phase A), `MASTER.plan.md` §2 AC-CLI-\* / §3.2–§3.4.

**DOUBT cycle (degraded — subagent, no nested reviewer):** Cross-examined artifact (`backend/app/ops/db_inspector.py`, `scripts/qmd_ops.py`, `tests/test_ops_db_inspector.py`) against contract fields, forbidden args, safety invariants, and MASTER out-of-scope table. Cross-model skipped: non-interactive audit subagent.

**RECONCILE:** Core read-only inspect behavior and JSON shape satisfy the frozen contract. Two production import paths are absent from `implement.jsonl` (traceability gap, not behavioral scope creep). One contract-listed acceptance test (forbidden SQL flag) is missing. No evidence of 017/migration/network/QMT leakage in ops deliverables.

## §tests ran / commands

| Command                                                                                                            | Result                                                                                                                                                |
| ------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `python -m pytest tests/test_ops_db_inspector.py -q`                                                               | 10 passed                                                                                                                                             |
| `python scripts/qmd_ops.py db-inspect --help`                                                                      | Only contract-allowed flags; no forbidden flags                                                                                                       |
| `rg` forbidden patterns in `backend/app/ops/`, `scripts/qmd_ops.py`                                                | No `apply_migrations`, `writer(`, `--enable-qmt`, `--allow-network`, `--sql`, DML verbs                                                               |
| `rg` future-phase commands in ops (`env-doctor`, `source probe`, `data health`, etc.)                              | No matches                                                                                                                                            |
| `rg` layer 017–023 / `layer*` in ops + qmd_ops                                                                     | No matches                                                                                                                                            |
| `python -m ruff check backend/app/ops scripts/qmd_ops.py tests/test_ops_db_inspector.py`                           | 4 style issues (I001, E501×2, F401) — not spec blockers                                                                                               |
| Manual contract field diff: `REQUIRED_TOP_LEVEL_FIELDS` vs `ops_db_inspect_contract.yaml` `required_output_fields` | Exact match (11 fields)                                                                                                                               |
| Manual `KEY_TABLES` vs contract `key_tables`                                                                       | 14/14 match                                                                                                                                           |
| `check.jsonl` vs changed impl paths                                                                                | check.jsonl lists audit gates only (contract, Phase A doc, registries); impl paths correctly traced via MASTER §3.1 + contract `implementation_paths` |

## Findings (ID | Sev | Finding | §4.3?)

| ID     | Sev  | Finding                                                                                                                                                                                                                                                                                                                  | §4.3? |
| ------ | ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----- |
| A1-F01 | MED  | **`implement.jsonl` undeclared production import:** `backend/app/ops/db_inspector.py` imports `quote_ident` from `backend/app/db/sql_identifiers.py`. Contract §8.3 authorizes identifier utilities; `implement.jsonl` lists `connection.py` (L34) but not `sql_identifiers.py`. Execute trace incomplete for A5.        | Y     |
| A1-F02 | MED  | **`implement.jsonl` undeclared CLI default path:** `scripts/qmd_ops.py` imports `DATA_ROOT` from `backend/app/config.py` for `_default_db_path()` / `_default_data_root()`. Not listed in `implement.jsonl` (41 lines, none reference `config.py`).                                                                      | Y     |
| A1-F03 | LOW  | **Contract §11.1 test gap:** `db_inspect_cli.md` requires “Forbidden SQL flag — v1 CLI rejects or does not expose free SQL.” `tests/test_ops_db_inspector.py` has no assertion that `--sql` is absent or rejected. CLI help confirms absence; automated AC-CLI-3 trace is incomplete.                                    | Y     |
| A1-F04 | LOW  | **`--output` mkdir drift:** `qmd_ops.py` L72 `args.output.parent.mkdir(parents=True, exist_ok=True)` creates parent dirs. `db_inspect_cli.md` §6.3 states parent “must already exist unless explicitly created by a future report command.” Phase A inspect is not that future command.                                  | Y     |
| A1-F05 | INFO | **Contract `implementation_paths` includes deferred `backend/app/cli/main.py`:** Listed in YAML L18 but MASTER §3.2 defers packaging to Round 5. Implementation correctly uses transitional `scripts/qmd_ops.py` only — not a leakage finding, but contract path list overstates v1 deliverables.                        | N     |
| A1-F06 | INFO | **GitNexus index stale for new symbols:** `impact({target: "DbInspector"})` and `context({name: "DbInspector"})` return not found. New ops module not yet in graph; `ConnectionManager.reader` impact shows LOW risk (1 direct upstream caller in indexed graph — `ci_ingestion_smoke.py`; inspect path not yet linked). | N     |
| A1-F07 | INFO | **Scope leakage negative (017 / migration / network / QMT):** No ops changes under `backend/app/layer*`, `migrations/`, sync/fetch orchestration, or forbidden CLI flags. Tests use `apply_migrations`/`writer()` only for fixture setup — outside production inspect path.                                              | N     |

### MASTER §2 AC spot-check (A1-relevant)

| AC       | A1 assessment                                                                                       |
| -------- | --------------------------------------------------------------------------------------------------- |
| AC-CLI-1 | PASS — `DbInspector.inspect()` + all contract top-level fields present                              |
| AC-CLI-2 | PASS — `qmd_ops.py db-inspect` thin wrapper; `--format text\|json`                                  |
| AC-CLI-3 | PASS_WITH_GAP — read-only invariant tested (byte-unchanged DB); forbidden-SQL test missing (A1-F03) |
| AC-CLI-4 | PASS — 14 key_tables, data_root counts, deferred_item_mapping, schema + evidence blocks             |
| AC-CLI-5 | PASS — missing DB → FAIL; schema-only → WARN; semantic status rules in `_derive_status`             |
| AC-OPS-1 | PASS — no `--enable-qmt`; inspect reports evidence only                                             |

## GitNexus evidence

| Call                                                                                                           | Result                                                                                                  |
| -------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `impact({target: "DbInspector", direction: "upstream", file_path: "backend/app/ops/db_inspector.py"})`         | **UNKNOWN** — symbol not indexed (new file)                                                             |
| `context({name: "DbInspector", file_path: "backend/app/ops/db_inspector.py"})`                                 | **Not found** — index stale                                                                             |
| `impact({target: "reader", kind: "Method", direction: "upstream", file_path: "backend/app/db/connection.py"})` | **LOW** risk; d=1: `ci_ingestion_smoke.main`; 1 process affected; inspect’s new caller not yet in graph |
| `query({query: "db inspector ops read-only ConnectionManager"})`                                               | Returns `ConnectionManager.reader` + existing read paths; no `DbInspector` process yet                  |

**Undeclared dependency conclusion (adversarial trigger):** At least two production modules used by deliverables are absent from `implement.jsonl`: `sql_identifiers.py` (A1-F01), `config.py` (A1-F02). `duckdb` is imported in `db_inspector.py` for type hints only; connections go through `ConnectionManager.reader()` — consistent with contract §8.1.

## §4.3 repair items

| Item    | Action                                                                                                                                       | Owner                   |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------- |
| R-A1-01 | Append `backend/app/db/sql_identifiers.py` to `implement.jsonl` with reason “quote_ident for fixed metadata COUNT queries per contract §8.3” | Execute / Plan hygiene  |
| R-A1-02 | Append `backend/app/config.py` to `implement.jsonl` with reason “DATA_ROOT defaults for transitional CLI”                                    | Execute / Plan hygiene  |
| R-A1-03 | Add test `test_qmdOps_cli_rejectsForbiddenSqlFlag` (subprocess `--sql` → exit ≠ 0 or argparse error) per `db_inspect_cli.md` §11.1           | A8 or follow-up Execute |
| R-A1-04 | Either remove `mkdir(parents=True)` from `--output` path or amend `db_inspect_cli.md` §6.3 to allow mkdir for `--output` in Phase A          | Docs / CLI alignment    |
| R-A1-05 | Run `node .gitnexus/run.cjs analyze` so `DbInspector` / `format_text_report` enter graph for future impact gates                             | Ops hygiene             |

None of R-A1-01–05 block Phase A behavioral correctness; they close traceability and contract-test gaps before A9 final PASS.
