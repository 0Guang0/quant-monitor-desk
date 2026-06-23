# MASTER 计划 — B-19 Round 3 staged real-data pilot v2

> **Execute 入口** — staged-only；**不得**声称 production-live readiness。  
> 索引：`research/source-index.md` · `context_pack.json` · Audit：`AUDIT.plan.md`

---

## 0. 元信息

| 字段                      | 值                                                                 |
| ------------------------- | ------------------------------------------------------------------ |
| 任务 slug                 | `06-24-round3-real-data-staged-pilot-v2`                           |
| 分支                      | `feature/round3-real-data-staged-pilot-v2`                         |
| 前置                      | PROMPT_14 merged；R3X residual CLOSED；R3Y strict audit WARN_ALLOW |
| manifest_protocol_version | `3`                                                                |
| `EVIDENCE_ROOT`           | `.trellis/tasks/06-24-round3-real-data-staged-pilot-v2/execute-evidence/` |
| analysis_waiver           | `false`                                                            |
| 原计划                    | `research/source-index.md` · `research/original-plan-trace.md`     |

### Staged downstream limitations（§16 强制）

1. `production_live_pilot_policy.md` — staged-only / sandbox-first
2. `R3-B2.75-REQ2-EM` — **DEFERRED**；不得作 live 前提
3. `staged_acceptance_policy.md` — 不得 staged 冒充 live
4. 允许真实网络 fetch，但限于 caps 内小样本；**无** production clean write
5. AUD-08 `WARN_ALLOW_WITH_CONTROLS` — 见下表

### AUD-08 控件（PROMPT_19 必守）

| 控件 | 执行要求 |
| ---- | -------- |
| REQ2-EM DEFERRED | closeout 不得引用 EM live unblock |
| sync `adapter=` 旁路 | 扩样前确认生产 CLI 不经旁路；§1.5 停损 |
| mutation proof | closeout 须 `db_hash_unchanged` + `row_counts_unchanged`；**R3Y-MUT-PROOF-001** 闭合 AUD-04 |
| 授权链 | 沿用 PROMPT_14 授权路径；sandbox WriteManager only |
| production-live 声称 | `production_live_readiness_claim: false` 强制 |

### 默认 v2 caps（可 §8.1 冻结到 JSON）

| 项 | 默认 |
| -- | ---- |
| `pilot_id` | `r3y-staged-pilot-v2-20260624` |
| `max_symbols` | 5 |
| `max_trade_days` | 30 |
| `max_rows_per_source_domain` | 500 |
| `max_network_calls_per_run` | 25 |
| `sandbox_root` | `.audit-sandbox/r3y-staged-pilot-v2/` |
| `production_clean_write` | `false` |

### Failure modes / 回滚

| 场景 | 处理 |
| ---- | ---- |
| 超 cap 无用户批准 | `StagedPilotAuthorizationError`；无 fetch |
| production DB 变异 | 中止；记录 MUTATION_DETECTED；不勾 GREEN |
| 非 staged mode / clean write | 拒绝 |
| scope 偏离任务卡 | 停止 Execute；回 Plan |
| 回滚 | revert 本分支 ops/tests 改动；无 prod migration |

### 0.1 门控速查

| 项        | 值                                                                 |
| --------- | ------------------------------------------------------------------ |
| 怎么测    | §8 RED→GREEN；`tests/test_staged_pilot.py` + §10 Tier A            |
| 怎么验收  | §10 Tier A + 九切片 evidence                                       |
| 什么叫过  | §2 全部 AC + AUD-08 控件 + 无 production-live 声称                 |
| prod-path | Tier B：`uv run pytest -q` 全库回归（仅 §8.10）                    |
| 6.pre     | `research/gitnexus-execute-summary.md`                             |

### 0.3 Execute 强制必读清单

**规则：** Phase 0 Boot **必须 Read `implement.jsonl` 每一条**；先读 `research/integration-ledger.md`。  
**禁止**在 §8.0 枚举路径清单 — 以 §0.3 + implement.jsonl 为准。

