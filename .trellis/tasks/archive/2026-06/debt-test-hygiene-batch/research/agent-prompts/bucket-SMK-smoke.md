# Agent 派发 — 桶 SMK（Smoke）

> **Worktree：** `debt/test-hygiene/bucket-smk-smoke` from `master`  
> **Bucket ID：** SMK

## Allowed files

```
tests/smoke/test_foundation_smoke.py
```

只读：`tests/smoke/__init__.py`

## 特殊注意

- smoke 测试在禁止删清单：**不得** deletion candidate
- ponytail 强度 **full** 即可（非 ultra）：保持端到端路径可读，优先删重复 import/setup
- 文件极小：align-checklist 仍须逐用例填写

## 验证命令

```powershell
cd C:\Users\Guang\Desktop\quant-monitor-desk
uv run python -m pytest tests/smoke/test_foundation_smoke.py -q --tb=short
```

## 证据

`.trellis/tasks/debt-test-hygiene-batch/execute-evidence/bucket-SMK-*`

## 公共约束

见 `_COMMON.md`。
