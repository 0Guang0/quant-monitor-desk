# closed-claim matrix — R3Y-AUD-01

> **基准 HEAD:** `61436a51` · **审计日:** 2026-06-23  
> **图例:**  
> - **V** VERIFIED — code trace + 专用/伞测 pytest 在本 worktree 绿  
> - **P** PARTIAL — code 存在，测试间接或仅 merge 自述  
> - **I** INHERITED — 闭合证据来自前置 PROMPT/POST14，非 PROMPT_15 本地 evidence  
> - **U** UNVERIFIED — 仅 merge_gate 声称，本 agent 未 trace 到独立测试  
> - **C** CONTRADICTED — 代码或测试与 FIXED 声称冲突  

**伞测:** `uv run pytest tests/test_r3x_residual_open_items_closure.py -q` → **18 passed, exit 0**

---

## 汇总

| PROMPT | 任务 | merge 声称闭合数 | 本矩阵抽样 | V | P | I | U | C |
|--------|------|------------------|------------|---|---|---|---|---|
| 11 | contract architecture audit | 审计产出（非 fix） | 见 §11 | — | — | — | — | — |
| 12 | data-source routing blockers | 5 FIXED + 5 defer | §12 | 5 | 0 | 0 | 5* | 0 |
| 13 | db write validation blockers | 5 FIXED + defer | §13 | 3 | 2 | 0 | 多 | 0 |
| 14 | real-data staged pilot | feature 验收 | §14 | — | — | 多数 I→POST14 | — | — |
| 15 | r3x residual closure | **73 FIXED/CLOSED, 0 OPEN** | §15 | 18 | 12 | 25 | 16 | 1 |
| 16 | ponytail bucket A | 8 FIXED | §16 | 6 | 2 | 0 | 0 | 0 |
| 17 | ponytail low touch | debt | §17 | — | — | — | — | — |

\*PROMPT_12 defer 项在 PROMPT_15 重新标 FIXED — 见 §12↔§15 交叉表

---

## §11 — PROMPT_11（review，非实现闭合）

| 产出 | 声称 | Code | Test | Evidence | Verdict |
|------|------|------|------|----------|---------|
| ADV-R3X 清单 / adversarial_audit_report | 识别 OPEN 项 | N/A（审计） | N/A | `archive/.../06-22-round3-contract-architecture-adversarial-audit/` | 审计基线，非 closure claim |

---

## §12 — PROMPT_12 `fix-round3-data-source-routing-blockers`

| ID | merge 声称 | Code trace | Test | Evidence file | Verdict | 备注 |
|----|------------|------------|------|---------------|---------|------|
| ADV-A2-001 | FIXED | `data_adapter_contract.md` DISABLED_SOURCE | `test_data_adapter_contract.py` | merge_gate only | **V** | |
| ADV-A2-003 | FIXED | `source_registry.yaml` domain_roles | `test_source_capabilities.py` | merge_gate only | **V** | |
| ADV-A2-005 | FIXED | `service.py` `_default_operation` | `test_r3x_residual::test_defaultOperation_*` | 伞测 | **V** | |
| ADV-A2-006 | FIXED | `platform_source_matrix.yaml` | `test_platform_source_matrix.py` | merge_gate only | **P** | 未在本 agent 复跑 |
| ADV-A2-007 | FIXED | `route_models.py` requested_source_id | `test_datasource_service.py` | merge_gate only | **P** | |
| ADV-A2-002 | **deferred** → P15 FIXED | `base_adapter.health_check` STUB_OK | `test_advA2_002_*` 伞测 | P12 defer / P15 无 green | **P** | 跨 PROMPT 状态翻转 |
| ADV-A2-004 | **deferred** → P15 FIXED | `CninfoAdapter.supported_domains` | `test_advA2_004_*` 伞测 | 同上 | **P** | 声明域存在 ≠ adapter 实现完成 |
| ADV-A2-009 | **deferred** → P15 FIXED | `_ADAPTER_TYPES["tdx_pytdx"]` | `test_advA2_009_*` 伞测 | 同上 | **V** | disabled-by-default 未变 |
| ADV-A2-010 | **deferred** → P15 FIXED | `route_planner` DISABLED_SOURCE | 间接 `test_source_route_planner` | 无专用 ID 测试 | **P** | |
| ADV-A2-012 | **deferred** → P15 FIXED | `_MATRIX_CACHE` | 无专用测试 | 无 | **U** | 仅 merge 叙事 |

