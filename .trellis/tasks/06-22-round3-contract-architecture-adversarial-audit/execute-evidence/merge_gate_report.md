# Merge Gate Report — review/round3-contract-architecture-adversarial-audit (R3X)

| Field | Value |
| ----- | ----- |
| Branch | `review/round3-contract-architecture-adversarial-audit` |
| Worktree | `C:\Users\Guang\.cursor\worktrees\quant-monitor-desk-wt-review-r3-contract-architecture-audit` |
| Base | `master` @ `8961691a` |
| Task card | `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3X_contract_architecture_adversarial_audit.md` |
| Prompt | `docs/implementation_tasks/ROUND_3_PARALLEL_PROMPTS/PROMPT_11_review_round3_contract_architecture_adversarial_audit.md` |
| Slice type | Read-only adversarial audit (no implementation / no live fetch / no production DB write) |
| Date | 2026-06-22 |

## Verdict: **WARN**

Round 3 **staged-only** 下游（019 Layer2、023A Layer5 foundation、018C live probe plan）已合入且 gate 证据充分；核心骨架（DataSourceService、SourceRoutePlanner、WriteManager、DbValidationGate、sync orchestrator）有定向测试支撑。

但合约与实现之间存在 **8 项 HIGH** 级对抗性发现（其中 3 项为 registry 已登记主题的加强核实，5 项为 **NEW**），加上 **2 项 CRITICAL** 路由缺口，**不足以支撑 production-live readiness**。真实数据 staged pilot 可在 Batch 3 gate 约束下继续，但须显式避开未修复域（cninfo、未授权 macro primary、backfill gold path）。

**Production-live：BLOCKED**（政策门 + 本审计技术缺口叠加，非本报告单独新增政策）。

---

## Pre-flight

| Check | Status | Evidence |
| ----- | ------ | -------- |
| Base `master` @ `8961691a` clean | ✅ | `git status` empty; HEAD = merge PROMPT_10 |
| Review branch + worktree created | ✅ | `review/round3-contract-architecture-adversarial-audit` |
| Task card exists | ✅ | `R3X_contract_architecture_adversarial_audit.md` |
| No implementation code changes | ✅ | Review slice is report-only |
| No live fetch / production DB write | ✅ | Verification used targeted pytest only |
| PROMPT_07–10 batch evidence inspected | ✅ | See §Current batch artifacts below |

---

## Verification commands

| Command | Result | Notes |
| ------- | ------ | ----- |
| `pytest tests/test_source_capabilities.py -q` | ✅ green | |
| `pytest tests/test_source_route_planner.py -q` | ✅ green | |
| `pytest tests/test_datasource_service.py -q` | ✅ green | |
| `pytest tests/test_db_validation_gate.py -q` | ✅ green | |
| `pytest tests/test_write_manager.py -q` | ✅ green | |
| `pytest tests/test_sync_orchestrator.py -q` | ✅ green | |
| `pytest tests/test_ops_db_inspector.py -q` | ✅ green | |
| `pytest tests/test_module_boundaries.py -q` | ✅ green | |
| `pytest tests/test_round3_audit_registry_alignment.py -q` | ✅ green | |
| `pytest tests/test_unresolved_item_task_coverage.py -q` | ✅ green | |
| **Combined gate matrix** | **131 passed, 1 skipped** | 2026-06-22 review worktree |

---

## Current batch artifacts (PROMPT_07–10)

用户确认四分支已完成；以下证据在 base `8961691a` **可见**（无 `MISSING_CURRENT_BATCH_EVIDENCE`）。

### PROMPT_07 — `feature/round3-019-layer2-sensor` (merged `c940a8d0`)

