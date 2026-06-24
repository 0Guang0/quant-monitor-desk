# Agent 派发 — 桶 AUD（Audit / R3X Remediation）

> **Worktree：** `debt/test-hygiene/bucket-audit-r3x` from `master`  
> **Bucket ID：** AUD

## Allowed files

```
tests/test_audit_fixes.py
tests/test_audit_remediation.py
tests/test_r3x_ponytail_pilot_prep_bucket_a.py
tests/test_r3x_ponytail_structural_bucket_b.py
tests/test_r3x_residual_open_items_closure.py
```

## 特殊注意

- 本桶是 **Phase C 最可能产出 deletion 候选** 的区域，但须满足 DEBT.plan.md §3.5 全部条件
- `test_r3x_ponytail_pilot_prep_bucket_a.py` / `bucket_b` 是近期 ponytail pilot 成果：对齐时与 production 契约（DS/SC/OP 项）保持一致
- `test_audit_fixes.py` vs `test_audit_remediation.py`：若发现重复覆盖，在 candidates 中说明 **replacement_coverage**，不要 Phase A 直接删
- 历史 Round2 audit 回归可能已 stale：用 `/ponytail ultra` 评估是否 whole-file 候选，仍须用户 Phase D 批准

## 验证命令

```powershell
cd C:\Users\Guang\Desktop\quant-monitor-desk
uv run python -m pytest tests/test_audit_fixes.py tests/test_audit_remediation.py tests/test_r3x_ponytail_pilot_prep_bucket_a.py tests/test_r3x_ponytail_structural_bucket_b.py tests/test_r3x_residual_open_items_closure.py -q --tb=short
```

## 证据

`.trellis/tasks/debt-test-hygiene-batch/execute-evidence/bucket-AUD-*`

## 公共约束

见 `_COMMON.md`。
