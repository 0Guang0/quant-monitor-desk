# Batch 3V Hardening Rules

> Applies to every task card in `BATCH_3V_VERIFIED_AUDIT_CLEANUP`.  
> If a card conflicts with these rules, the **stricter safety rule wins**.

---

## 1. Canonical execution rule

This batch is **verified-audit cleanup**, not production entry.

Allowed output language:

- `VR-* resolved with evidence`
- `VR-* re-deferred with owner, phase, closure test`
- `audit finding stale — reconciled against post Batch 01 master`
- `contract/runtime drift now test-detectable`
- `fail-closed behavior verified`

Forbidden output language:

- `production-live ready`
- `production clean write enabled`
- `production-ready`
- `full-market ingestion complete`
- `FRED/TDX/QMT/Yahoo production enabled`
- `Layer5 production-ready` (without post-audit evidence beyond reconcile)

---

## 2. Closeout rule

- Do not close a `VR-*` item by implication.
- If master already fixed the issue, produce **reconciliation evidence** and update registry — do not reimplement.
- If scope exceeds the card, **split** to Round 3F / 3G / 4 / 5 — do not absorb into Batch 3V.

---

## 3. Live / production boundary

- **No live source fetch** in Batch 3V.
- **No production clean write.**
- **No production DB mutation** unless a card explicitly requires read-only inspect evidence.
- db-inspect and reconcile paths remain read-only.

---

## 4. Implementation discipline（**MUST · 派发前抄入 Plan Boundary**）

| Rule                     | Requirement                                                                                                                                |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------ |
| **karpathy-guidelines**  | All production **and test** code; read before GREEN                                                                                        |
| **testing-guidelines**   | All tests; sufficient behavioral coverage; no weak-only asserts                                                                            |
| `/to-issues`             | Plan freeze (complex) or `DEBT.plan` slices (debt-lite) before code                                                                        |
| **TDD**                  | Production code: RED (must FAIL) → karpathy + testing-guidelines → GREEN + `execute-evidence`                                              |
| **Ponytail**             | `backend/` · `scripts/` · `tests/` — minimal diff; Chinese docstrings exempt from «few comments»                                           |
| **Five-field docstring** | Every `test_*`: 覆盖范围 / 测试对象 / 目的/目标 / 验证点 / 失败含义 — missing = **BLOCKING**                                               |
| **Full pytest**          | After any fix: `uv run pytest -q` all green before branch Done                                                                             |
| **Test purpose frozen**  | May change implementation and assertion detail; **must not** weaken 目的/目标 to pass                                                      |
| **Code lookup**          | **GitNexus** + **codebase-memory MCP** — **peer cross-check** (not sequential); reconcile before edits; grep only for gaps                 |
| GitNexus commit gate     | `impact()` before symbol edits; `detect_changes()` before commit                                                                           |
| Registry                 | Main session batch-closes rows; agents propose deltas only                                                                                 |
| **debt-lite TDD**        | Touching `scripts/` or manifest/registry tests: RED → GREEN + `execute-evidence` (REG); L5R: targeted pytest mandatory before `VR-*` close |

### 4.1 CI scripts vs one-off checks

| 类型               | 规则                                                                                                                                                     |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **持久 CI 门禁**   | 可保留：须进 `test_catalog.yaml`、有 pytest 包装、对应 `VR-*` Done 条件（例：`check_manifest_files.py` + `test_manifest_files_check.py` → `VR-DOC-001`） |
| **一次性流程脚本** | **禁止**合入 `master`；审计/协调用毕即删或改为文档命令；不得留无 catalog、无 VR 归属的 `scripts/check_*.py`                                              |
| **合并方向**       | 新门禁优先扩展现有 checker（如 `check_docs_specs_indexed`）而非平行新增脚本                                                                              |

---

## 7. Debt-lite vertical slice rule (REG / L5R)

| Branch      | Vertical slice                                                                              | Forbidden horizontal close                                                                 |
| ----------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| **B3V-REG** | One slice per `VR-REG-001` vs `VR-DOC-001`; manifest checker test before manifest row edits | Bulk registry rewrite without per-VR evidence                                              |
| **B3V-L5R** | `B03-L5-*` vs `B03-MODEL-*` separate slices; matrix file required                           | Single "reconcile report" closing both `VR-L5-001` and `VR-MODEL-001` without per-VR proof |

---

## 5. Per-track hard stops

Stop immediately if any task attempts to:

- enable production clean write or expand write permissions
- fetch live market/macro data
- implement Round 4 API/UI/Agent/notification features
- implement Round 5 security CI (except documenting route to Round 5 card)
- run full-market or full-history scans
- mark designed DB tables as implemented without schema/migration/tests
- edit `layer5_evidence/**` in the reconcile branch without a dedicated runtime follow-up branch

---

## 6. Reconcile-first rule (B3V-L5R)

For `VR-L5-001` / `VR-MODEL-001`:

1. Read post Batch 01 master (`376e30e6`+).
2. If evidence chain / table matrix already satisfied → update registry only.
3. If gaps remain → create **precise** follow-up task (often Round 3F migration ownership).
4. Do not blindly re-run full `023` implementation in Batch 3V.

---

## 8. Conflict with Batch 01 evidence

Batch 01 staged/sandbox evidence does **not** authorize production entry. Batch 3V must not weaken Batch 01 hardening (whitelist, disabled-by-default sources, no `source_health_snapshot` table creation here).
