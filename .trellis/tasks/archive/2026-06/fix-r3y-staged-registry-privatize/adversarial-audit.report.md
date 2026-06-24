# Adversarial Audit — R3Y-STAGED-REG-001 (β-2 staged registry privatize)

**Branch:** `fix/r3y-staged-registry-privatize`  
**Worktree:** `quant-monitor-desk-wt-fix-r3y-staged-reg`  
**Auditor:** adversarial audit agent (composer-2.5)  
**Date:** 2026-06-24  
**Scope:** MAP §2.2 β-2 — privatize `register_staged_file_registry_rows` WriteManager bypass (not registry trio, not ops rewrite)

**Sources read:** `agents/audit-adversarial-authority.md`, `WAVE_C_MAIN_SESSION_COORDINATOR_PLAYBOOK.md` §8.4, `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §2.2, `DEBT.plan.md`, `docs/quality/ROUND3_WAVE_B_PENDING_FIX_REGISTRY.md` §2, `docs/modules/write_manager.md` (§4 旁路禁令), `backend/app/storage/staged_evidence.py`, `backend/app/ops/staged_pilot.py` (import 邻接), 三测文件 diff, pytest 复跑输出

---

## Verdict

**PASS (β-2 slice)** — 公开 `register_staged_file_registry_rows` 已退役；`__all__` 仅导出常量；metadata-only 策略有模块级注释；`test_staged_pilot` WriteManager 路径仍绿；MAP 验证 + 全量 pytest 绿。

**Registry `R3Y-STAGED-REG-001` 台账 CLOSED** 须待主会话 Wave C 合并后批处理 registry 三件套 — 本分支 **runtime + 测试已满足 §8.4 关闭 ID 行为面**。

| 指标                | 值                       |
| ------------------- | ------------------------ |
| **Overall verdict** | PASS                     |
| **OPEN**            | **0**                    |
| **BLOCKING**        | 0（原 2 项已修复）       |
| **NON-BLOCKING**    | 0（原 4 项已关闭或接受） |

---

## §8.4 PASS 表逐行

| 维度           | PASS 条件                                                   | 结论     | 证据                                                            |
| -------------- | ----------------------------------------------------------- | -------- | --------------------------------------------------------------- |
| **权威索引**   | §3.1 + §3.5 全文已入 `DEBT.plan.md`                         | **PASS** | `.trellis/tasks/fix-r3y-staged-registry-privatize/DEBT.plan.md` |
| **范围**       | 仅 allowed：`staged_evidence.py` + 聚焦 storage/staged 测试 | **PASS** | diff 3 文件；AA-03 略超 MAP 已接受                              |
| **关闭 ID**    | 私有化 + metadata-only 注释 + pytest                        | **PASS** | 符号 `_register_*`；L15–21 注释；4 项 R3Y 测                    |
| **行为**       | staging 写路径不得再为公开 API；staged pilot 仍绿           | **PASS** | `staged_pilot` 仅 import 常量；WriteManager 测绿                |
| **测试**       | MAP pytest 绿；五字段 + ponytail                            | **PASS** | 71 + full suite；新增测五字段齐全                               |
| **对抗性审计** | 无 OPEN；未改 `ops/**`、`layer4_markets/**`                 | **PASS** | 本报告 OPEN=0                                                   |
| **Registry**   | 本分支不改三件套；主会话批处理                              | **PASS** | git diff 无 `docs/*REGISTRY*`                                   |

---

## Findings table

| ID    | 严重度       | 状态       | Finding                                                           | 处置                                                                                                                         |
| ----- | ------------ | ---------- | ----------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| AA-01 | **BLOCKING** | **CLOSED** | 缺 `DEBT.plan.md`（§8.4 权威索引门禁）                            | 已创建 `DEBT.plan.md` 含 §3.1 + §3.5 全文表                                                                                  |
| AA-02 | **BLOCKING** | **CLOSED** | 缺 merge gate / TDD 证据路径                                      | 已补 `execute-evidence/β2-red.txt`、`β2-green.txt`、`merge_gate_report.md`                                                   |
| AA-03 | NON-BLOCKING | **CLOSED** | `tests/test_r3x_ponytail_pilot_prep_bucket_a.py` 略超 MAP allowed | **接受**：私有化后 import 断裂必改；仅符号重命名，无行为变更；已记入 `DEBT.plan.md` Boundary                                 |
| AA-04 | NON-BLOCKING | **CLOSED** | `test_raw_store` 与 bucket_a 均含 phase 门禁测（SC-02 重叠）      | **接受**：MAP 聚焦文件须自有 R3Y 守卫；bucket_a 保留 PROMPT_16 SC-02 映射                                                    |
| AA-05 | NON-BLOCKING | **CLOSED** | 私有化后 Python 仍允许 `import _register_*`；无生产引用静态证明   | 已增 `test_stagedEvidence_noProductionReferenceToRegistryBypass`                                                             |
| AA-06 | NON-BLOCKING | **CLOSED** | 私有 legacy INSERT 仍存在（裸 SQL bypass WriteManager）           | **设计内**：R3Y 要求「私有化**或**经 WriteManager」；生产 staged pilot 已走 WriteManager；私有 helper 仅测试 path/phase 回归 |
| AA-07 | NON-BLOCKING | **CLOSED** | Registry 三件套仍标 OPEN                                          | **主会话职责** — β-2 PR 故意不改；merge gate 已注明 defer                                                                    |

---

## 计划外发现

| ID  | 严重度 | 状态 | Finding                   | 说明                                                                                                                        |
| --- | ------ | ---- | ------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| —   | —      | —    | （无额外计划外 BLOCKING） | 已对抗搜索：`rg register_staged_file_registry_rows backend/` 仅 `staged_evidence.py`；`ops/staged_pilot` 仅 import 质量常量 |

---

## Adversarial checks (1–8)

### 1. 生产代码能否仍 `import register_staged_file_registry_rows`？

| 路径                                                                                 | 结果                                                       |
| ------------------------------------------------------------------------------------ | ---------------------------------------------------------- |
| `from backend.app.storage.staged_evidence import register_staged_file_registry_rows` | **ImportError**（符号不存在）                              |
| `from backend.app.storage.staged_evidence import *`                                  | **不含** bypass（`__all__` 仅三常量）                      |
| `hasattr(staged_evidence, "register_staged_file_registry_rows")`                     | **False**（`test_stagedEvidence_publicBypassNotExported`） |

### 2. `ops/staged_pilot` 是否仍旁路 WriteManager？

否 — 仅 import `STAGED_FILE_REGISTRY_*` 常量；`run_staged_pilot_raw_only` 经 `_StagedPilotFileRegistry` + WriteManager（`test_stagedPilot_mockFetchSuccess_usesWriteManagerStagedQualityFlag` 仍绿）。

### 3. `backend/` 除定义文件外是否引用旁路符号？

否 — `test_stagedEvidence_noProductionReferenceToRegistryBypass` 扫描全 `backend/**/*.py`（排除 `staged_evidence.py`）。

### 4. metadata-only 策略是否文档化？

是 — 模块顶注释 L15–21 + 私有函数 docstring L49–54 写明 `can_write_clean=false`、WriteManager 生产路径、`write_contract.yaml` staging 约束。

### 5. phase 门禁是否仍有效？

是 — `phase != phase3_staged` → `ValueError`；`test_stagedEvidence_rejectsWrongPhase` + bucket*a `test_sc02*\*` 双覆盖。

### 6. path sandbox（ADV-A1-004）是否回归？

是 — `test_stagedEvidence_pathEscape_rejected`、`test_stagedEvidence_allowedPath_registersRow` 仍绿。

### 7. 越界文件？

| Forbidden                       | Touched? |
| ------------------------------- | -------- |
| `backend/app/ops/**`            | **No**   |
| `backend/app/layer4_markets/**` | **No**   |
| registry trio                   | **No**   |

### 8. pytest 复跑（本审计）

```text
uv run pytest tests/test_staged_pilot.py tests/test_raw_store.py -q  → 71 passed, exit 0
uv run pytest -q                                                      → full suite green, exit 0
```

---

## §6 主会话验收前置（β-2）

| 项                    | 对抗性审计后状态                   |
| --------------------- | ---------------------------------- |
| MAP §2.2 Verification | 绿                                 |
| `uv run pytest -q`    | 绿                                 |
| DEBT.plan + 证据      | 齐                                 |
| 对抗性报告 OPEN       | **0**                              |
| worktree 提交         | **待主会话**（修复+审计未 commit） |
| registry 行 CLOSED    | **待主会话批处理**                 |

**可进入主会话 §6 + §8.4 验收提交：** **是**（pytest 全绿、OPEN=0、diff 在 allowed 内；主会话须 commit + registry 批处理）。

---

## Repair actions taken by adversarial audit

1. 创建 `DEBT.plan.md`（§3.1 + §3.5 权威索引）
2. 补 `execute-evidence/`（β2-red、β2-green、merge_gate_report）
3. 新增 `test_stagedEvidence_noProductionReferenceToRegistryBypass`
4. 复跑 MAP + 全量 pytest 确认绿

---

_Auditor model: composer-2.5 only（禁 fast）_