### 0.3a Execute 工程纪律 — Ponytail

1. Boot 起 MUST Read `.cursor/rules/ponytail.mdc`；**每个 §8.x 步开始前**对照 ladder
2. 写业务代码前：YAGNI → 复用 `staged_pilot.py` / `mutation_proof.py` → 最小 diff
3. TDD 顺序：RED → karpathy-guidelines → testing-guidelines → ponytail → GREEN
4. 每步 GREEN 证据含 ponytail self-check 一行
5. 禁止新抽象/新依赖；有意简化用 `ponytail:` 注释

### 0.3b Execute 工程纪律 — 测试与回归（强制）

1. TDD：每 §8.x 先 RED → `karpathy-guidelines` + `testing-guidelines` → GREEN
2. 每步 GREEN 后 Read `incremental-implementation`；Tier B `uv run pytest -q` **仅 §8.10**
3. 任何修复后至少跑当前步 L1 `tests/test_staged_pilot.py` 子集
4. **禁止弱化测试目的**；测试 docstring 须含 **覆盖范围**、**测试对象**、**目的**（**目的**须通俗中文，小白能懂在防什么/证明什么）
5. ponytail 违规 → 停止当前 §8 步

### 0.4 上下文打包（v3）

Execute 以 MASTER inline + ledger pointer 为准。

### 0.5 Execute 开场白

```text
进入 Execute。MUST Read trellis-execute SKILL + ponytail（§0.3a）。Phase 0（§0.3 + ledger）→ §8.x → §10 → Audit。勿 finish-work。
```

---

## 1. 目标

在 PROMPT_14 v1 基础上扩样 baostock / cninfo / akshare validation，产出 v2 证据链，回答 R3Y 任务卡 §3 九个问题。

### 1.1 目的

暴露真实数据质量、路由、schema、validation、conflict、no-mutation；为 PROMPT_20 read-only data health 与可选 sandbox clean-write rehearsal 提供输入。

### 1.2 前置

- PROMPT_14 + post-14 audit + R3X residual closure merged
- R3Y strict audit `WARN_ALLOW_WITH_CONTROLS`
- 波次 B 前置：registry hygiene（`fix/r3y-registry-lineage-defer`）与 sync guard（`fix/r3y-sync-adapter-guard`）见 `round3-wave-a-slice-plans.md`；**不阻塞**本分支 Plan freeze

### 1.3 约束

- staged-only；allowed 见 §3.1 · `research/worktree-slices.md`
- `R3-B2.75-REQ2-EM` DEFERRED
- 九垂直切片独立 evidence（不得单脚本冒充）

### 1.5 停止条件

| #   | 事件 | 处理 |
| --- | ---- | ---- |
| 1   | Plan 未 freeze / 用户未批准 | 禁止 `task.py start` |
| 2   | 触发 §3.3 forbidden 路径 | 立即停止；revert |
| 3   | production clean table 行数/hash 变化 | 中止；MUTATION_DETECTED 证据 |
| 4   | 未经批准的 caps 扩样 | `StagedPilotAuthorizationError` |
| 5   | 声称 production-live readiness | 中止；修正 MASTER/closeout |
| 6   | 生产入口使用 sync `adapter=` 旁路 | 停止；回协调者（AUD-08） |
| 7   | RED 非预期全库红 | 停当前 §8 步 |

### 1.6 原计划归并

