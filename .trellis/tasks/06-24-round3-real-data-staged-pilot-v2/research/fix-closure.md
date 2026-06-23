# Phase 7 Re-audit Fix Closure — B-19

**Branch:** `feature/round3-real-data-staged-pilot-v2`  
**Fix commit message:** `fix(B-19): close Phase 7 re-audit findings`  
**Date:** 2026-06-24

---

## OOB-1 — closeout 三态语义（A1/A4/A5/A7 · PRIORITY）

| 项 | 处置 |
|----|------|
| **问题** | `build_pilot_v2_closeout` 用 `is True` 将 proof `None` coerce 为 JSON `false` |
| **修复** | 保留 `db_hash_unchanged` / `row_counts_unchanged` 原始三态（`true`/`false`/`null`）；gate 仍用 `is True` 判定 `closeout_pass` |
| **附加** | closeout 写入 `mutation_proof_reason`（当 proof 含 `reason` 时） |
| **证据** | `pilot_v2_closeout.json` L3/L14 现为 `null`；`test_stagedPilotV2_closeoutThreeStateSemantics` |
| **状态** | **CLOSED** |

---

## OOB-2 — execute-evidence v1 残留（A1/A5）

| 删除文件 | v2 权威替代 |
|----------|-------------|
| `conflict_check_summary.json` | `conflict_check_summary_v2.json` |
| `validation_report_summary.json` | `validation_report_v2.json` |
| `production_db_no_mutation_proof.md` | `no_mutation_proof_v2.md` |

**状态：** **CLOSED** — handoff 仅以 `*_v2.*` / `pilot_v2_*.json` 为准。

---

## OOB-3 — GitNexus 索引（A1）

**处置：** 文档记录。worktree 与主仓双索引冲突；v2 符号未入索引。合并前于 worktree 路径执行 `node .gitnexus/run.cjs analyze`。

**状态：** **CLOSED（文档）**

---

## OOB-4 — AGENTS/CLAUDE 脏改动（A1）

**状态：** **CLOSED** — 用户已还原；本 fix 未改 `AGENTS.md` / `CLAUDE.md`。

---

## A2 U-A2-01 — authorization_gate 传入 preview

**修复：** `run_staged_pilot_raw_only` 调用 `preview_staged_pilot(..., authorization_gate=authorization_gate)`。

**状态：** **CLOSED**

---

## A2 U-A2-02 — akshare taxonomy 静态默认

**处置：** `capture_akshare_validation_taxonomy_v2` docstring 注明 ponytail 静态 SUCCESS/NETWORK_ERROR 占位；符合任务卡 re-defer 叙事。

**状态：** **CLOSED（文档）**

---

## A2 U-A2-03 — v1 triple 冗余检查

**修复：** 从 `validate_pilot_v2_authorization` 移除 `APPROVED_PILOT_REQUESTS` triple 检查；v2 envelope 检查更严格且已覆盖。

**状态：** **CLOSED**

---

## A2 U-A2-04 — staged_pilot.py 单文件 2074+ 行

**处置：** ponytail 折中 — 九切片 trace 可读性优先于拆文件；不阻 merge。

**状态：** **CLOSED（文档 defer）**

---

## A5 OOF-1 — user-auth-required 路由矩阵

**修复：**
1. `_route_status_examples_for_v2`：`USER_AUTH_REQUIRED` 优先于 FallbackPolicy → `route_kind: user_auth_required`
2. `capture_route_preview_matrix_v2`：`required_kinds` 含 `user_auth_required`；registry 无独立 skipped 时以 user_auth 满足 SP2-05
3. 测试断言 `USER_AUTH_REQUIRED` → `user_auth_required`

**状态：** **CLOSED**

---

## A5 OOF-2 — evidence mock 非 live fetch

**处置：** sandbox 单测 + mock manifest 符合 R3Y staged scope；live micro-fetch 交 PROMPT_20。

**状态：** **CLOSED（文档 defer）**

---

## A5 OOF-3 — prod DuckDB 缺失

**处置：** 环境性；`audit-prod-path-na.md` + INCONCLUSIVE fail-closed 已覆盖。合并后在有 `data/duckdb/` 环境补跑 `AUDIT_PROD_ROOT`。

**状态：** **CLOSED（文档）**

---

## A5 OOF-4 — closeout_pass false vs Audit PASS

**处置：** closeout 表「implementation audit PASS ≠ pilot operational PASS」；`production_live_readiness_claim: false` 恒真。

**状态：** **CLOSED（文档）**

---

## A5 OOF-5 — Tier B 全库未复跑

**处置：** 本 fix 跑 `uv run pytest -q` exit 0；Phase 7 独立复验 49 staged 测已绿。

**状态：** **CLOSED**

---

## A7 P7-01 — closeout 三态

同 **OOB-1**。**CLOSED**

---

## A7 P7-02 — no_mutation_proof_v2.md 明细

**修复：** `write_no_mutation_proof_v2` 追加 `reason`、key/all table counts（DB 存在时）、R3Y 说明段。

**状态：** **CLOSED**

---

## A7 P7-03 — byte-equal vs SHA256

**修复：** `build_production_mutation_proof` 在 DB 存在时返回 `db_sha256`；markdown 注明 byte-equal 为 gate、SHA256 对齐 backup manifest。

**状态：** **CLOSED**

---

## A7 P7-04 — prod DB 存在时端到端未演练

同 **OOF-3**。**CLOSED（文档）**

---

## A7 P7-05 — sandbox 双遍 migrate smoke

**处置：** ponytail defer — 低优先级；sandbox 半写仅影响 pilot 重跑，不触 prod。

**状态：** **CLOSED（defer）**

---

## Ponytail 自检

| 梯级 | 问题 | 结论 |
|------|------|------|
| 1 YAGNI | 需要新模块吗？ | 否 — 改 shared `build_pilot_v2_closeout` + `mutation_proof` 一次 |
| 2 复用 | 已有 helper？ | gate 逻辑保留 `is True`；仅序列化层改三态 |
| 6 最小 | diff 规模 | ~80 行行为 + 测试 + 删 3 v1 文件 |
| 注释 | 有意简化 | akshare taxonomy docstring；route skipped/user_auth 口径 |

---

## 验证

```text
uv run pytest tests/test_staged_pilot.py -q  → 41 passed
uv run pytest -q                             → exit 0
execute-evidence 已 regen（closeout null、route user_auth_required）
```