| Item | Status |
| ---- | ------ |
| Merge gate | **PASS** (rev 3) — `.trellis/tasks/06-22-round3-019-layer2-sensor/execute-evidence/merge_gate_report.md` |
| Tests | 32 passed — `tests/test_layer2_sensor_loader.py` |
| Snapshot lineage | ✅ `axis_snapshot_lineage` (`layer_id=layer2`); `backend/app/layer2_sensors/lineage.py` |
| no-future-data | ✅ `reject_future_observation()` + 4 dedicated tests |
| double_count_guard | ✅ `double_count_guard.py` + axis-input rejection tests |
| Staged-only | ✅ fixture loader; no production DB mutation |
| 023A contract conflict | ✅ `snapshot_lineage_contract.yaml` untouched |

### PROMPT_08 — `feature/round3-023a-evidence-foundation` (merged `8a10dcb8`)

| Item | Status |
| ---- | ------ |
| Merge gate | **PASS** — `.trellis/tasks/06-22-round3-023a-evidence-foundation/execute-evidence/merge_gate_report.md` |
| Agent-text-not-fact-source | ✅ `EvidenceFoundationValidator` rejects factual agent provenance |
| Manual-review | ✅ `need_human_review=True` requires `manual_review_state=queued` |
| Lineage envelope | ✅ `Layer5LineageBuilder` aligns `LINEAGE_REQUIRED_FIELDS` |
| Defer | Full 023 → `023b`; `R3-PARTIAL-4` queue UX |

### PROMPT_09 — `review/round3-019-plan-audit`

| Item | Status |
| ---- | ------ |
| Report | **WARN** (0 BLOCK) — `docs/implementation_tasks/ROUND_3_REVIEW/019_plan_audit_report.md` |
| Trellis merge_gate | N/A — review lane; no `.trellis/tasks/**/merge_gate_report.md` for 09 |
| Open non-blockers | F-019-R01..R03 (AUDIT checklist / defer cross-ref / fixture comment) **未关闭** |
| 019 merge recommendation | ✅ 可继续 staged-only |

### PROMPT_10 — `debt/r3b275-018c-live-manual-probe-plan` (merged `8961691a`)

| Item | Status |
| ---- | ------ |
| Merge gate | **PASS (planning-only)** — `.trellis/tasks/06-22-round3-018c-live-manual-probe-plan/execute-evidence/merge_gate_report.md` |
| Live network | **No** |
| Production DB | **No mutation** |
| Authorization checklist | ✅ `authorization_checklist.md` + `tdx_live_manual_probe_gate.py` |
| tdx_pytdx | ✅ `enabled_by_default: false`, `validation_only: true` (registry L94–108) |
| `R3-B2.75-REQ2-EM` | **Open** — Eastmoney hist not closed |
| Adversarial F-22 | **Open** — commit pending user request (planning slice) |

---

## Completion quality summary

| 维度 | 评估 |
| ---- | ---- |
| 设计/契约 → 实现覆盖 | **部分对齐**：数据源门面、写路径、L1/L2/L5 staged 模块、ops read-only 工具已落地；L3/L4、gold backfill、production CLI、Round4 API 仍 deferred |
| Skeleton vs 实质实现 | L2/L5 本批次为 **staged 实质实现**（非空 stub）；sync `run_backfill`、reconcile、revision_audit 仍为 **partial/stub** |
| 测试质量 | Gate 矩阵 131 pass；Layer2 32、Layer5 foundation、018C auth 有专测；但 route/contract 缝隙部分 **无回归测试**（如 `validation_only` primary、cninfo matrix） |
| 文档时效 | `docs/quality/adversarial_audit_report.md`（2026-06-22 早批）将 Layer2 标为「未实现」——与 019 合入后 **过时**；`MIGRATION_008_PLAN` vs migration 009 状态 **矛盾** |
| Registry 对齐 | `BLOCK-R3-001/002` CLEAR；OPEN 阻塞项 0；本审计 5 NEW HIGH 建议 coordinator 评估是否入 `AUDIT_DEFERRED_REGISTRY` |

---

## Findings (deduplicated)

