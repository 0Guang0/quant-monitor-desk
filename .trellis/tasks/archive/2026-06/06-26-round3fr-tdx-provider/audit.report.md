# Audit Report — R3FR-03 TDX Provider Refactor (Repair)

## 1. 元信息

| 字段            | 值                                                                       |
| --------------- | ------------------------------------------------------------------------ |
| 任务 slug       | `06-26-round3fr-tdx-provider`                                            |
| 分支            | `refactor/round3fr-tdx-provider`                                         |
| 基线 commit     | `407f4aa2`                                                               |
| Execute handoff | `validate-execute-handoff` exit 0                                        |
| Repair 证据     | `repair-evidence/repair-green.txt` · `repair-evidence/loop-maintain.txt` |

---

## 2. 维度验证汇总（AUDIT.plan §2）

| 维  | 验证                 | 结果                 | 证据                                          |
| --- | -------------------- | -------------------- | --------------------------------------------- |
| A1  | Spec / scope         | **PASS**             | `EXECUTION_INDEX.md` · frozen card            |
| A2  | Ponytail / 最小 diff | **PASS**             | gate 集中签发；port 无公有 issue              |
| A3  | Security / live gate | **PASS**             | stack enforce + gate-only token               |
| A4  | Code quality         | **PASS**             | normalizer 下沉；content_hash                 |
| A5  | AC 闭合              | **PASS**             | `adversarial-plan-audit.report.md` ADV 全闭合 |
| A6  | Performance          | **SKIP**             | 无 perf SLA                                   |
| A7  | Ops / CLI            | **PASS**             | data health 非 placeholder                    |
| A8  | Test gap             | **PASS** (Repair 后) | G1/G2 + bypass 负例测                         |

---

## 3. 分维度要点

### 3.4 A4 · Code Quality

**PASS（Repair 后）。** `TdxPytdxAuthorization` 与 `issue_tdx_live_authorization_after_gate` 收归 `tdx_live_manual_probe_gate.py`；port 仅 `is_gate_issued_token` 校验；`parse_index_instrument` 与 bar 行映射在 `normalizers/tdx.py`；`security_list` manifest 含 `content_hash`。

### 3.8 A8 · Test Gap

**PASS（Repair 后）。** 新增/更新：`test_tdxPytdxPort_issueAuthorizationNotPublicOnPortModule`、`test_tdxPytdxPort_directCallWithGateToken_blockedByStack`、`test_tdxPytdxPort_remainingNetworkCalls_exhausted`、`test_validateTdxLiveManualProbe_sessionIdMismatch_blocks`（G2）、`test_capabilityRegistry_rejectsTdxPytdxProposedDisabledSource`（G1）；`max_network_calls=0` 断言 `invalid (must be positive)`。

---

## 4. 风险与结论（A9）

### 4.2 结论

- [x] **PASS** — Repair 闭合 §4.3；可进入 merge gate（未 commit）
- [ ] **PASS_WITH_FIXES**
- [ ] **FAIL**

### 4.3 修复项（Repair 已闭合）

| ID                | 维度 | 问题                                                  | 根因修复                                                                                       | 优先级 | 状态       |
| ----------------- | ---- | ----------------------------------------------------- | ---------------------------------------------------------------------------------------------- | ------ | ---------- |
| AA-R3FR03-A4-01   | A4   | port 公有 `issue_tdx_live_authorization` 可自签 token | 签发迁至 `issue_tdx_live_authorization_after_gate`；port 仅 `is_gate_issued_token`             | P0     | **CLOSED** |
| AA-R3FR03-A4-02   | A3   | 有 gate token 仍可直调 `TdxPytdxFetchPort`            | `enforce_live_entrypoint_stack()` + `test_tdxPytdxPort_directCallWithGateToken_blockedByStack` | P0     | **CLOSED** |
| AA-R3FR03-A4-03   | A4   | port 无 `remaining_network_calls` 预算                | `TdxPytdxFetchPort.remaining_network_calls` fail-fast                                          | P2     | **CLOSED** |
| AA-R3FR03-A4-04   | A4   | `parse_index_instrument` 在 gate 模块                 | 下沉 `normalizers/tdx.py`；gate 委托                                                           | P2     | **CLOSED** |
| AA-R3FR03-A4-05   | A4   | bar 行 `datetime`/`vol` 未规范化                      | `_normalize_bar_row` → `trade_date`/`volume`                                                   | P2     | **CLOSED** |
| AA-R3FR03-A4-06   | A4   | security_list manifest 缺 `content_hash`              | port `_fetch_manifest` 写入 `content_hash`                                                     | P2     | **CLOSED** |
| AA-R3FR03-A8-01   | A8   | G1 — proposed disabled 源未测                         | `test_capabilityRegistry_rejectsTdxPytdxProposedDisabledSource`                                | P2     | **CLOSED** |
| AA-R3FR03-A8-02   | A8   | G2 — session_id 不匹配未测                            | `test_validateTdxLiveManualProbe_sessionIdMismatch_blocks`                                     | P2     | **CLOSED** |
| AA-R3FR03-OPS-01  | A7   | `max_network_calls<=0` 文案误导                       | `invalid (must be positive)`                                                                   | P2     | **CLOSED** |
| AA-R3FR03-LOOP-01 | A5   | `fetch_ports` 未映射 authority graph                  | `backend/app/datasources/**` 已覆盖 fetch_ports                                                | P2     | **CLOSED** |

### 4.4 Deferred（非 OPEN）

| ID      | 问题             | 理由                                 |
| ------- | ---------------- | ------------------------------------ |
| B01-C03 | TDX live primary | 活卡 §12 显式 defer；仅 manual probe |

---

## 5. Repair 复验

| 项                         | 结果     | 证据                                        |
| -------------------------- | -------- | ------------------------------------------- |
| §4.3 全部关闭              | **PASS** | 上表                                        |
| `uv run pytest -q`         | **PASS** | `repair-evidence/repair-green.txt` (exit 0) |
| `loop_maintain.py --fix`   | **PASS** | `repair-evidence/loop-maintain.txt`         |
| `validate-execute-handoff` | **PASS** | exit 0                                      |

**复验 PASS → 可 finish-work / merge gate（待用户 commit）**
