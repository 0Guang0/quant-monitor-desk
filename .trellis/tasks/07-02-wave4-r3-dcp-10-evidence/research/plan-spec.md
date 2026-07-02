# Plan Spec — R3-DCP-10 Layer5 Evidence Binding

## Objective

Bind Layer5 factual evidence to real Tier A fetch provenance for one P0 CN equity daily bar path (mootdx → security_bar_1d → foundation + lineage).

## Tech Stack

Python 3.12 · DuckDB · pytest · existing DataSourceService / WriteManager chain

## Commands

```bash
uv run pytest tests/test_layer5_provenance_bridge.py -q      # S01
uv run pytest tests/test_layer5_mootdx_bar_clean_e2e.py -q   # S02
uv run pytest -q                                              # S03
```

## Project Structure

```
backend/app/datasources/normalizers/evidence_bundle.py  # extend bundle_layer5_provenance
backend/app/layer5_evidence/provenance.py                # new bridge (Execute)
backend/app/layer5_evidence/{foundation,lineage,models}.py
tests/test_layer5_provenance_bridge.py                   # Execute
tests/test_layer5_mootdx_bar_clean_e2e.py                # Execute
```

## Code Style

ponytail · karpathy-guidelines · 中文五字段 docstring on tests

## Testing Strategy

TDD RED→GREEN per slice. S01 unit proves mapping; S02 e2e proves fetch→clean→Layer5. No live network default.

## Boundaries

### Always

- WriteManager clean path only
- Provenance from same-run fetch bundle
- replay fixture default

### Never

- Staged placeholder fetch ids in e2e assertions
- New migration without ADR
- Runtime import 参考项目
- Full instrument matrix

## Success Criteria

- [ ] Provenance mapping table (reference-adoption-dcp10 §4) implemented
- [ ] `test_layer5_mootdx_bar_clean_e2e.py` GREEN
- [ ] ACC-LAYER-E2E G5 subset closed
- [ ] `uv run pytest -q` exit 0

## ASSUMPTIONS

- DCP-05 mootdx incremental e2e remains green on master
- `cn_market_evidence_v1` schema_version stable
- Layer5 DB persistence deferred (foundation validator slice only)

## Open Questions

None at Plan freeze.
