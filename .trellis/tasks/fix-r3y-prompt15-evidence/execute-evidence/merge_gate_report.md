# Merge gate — fix/r3y-prompt15-evidence (α-3)

**Slice:** α-3 close `R3Y-PROMPT15-EVID-001` (PROMPT_15 execute evidence backfill)  
**Branch:** `fix/r3y-prompt15-evidence` @ `555fd33b`  
**Registry:** **不修改**三 registry — closure 由主会话 Wave C 批处理

## Problem closed

AUD-01 F-01：PROMPT_15 merge_gate 宣称 73 项闭合，但 execute-evidence 无 `*-green.txt`，仅 `# exit 0` 占位。

## Solution

| 产物 | 路径 |
| ---- | ---- |
| closed-claim 索引 SSOT | `.trellis/tasks/archive/2026-06/fix-round3-r3x-residual-open-items-closure/execute-evidence/closed_claim_evidence_index.yaml` |
| 9 × green.txt | 同上 `execute-evidence/g*.txt`, `umbrella-r3x-green.txt`, `full-pytest-green.txt` |
| merge_gate 更新 | 同上 `merge_gate_report.md`（Execute evidence 节） |
| 审计门禁测试 | `tests/test_r3x_residual_open_items_closure.py::test_r3yPrompt15_closedClaimEvidenceIndexMapsToGreenTxt` |

## GitNexus

| Tool | Result |
| ---- | ------ |
| `impact(test_r3yPrompt15_*)` | 新符号未入索引（stale index）；仅 tests/ 增量 |
| `detect_changes(all)` | **LOW** — 1 test file；0 affected processes |

## Commands

```bash
uv run pytest tests/test_r3x_residual_open_items_closure.py -q
# 19 passed

uv run pytest -q
# full suite green — see full-pytest-green.txt
```

## Evidence

| File | Status |
| ---- | ------ |
| `execute-evidence/α3-red.txt` | RED — index missing |
| `execute-evidence/α3-green.txt` | GREEN — 1 passed |
| archive `execute-evidence/*-green.txt` | 9 files |
| archive `closed_claim_evidence_index.yaml` | 73 claim_ids |

## Files changed

- `tests/test_r3x_residual_open_items_closure.py` — evidence index gate test + path constants
- `.trellis/tasks/fix-r3y-prompt15-evidence/DEBT.plan.md`
- `.trellis/tasks/archive/2026-06/fix-round3-r3x-residual-open-items-closure/execute-evidence/**`

## Out of scope (explicit)

- `backend/**` — 未改
- registry 三件套 — 未改
- `R3Y-TEST-DEPTH-001` — Batch 6 per-ID runtime depth
- 对抗性审计 — 留给主会话下一派发

## Remaining deferred

| ID | Owner | Note |
| -- | ----- | ---- |
| `R3Y-TEST-DEPTH-001` | Batch 6 | per-ID runtime-strong pytest |
| registry CLOSED row | 主会话 | Wave C merge 后批处理 `R3Y-PROMPT15-EVID-001` |

## Adversarial audit

| 项 | 值 |
| -- | -- |
| 报告 | `adversarial-audit.report.md` |
| Verdict | **PASS** |
| OPEN (BLOCKING) | **0** |
| 审计补丁 | `closed_claim_evidence_index.yaml` g3/g7 claim_id 校正 + 测试 exact 73-ID 集合断言 |
