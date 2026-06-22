# QMD Ops Report CLI Design

> Status: user-frozen design input for Round 5 / Phase E. This document is not runtime code.
>
> Scope: convert local JSON evidence from ops tools into operator-readable Markdown/HTML reports—fully offline, no upload.
>
> Reference landing: `R3-REF-OPS-DB-DATA-HEALTH` / `R3D_ops_db_data_health_reference.md`.

## 1. Decision summary

The ops report tool answers:

> Given JSON evidence already produced on this machine, render a local report an operator can read without exposing data to the network.

Final command:

```bash
qmd ops report
```

Depends on stable JSON shapes from:

- `qmd ops db-inspect --format json`
- `qmd data health --format json` (Phase C)
- future `qmd ops source-health snapshot --read-only-preview`

Round 3 v1 does **not** implement this command.

## 2. Reference adoption boundary

| Reference pattern | Source | Adopt | Do not adopt |
| ----------------- | ------ | ----- | ------------ |
| Local-only / browser-side privacy wording | [ptqmt-site](https://github.com/quant-king299/ptqmt-site) | Report header/footer: data stays on device; no cloud upload | Online site layout as runtime dependency |
| Operator doc organization: summary → details → next steps | ptqmt-site + EasyXT troubleshooting style | Section order in Markdown/HTML templates | Trading tutorial or broker marketing copy |
| Repeatable local artifact generation | [JQ2PTrade](https://github.com/quant-king299/JQ2PTrade) report-builder pattern (concept only) | `--input` JSON + `--output` local file | Strategy/backtest report semantics |

Cross-reference: `docs/ops/privacy_data_flow.md`, `specs/contracts/user_input_privacy_contract.yaml`.

## 3. CLI contract (design)

```bash
qmd ops report \
  --input evidence/db_inspect_20260622.json \
  --format markdown \
  --output reports/local/db_inspect_20260622.md
```

### 3.1 Arguments

| Argument | Required | Default | Behavior |
| -------- | -------- | ------- | -------- |
| `--input` | Yes | — | Path to JSON evidence file (db-inspect, data-health, or merged bundle) |
| `--format` | No | `markdown` | `markdown` or `html` |
| `--output` | No | stdout | Local file path under project `data/reports/` or user-specified dir |
| `--title` | No | derived from evidence `mode` + timestamp | Report title |
| `--redact` | No | true | Strip paths/secrets per privacy contract |

### 3.2 Forbidden arguments

```text
--upload
--allow-network
--embed-external-cdn
--show-secrets
```

## 4. Report sections (QMD-owned)

1. **Privacy banner** — local-only; no transmission (ptqmt-site pattern).
2. **Executive summary** — PASS/WARN/FAIL, timestamp, evidence source command.
3. **DB / data path provenance** — `db.path`, `data_root.path`, row counts (from db-inspect).
4. **Domain health findings** — when input includes data-health JSON.
5. **Deferred item mapping** — trace hints for registry IDs (e.g. `DB-R3-001`).
6. **Next steps** — links to `docs/ops/TROUBLESHOOTING.md`, `ERROR_CODE_GUIDE.md` anchors only (no live URLs required).

Reports must never include raw credentials, full row payloads, or network calls.

## 5. JSON input compatibility

| `evidence_type` | Source command | Minimum fields |
| --------------- | -------------- | -------------- |
| `db_inspect` | `qmd ops db-inspect` | `status`, `db`, `key_tables`, `deferred_item_mapping` |
| `data_health` | `qmd data health` | `status`, `domain`, `summary`, `findings` |
| `bundle` | merge of above | `items[]` with `evidence_type` discriminator |

Unknown evidence types: render metadata + warning; do not crash.

## 6. Safety invariants

1. Pure local transform: read JSON file → write report file.
2. No DuckDB open required for v1 (optional future: `--live-db-inspect` stays out of Phase E v1).
3. No network, no upload, no external asset fetch.
4. Default redaction for home paths and tokens.

## 7. Implementation locations (future)

| Artifact | Path |
| -------- | ---- |
| Report builder | `backend/app/ops/report_models.py` |
| CLI | `scripts/qmd_ops.py` or `backend/app/cli/main.py` |
| Tests | `tests/test_ops_report.py` (future) |
| Output dir | `data/reports/` per `docs/modules/local_file_system.md` |

## 8. Phase plan

| Phase | Tool | Report support |
| ----- | ---- | -------------- |
| Phase A | `db-inspect` | JSON only; no report CLI |
| Phase C | `data health` | JSON only |
| Phase E | `qmd ops report` | Markdown/HTML from JSON |

## 9. External URLs (Source Context Index)

- `https://github.com/quant-king299/ptqmt-site` — privacy/report organization (primary)
- `https://github.com/quant-king299/EasyXT` — troubleshooting section style (secondary)
- `https://github.com/quant-king299/JQ2PTrade` — local report artifact pattern (secondary, backtest report concept only)
