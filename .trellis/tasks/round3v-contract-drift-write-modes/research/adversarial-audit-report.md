# 对抗性审计 — B3V-OPS Contract Drift & Write Modes（Post-Repair）

> **模式：** Post-Repair 对抗性复验（只读 + pytest 子集复跑；未改 registry 三件套）  
> **分支：** `fix/round3v-contract-drift-write-modes`  
> **Worktree：** `quant-monitor-desk-wt-b3v-ops`  
> **HEAD：** `e81e430` — `fix(b3v-ops): close contract drift audit findings with zero OPEN`  
> **日期：** 2026-06-25  
> **权威：** `agents/audit-adversarial-authority.md` · `BATCH_3V_ZERO_OPEN_CLOSURE_POLICY.md` · `repair-evidence/zero-open-signoff.md` · `research/audit-a1..a8-report.md` · `MASTER.plan.md` · `B02_01_contract_drift_and_write_modes.md`

---

## Verdict

| 项                    | 值 |
| --------------------- | -- |
| **总判定**            | **PASS** |
| **BLOCKING OPEN**     | **0** |
| **NON-BLOCKING OPEN** | **0** |
| **书面 DEFER**        | **1** — `B02-CLOSE-01` registry 三件套（主会话 coordinator；设计内） |
| **A6**                | **SKIP**（无 perf 阈值 / 热路径未改） |

**零遗留（分支 scope）：** OPEN 清单 **0 行**；A1–A8 全 PASS 或 CLOSED；registry defer 有 owner/handoff，**不计入本分支 OPEN**。

---

## 对抗性三问（用户指定）

### Q1 — VR 是否真闭合？

| VR ID | 任务卡 AC | 技术证据 | 对抗性复验 |
| ----- | --------- | -------- | ---------- |
| `VR-OPS-001` | YAML SSOT + 漂移测 | `db_inspector.py` import-time loader；`test_opsInspect_keyTables_matchContract` + `test_opsInspect_deferredMapping_matchContract` | **CLOSED** — 全量 key_tables（21 表）+ deferred 5 项与 YAML 逐条相等；改 YAML 无 loader 则 RED |
| `VR-WRITE-001` | implemented/reserved 分栏 + parity + reserved 早拒 | `write_contract.yaml` 顶层分栏；4 条 write 漂移/parity/早拒测 | **CLOSED** — `implemented_modes == SUPPORTED_MODES`；`reserved_modes == UNSUPPORTED_MODES`（repair A1-F01）；每 reserved `write()` 抛约定 `ValueError` 且无行写入 |

**Registry 行（`B02-CLOSE-01`）：** MASTER §3.2 / §1.2 明确 **排除** — 「技术证据闭合，registry 行由主会话 Batch 收口」。`repair-evidence/registry-ready.md` 含 coordinator handoff。**对抗性判定：设计内 DEFER，非本分支 OPEN。**

> 任务卡 §8「VR closed or precisely re-deferred with evidence」— 分支交付满足 **技术 closed + registry re-defer 书面证据**。

### Q2 — WriteManager 未改是否留洞？

| 检查点 | 结果 |
| ------ | ---- |
| GitNexus HIGH impact 规避 | MASTER §0 停止条件 #5 + `context-closure.md` 记录 **未改 `WriteManager.write` 符号** — 符合 Plan |
| reserved 早拒语义 | `write()` L394–400：`UNSUPPORTED_MODES` → 契约措辞 `defined in contract but not implemented yet`；漂移测逐模式断言 |
| 未知 write_mode | 不在 SUPPORTED/UNSUPPORTED → 通用 `unsupported write_mode` — **可接受**（fail-closed，无写副作用） |
| 双 SSOT 检测 | parity 测双向锁定 YAML ↔ 类常量；CI 子集 57 passed |
| 生产 bypass 路径 | 无新 API/CLI；`validation_gate` 未改；reserved 未实现 runtime |

**对抗性结论：** WriteManager 硬编码 + 漂移测是 **Plan 既定模式**（非遗漏）。当前无 BLOCKING 洞。  
**残余风险（INFO，非 OPEN）：** 若未来仅改 `write_request.write_mode` enum 而不同步 `implemented_modes`/`reserved_modes`，现有测 **不会** 直接 RED（见 §计划外发现 AA-B3V-ADV-02）。当前三者手动对照一致。

### Q3 — 契约双 SSOT 是否漂移？

| 路径 | SSOT 模式 | 漂移 gate | 对抗性 |
| ---- | --------- | --------- | ------ |
| **Ops inspect** | YAML loader（真 SSOT） | 全量 drift 测 + `quote_ident` fail-fast（A3-F01 repair） | **无漂移** — 代码从契约加载，非双源 |
| **Write modes** | YAML（契约）+ `WriteManager` 类常量（runtime） | parity 测 ×2 + reserved 行为测 + `test_catalog.yaml` `verifies.specs` 双契约 | **受控双源** — 测试锁死；非 loader 统一但 AC 不要求 WriteManager loader |
| **write_request enum** | YAML 内嵌 5 模式 | **无专用 union 测** | 当前 `implemented ∪ reserved == enum` 人工核对一致；见 ADV-02 |

**对抗性结论：** Ops 路径真 SSOT；Write 路径为 **测试门控双源**，与 MASTER §2.2 / `context-closure.md` 一致，**不构成当前 OPEN 漂移**。