| 来源 | 内容 |
| ---- | ---- |
| `PROMPT_19_*.md` | 分支、切片、验证、allowed files |
| `R3Y_real_data_staged_pilot_v2.md` | AC 表、caps、禁止项 |
| `R3Y_staged_pilot_v2_execution_addendum.md` | /to-issues、TDD、ponytail |
| `R3Y-AUD-08-go-no-go.md` | WARN_ALLOW 控件 |
| `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §2.2 | PROMPT_19 索引（§2.4.2 待 map 增补） |
| 纠偏 | v1 evidence 路径见 `source-index.md` §B |

---

## 2. 预期结果（AC）

| ID | 预期结果 | 验证链 | 切片 |
| -- | -------- | ------ | ---- |
| AC-SP2-01 | `pilot_v2_caps.json` 冻结 ID/caps/sandbox | §8.1 | R3Y-SP2-01 |
| AC-SP2-02 | baostock 扩样 raw/staging manifest v2 | §8.2 | R3Y-SP2-02 |
| AC-SP2-03 | cninfo metadata 扩样 + schema notes | §8.3 | R3Y-SP2-03 |
| AC-SP2-04 | akshare validation taxonomy + re-defer | §8.4 | R3Y-SP2-04 |
| AC-SP2-05 | `route_preview_matrix_v2.json` 全状态 | §8.5 | R3Y-SP2-05 |
| AC-SP2-06 | `validation_report_v2.json` 质量暴露 | §8.6 | R3Y-SP2-06 |
| AC-SP2-07 | `conflict_check_summary_v2.json` | §8.7 | R3Y-SP2-07 |
| AC-SP2-08 | `no_mutation_proof_v2.md` + **R3Y-MUT-PROOF-001** | §8.8 | R3Y-SP2-08 |
| AC-SP2-09 | `pilot_v2_closeout.json` expand/re-defer 矩阵 | §8.9 | R3Y-SP2-09 |
| AC-MUT-001 | `proof_status=VERIFIED` 仅当 hash∧counts 均为 true；否则 `MUTATION_DETECTED`/`INCONCLUSIVE` | §8.8; `test_mutationProof_*` | β-1 |

---

## 3. 范围

### 3.1 In scope

- `backend/app/ops/staged_pilot.py`
- `backend/app/ops/staged_pilot_fetch_ports.py`
- `backend/app/ops/mutation_proof.py`（R3Y-MUT-PROOF-001）
- 窄 pilot 所需 `datasources/` / `storage/` 修复
- `tests/test_staged_pilot.py`、`tests/test_vendor_fetch_e2e.py`（若需）、`tests/test_production_live_pilot_policy.py`
- `.trellis/tasks/06-24-round3-real-data-staged-pilot-v2/execute-evidence/*` v2 产物 → **`EVIDENCE_ROOT`**（§0）

### 3.2 Out of scope · defer

| 项 | 偿还 |
| -- | ---- |
| TDX live fetch | 用户另开授权任务 |
| QMT / xqshare / yahoo default / live FRED | DEFERRED |
| production clean write | sandbox rehearsal 另判 |
| full market scan / full history | 禁止 |
| PROMPT_20 data health CLI | 后续任务 |

### 3.3 禁止修改

- production migration / `data/duckdb/quant_monitor.duckdb` 直接写
- `layer2_sensors/`、`layer3_chains/` 等 modeling 包（非 pilot 必需）
- registry 大规模改写（除非协调者另批）
- 声称 production-live readiness

---

## 4. 代码地图

| 路径 | 操作 |
| ---- | ---- |
| `backend/app/ops/staged_pilot.py` | 修改 — v2 caps、evidence 文件名、closeout 字段 |
| `backend/app/ops/staged_pilot_fetch_ports.py` | 修改 — 窄 fetch 修复（若 RED 暴露） |
| `backend/app/ops/mutation_proof.py` | 修改 — R3Y-MUT-PROOF-001 proof_status 语义 |
| `tests/test_staged_pilot.py` | 修改 — v2 切片测试 + 对抗 mutation |
| `.trellis/tasks/06-24-round3-real-data-staged-pilot-v2/execute-evidence/pilot_v2_caps.json` 等 | 创建 — 九切片 evidence |

---

## 5. 测试契约

### 5.0 规范

1. 注释：`purpose` / `target` / `verifies` / `failure_meaning`（中文）
2. 只 mock 外部网络（单元）；vendor e2e 可选隔离
3. 每测至少一条业务语义断言
4. MUT-PROOF 对抗测使用 `tmp_path` DuckDB fixture

### 5.1 测试文件路径

| 路径 | 目标 | 测试目的 | §8 步 |
| ---- | ---- | -------- | ----- |
| `tests/test_staged_pilot.py` | `staged_pilot.py`, `mutation_proof.py` | v2 caps/fetch/evidence/closeout | 8.1–8.9 |
| `tests/test_production_live_pilot_policy.py` | policy gates | staged-only 不回退 | 8.10 |
| `tests/test_source_route_planner.py` | route planner | route 回归 | 8.10 |
| `tests/test_datasource_service.py` | datasource service | fetch 门面回归 | 8.10 |

### 5.2 成功/失败语义

| 能力 | 成功怎么测 | 失败怎么测 | 场景 |
| ---- | ---------- | ---------- | ---- |
| v2 caps | 合法 envelope → caps JSON 写出 | 超 symbol/row/network → 拒绝 | S1 |
| baostock 扩样 | manifest v2 含 hash/fetch_id | 超 cap → 无 fetch | S2 |
| mutation proof | hash+count 均不变 → VERIFIED | KEY 表变异 → MUTATION_DETECTED | S3 |
| akshare validation | taxonomy 记录 SUCCESS/ERROR | 当 primary → 拒绝 | S4 |
| closeout | 九切片字段 + rehearsal 判定 | 缺 evidence → 失败 | S5 |

### 5.3 用例设计

| 测试文件 | `test_*` 名称 | contract / AC | 断言语义 | §8 |
| -------- | ------------- | ------------- | -------- | -- |
| `test_staged_pilot.py` | `test_stagedPilotV2_capsJson_matchesApprovedEnvelope` | AC-SP2-01 | caps 字段与 envelope 一致 | 8.1 |
| 同上 | `test_stagedPilotV2_capsExceedingMaxSymbols_rejects` | AC-SP2-01 | 超 max_symbols 拒绝 | 8.1 |
| 同上 | `test_stagedPilotV2_baostockExpanded_writesManifestV2` | AC-SP2-02 | manifest v2 必需字段 | 8.2 |
| 同上 | `test_stagedPilotV2_cninfoExpanded_schemaFieldsPresent` | AC-SP2-03 | cninfo 必需 metadata 字段 | 8.3 |
| 同上 | `test_stagedPilotV2_akshareValidation_recordsTaxonomy` | AC-SP2-04 | taxonomy 含 status 枚举 | 8.4 |
| 同上 | `test_stagedPilotV2_routePreviewMatrixV2_allStatuses` | AC-SP2-05 | selected/skipped/disabled/validation-only | 8.5 |
| 同上 | `test_stagedPilotV2_validationReportV2_exposesQualityFlags` | AC-SP2-06 | quality_flags / row_count | 8.6 |
| 同上 | `test_stagedPilotV2_conflictSummaryV2_primaryOrDeferred` | AC-SP2-07 | conflict 或 deferred reason | 8.7 |
| 同上 | `test_mutationProof_verifiedOnlyWhenHashAndCountsUnchanged` | AC-MUT-001 | VERIFIED 收紧 | 8.8 |
| 同上 | `test_mutationProof_mutationDetectedWhenKeyTableRowsChange` | AC-MUT-001 | KEY 表变异 → MUTATION_DETECTED | 8.8 |
| 同上 | `test_mutationProof_mutationDetectedWhenNonKeyTableRowCountChanges` | AC-MUT-001 | 非 KEY 表行数变 → MUTATION_DETECTED | 8.8 |
| 同上 | `test_mutationProof_inconclusiveWhenHashChangesKeyCountUnchanged` | AC-MUT-001 | hash 变、KEY count 不变 → INCONCLUSIVE | 8.8 |
| 同上 | `test_stagedPilotV2_closeoutRequiresHashAndRowCountsUnchanged` | AC-MUT-001 / AUD-08 | closeout 须 `db_hash_unchanged`∧`row_counts_unchanged` | 8.9 |
| 同上 | `test_stagedPilotV2_closeoutMatrix_allSourcesClassified` | AC-SP2-09 | per-source expand/re-defer | 8.9 |

### 5.4 四层测试

| 层 | 范围 | 命令 | 通过 |
| -- | ---- | ---- | ---- |
| L1 单元 | staged pilot v2 | `uv run pytest tests/test_staged_pilot.py -q` | exit 0 |
| L2 集成 | route/datasource | `uv run pytest tests/test_source_capabilities.py tests/test_source_route_planner.py tests/test_datasource_service.py -q` | exit 0 |
| L3 管道 | storage/validation/policy | `uv run pytest tests/test_raw_store.py tests/test_db_validation_gate.py tests/test_ops_db_inspector.py tests/test_production_live_pilot_policy.py -q` | exit 0 |
| L4 E2E | 全量回归 | `uv run pytest -q` | exit 0；**仅 §8.10** |

---

## 6. 接口/契约

- **路由：** `source_route_contract.yaml`
- **质量：** `data_quality_rules.yaml`
- **冲突：** `source_conflict_rules.yaml`
- **写入：** `write_contract.yaml`（clean write forbidden）
- **资源：** `resource_limits.yaml` + §0 caps
- **政策：** `production_live_pilot_policy.md`、`staged_acceptance_policy.md`

### 6.1 `pilot_v2_closeout.json` 最小字段

| 字段 | 类型 | gate |
| ---- | ---- | ---- |
| `pilot_id` | string | 必填 |
| `production_live_readiness_claim` | `false` | 必填 |
| `mutation_proof_status` | `VERIFIED` \| `INCONCLUSIVE` \| `MUTATION_DETECTED` | 必填 |
| `db_hash_unchanged` | bool | **AUD-08**：closeout PASS 须 `true` |
| `row_counts_unchanged` | bool | **AUD-08**：closeout PASS 须 `true` |
| `per_source` | `{source_id: expand\|retry\|re-defer\|block}` | AC-SP2-09 |
| `sandbox_clean_write_rehearsal` | bool | 默认 `false` |

---

## 7. Red Flags

| 风险 | 预防 |
| ---- | ---- |
| 九切片合并为单 run | §8 独立 evidence；AUDIT A5 抽检 |
| proof_status 假安全 | R3Y-MUT-PROOF-001 + 对抗测 |
| sync `adapter=` 旁路 | §1.5 #6；AUD-08 |
| validation-only 当 primary | SP2-04 硬拒绝 |
| 超 cap 无声扩样 | validate_authorization fail-closed |
| production-live 声称 | closeout 强制 false |
| 过度工程 | §0.3a ponytail；复用 v1 路径 |

---

## 8. 实现步骤（RED/GREEN）

### 8.0 垂直切片顺序

| 序 | ID | 交付物（完标准） | 依赖 | AC |
| -- | -- | ---------------- | ---- | -- |
| 1 | R3Y-SP2-01 | `pilot_v2_caps.json` | gate | AC-SP2-01 |
| 2 | R3Y-SP2-02 | baostock manifest v2 + tests | SP2-01 | AC-SP2-02 |
| 3 | R3Y-SP2-03 | cninfo manifest + schema notes | SP2-01 | AC-SP2-03 |
| 4 | R3Y-SP2-04 | akshare taxonomy JSON | SP2-01 | AC-SP2-04 |
| 5 | R3Y-SP2-05 | `route_preview_matrix_v2.json` | SP2-01..04 | AC-SP2-05 |
| 6 | R3Y-SP2-06 | `validation_report_v2.json` | SP2-02..03 | AC-SP2-06 |
| 7 | R3Y-SP2-07 | `conflict_check_summary_v2.json` | SP2-06 | AC-SP2-07 |
| 8 | R3Y-SP2-08 | `no_mutation_proof_v2.md` + MUT-PROOF-001 | AUD-04 | AC-SP2-08, AC-MUT-001 |
| 9 | R3Y-SP2-09 | `pilot_v2_closeout.json` | SP2-01..08 | AC-SP2-09 |
| 10 | — | Tier A + 全库回归 | SP2-09 | §10 |

### 8.0 Boot gate

| 字段 | 内容 |
| ---- | ---- |
| 做什么 | 按 **§0.3** Read `implement.jsonl` 每一条 + `research/integration-ledger.md`；**§0.3a** ponytail；6.pre GitNexus；基线 pytest |
| RED 命令 | `uv run pytest tests/test_staged_pilot.py -q` |
| GREEN 命令 | `uv sync --locked` + `.trellis/tasks/06-24-round3-real-data-staged-pilot-v2/execute-evidence/8.0-boot-reads.txt` |
| RED 证据 | `.trellis/tasks/06-24-round3-real-data-staged-pilot-v2/execute-evidence/8.0-red.txt` |
| GREEN 证据 | `.trellis/tasks/06-24-round3-real-data-staged-pilot-v2/execute-evidence/8.0-green.txt` |
| 已执行 | [x] |

### 8.1 R3Y-SP2-01 — Pilot v2 plan/caps

| 字段 | 内容 |
| ---- | ---- |
| 做什么 | `PILOT_ID_V2`、caps JSON、`validate_authorization` v2 envelope |
| RED 命令 | `uv run pytest tests/test_staged_pilot.py::test_stagedPilotV2_capsExceedingMaxSymbols_rejects -q` |
| GREEN 命令 | `uv run pytest tests/test_staged_pilot.py::test_stagedPilotV2_capsJson_matchesApprovedEnvelope tests/test_staged_pilot.py::test_stagedPilotV2_capsExceedingMaxSymbols_rejects -q` |
| RED 证据 | `.trellis/tasks/06-24-round3-real-data-staged-pilot-v2/execute-evidence/8.1-red.txt` |
| GREEN 证据 | `.trellis/tasks/06-24-round3-real-data-staged-pilot-v2/execute-evidence/8.1-green.txt` + `.trellis/tasks/06-24-round3-real-data-staged-pilot-v2/execute-evidence/pilot_v2_caps.json` |
| 已执行 | [x] |

### 8.2 R3Y-SP2-02 — baostock expanded sample

| 字段 | 内容 |
| ---- | ---- |
| 做什么 | 3–5 symbols × ≤30 交易日；`raw_evidence_manifest_v2.json` / staging v2 |
| RED 命令 | `uv run pytest tests/test_staged_pilot.py::test_stagedPilotV2_baostockExpanded_writesManifestV2 -q` |
| GREEN 命令 | 同上 exit 0 |
| RED 证据 | `.trellis/tasks/06-24-round3-real-data-staged-pilot-v2/execute-evidence/8.2-red.txt` |
| GREEN 证据 | `.trellis/tasks/06-24-round3-real-data-staged-pilot-v2/execute-evidence/8.2-green.txt` + manifest v2 文件 |
| 已执行 | [x] |

### 8.3 R3Y-SP2-03 — cninfo metadata expanded

| 字段 | 内容 |
| ---- | ---- |
| 做什么 | cninfo 小样本；`cninfo_schema_notes_v2.md` |
| RED 命令 | `uv run pytest tests/test_staged_pilot.py::test_stagedPilotV2_cninfoExpanded_schemaFieldsPresent -q` |
| GREEN 命令 | 同上 exit 0 |
| RED 证据 | `.trellis/tasks/06-24-round3-real-data-staged-pilot-v2/execute-evidence/8.3-red.txt` |
| GREEN 证据 | `.trellis/tasks/06-24-round3-real-data-staged-pilot-v2/execute-evidence/8.3-green.txt` |
| 已执行 | [x] |

### 8.4 R3Y-SP2-04 — akshare validation retry/re-defer

| 字段 | 内容 |
| ---- | ---- |
| 做什么 | validation-only 重试；`akshare_validation_taxonomy_v2.json` |
| RED 命令 | `uv run pytest tests/test_staged_pilot.py::test_stagedPilotV2_akshareValidation_recordsTaxonomy -q` |
| GREEN 命令 | 同上 exit 0 |
| RED 证据 | `.trellis/tasks/06-24-round3-real-data-staged-pilot-v2/execute-evidence/8.4-red.txt` |
| GREEN 证据 | `.trellis/tasks/06-24-round3-real-data-staged-pilot-v2/execute-evidence/8.4-green.txt` + taxonomy JSON |
| 已执行 | [x] |

### 8.5 R3Y-SP2-05 — route preview matrix v2

| 字段 | 内容 |
| ---- | ---- |
| 做什么 | `route_preview_matrix_v2.json` 全 route status |
| RED 命令 | `uv run pytest tests/test_staged_pilot.py::test_stagedPilotV2_routePreviewMatrixV2_allStatuses -q` |
| GREEN 命令 | 同上 exit 0 |
| RED 证据 | `.trellis/tasks/06-24-round3-real-data-staged-pilot-v2/execute-evidence/8.5-red.txt` |
| GREEN 证据 | `.trellis/tasks/06-24-round3-real-data-staged-pilot-v2/execute-evidence/8.5-green.txt` + `route_preview_matrix_v2.json` |
| 已执行 | [x] |

### 8.6 R3Y-SP2-06 — validation report v2

| 字段 | 内容 |
| ---- | ---- |
| 做什么 | 对 staging evidence 生成 `validation_report_v2.json` |
| RED 命令 | `uv run pytest tests/test_staged_pilot.py::test_stagedPilotV2_validationReportV2_exposesQualityFlags -q` |
| GREEN 命令 | 同上 exit 0 |
| RED 证据 | `.trellis/tasks/06-24-round3-real-data-staged-pilot-v2/execute-evidence/8.6-red.txt` |
| GREEN 证据 | `.trellis/tasks/06-24-round3-real-data-staged-pilot-v2/execute-evidence/8.6-green.txt` + `validation_report_v2.json` |
| 已执行 | [x] |

### 8.7 R3Y-SP2-07 — conflict summary v2

| 字段 | 内容 |
| ---- | ---- |
| 做什么 | `conflict_check_summary_v2.json` |
| RED 命令 | `uv run pytest tests/test_staged_pilot.py::test_stagedPilotV2_conflictSummaryV2_primaryOrDeferred -q` |
| GREEN 命令 | 同上 exit 0 |
| RED 证据 | `.trellis/tasks/06-24-round3-real-data-staged-pilot-v2/execute-evidence/8.7-red.txt` |
| GREEN 证据 | `.trellis/tasks/06-24-round3-real-data-staged-pilot-v2/execute-evidence/8.7-green.txt` |
| 已执行 | [x] |

### 8.8 R3Y-SP2-08 — no-mutation proof v2 + R3Y-MUT-PROOF-001

| 字段 | 内容 |
| ---- | ---- |
| 做什么 | 收紧 `build_production_mutation_proof`；DB 存在/缺失；对抗 KEY 表变异；`no_mutation_proof_v2.md` |
| RED 命令 | `uv run pytest tests/test_staged_pilot.py::test_mutationProof_verifiedOnlyWhenHashAndCountsUnchanged tests/test_staged_pilot.py::test_mutationProof_mutationDetectedWhenKeyTableRowsChange -q` |
| GREEN 命令 | 同上 exit 0 |
| RED 证据 | `.trellis/tasks/06-24-round3-real-data-staged-pilot-v2/execute-evidence/8.8-red.txt` |
| GREEN 证据 | `.trellis/tasks/06-24-round3-real-data-staged-pilot-v2/execute-evidence/8.8-green.txt` + `no_mutation_proof_v2.md` |
| 已执行 | [x] |

### 8.9 R3Y-SP2-09 — close/re-defer matrix

| 字段 | 内容 |
| ---- | ---- |
| 做什么 | `pilot_v2_closeout.json`：per source expand/retry/re-defer/block + `sandbox_clean_write_rehearsal` |
| RED 命令 | `uv run pytest tests/test_staged_pilot.py::test_stagedPilotV2_closeoutMatrix_allSourcesClassified -q` |
| GREEN 命令 | 同上 exit 0 |
| RED 证据 | `.trellis/tasks/06-24-round3-real-data-staged-pilot-v2/execute-evidence/8.9-red.txt` |
| GREEN 证据 | `.trellis/tasks/06-24-round3-real-data-staged-pilot-v2/execute-evidence/8.9-green.txt` + `pilot_v2_closeout.json` |
| 已执行 | [x] |

### 8.10 Final gates

| 字段 | 内容 |
| ---- | ---- |
| 做什么 | §10 Tier A + **Tier B 全库 pytest（本任务唯一一次）** |
| GREEN 命令 | 见 §10 |
| RED 证据 | `.trellis/tasks/06-24-round3-real-data-staged-pilot-v2/execute-evidence/8.10-red.txt` |
| GREEN 证据 | `.trellis/tasks/06-24-round3-real-data-staged-pilot-v2/execute-evidence/8.10-green.txt` |
| 已执行 | [x] |

---

## 9. 四层测试（汇总）

见 §5.4。

---

## 10. Tier 验收

| Tier | 命令 | 通过 |
| ---- | ---- | ---- |
| A | `uv sync --locked` | exit 0 |
| A | `uv run pytest tests/test_staged_pilot.py -q` | exit 0 |
| A | `uv run pytest tests/test_source_capabilities.py tests/test_source_route_planner.py tests/test_datasource_service.py -q` | exit 0 |
| A | `uv run pytest tests/test_raw_store.py tests/test_db_validation_gate.py tests/test_ops_db_inspector.py tests/test_production_live_pilot_policy.py -q` | exit 0 |
| A | vendor e2e（若改动）`uv run pytest tests/test_vendor_fetch_e2e.py -q` | exit 0 |
| B | `uv run pytest -q` | exit 0；**仅 §8.10** |

**交接：** §8 证据齐 → Audit（非 finish-work）。§8.1–8.9 每步 GREEN 后仅跑当前步 RED 用例 + 既有全绿，**不**跑 Tier B。

---

## 11. Execute Skill 冻结

| Skill | 本任务 | 已执行 |
| ----- | ------ | ------ |
| trellis-execute | 必做 | [x] |
| test-driven-development | 必做 | [x] |
| incremental-implementation | 必做 | [x] |
| karpathy-guidelines | 必做（GREEN 前） | [x] |
| testing-guidelines | 必做 | [x] |
| ponytail（`.cursor/rules/ponytail.mdc`） | 必做 — Execute 全程 | [x] |
| gitnexus-impact | 必做 | [x] |
| trellis-check | **不用** → Audit A1 | — |

路径见 `execute-skill-paths.yaml`。

---

## 12. Audit 交接

- [x] §8 全部步骤已执行
- [x] `validate-execute-handoff` 通过
- [x] 无 production-live 声称
- [x] 九切片 evidence 可独立审查（路径 = `EVIDENCE_ROOT`）
- [x] 每步 GREEN 后已 Read `incremental-implementation`；未弱化测试目的（§0.3b）
- [x] 新增/修改测试含中文 **覆盖范围 / 测试对象 / 目的**
- [x] 代码修复后至少跑当前步 L1；§8.10 前完成 Tier B `uv run pytest -q`