格式：`ADV-R3X-<area>-<n>`。`status` 已与 `docs/UNRESOLVED_ISSUES_REGISTRY.md` / `docs/AUDIT_DEFERRED_REGISTRY.md` 交叉核对。

### CRITICAL

#### ADV-R3X-ROUTE-001 — `validation_only` 源可作 Primary 被路由选中

```yaml
id: ADV-R3X-ROUTE-001
severity: HIGH
dimension: vulnerability
status: NEW
claim: akshare 等 validation_only 源可在 macro_supplementary 域成为 READY Primary
expected: source_registry.yaml L59-63 validation_only:true 不得作唯一事实源；source_route_contract.yaml L41-47 禁止 Validation 升格 Primary
actual: SourceRoutePlanner 不读取 validation_only；macro_supplementary primary=akshare 可 READY（route_planner.py L109-140）
impact: validation 聚合源进入主抓取/主写路径，污染 clean 表血缘
blocks_real_data_pilot: partial  # B2.75 显式授权 akshare macro 为 staged 例外
blocks_production_live: true
recommended_action: fix
suggested_branch: feature/round3-route-validation-only-guard
```

#### ADV-R3X-ROUTE-002 — 平台矩阵缺失阻断 cninfo 域

```yaml
id: ADV-R3X-ROUTE-002
severity: HIGH
dimension: gap
status: NEW
claim: cn_filings / cninfo 在 DataSourceService 路径永不可 READY
expected: source_registry.yaml L129-135 cn_filings primary=cninfo, domain_enabled
actual: platform_source_matrix.yaml 仅含 qmt/baostock/akshare；缺失源返回 platform_matrix_missing（route_planner.py L50-54）
impact: 公告域无法经标准门面调度
blocks_real_data_pilot: true  # 若 pilot 含 cninfo
blocks_production_live: true
recommended_action: fix
suggested_branch: feature/round3-platform-matrix-cninfo
```

### HIGH

#### ADV-R3X-SYNC-001 — Orchestrator adapter 旁路 DataSourceService

```yaml
id: ADV-R3X-SYNC-001
severity: HIGH
dimension: deviation
status: NEW
claim: run_incremental/run_backfill 可直接 adapter.fetch() 绕过门面
expected: datasource_service_contract.yaml L26-39 sync runners 须经 DataSourceService
actual: orchestrator.py L131-160; runners.py adapter= 路径直接 fetch
impact: 跳过 route plan、capability assert、统一 fetch_log
blocks_real_data_pilot: partial
blocks_production_live: true
recommended_action: fix
suggested_branch: feature/round3-sync-service-only-fetch
```

#### ADV-R3X-WRITE-001 — write_audit source_used 硬编码 job spec

```yaml
id: ADV-R3X-WRITE-001
severity: HIGH
dimension: deviation
status: NEW
claim: 清洁写 source_used 固定为 spec.source_id 而非实际 fetch/route 源
expected: write_contract.yaml + source_route_contract.yaml L46 禁止事后篡改 source_used
actual: runners.py L115-118 source_used=spec.source_id, source_role="primary"
impact: fallback 场景下审计血缘造假
blocks_real_data_pilot: partial
blocks_production_live: true
recommended_action: fix
suggested_branch: feature/round3-write-source-used-from-fetch
```

#### ADV-R3X-CONFLICT-001 — 冲突阈值域名漂移

```yaml
id: ADV-R3X-CONFLICT-001
severity: HIGH
dimension: deviation
status: NEW
claim: cn_equity_daily_bar 等大偏差不报 severe
expected: source_conflict_rules.yaml 阈值覆盖生产域（registry 用 cn_equity_daily_bar）
actual: 阈值仅在 market_bar_1d；_threshold_for 对 canonical 域返回 None（validators/source_conflict.py L115-158）
impact: 多源冲突静默通过，DbValidationGate severe 阻断失效
blocks_real_data_pilot: true
blocks_production_live: true
recommended_action: fix
suggested_branch: feature/round3-conflict-domain-alias
```

