# 016D — Define Data Sync Quick Reference and Error Guides

## Scope

Design/docs only. Do not change code.

## Inputs

- `docs/ops/data_sync_quick_reference.md`
- `docs/ops/data_sync_command_matrix.md`
- `docs/ops/ERROR_CODE_GUIDE.md`
- `docs/ops/TROUBLESHOOTING.md`
- `docs/ops/incident_playbook.md`
- `docs/ops/db_inspect_cli.md`
- `specs/contracts/data_cli_contract.yaml`
- `specs/contracts/ops_db_inspect_contract.yaml`

## Required design updates

1. Add operator-oriented data sync command matrix.
2. Every write-capable command must have dry-run design.
3. Every failure must include error code and docs anchor.
4. Disabled source and ResourceGuard pauses must be documented as normal protected outcomes.

## Future implementation tasks

- Add CLI wrapper only after user approval.
- Add `tests/test_data_cli_contract.py`.
- Link API/CLI errors to docs anchors.

## Acceptance commands

```bash
python scripts/check_doc_links.py
python -m pytest tests/test_data_cli_contract.py tests/test_documentation_index.py -q
```
