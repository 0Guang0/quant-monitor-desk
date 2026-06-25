# B3F-HYG Repair 二轮 — Audit WARN 闭合

> 基线 commit：`e65c9718492f5880b959baaa3ce448503c86bf2c`  
> 日期：2026-06-25

## 闭合项

| WARN ID | 维 | 修复 |
|---------|-----|------|
| AA-HYG-A1-02 | A1 | `audit.report.md` + `audit_matrix.json` + `research/audit-evidence/a1–a8.md` |
| AA-HYG-A5-01 | A5 | `8.3-green.txt` 全量 §8.6 日志（含 53 passed layer1 obs） |
| AA-HYG-A5-02 / A8-01 | A5/A8 | `test_layer1_observation_ingestion.py` autouse RG stub（ponytail，对齐 staged_pilot） |

## 复验命令

```text
QMD_RESOURCE_PROFILE=normal
uv run pytest tests/test_resource_guard.py tests/test_production_equivalent_smoke_budget.py tests/test_layer1_sandbox_bootstrap.py -q  → 42 passed
uv run pytest tests/test_layer1_observation_ingestion.py -q  → 53 passed
uv run python scripts/loop_maintain.py  → OK
```

证据：`research/execute-evidence/8.3-green.txt`
