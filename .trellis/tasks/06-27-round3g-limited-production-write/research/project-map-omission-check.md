# Project Map Omission Check — R3G-03

> `uv run python scripts/check_docs_specs_indexed.py` — **OK** (2026-06-27)

## 机械检查

```
OK: docs/specs indexed (MIGRATION_MAP + generated index)
```

## EXECUTION_INDEX §3 倒查 project_map

对照 `docs/generated/project_map.generated.json` 中 `backend/app/ops/sandbox_clean_write` 与 Round 3G 相关路径：

| 路径                                                              | project_map              | §3 manifest        | 结论 |
| ----------------------------------------------------------------- | ------------------------ | ------------------ | ---- |
| `backend/app/ops/sandbox_clean_write/rehearsal_runner.py`         | 应有                     | 已列               | OK   |
| `backend/app/ops/sandbox_clean_write/adversarial_audit.py`        | 应有                     | 已列（对抗审计补） | OK   |
| `backend/app/ops/sandbox_clean_write/audit_decision.py`           | 应有                     | 已列               | OK   |
| `backend/app/ops/mutation_proof.py`                               | 应有                     | 已列               | OK   |
| `backend/app/ops/sandbox_clean_write/limited_production_entry.py` | 已存在（R3G-03 Execute） | 活卡 §4；frozen §4 | OK   |
| `specs/contracts/sandbox_clean_write_contract.yaml`               | 应有                     | 已列               | OK   |
| `tests/test_round3g_limited_production_clean_write.py`            | 应有                     | 通过 §2 引用       | OK   |
| `tests/test_round3g_limited_production_rollback.py`               | 应有                     | 通过 §2 引用       | OK   |
| `docs/implementation_tasks/.../R3G_03_*.md`                       | README 索引              | source_card        | OK   |

## 发现遗漏（已修复）

| ID   | 遗漏                                              | 修复                                  |
| ---- | ------------------------------------------------- | ------------------------------------- |
| O-01 | §3 初稿缺 `adversarial_audit.py`                  | 已加入 EXECUTION_INDEX §3             |
| O-02 | §3 缺 R3G-02 execute-evidence 指针                | 已加入                                |
| O-03 | §3 缺 `rehearsal_plan.py`                         | 已加入                                |
| O-04 | §3 缺 `tests/fixtures/sandbox_clean_write/r3g01/` | 已加入（promote 对齐 rehearsal 证据） |

## 仍待 Execute

| ID   | 项                                          | 说明                     |
| ---- | ------------------------------------------- | ------------------------ |
| O-05 | `tests/fixtures/sandbox_clean_write/r3g03/` | ✅ Plan 最小四套样板已建 |
| O-06 | `loop_maintain` catalog 新测模块            | Execute 新文件后 `--fix` |

## 结论

**索引完整**（Plan 门禁）；无未解释的 project_map 包缺口。