#### ADV-R3X-VALID-001 — schema_hash_changed 门未实现

```yaml
id: ADV-R3X-VALID-001
severity: HIGH
dimension: gap
status: NEW
claim: 未批准 schema 变更仍可清洁写
expected: write_contract.yaml L31-35 schema_hash_changed && !schema_change_approved → reject
actual: DbValidationGate 仅查 status/can_write_clean/needs_manual_review/severe conflict（validation_gate.py L108-138）
impact: schema drift 可进入 clean 表
blocks_real_data_pilot: partial
blocks_production_live: true
recommended_action: fix
suggested_branch: feature/round3-schema-hash-gate
```

#### ADV-R3X-SYNC-002 — backfill 绕过冲突 gate

```yaml
id: ADV-R3X-SYNC-002
severity: HIGH
dimension: vulnerability
status: DUPLICATE  # R3-PARTIAL-1
claim: backfill _write_clean 固定 conflict_report_id=None
expected: incremental 路径 SEVERE_CONFLICT → WAITING_RECONCILE；gate 查 open severe
actual: runners.py L516 conflict_report_id=None（backfill shard write）
impact: backfill gold path 无 severe 冲突保护
blocks_real_data_pilot: true
blocks_production_live: true
recommended_action: fix  # 已有 registry 条目
suggested_branch: feature/round3-backfill-gold-path
```

#### ADV-R3X-L1-001 — Layer1 工程 guardrail 未接入 commit

```yaml
id: ADV-R3X-L1-001
severity: HIGH
dimension: gap
status: NEW
claim: AxisEngineeringGuardrailValidator 存在但未进入 runtime commit
expected: layer1 设计：forbidden substitutes / shadow constraints 在写入前 enforced
actual: guardrails.py 定义 validator；全库仅定义处引用，axis commit 路径未调用
impact: 工程约束可绕过
blocks_real_data_pilot: partial
blocks_production_live: true
recommended_action: fix
suggested_branch: feature/round3-l1-guardrail-wire
```

#### ADV-R3X-L1-002 — 禁止操作词默认路径静默替换

```yaml
id: ADV-R3X-L1-002
severity: HIGH
dimension: deviation
status: NEW
claim: 默认 interpretation 将禁止词替换为「观察」而非拒绝
expected: 禁止交易动作语义应 reject（layer1_global_regime_panel 设计）
actual: interpretation.py L46-49 replace(term, "观察")；reject_if_forbidden 存在但非默认路径
impact: 动作语义污染可进入快照/展示
blocks_real_data_pilot: partial
blocks_production_live: true
recommended_action: fix
suggested_branch: feature/round3-l1-forbidden-reject
```

### MEDIUM

| ID | claim | status | blocks_pilot | blocks_live |
| -- | ----- | ------ | ------------ | ----------- |
| ADV-R3X-PILOT-001 | live_pilot `create_adapter().fetch()` 绕过门面 | NEW | false | true |
| ADV-R3X-PILOT-002 | pilot 合成 validation_report 可写 clean（sandbox 内） | NEW | false | true |
| ADV-R3X-SERVICE-001 | `file_registry_factory=None` → test adapter | NEW | true | true |
| ADV-R3X-ROUTE-003 | planner 未 enforce `domain_enabled_by_default` | NEW | partial | partial |
| ADV-R3X-ROUTE-004 | Validation 角色选中无 quality flag | NEW | partial | true |
| ADV-R3X-SYNC-003 | `conflict_staging_table=None` 时跳过冲突校验 | NEW | true | true |
| ADV-R3X-WRITE-002 | write_mode 合约部分未实现 | DUPLICATE R2-RISK-3 | false | partial |
| ADV-R3X-LINEAGE-001 | L3/L4 snapshot lineage 未实现 | NEW | partial | true |
| ADV-R3X-STAGE-001 | staged_evidence 旁路 WriteManager | ALREADY_DEFERRED / documented exception | false | partial |
| ADV-R3X-DOC-001 | adversarial_audit_report Layer2「未实现」与 019 矛盾 | NEW | false | false |

