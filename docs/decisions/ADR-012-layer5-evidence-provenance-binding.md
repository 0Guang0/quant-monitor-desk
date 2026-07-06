# ADR-012：Layer5 证据血缘绑定

**Status:** Accepted (Plan freeze)  
**Date:** 2026-07-02  
**Context:** R3-DCP-05 closed Tier A incremental clean writes including mootdx → `security_bar_1d`. Layer5 foundation/lineage (023A) validates provenance shape but tests use staged placeholders (`fetch-staged-001`). Wave 4 DCP-10 must prove **one** factual evidence path binds real fetch bundle fields.

## Decision

1. **P0 vertical slice (frozen):**

| field          | value                             |
| -------------- | --------------------------------- |
| data_domain    | `cn_equity_daily_bar`             |
| source_id      | `mootdx`                          |
| instrument_id  | `sh.600519`                       |
| clean_table    | `security_bar_1d`                 |
| evidence_kind  | `factual_source` / `price_volume` |
| schema_version | `cn_market_evidence_v1`           |

2. **Provenance field mapping** (fetch bundle → Layer5):

| bundle field              | Layer5 destination                                                                  |
| ------------------------- | ----------------------------------------------------------------------------------- |
| `source_fetch_id`         | `SourceProvenance.source_fetch_ids[0]` · lineage `source_fetch_ids`                 |
| `content_hash`            | `SourceProvenance.source_content_hashes[0]` · lineage `source_content_hashes`       |
| `schema_hash`             | `SourceProvenance.source_dataset_ids` entry `schema:{schema_hash}@{schema_version}` |
| `schema_version`          | `source_dataset_ids` entry `version:{schema_version}`                               |
| `source_id` + clean table | `source_dataset_ids` entry `clean:security_bar_1d@{source_id}`                      |
| `data_domain`             | `source_dataset_ids` entry `domain:cn_equity_daily_bar`                             |

3. **Implementation:** Extend `bundle_layer5_provenance` + QMD-owned `build_source_provenance_from_bundle` in `layer5_evidence/provenance.py`. E2e test reads bundle from same incremental run raw layout.

4. **No new migration.** No evidence_chain DB persistence in DCP-10 (foundation + lineage envelope only).

5. **ACC-LAYER-E2E-LIVE-001:** DCP-10 closes **G5 subset** only; L1–L4 and full L1–L5 chain remain open for DCP-07/08 + `R3H-05-GATE`.

## Alternatives considered

- **baostock as P0:** Rejected for DCP-10 — mootdx has green DCP-05 e2e + existing `cn_market_bundle_layer5_provenance`; baostock remains in layer5_instrument_source_plan for later wave.
- **Add schema_hash to SourceProvenance dataclass:** Rejected — breaks snapshot_lineage_contract parity; dataset id encoding is ponytail-compatible.
- **Live fetch in AC:** Rejected — replay proves binding logic; live gated by ADR-008.

## Consequences

- Execute touches `evidence_bundle.py`, new `layer5_evidence/provenance.py`, two test modules.
- GitNexus impact LOW on `Layer5LineageBuilder`.
- K1 layer5 readiness may note mootdx bar provenance sample (Execute S03).
