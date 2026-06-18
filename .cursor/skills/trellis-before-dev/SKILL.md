---
name: trellis-before-dev
description: "Plan Phase 5c — integration-ledger-first manifest curation (E1–E15, v3 V7). Execute does NOT re-run; read implement.jsonl + MASTER §0.3 + ledger."
---

Read the relevant development guidelines before starting your task.

## Phase 5c workflow (ledger-first · v3)

Execute these steps **in order**:

1. **Read task artifacts**
   - `prd.md`, `design.md` (if present), `research/original-plan-trace.md` (manifest column)
   - `research/input-inventory.md` (P0i — doc universe already audited)
   - `research/integration-ledger.md` (packing map: inline vs pointer)

2. **Predecessor inherit (E2)** — if `task.json` has `predecessor_tasks`:
   - Read predecessor `implement.jsonl`
   - Merge **wiring-class** paths into this task's `implement.jsonl`

3. **Curate integration-ledger.md** (before bloating implement):
   - Every **pointer** / **summary+pointer** row needs: `source`, `category`, `master_anchor`, `execute_extract`, `for_ac_step`
   - **inline** decisions go to MASTER §4–§6 first; ledger row notes anchor only

4. **Build implement.jsonl** (L1 mechanical closure):
   ```bash
   python .trellis/scripts/task.py suggest-implement-context .trellis/tasks/<slug>
   ```
   Append missing paths. Align `check.jsonl` ⊆ `implement.jsonl` (E14).

5. **Sync reasons from ledger (V4/V7)**:
   ```bash
   python .trellis/scripts/patch_implement_from_ledger.py .trellis/tasks/<slug>
   ```
   Every implement row (except MASTER + trellis-execute) must have `extract: … | for: …`.

6. **Sync MASTER §9/§10** — every `tests/*.py` and `scripts/*.py` in §9/§10 must appear in implement (E3).

7. **Validate phase 5c**:
   ```bash
   python .trellis/scripts/task.py validate-plan-phase .trellis/tasks/<slug> 5c
   ```

**Do NOT list Execute-created paths** in implement (E11): new orchestrator files, new migrations, etc.

**Do NOT duplicate ledger in MASTER §0.3** — §0.3 points to implement + ledger; grouping lives in ledger categories.

This step is **mandatory** before Plan freeze.
