# Plan QC Report — B3V-OPS Contract Drift & Write Modes

> **Agent:** Plan 质检 Agent-2 · **model:** `composer-2.5`  
> **Worktree:** `../quant-monitor-desk-wt-b3v-ops`  
> **输入:** `MASTER.plan.md` · `implement.jsonl`（**30 行**）· `vertical-slices.md` · `plan.freeze.md`  
> **对照:** Playbook §3.2 · §3.9 · §3.10 · `B02_01` · manifest `B3V-C01`  
> **禁止:** Execute（本报告仅 Plan 质检）

---

## 1. 执行摘要

| 项 | 结果 |
| -- | ---- |
| `validate-plan-freeze` | **exit 0**（2026-06-25 复检） |
| manifest `B3V-C01` / 分支 / VR-* | **对齐** |
| B02_01 五切片垂直（CLOSE 排除） | **PASS** |
| registry 闭合排除 | **PASS** |
| WriteManager HIGH impact → §7 | **PASS** |
| B02-CLOSE-01 → 主会话 | **PASS** |
| §3.9 追溯规则 | **PASS**（1 项 LOW 文档索引缺口，见 §2.2） |
| 初检遗留（阻断级） | **0** |
| **Verdict** | **PASS** — 可进入 Execute（`composer-2.5` only；禁 fast） |

---

## 2. 权威索引核对表（Playbook §3.10）

### 2.1 Playbook §3.1 共用底座（MASTER Source Context Index §3.1 摘要）

| 路径 | MASTER | implement.jsonl | 摘要一句 | 遗漏风险 |
| ---- | ------ | --------------- | -------- | -------- |
| `BATCH_3V_COORDINATOR_PLAYBOOK.md` | [x] L67 | L11 | §3.1+§3.2+§4 正式线 | 无 |
| `BATCH_3V_TASK_CARD_MANIFEST.md` | [x] L68 | L8 | C01 依赖与分支锁 | 无 |
| `BATCH_3V_HARDENING_RULES.md` | [x] L69 | L9 | 禁 production-live | 无 |
| `BATCH_3V_VERIFIED_AUDIT_CLEANUP/README.md` | [x] L70 | L10 | Batch 3V 入口 | 无 |
| `PROJECT_IMPLEMENTATION_ROADMAP.md` | [x] L71 | L13 | Round 3V.1 血缘 | 无 |
| `GLOBAL_EXECUTION_RULES.md` 等 ×3 | [x] L72 | L14–16 | 全局纪律 | 无 |
| `staged_acceptance_policy.md` | [x] L73 | L17 | 分层验收 | 无 |
| `quant_monitor_desk_verified_audit_report_2026-06-25_v3_INDEX.md` | [x] L74 | L12 | VR-OPS/WRITE 路由 | 无 |
| Registry 三件套 + `UNRESOLVED_ITEM_TASK_COVERAGE.md` | [x] L75（**只读**） | L27–28 | 本任务不闭合 | 无 |
| `docs/architecture/module_boundary_matrix.md` | §3 引用 | L26 | ops/db 边界 | 无 |

> Playbook §3.1 其余协调/Handoff 路径由 `context_pack.json` + `integration-ledger.md` 路由；`integration-audit.md` 已 PASS，不列为阻断缺口。

### 2.2 Playbook §3.2 B3V-OPS 专属（任务卡 + 漂移触点）

| 路径 | MASTER §3.2 | implement.jsonl | 摘要一句 | 遗漏风险 |
| ---- | ----------- | --------------- | -------- | -------- |
| `B02_01_contract_drift_and_write_modes.md` | [x] L81 | L7 | VR AC + 六切片原文 | 无 |
| `specs/contracts/ops_db_inspect_contract.yaml` | [x] L82 | L18 | key_tables + deferred SSOT | 无 |
| `docs/modules/ops_db_inspect.md` | — | — | Playbook 列出；**仓库无此文件** | **无**（以 YAML + `db_inspector` 为准；Playbook/doc 债务） |
| `docs/ops/db_inspect_cli.md` | — | — | CLI 漂移对照文档 | **低**（文件存在但未入 MASTER/implement；Execute Boot 建议补读，非阻断） |
| `backend/app/ops/db_inspector.py` | [x] L85 | L21 | inspect 运行时 + loader | 无 |
| `specs/contracts/write_contract.yaml` | [x] L83 | L19 | 写模式契约 | 无 |
| `backend/app/db/write_manager.py` | [x] L86 | L22 | SUPPORTED/UNSUPPORTED | 无 |
| `tests/test_ops_db_inspector.py` | [x] L87 | L23 | inspect 回归 | 无 |
| `tests/test_write_manager.py` | [x] L88 | L24 | write 回归 | 无 |
| `tests/test_db_validation_gate.py` | [x] L89 | L25 | gate 回归（只跑不改） | 无 |
| `tests/test_contract_drift_ops_write.py` | [x] L90 | L29 | 漂移/parity 新测 RED 占位 | 无 |
| `specs/contracts/runtime_versions.md` | [x] L84 | L20 | runtime 锁 | 无 |
| VR INDEX（`VR-OPS-001` / `VR-WRITE-001`） | §2 AC | L12 | 审计路由 | 无 |

