# 016A — Define SourceCapabilityRegistry

## Scope

Design/spec only. Do not change code.

## Inputs

- `docs/modules/source_capability_registry.md`
- `specs/datasource_registry/source_capabilities.yaml`
- `specs/contracts/source_capability_contract.yaml`
- `docs/modules/data_sources.md`

## Required design updates

1. Treat `SourceRegistry` as source/domain/role authority.
2. Add `SourceCapabilityRegistry` as operation/field/frequency authority.
3. Require every `allowed_domain` to have capability coverage.
4. Require adapter `supported_domains` to be subset of capability registry.
5. Keep QMT/qmt_xqshare disabled until user authorization.

## Future implementation tasks

- Add `backend/app/datasources/capability_registry.py`.
- Add `tests/test_source_capabilities.py`.
- Wire capability check before any production fetch.

## Acceptance commands

```bash
python -m pytest tests/test_source_capabilities.py tests/test_source_registry.py tests/test_adapter_skeletons.py -q
```

## Phase A evidence

This task is complete when design docs/contracts exist and are indexed. No code changes are allowed in Phase A.