---

## Repair 闭合对抗性抽检

| ID | 原级 | Repair 声称 | 对抗性复验 |
| -- | ---- | ----------- | ---------- |
| A1-F01 | LOW | `test_writeContract_reservedModes_matchUnsupportedModes` | **CLOSED** — 测存在且绿 |
| A3-F01 | P3 | `_key_tables_from_contract` + `quote_ident` | **CLOSED** — L24–28 fail-fast |
| A4-O03/O04 | NON-BLOCKING | test_catalog 双契约 + 撤销格式噪音 | **CLOSED** — L168–169 两 YAML |
| A4 | NON-BLOCKING | 测试 import `_deferred_mapping_from_contract` | **CLOSED** — DRY 一致 |
| A5-F01/F04 | NON-BLOCKING | 证据加厚 + A8 sandbox rerun | **CLOSED** — `a8-rerun.txt` / 本次复跑一致 |
| A7 | — | 零 schema | **CLOSED** — diff 无 migration |
| A8 | — | 57 passed sandbox | **CLOSED** — 见 §门控复跑 |
| AA-B3V-03 | — | Registry defer handoff | **DEFER CLOSED** — 非 agent OPEN |

---

## A1–A8 维度摘要（对抗性复验）

| 维 | Phase 7 Verdict | 对抗性 | 计划外 |
| -- | --------------- | ------ | ------ |
| A1 | PASS_WITH_FINDINGS → repair | **PASS** — A1-F01 已关 | 无新 scope creep |
| A2 | PASS | **PASS** | 无 ≥20 行死码 |
| A3 | PASS | **PASS** | 只读路径；无 writer/DML |
| A4 | PASS | **PASS** | loader 容错仍为 INFO |
| A5 | PASS | **PASS** | VR 技术证据齐 |
| A6 | SKIP | **SKIP** | import-time YAML ~6KB 可忽略 |
| A7 | PASS | **PASS** | 零 schema / 零 prod DB |
| A8 | PASS | **PASS** | 5 drift 测 + 回归绿 |

---

## 门控复跑（对抗性 sandbox）

| 命令 | exit | 摘要 |
| ---- | ---- | ---- |
| `uv run pytest tests/test_contract_drift_ops_write.py tests/test_ops_db_inspector.py tests/test_write_manager.py -v --basetemp=.audit-sandbox/pytest` | **0** | **57 passed, 1 skipped**（2026-06-25 对抗性复跑） |

与 `repair-evidence/a8-rerun.txt` / `zero-open-signoff.md` 一致。

---

## 计划外发现

> 已对抗搜索：契约 enum 并集、WriteManager bypass、db_inspector mutation、registry 三件套 diff、production-live 措辞、`FUTURE_PHASE_KEY_TABLES` 硬编码。

| ID | 级别 | 发现 | 处置 |
| -- | ---- | ---- | ---- |
| AA-B3V-ADV-01 | INFO | `FUTURE_PHASE_KEY_TABLES` 仍为 `db_inspector.py` 硬编码 frozenset | **wont-fix** — 非 VR-OPS key_tables SSOT 范围；Batch 5 前瞻清单 |
| AA-B3V-ADV-02 | INFO | 无测断言 `write_request.write_mode` enum == `implemented_modes ∪ reserved_modes` | **wont-fix** — MASTER §5.3 冻结用例未列；当前三者一致；未来可加 hygiene 测 |
| AA-B3V-ADV-03 | INFO | Write 路径双 SSOT（YAML + 类常量）非 loader 统一 | **accepted** — Plan 既定；parity 测为 closure test |
| — | — | live fetch / prod DB 写 / registry 三件套编辑 / reserved 实现 | **无新发现** |

**显式声明：** 对抗性搜索未发现新的 BLOCKING 或 NON-BLOCKING OPEN。

---

## 书面 DEFER（非 OPEN）

| 项 | owner | phase | closure_test |
| -- | ----- | ----- | ------------ |
| `B02-CLOSE-01` registry 三件套（`RESOLVED_ISSUES_REGISTRY.md` 等） | Batch 3V merge coordinator | post B3V-OPS merge | `registry-ready.md` + VR 技术证据 + coordinator §7.3 批处理 |

---

## 合并注意

1. **B3V-OPS 先于 B3V-SYNC 合并**（`BATCH_3V_ZERO_OPEN_CLOSURE_POLICY.md` §跨分支依赖）— write-mode 契约稳定后再审 crash-window。
2. Registry 三件套由主会话统一闭合；**本分支不得** agent 直接改 registry。
3. 全库 `uv run pytest -q` 非本任务 A8 必跑项；分支 Done 以 owned VR 子集 + closure report 为准。

---

## 最终判定

**PASS — 0 OPEN（分支 scope）**

- `VR-OPS-001` / `VR-WRITE-001` 技术证据经对抗性复验 **真闭合**。
- `WriteManager` 未改 **不留 BLOCKING 洞**；parity + reserved 早拒测覆盖任务卡 AC。
- 契约 **Ops 真 SSOT / Write 测试门控双源** — 当前无漂移；registry defer 为设计内 HANDOFF。

*审计员：trellis-check（post-repair adversarial）· 只读 · 未改 registry 三件套*