---

## §13 — PROMPT_13 `fix-round3-db-write-validation-blockers`

| ID | merge 声称 | Code trace | Test | Evidence | Verdict |
|----|------------|------------|------|----------|---------|
| ADV-A1-003 | FIXED | `validation_gate.py` SCHEMA_DRIFT | `test_db_validation_gate.py` | merge_gate | **V** | 未在伞测 |
| ADV-A1-004 | FIXED | `staged_evidence._resolve_under_data_root` | `test_raw_store.py` | merge_gate | **V** | bypass 仍 documented |
| ADV-A1-005 | FIXED | `failed_write_audit_sidecar.py` | `test_write_manager.py` | merge_gate | **P** | 未独立复跑 |
| ADV-A3-001 | FIXED | `runners.py` SEVERE_CONFLICT→WAITING_RECONCILE | `test_sync_orchestrator.py` | merge_gate | **P** | |
| ADV-A3-003 | FIXED | conflict_report_id persist | `test_sync_orchestrator.py` | merge_gate | **P** | |
| ADV-A1-001..015（除 003–005） | **defer** → P15 FIXED | 见 §15 ADV-A1 | 伞测仅 001/012 | P15 无 green | **P/I** | |

merge_gate L50 明确：`staged file_registry path still bypasses WriteManager` — **与 FIXED 叙事并存（documented exception）**

---

## §14 — PROMPT_14 `feature-round3-real-data-staged-pilot`

| 声称 | 验证 | Verdict |
|------|------|---------|
| staged pilot mock fetch + evidence 工件 | `feature-round3-real-data-staged-pilot/execute-evidence/*.json` + `verification-minimum.txt`（全量 pytest 摘要无逐用例） | **I** → POST14 A-* 接管闭合 |
| 不经 WriteManager 路径 | POST14 A-004 改 `_StagedPilotFileRegistry` | **V** via POST14 |

---

## §15 — PROMPT_15 `fix-round3-r3x-residual-open-items-closure`（主矩阵）

### 15.1 ADV-R3X（route / sync / write / pilot）