### 2.3 manifest `B3V-C01` 对照

| manifest 字段 | 期望值 | MASTER / task.json | 状态 |
| ------------- | ------ | ------------------ | ---- |
| ID | `B3V-C01` | `task.json` meta · MASTER §0 | PASS |
| Card | `B02_01_contract_drift_and_write_modes.md` | predecessor_tasks · Source Index | PASS |
| Owns | `VR-OPS-001`, `VR-WRITE-001` | §2 AC · `original-plan-trace.md` | PASS |
| Branch | `fix/round3v-contract-drift-write-modes` | §0 · worktree 一致 | PASS |
| Track | complex §4 | `task_track: complex` | PASS |
| Branch owns（manifest §3） | ops/write 契约 + 两运行时 + parity 测 | MASTER §0 Batch 边界表 | PASS |
| Must not own | migration · live fetch · production clean write | §0 · §3.2 out | PASS |
| Registry close owner | B3V-C01 提交**技术证据**；主会话 reconcile | §1.2 · §3.2 defer | PASS |

---

## 3. Playbook §3.9 追溯规则逐项

| 规则 | 检查 | 结论 |
| ---- | ---- | ---- |
| **索引行** | §3.2 核心路径均在 MASTER Source Index + implement（CLI 文档 1 项 LOW） | PASS |
| **VR 追溯** | `VR-OPS-001` → AC-OPS-DRIFT → S1 → §9.1–9.2 → §6/§10；`VR-WRITE-001` → AC-WRITE-SPLIT/RESERVED → S2–S3 → §9.3–9.5 | PASS |
| **负向边界** | §0 Must not · §3.2 out/defer · manifest §3 Must not own · B02_01 §4 Forbidden 对齐 | PASS |
| **切片垂直** | 5 切片各绑单一 VR/子 AC；无水平合并两 VR（§8 + `vertical-slices.md`） | PASS |
| **证据路径** | §9 每步 `execute-evidence/{9.x}-red/green.txt` 预定 | PASS |
| **复检** | 本表 §2 遗漏风险列：阻断 **0**；LOW **1**（db_inspect_cli 可选补读） | PASS |

---

## 4. B02_01 任务卡对照

### 4.1 六切片 → MASTER §8

| 任务卡切片 | MASTER 切片 | VR / AC | 状态 |
| ---------- | ----------- | ------- | ---- |
| B02-OPS-01 | OPS-01 | VR-OPS-001 | 在 scope |
| B02-OPS-02 | OPS-02 | VR-OPS-001 | 在 scope |
| B02-WRITE-01 | WRITE-01 | VR-WRITE-001 | 在 scope |
| B02-WRITE-02 | WRITE-02 | VR-WRITE-001 | 在 scope |
| B02-WRITE-03 | WRITE-03 | VR-WRITE-001 | 在 scope |
| **B02-CLOSE-01** | **排除** | 主会话 registry | **PASS**（§3.2 · `vertical-slices.md` 禁止切片表） |

### 4.2 Forbidden scope（B02_01 §4）

| 禁止项 | MASTER 落点 | 状态 |
| ------ | ----------- | ---- |
| 实现 reserved 三模式运行时 | §1.4 · §3.2 out | PASS |
| 改 production clean-write | §0 Must not · §1.4 | PASS |
| DB 写 / migration | §1.4 · AC-BOUND | PASS |
| registry 闭合 | §1.5 #6 · §3.2 defer · §10 DoD | PASS |

### 4.3 验收命令（B02_01 §7 + 任务扩展）

