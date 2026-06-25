# Repair/Debt Lite Plan — round3f-registry-batch-closeout (B3F-REG)

> Track: **debt-lite** · Branch: `chore/round3f-registry-batch-closeout` · Baseline: `7f628c9`  
> Playbook: `BATCH_3F_COORDINATOR_PLAYBOOK.md` §3.8 + §5.1 · Manifest: §2–§4

## Slice table（每行一个 registry ID 或 reconcile 主题）

| Slice  | Registry / theme  | Decision                                                      | Verification                                             |
| ------ | ----------------- | ------------------------------------------------------------- | -------------------------------------------------------- |
| REG-01 | `R3-PARTIAL-5`    | **VERIFY-ONLY** — RESOLVED B3V-C04; COVERAGE+map CLOSED       | `test_batch3vR3Partial5_*` · `test_batch3fMap_*`         |
| REG-02 | `R2-RISK-3`       | **VERIFY-ONLY** — RESOLVED post-14 B-008; COVERAGE+map CLOSED | `test_post14R2Risk3_*` · `test_batch3fR2Risk3_*`         |
| REG-03 | `R3-AUDIT-DEF-03` | **VERIFY-ONLY** — RESOLVED post-14 Slice 3; COVERAGE CLOSED   | `test_post14AuditDef03_*` · `test_batch3fR3AuditDef03_*` |
| REG-04 | `WAVE-B-HYG-01`   | **RECONCILED** — Last reconciled token parity                 | `test_r3yRegistrySlice_alpha2LastReconciled`             |
| REG-05 | `WAVE-B-HYG-02`   | **RECONCILED** — substrings OK; stricter assert → B3F-HYG     | alignment tests pass                                     |
| REG-06 | `WAVE-B-HYG-03`   | **RE-DEFERRED** ops escape hatch                              | Wave-B §5 note only                                      |
| REG-07 | `R3F-LIN-03`      | **RECONCILE** Wave-B residual hygiene rows                    | `test_batch3fWaveBHygieneRegistry_*`                     |

## Allowed files

- `docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md`
- `docs/quality/待修复清单.md`
- `ROUND3_BATCH_IMPLEMENTATION_MAP.md` (Batch 6 closed-row narrative only)
- `tests/test_unresolved_item_task_coverage.py`
- `tests/test_round3_audit_registry_alignment.py`
- `.trellis/tasks/round3f-registry-batch-closeout/**`

## Forbidden

- Direct commit `RESOLVED` / `UNRESOLVED` / `AUDIT_DEFERRED` closure rows (proposed delta only)
- `backend/app/**` runtime changes
- Reopen `R3-PARTIAL-5` / `R2-RISK-3` / `R3-AUDIT-DEF-03` implementation

## Verification (§8.7)

```bash
uv sync --locked
uv run pytest tests/test_unresolved_item_task_coverage.py tests/test_round3_audit_registry_alignment.py -q
uv run python scripts/check_manifest_files.py
uv run pytest -q
```

## Merge gate

- Six complex-line evidence 齐后主会话合并（本分支排最后）
- `research/registry_proposed_delta.yaml` 交主会话批处理 registry 三件套