| ID | 声称 | Code | Test | Verdict | Finding |
|----|------|------|------|---------|---------|
| ADV-R3X-ROUTE-001 | FIXED | `route_planner.py:143` validation_only_cannot_be_primary | `test_advR3xRoute001_*` | **V** | |
| ADV-R3X-ROUTE-002 | ALREADY_CLOSED | platform matrix | 无伞测 | **I** | 依赖 P12 回归 |
| ADV-R3X-ROUTE-003 | FIXED | `route_planner.py:173` DOMAIN_DISABLED_BY_DEFAULT | `test_advR3xRoute003_*` | **V** | |
| ADV-R3X-ROUTE-004 | FIXED | `route_planner.py:200` VALIDATION_SOURCE_USED | `test_advR3xRoute004_*` | **V** | conditional assert |
| ADV-R3X-SYNC-001 | FIXED | orchestrator `fetch_callable`→`service.fetch` | `test_sync_orchestrator` datasource_service 3 处 | **C→P** | **adapter= 旁路仍在** |
| ADV-R3X-SYNC-002 | ALREADY_CLOSED | — | 无 | **I** | |
| ADV-R3X-SYNC-003 | FIXED | `runners.py:147` CONFLICT_CHECK_SKIPPED | 无 event 断言 | **P** | |
| ADV-R3X-WRITE-001 | FIXED | `runners.py:397,725` fetch_result.source_id | 间接 sync tests | **P** | |
| ADV-R3X-WRITE-002 | FIXED | `write_manager.UNSUPPORTED_MODES` | `test_advR3xWrite002_*` | **V** | |
| ADV-R3X-VALID-001 | ALREADY_CLOSED | validation_gate | 无伞测 | **I** | |
| ADV-R3X-CONFLICT-001 | FIXED | CONFLICT_DOMAIN_ALIASES | `test_advR3xConflict001_*` | **V** | |
| ADV-R3X-L1-001 | FIXED | ingestion_commit guardrail | 无伞测 | **U** | |
| ADV-R3X-L1-002 | FIXED | interpretation forbidden terms | `test_advR3xL1_002_*` | **V** | |
| ADV-R3X-PILOT-001 | FIXED | `live_pilot_phase3` service.fetch | `test_batch275_live_pilot_gate.py` | **I** | 非伞测 |
| ADV-R3X-PILOT-002 | FIXED | DbValidationGate synthetic flags | `test_batch275_*` / gate tests | **I** | |
| ADV-R3X-SERVICE-001 | FIXED | production fetch 需 port | `test_advR3xService001_*` | **V** | |
| ADV-R3X-STAGE-001 | FIXED | Layer1 `_register_clean_file_registry_rows` | `test_layer1_*` / POST14 | **I** | |
| ADV-R3X-DOC-001 | FIXED | adversarial_audit_report 刷新 | 无 auto test | **U** | 文档闭合 |
| ADV-R3X-CAP-001 | FIXED | ADAPTER_DOMAIN_COMPATIBILITY_MAP {} | `test_advR3xCap001_*` | **V** | |
| ADV-R3X-CAP-002 | FIXED | tdx_pytdx factory | `test_advR3xCap002_*` | **V** | |

### 15.2 ADV-A1（write / registry）

| ID | 声称 | 伞测 | 其它测试 | Verdict |
|----|------|------|----------|---------|
| ADV-A1-001 | FIXED | `test_advA1_001_*` | — | **V** |
| ADV-A1-002 | FIXED | — | write_manager 间接 | **U** |
| ADV-A1-003 | ALREADY_CLOSED | — | `test_db_validation_gate` | **I** |
| ADV-A1-004 | ALREADY_CLOSED | — | `test_raw_store` | **I** |
| ADV-A1-005 | ALREADY_CLOSED | — | `test_write_manager` | **I** |
| ADV-A1-006 | FIXED | — | 无专用 | **U** |
| ADV-A1-007 | FIXED | — | 无专用 | **U** |
| ADV-A1-008 | FIXED | — | resource_guard tests | **P** |
| ADV-A1-009 | FIXED | — | migration tests | **P** |
| ADV-A1-010 | FIXED | — | yaml 存在性 | **U** |
| ADV-A1-011 | FIXED | — | 无专用 | **U** |
| ADV-A1-012 | FIXED | `test_advA1_012_*` | — | **V** |
| ADV-A1-013 | FIXED | — | 无专用 | **U** |
| ADV-A1-014 | FIXED | — | 无专用 | **U** |
| ADV-A1-015 | FIXED | 同 012 | — | **V** |

### 15.3 ADV-A2 / ADV-A3 / ADV-A5 / ADV-A6 / F-019 / Registry

| 集群 | FIXED 数 | 伞测覆盖 | Verdict 摘要 |
|------|----------|----------|--------------|
| ADV-A2（P15 表） | 9 | 002/004/009 + defaultOperation | **V:4 P:3 I:2 U:1** |
| ADV-A3 | 16 | 仅 016 伞测 | **V:1 P:4 I:4 U:7** |
| ADV-A5 | 2 | 001 伞测 + production_gate | **V:1 P:1** |
| ADV-A6 | 4 | 004 伞测（vite proxy 字符串） | **V:1 U:3** |
| F-019 | 3 | 无 | **U:3** |
| Registry R1–R4 | 4 | `test_round3_audit_registry_alignment`（AUD-06） | **I** — 交 AUD-06 |

### 15.4 PROMPT_15 证据完整性

