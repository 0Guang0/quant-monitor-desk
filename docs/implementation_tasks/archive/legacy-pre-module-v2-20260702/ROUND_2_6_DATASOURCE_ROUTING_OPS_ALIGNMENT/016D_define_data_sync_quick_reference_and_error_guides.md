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

## Unresolved item coverage（Plan 不得遗漏）

Plan 阶段必须读取 `docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md`，并核对以下仍未闭合项：

| ID            | 目标阶段                                  | 本任务卡处理要求                                                                                                                     |
| ------------- | ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `R2.6-IMPL-6` | Round3 Batch6 ops 或 Round5 task 035 prep | `qmd data` / production CLI 必须有 dry-run、route-preview、error_code/docs_anchor、smoke test；若不实现，保留 explicit re-deferral。 |
| `D2-P1-3`     | Round3 Batch6 ops / task 035 prep         | `python -m quant_monitor.sync` 或 successor console script smoke 必须在 CLI 计划中出现。                                             |
| `R2-GAP-1`    | Round3 Batch6 init / Round5 packaging     | `init_db --sync-registry` 或 documented CI one-liner 必须进入 operator docs 或明确 re-defer。                                        |
| `D7-P2-2`     | Batch6 / Round5 packaging                 | 移除 `sys.path.insert` smell，改为 editable install / console scripts；若不关闭，必须转交 035。                                      |