| 命令 | MASTER | 状态 |
| ---- | ------ | ---- |
| `uv sync --locked` | §6 Tier A | PASS |
| `pytest test_ops_db_inspector.py` | §6 · §9.0 | PASS |
| `pytest test_write_manager.py test_db_validation_gate.py` | §6 · §9.0 | PASS |
| `pytest test_contract_drift_ops_write.py` | §5–§6（任务卡未列文件名，Plan 正确扩展） | PASS |
| `ruff check backend/app/ops backend/app/db tests` | §6 | PASS |

---

## 5. 专项检查（用户点名项）

### 5.1 五切片垂直

| ID | VR | 依赖 | 证据 | 独立可测 |
| -- | -- | ---- | ---- | -------- |
| OPS-01 | VR-OPS-001 | — | 9.1 | 是 |
| OPS-02 | VR-OPS-001 | OPS-01 | 9.2 | 是 |
| WRITE-01 | VR-WRITE-001 | — | 9.3 | 是 |
| WRITE-02 | VR-WRITE-001 | WRITE-01 | 9.4 | 是 |
| WRITE-03 | VR-WRITE-001 | WRITE-01 | 9.5 | 是 |

**结论：** PASS — 与 `vertical-slices.md`、`original-plan-trace.md` 一致。

### 5.2 registry 排除

| 检查点 | 位置 | 状态 |
| ------ | ---- | ---- |
| Must not：registry 三件套直接闭合 | MASTER §0 | PASS |
| out/defer：registry 闭合 | §3.2 | PASS |
| 停止条件 #6：Agent 改 registry | §1.5 | PASS |
| §10 DoD：未改 registry | §10 | PASS |
| §1.2：VR 技术证据 vs registry 主会话收口 | §1.2 | PASS |
| manifest §4：Agents 仅 proposed deltas | manifest C01 §4 | PASS |

### 5.3 WriteManager HIGH impact（§7）

| 检查点 | 位置 | 状态 |
| ------ | ---- | ---- |
| Red Flag：HIGH blast + 每步 `impact()` | §7 | PASS |
| 停止条件 #5：未跑 impact 禁止改符号 | §1.5 | PASS |
| §9.5 绑定 `gitnexus-impact` | §9.5 | PASS |
| §11 Execute Skill：`gitnexus-impact` 必做 | §11 | PASS |
| `integration-audit.md` 对抗项 #5 | research | PASS |

### 5.4 B02-CLOSE-01 主会话

| 检查点 | 状态 |
| ------ | ---- |
| 不在 §8 实现顺序 | PASS |
| `vertical-slices.md` 禁止切片表 | PASS |
| `original-plan-trace.md` 标记 **排除** | PASS |
| AC-EVIDENCE：execute 证据齐；registry 主会话登记 | PASS |

---

## 6. 机器门禁

```text
python .trellis/scripts/task.py validate-plan-freeze .trellis/tasks/round3v-contract-drift-write-modes
→ exit 0（Plan freeze validation passed）
```

| 门禁 | 结果 |
| ---- | ---- |
| `implement.jsonl` 首条 = MASTER | PASS |
| `integration-ledger.md` 在 manifest | PASS |
| `manifest_protocol_version: "3"` | PASS |
| `plan.freeze.md` §3.6 记录 | PASS |
| RED 占位测可 FAIL | `test_contract_drift_ops_write.py` 四测 `pytest.fail` | PASS |

---

## 7. 发现项

| # | 发现 | 严重度 | 处置 |
| - | ---- | ------ | ---- |
| F1 | `docs/ops/db_inspect_cli.md` 在 Playbook §3.2 列出但未入 MASTER/implement | LOW | Execute Boot 补读；或协调者批准前补一行 implement（**非阻断**） |
| F2 | `docs/modules/ops_db_inspect.md` Playbook 引用但仓库不存在 | INFO | 以 `ops_db_inspect_contract.yaml` + 运行时为准；Playbook 后续清理 |
| F3 | 输入称 implement 29 行，实际 **30** 行 | INFO | 计数更正；内容完整 |

**阻断级遗留：0**

---

## 8. Verdict

| 字段 | 值 |
| ---- | -- |
| **结论** | **PASS** |
| **可派发 Execute** | **是**（`composer-2.5`；禁 `composer-2.5-fast`） |
| **前置** | 用户/协调者批准 `plan.freeze.md` §5 → `task.py start` |
| **Execute 禁止项** | registry 闭合 · reserved 实现 · production clean write · 无 impact 改 WriteManager |
| **建议（可选）** | Boot 补读 `docs/ops/db_inspect_cli.md`；CLOSE-01 留给主会话 Batch 收口 |

---

_Plan QC · B3V-OPS · 2026-06-25 · Agent-2_