### LOW

| ID | claim | status |
| -- | ----- | ------ |
| ADV-R3X-CAP-001 | ADAPTER_DOMAIN_COMPATIBILITY_MAP 遗留域名双轨 | NEW |
| ADV-R3X-CAP-002 | tdx_pytdx runtime assert 测试覆盖弱于 qmt_xqshare | NEW |

---

## Blocker matrix

| 门槛 | 状态 | 依据 |
| ---- | ---- | ---- |
| Round 3 planning continuation | ✅ **CLEAR** | BLOCK-R3-001/002 |
| Batch 3 staged downstream (019/023A) | ✅ **CLEAR** | R3-B3-STAGED-DOWNSTREAM-GATE CLOSED |
| Real-data staged pilot (bounded) | ⚠️ **CONDITIONAL** | 可用 service 路径 + sandbox + raw_only；避开 cninfo、未授权 macro primary、backfill gold |
| Production-live readiness | ❌ **BLOCKED** | PILOT_FAIL_SOURCE、R3-B2.75-REQ2-EM、B2.5-O-05 FRED、R2.6-IMPL-8 + 本审计 HIGH/CRITICAL 缺口 |

---

## Recommended next branches (coordinator)

| Priority | Branch | Closes |
| -------- | ------ | ------ |
| P0 | `feature/round3-route-validation-only-guard` | ADV-R3X-ROUTE-001 |
| P0 | `feature/round3-platform-matrix-cninfo` | ADV-R3X-ROUTE-002 |
| P0 | `feature/round3-conflict-domain-alias` | ADV-R3X-CONFLICT-001 |
| P1 | `feature/round3-sync-service-only-fetch` | ADV-R3X-SYNC-001 |
| P1 | `feature/round3-write-source-used-from-fetch` | ADV-R3X-WRITE-001 |
| P1 | `feature/round3-schema-hash-gate` | ADV-R3X-VALID-001 |
| P1 | `feature/round3-backfill-gold-path` | ADV-R3X-SYNC-002 / R3-PARTIAL-1 |
| P2 | `feature/round3-l1-guardrail-wire` + `feature/round3-l1-forbidden-reject` | ADV-R3X-L1-* |
| P2 | `debt/r3x-doc-adversarial-report-refresh` | ADV-R3X-DOC-001 |

---

## Registry actions for coordinator

1. 评估 5 项 **NEW HIGH** 是否写入 `AUDIT_DEFERRED_REGISTRY.md`（尤其 ADV-R3X-SYNC-001、ADV-R3X-VALID-001、ADV-R3X-L1-*）。
2. 保持 `R3-PARTIAL-1` 为 ADV-R3X-SYNC-002 的 canonical ID，避免重复登记。
3. 刷新 `docs/quality/adversarial_audit_report.md` Layer2 排除前提（019 已合入）。
4. 统一 migration 008 plan vs 009 applied 叙事（`A9-*` / `B2.5-O-06`）。

---

## Forbidden scope honored

- ✅ No implementation code changes
- ✅ No contract/spec edits to hide findings
- ✅ No production DB writes / migrations
- ✅ No external source fetch / QMT / xqshare / tdx live enablement
- ✅ No direct merge of feature branches
- ✅ Unverified claims marked NEEDS_VERIFICATION or tied to file refs above

---

## Coordinator acceptance checklist

- [ ] Verdict PASS/WARN/BLOCK recorded → **WARN**
- [ ] PROMPT_07–10 evidence included or MISSING flagged → **included**
- [ ] Findings have severity, expected, actual, impact, file refs → **yes**
- [ ] Staged pilot vs production-live blockers explicit → **yes (§Blocker matrix)**
- [ ] Dedup against unresolved/deferred registries → **yes (§Findings status)**
- [ ] Next branch recommendations → **yes (§Recommended next branches)**
