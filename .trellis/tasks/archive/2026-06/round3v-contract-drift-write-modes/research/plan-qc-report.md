# Plan QC Report — B3V-OPS Contract Drift & Write Modes

> **Agent:** Plan 质检 Agent-2 · **model:** `composer-2.5`  
> **Worktree:** `../quant-monitor-desk-wt-b3v-ops`  
> **输入:** `MASTER.plan.md` · `implement.jsonl`（**31 行**）· `context_pack.json` · `plan.freeze.md`  
> **对照:** Playbook §3.2 · §3.8–§3.10 · §2.5/§2.6 · `B02_01` · manifest `B3V-C01`  
> **禁止:** Execute（本报告仅 Plan 质检）

---

## 1. 执行摘要

| 项                                                 | 结果                                                      |
| -------------------------------------------------- | --------------------------------------------------------- |
| `validate-plan-freeze`                             | **exit 0**（2026-06-28 复检）                             |
| `check_docs_specs_indexed.py`                      | **exit 0**                                                |
| frozen 三件套（MASTER + implement + context_pack） | **对齐**                                                  |
| manifest `B3V-C01` / 分支 / VR-\*                  | **对齐**                                                  |
| B02_01 五切片垂直（CLOSE 排除）                    | **PASS**                                                  |
| §2.5/§2.6 边界（MASTER §0 + §3.2 out）             | **PASS**                                                  |
| VR-OPS-001 / VR-WRITE-001 closure test             | **PASS**（5 条 pytest）                                   |
| OPS-01..WRITE-03 竖条                              | **PASS**                                                  |
| registry 闭合排除                                  | **PASS**                                                  |
| §3.10 遗漏风险列                                   | **全「无」**                                              |
| 初检遗留（阻断级）                                 | **0**                                                     |
| **Verdict**                                        | **PASS** — 可进入 Execute（`composer-2.5` only；禁 fast） |

---

## 2. 权威索引核对表（Playbook §3.10）

### 2.1 Playbook §3.1 共用底座（MASTER Source Context Index §3.1 摘要）

| 路径                                                              | 已入 MASTER/implement | 摘要一句             | 遗漏风险 |
| ----------------------------------------------------------------- | --------------------- | -------------------- | -------- |
| `BATCH_3V_COORDINATOR_PLAYBOOK.md`                                | [x] L67 / L11         | §3.1+§3.2+§4 正式线  | 无       |
| `BATCH_3V_TASK_CARD_MANIFEST.md`                                  | [x] L68 / L8          | C01 依赖与分支锁     | 无       |
| `BATCH_3V_HARDENING_RULES.md`                                     | [x] L69 / L9          | 禁 production-live   | 无       |
| `BATCH_3V_VERIFIED_AUDIT_CLEANUP/README.md`                       | [x] L70 / L10         | Batch 3V 入口        | 无       |
| `PROJECT_IMPLEMENTATION_ROADMAP.md`                               | [x] L71 / L13         | Round 3V.1 血缘      | 无       |
| `GLOBAL_EXECUTION_RULES.md` 等 ×3                                 | [x] L72 / L14–16      | 全局纪律             | 无       |
| `staged_acceptance_policy.md`                                     | [x] L73 / L17         | 分层验收             | 无       |
| `quant_monitor_desk_verified_audit_report_2026-06-25_v3_INDEX.md` | [x] L74 / L12         | VR-OPS/WRITE 路由    | 无       |
| Registry 三件套 + `UNRESOLVED_ITEM_TASK_COVERAGE.md`              | [x] L75 / L27–28      | 本任务不闭合（只读） | 无       |
| `docs/architecture/module_boundary_matrix.md`                     | §3 / L26              | ops/db 边界          | 无       |

> Playbook §3.1 其余协调/Handoff 路径由 `context_pack.json` + `integration-ledger.md` 路由；`integration-audit.md` 已 PASS。

### 2.2 Playbook §3.2 B3V-OPS 专属（逐行）