| 检查项 | 结果 |
|--------|------|
| `execute-evidence/*-green.txt` | **0 文件** |
| merge_gate Tests 节 | 仅 `# exit 0` 注释 |
| 伞测 / 声称闭合比 | **18 / 73 = 24.7%** |
| pytest 本 agent 复跑 | **18 passed** |

---

## §16 — PROMPT_16 `fix-round3-ponytail-pilot-prep-bucket-a`

| ID | 声称 | Code | Test | green.txt | Verdict |
|----|------|------|------|-----------|---------|
| DS-01 | FIXED | fetch_log 单写者 | `test_r3x_ponytail_pilot_prep_bucket_a` | DS-01-green.txt | **V** |
| DS-02 | FIXED | `_build_adapter` dedupe | 伞测 | DS-02-green.txt ✓ | **V** |
| DS-03 | ALREADY_CLOSED | fetch 需 port | 伞测 | DS-03-green.txt | **V** |
| SC-02 | FIXED | phase3_staged gate | 伞测 | SC-02-green.txt | **V** |
| OP-02 | FIXED | mutation_proof | 伞测 | OP-02-green.txt | **P** | 未复跑 |
| SY-04 | FIXED | `_fetch_with_guard` 统一 | 伞测 | SY-04-green.txt | **P** | 与 SYNC-001 旁路相关 |
| VA-03 | ALREADY_CLOSED | as_text(None) | 伞测 | VA-03-green.txt | **V** |
| DB-03 | FIXED | assert_can_write | 伞测 | DB-03-green.txt | **P** | |

**PROMPT_16 evidence 质量显著优于 PROMPT_15**（8/8 有 green.txt 或伞测映射）。

---

## §17 — PROMPT_17 `debt-round3-ponytail-low-touch`

| 声称 | 验证 | Verdict |
|------|------|---------|
| 结构性债务低触碰修复 | `tests/test_r3x_ponytail_structural_bucket_b.py`（AUD-07 范围） | **交 AUD-07** |

本 agent 未将 PROMPT_17 标为 PROMPT_15 式「0 OPEN」闭合；视为独立 debt slice。

---

## §12 ↔ §15 交叉 — defer 翻转追踪

| ID | P12 @ merge | P15 @ merge | 本审计 code | 本审计 test | 翻转可信？ |
|----|-------------|-------------|-------------|-------------|------------|
| ADV-A2-002 | defer | FIXED | health_check STUB | 伞测绿 | **P** — 缺增量 commit evidence |
| ADV-A2-004 | defer | FIXED | supported_domains 声明 | 伞测绿 | **P** — 实现深度未证 |
| ADV-A2-009 | defer | FIXED | 工厂注册 | 伞测绿 | **V** |
| ADV-A2-010 | defer | FIXED | DISABLED guard | 间接 | **P** |
| ADV-A2-012 | defer | FIXED | _MATRIX_CACHE | 无 | **U** |

---

## 反证结论矩阵（按 AUD-01 必答问题）

| 问题 | 答案 |
|------|------|
| PROMPT_11–17 closed 是否真闭合？ | **部分** — 代码多数到位；P15 全量 73 项 **不可证** |
| 测试绿但 runtime 未覆盖？ | **是** — SYNC-001 adapter 旁路；多 ADV-A3/A6/F-019 无行为测试 |
| merge report 能当事实吗？ | **否** — 已用 trace 纠偏 |
| 建议 gate | **WARN** — 见 `R3Y-AUD-01-closed-claims.md` |

---

## 关键 finding 摘要（Top 3）

1. **PROMPT_15：73 项闭合 vs 18 伞测 + 0 green.txt** — 证据链不满足 A5「不以自述为 PASS」。
2. **ADV-R3X-SYNC-001：adapter= 旁路仍合法** — FIXED 声称过度；生产需 fail-closed 或 registry 回退。
3. **PROMPT_12 defer → P15 FIXED 无增量 evidence** — 至少 ADV-A2-012 仍 UNVERIFIED；跨 PROMPT 叙事需 commit 级追溯。
