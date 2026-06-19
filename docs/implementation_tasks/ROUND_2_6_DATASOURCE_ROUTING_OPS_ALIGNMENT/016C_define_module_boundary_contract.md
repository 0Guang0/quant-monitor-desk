# 016C — Define Module Boundary Contract

## Scope

Design/spec only. Do not change code.

## Inputs

- `docs/architecture/module_boundary_matrix.md`
- `specs/contracts/module_boundary_contract.yaml`

## Required design updates

1. Datasources must not import API/Agent/WriteManager.
2. API must not import vendor adapters.
3. Agent must remain read-only and must not import WriteManager or sync runners.
4. Round3 Layer modules must consume clean snapshots, lineage, and quality flags rather than raw adapters.
5. Frontend must never be imported by backend modules.

## Future implementation tasks

- Add `scripts/check_module_boundaries.py`.
- Add `tests/test_module_boundaries.py`.
- Fix any import violations with minimal refactor.

## Acceptance commands

```bash
python scripts/check_module_boundaries.py
python -m pytest tests/test_module_boundaries.py -q
```

## Residual risk

This Phase A only defines the boundary contract. The actual import scan is a future implementation step.