| 路径                                           | 已入 MASTER/implement | 摘要一句                                     | 遗漏风险 |
| ---------------------------------------------- | --------------------- | -------------------------------------------- | -------- |
| `B02_01_contract_drift_and_write_modes.md`     | [x] L81 / L7          | VR AC + 六切片原文                           | 无       |
| `specs/contracts/ops_db_inspect_contract.yaml` | [x] L82 / L18         | key_tables + deferred SSOT                   | 无       |
| `docs/modules/ops_db_inspect.md`               | [x] L83 / —           | Playbook 债务；仓库无文件；SSOT=YAML+runtime | 无       |
| `docs/ops/db_inspect_cli.md`                   | [x] L84 / L19         | CLI 漂移对照                                 | 无       |
| `backend/app/ops/db_inspector.py`              | [x] L87 / L22         | inspect 运行时 + loader                      | 无       |
| `specs/contracts/write_contract.yaml`          | [x] L85 / L20         | 写模式契约                                   | 无       |
| `backend/app/db/write_manager.py`              | [x] L88 / L23         | SUPPORTED/UNSUPPORTED                        | 无       |
| `tests/test_ops_db_inspector.py`               | [x] L89 / L24         | inspect 回归                                 | 无       |
| `tests/test_write_manager.py`                  | [x] L90 / L25         | write 回归                                   | 无       |
| VR INDEX（`VR-OPS-001` / `VR-WRITE-001`）      | §2 / L12              | 审计路由                                     | 无       |

### 2.3 MASTER 增补（非 Playbook §3.2 原表 · 任务必需）

| 路径                                     | 已入 MASTER/implement | 摘要一句              | 遗漏风险 |
| ---------------------------------------- | --------------------- | --------------------- | -------- |
| `specs/contracts/runtime_versions.md`    | [x] L86 / L21         | runtime 锁            | 无       |
| `tests/test_db_validation_gate.py`       | [x] L91 / L26         | gate 回归（只跑不改） | 无       |
| `tests/test_contract_drift_ops_write.py` | [x] L92 / L30         | 漂移/parity 新测      | 无       |

---

## 3. Playbook §3.8 checklist

| 项                                                        | 状态                            |
| --------------------------------------------------------- | ------------------------------- |
| §3.1 + §3.2 每一行已入 MASTER/implement                   | **PASS**                        |
| `authority_graph.yaml` 模块（ops/validators/db_platform） | **PASS** — `context_pack.json`  |
| `GLOBAL_TASK_TEMPLATE` + Red Flags                        | **PASS** — MASTER §1–§11        |
| `BATCH_3V_HARDENING_RULES` §3–§7 + §2.5/§2.6              | **PASS** — §0 边界表            |
| 任务卡 §必读 无缺口                                       | **PASS**                        |
| `/to-issues` 竖条冻结                                     | **PASS** — `vertical-slices.md` |
| 每个 owned VR-\* closure test                             | **PASS** — 见 §4                |
| `check_docs_specs_indexed.py` exit 0                      | **PASS**                        |
| `BATCH_3V_SELF_CHECK` PASS_FOR_DISPATCH                   | **PASS**                        |
| 复检零遗留                                                | **PASS**                        |

---

## 4. VR closure test 追溯（§3.9）

