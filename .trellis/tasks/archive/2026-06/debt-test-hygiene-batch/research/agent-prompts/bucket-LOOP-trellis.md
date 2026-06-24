# Agent 派发 — 桶 LOOP（Loop Engineering / Trellis / Docs / Scaffold）

> **Worktree：** `debt/test-hygiene/bucket-loop-trellis` from `master`  
> **Bucket ID：** LOOP

## Allowed files

```
tests/test_loop_engineering_flow.py
tests/test_docs_specs_indexed.py
tests/test_documentation_index.py
tests/test_trellis_validate_plan.py
tests/test_trellis_validate_execute.py
tests/test_docstring_quadruple_coverage.py
tests/test_module_boundaries.py
tests/test_project_scaffold.py
tests/test_backend_smoke.py
```

## 特殊注意

- **本桶全部在禁止删清单 §3.4**：`deletion-candidates.yaml` 必须为 `candidates: []`
- `test_loop_engineering_flow.py` 验证 catalog/loop CI：改动必须保持与 `scripts/check_test_catalog.py` 一致
- trellis validate 测试可能扫描 `.trellis/tasks/`：ponytail 勿缩短到漏检真实 gate
- meta 测试（docstring_quadruple、module_boundaries）改动需格外谨慎：断言减少必须仍满足注释验证点

## 验证命令

```powershell
cd C:\Users\Guang\Desktop\quant-monitor-desk
uv run python -m pytest tests/test_loop_engineering_flow.py tests/test_docs_specs_indexed.py tests/test_documentation_index.py tests/test_trellis_validate_plan.py tests/test_trellis_validate_execute.py tests/test_docstring_quadruple_coverage.py tests/test_module_boundaries.py tests/test_project_scaffold.py tests/test_backend_smoke.py -q --tb=short
```

## 证据

`.trellis/tasks/debt-test-hygiene-batch/execute-evidence/bucket-LOOP-*`

## 公共约束

见 `_COMMON.md`。
