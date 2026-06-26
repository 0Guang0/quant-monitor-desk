# A7 — Ops / CLI / DB（R3FR-07 对抗性二审）

| 字段             | 值                                          |
| ---------------- | ------------------------------------------- |
| **Verdict**      | **SKIP**                                    |
| **Branch**       | `chore/round3fr-cleanup-rehome` vs `master` |
| **Date**         | 2026-06-27                                  |
| **Model**        | composer-2.5                                |
| **BLOCKING**     | 0                                           |
| **NON-BLOCKING** | A7-001 ~ A7-006                             |

## SKIP 确认

- 4 个 backend 文件仅 +20 行 docstring；无 `health_check`/`init_basic`/migrate 逻辑变更
- `uv run pytest tests/test_qmd_data_cli.py tests/test_data_cli_contract.py tests/test_r3fr07_legacy_wrapper_cleanup.py::test_healthCheck_canonicalRedirectDoc -q` → **22 passed**
- 契约 `must_use` / `forbidden_args` / `cli_envelope_from_report` 与 `data_cli_contract.yaml` 对齐

## NON-BLOCKING（统一修复登记）

| ID     | 发现                                                                              |
| ------ | --------------------------------------------------------------------------------- |
| A7-001 | 预存 `init_basic(dry_run=False)` 写库路径（OUT-OF-SCOPE 本分支，仍须修复/文档化） |
| A7-002 | `db-path` 未实扫 DuckDB，仅 limitation 文案                                       |
| A7-003 | `schema_hash_coverage` 恒 `{}`                                                    |
| A7-004 | GitNexus 未索引 `run_data_health_profile`                                         |
| A7-005 | `tdx_manual_probe` redirect 无专用单测（合并 A8 G4）                              |
| A7-006 | `init-basic` 缺对等 ops 设计文档                                                  |

**落盘：** 主会话代写（A7 agent readonly）。