| VR ID          | AC                | 切片     | closure test                                             | 遗漏风险           |
| -------------- | ----------------- | -------- | -------------------------------------------------------- | ------------------ |
| `VR-OPS-001`   | AC-OPS-DRIFT      | OPS-01   | loader + `KEY_TABLES` 来自 YAML                          | 无                 |
| `VR-OPS-001`   | AC-OPS-DRIFT      | OPS-02   | `test_opsInspect_keyTables_matchContract`                | 无                 |
| `VR-OPS-001`   | AC-OPS-DRIFT      | OPS-02   | `test_opsInspect_deferredMapping_matchContract`          | 无                 |
| `VR-WRITE-001` | AC-WRITE-SPLIT    | WRITE-01 | `write_contract` implemented/reserved 分栏               | 无                 |
| `VR-WRITE-001` | AC-WRITE-SPLIT    | WRITE-02 | `test_writeContract_implementedModes_matchWriteManager`  | 无                 |
| `VR-WRITE-001` | AC-WRITE-SPLIT    | WRITE-02 | `test_writeContract_reservedModes_matchUnsupportedModes` | 无                 |
| `VR-WRITE-001` | AC-WRITE-RESERVED | WRITE-03 | `test_writeManager_reservedModes_rejectWithoutWrite`     | 无                 |
| B02-CLOSE-01   | registry          | **排除** | 主会话 Batch 收口                                        | 无（设计内 defer） |

---

## 5. OPS-01..WRITE-03 竖条

| ID       | VR           | 依赖     | MASTER §8 | MASTER §9 | 证据预定            | 遗漏风险 |
| -------- | ------------ | -------- | --------- | --------- | ------------------- | -------- |
| OPS-01   | VR-OPS-001   | —        | 序 1      | 9.1       | `9.1-red/green.txt` | 无       |
| OPS-02   | VR-OPS-001   | OPS-01   | 序 2      | 9.2       | `9.2-red/green.txt` | 无       |
| WRITE-01 | VR-WRITE-001 | —        | 序 3      | 9.3       | `9.3-red/green.txt` | 无       |
| WRITE-02 | VR-WRITE-001 | WRITE-01 | 序 4      | 9.4       | `9.4-red/green.txt` | 无       |
| WRITE-03 | VR-WRITE-001 | WRITE-01 | 序 5      | 9.5       | `9.5-red/green.txt` | 无       |

---

## 6. §2.5 / §2.6 边界（B3V-OPS）

| Playbook                                            | MASTER 落点                       | 状态 |
| --------------------------------------------------- | --------------------------------- | ---- |
| Owns: ops inspect 契约 + write implemented/reserved | §0 Batch 边界表                   | PASS |
| Must not: reserved 实现 · production clean write    | §0 Must not · §1.4 · §3.2 out     | PASS |
| 核心文件锁：ops_db_inspect + write_contract         | §3.2 allowed 路径                 | PASS |
| registry 三件套主会话                               | §1.5 #6 · §3.2 defer B02-CLOSE-01 | PASS |

---

## 7. 对抗性修补记录（2026-06-28）

| #   | 漏洞                                                                    | 修补                                             |
| --- | ----------------------------------------------------------------------- | ------------------------------------------------ |
| P1  | `docs/ops/db_inspect_cli.md` Playbook §3.2 列出但未入 MASTER/implement  | MASTER §3.2 + implement.jsonl L19                |
| P2  | `docs/modules/ops_db_inspect.md` 仓库不存在无 Plan 行                   | MASTER §3.2 标注 Playbook 债务                   |
| P3  | `test_writeContract_reservedModes_matchUnsupportedModes` 未入 §5.3/§9.4 | MASTER §5.2/§5.3/§9.4 + `original-plan-trace.md` |

---

## 8. 机器门禁

```text
python .trellis/scripts/task.py validate-plan-freeze .trellis/tasks/round3v-contract-drift-write-modes
→ exit 0（2026-06-28 Plan QC 复检）

uv run python scripts/check_docs_specs_indexed.py
→ exit 0
```

---

## 9. Verdict

| 字段               | 值                                                                                 |
| ------------------ | ---------------------------------------------------------------------------------- |
| **结论**           | **PASS**                                                                           |
| **§3.10 遗漏风险** | **全「无」**                                                                       |
| **可派发 Execute** | **是**（`composer-2.5`；禁 `composer-2.5-fast`）                                   |
| **Execute 禁止项** | registry 闭合 · reserved 实现 · production clean write · 无 impact 改 WriteManager |

---

_Plan QC · B3V-OPS · 2026-06-28 · Agent-2 对抗性复检_
