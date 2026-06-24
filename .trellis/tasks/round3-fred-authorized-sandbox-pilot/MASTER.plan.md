# MASTER 计划 — B01-FRED FRED Authorized Sandbox Pilot

> **Execute 入口** — sandbox/raw-only；**不得**声称 production-live readiness。  
> 索引：`research/source-index.md` · `context_pack.json` · Audit：`AUDIT.plan.md`

---

## 0. 元信息

| 字段                      | 值                                                                        |
| ------------------------- | ------------------------------------------------------------------------- |
| 任务 slug                 | `round3-fred-authorized-sandbox-pilot`                                    |
| Playbook / Manifest       | `B01-FRED` / `B01-C02`                                                    |
| 分支                      | `feature/round3-fred-authorized-sandbox-pilot`                            |
| Worktree                  | `../quant-monitor-desk-wt-b01-fred`                                       |
| 前置                      | B01-WL Layer1 P0 macro 白名单（合并优先；Plan 期只读引用）                |
| manifest_protocol_version | `3`                                                                       |
| `EVIDENCE_ROOT`           | `.trellis/tasks/round3-fred-authorized-sandbox-pilot/execute-evidence/`   |
| analysis_waiver           | `false`                                                                   |
| 原计划                    | `research/source-index.md` · `research/original-plan-trace.md`            |
| Agent 模型                | `composer-2.5`（playbook §2.3）                                           |

### Batch 01 / Staged limitations（强制）

1. `BATCH_01_HARDENING_RULES.md` §1–§10 — 更严规则优先
2. `production_live_pilot_policy.md` — staged/sandbox-first；`B2.5-O-05` 不因 Request 3 关闭
3. `staged_acceptance_policy.md` — 不得 staged 冒充 live
4. **Registry 三件套** — 本分支 **proposed delta only**；主会话批处理 commit
5. **`data_health.py` 主体** — **B01-DH2 独占**；本任务仅 pilot-local validator + 回归跑 `test_ops_data_health.py`

### Live 授权 YAML 模板（hardening §3 · Execute FRED-07 必填）

> coordinator 会话 **2026-06-24** 已口头授权 live 联网；Execute 须在 `execute-evidence/authorization.yaml` 落盘后方可 live fetch。

```yaml
authorization_present: true
authorized_by: coordinator
authorized_at: "2026-06-24T00:00:00Z"
source_id: fred
domain: macro_series
operation: fetch_macro_series
symbols_or_series:
  - DGS10
  - T10Y3M
  - VIXCLS
  - SP500
  - DFII10
window: "3y"
max_rows: 100
max_calls: 10
write_target: raw_or_staging_or_sandbox
allow_production_clean_write: false
api_key_env: FRED_API_KEY
skip_live_fetch_default: true
```

### 默认 FRED pilot caps

| 项 | 默认 |
| --- | --- |
| `pilot_id` | `r3e-fred-sandbox-20260625` |
| `max_series` | 5 |
| `max_rows_per_series` | 100 |
| `max_network_calls_per_run` | 10 |
| `sandbox_root` | `.audit-sandbox/r3e-fred-sandbox/` |
| `production_clean_write` | `false` |

### Failure modes / 回滚

| 场景 | 处理 |
| ---- | ---- |
| WL 未合并且 `specs/model_inputs/**` 缺失 | 使用 Layer1 axis specs 只读回退；**不得 STOP Plan**；merge 前对齐 WL SSOT |
| WL 合并后 P0 列表与 pilot 不一致 | 停止当前 §8 步；更新 caps/测试 |
| 无 `FRED_API_KEY` | `FRED_PILOT_FAIL_AUTH` 或 skip live；mocked 须仍绿 |
| production DB 变异 | 中止；`MUTATION_DETECTED`；不勾 GREEN |
| 改 `data_health.py` 主体 | **立即停止**（forbidden） |
| `macro_supplementary` 冒充 FRED 关闭 B2.5-O-05 | 中止；re-defer |

### 0.1 门控速查

| 项 | 值 |
| --- | --- |
| 怎么测 | §8 RED→GREEN；`test_fred_source_registry.py` + `test_fred_sandbox_pilot.py` + `test_fred_staged_semantics.py` |
| 怎么验收 | playbook §8.5 + §10 Tier A |
| 什么叫过 | §2 全部 AC-FRED-* + 无 production-live 声称 |
| prod-path | Tier B：`uv run pytest -q`（仅 §8.8） |
| 6.pre | `research/gitnexus-summary.md` |

### 0.3 Execute 强制必读

Phase 0 **逐条 Read `implement.jsonl`**；先读 `research/integration-ledger.md`。  
标记 **必须读原文** 的 `docs/implementation_tasks/**` 任务卡不得仅用摘要替代。

### 0.3a Ponytail

Boot 起 Read `.cursor/rules/ponytail.mdc`；复用 `staged_pilot` / fetch port 模式；禁止新依赖；`ponytail:` 标注天花板。

### 0.3b 测试纪律

五字段 docstring（playbook §2.2.1）；TDD RED→GREEN；每步 GREEN 后 `incremental-implementation`；**禁止弱化测试目的**。

### 0.4 上下文打包（v3）

Execute 以 MASTER + ledger + implement.jsonl 为准。

### Source Context Index（Playbook §3.1 + §3.4）

| 路径 | 遵守什么 | 摘要 | implement |
| ---- | -------- | ---- | --------- |
| `BATCH_01_MAIN_SESSION_COORDINATOR_PLAYBOOK.md` | §2.5–§2.7 · §4 · §8.5 | FRED 文件锁；`/to-issues`；§6.0 验收命令；Track A #3（**MASTER 无损摘要**，协调者提交后精读） | [x] |
| `BATCH_01_HARDENING_RULES.md` | §3–§7 | 授权/registry/证据 | [x] |
| `R3E_fred_authorized_sandbox_pilot.md` | 任务卡 AC | FRED-only sandbox | [x] |
| `PROMPT_04_debt_r3b275_fred_staged_semantics.md` | legacy L04 | macro ≠ FRED | [x] |
| `018B_production_live_pilot_gate.md` | legacy L05 | sandbox/live opt-in gate | [x] |
| `R3Y_readonly_data_health_v1.md` | legacy L03 只读 | 只读 health 模式 | [x] |
| `BATCH_01_ADVERSARIAL_AUDIT.md` | §6 | 禁止水平单 PR | [x] |
| `BATCH_01_MODEL_SOURCE_READINESS/README.md` | Batch 入口 | staged 边界 | [x] |
| `datasource_service_contract.yaml` | fetch 契约 | sanctioned path | [x] |
| `runtime_versions.md` | 版本门控 | Boot 对照 | [x] |
| `backend/app/ops/data_health.py` | **只读** | forbidden 主体对照 | [x] |
| `PROJECT_IMPLEMENTATION_ROADMAP.md` | Round 3E.1 | 路线图锚点 | [x] |
| `R3D_model_input_whitelist.md` | WL 前置 | P0 macro 列表 | [x] |
| `environment_axis_indicator_spec.yaml` 等 | Layer1 P0 | FRED series SSOT 回退 | [x] |
| `source_registry.yaml` / `source_capabilities.yaml` | fred 行独占写 | sandbox/disabled | [x] |
| `route_planner.py` / `capability_registry.py` | 路由 | dry-run preview | [x] |
| `staged_pilot.py` / `staged_pilot_fetch_ports.py` | pilot 邻接 | 可窄扩展 FRED port | [x] |
| `tests/test_fred_staged_semantics.py` | 既有语义测试 | B2.5-O-05 门禁 | [x] |

---

## 1. 目标

建立 FRED-only、用户授权、受资源限制的 raw/staging/sandbox 试跑路径；为 `B2.5-O-05` 提供 FRED-only 关闭或 re-defer 证据。

### 1.1 目的

证明 FRED 可安全试接为宏观主干**候选**，但不进入 production-live / clean write。

### 1.2 前置

| Gate | 说明 |
| ---- | ---- |
| **B01-WL** | Layer1 P0 macro 白名单；**合并前**只读 `specs/layer1_axes/**` + `R3D_model_input_whitelist.md` |
| **Live 授权** | coordinator 2026-06-24；Execute 落盘 `authorization.yaml` 后 FRED-07 |
| **Registry** | 主会话 merge 轨道 #3（WL 已合并） |

### 1.3 约束

- sandbox/raw-only；`fred` disabled-by-default
- caps：≤5 series · ≤100 rows/series · ≤10 calls
- **Must not：** clean write、`data_health.py` 主体、macro 替代 FRED

### 1.5 停止条件

| # | 事件 | 处理 |
| --- | --- | --- |
| 1 | Plan 未 freeze / 用户未批准 Execute | 禁止 `task.py start` |
| 2 | 触发 §3.3 forbidden（含 `data_health.py` 主体） | 立即停止；revert |
| 3 | production clean table 变异 | 中止；MUTATION_DETECTED |
| 4 | 未经批准的 caps / 全 catalog 扫描 | `RESOURCE_GUARD_PAUSED` |
| 5 | 声称 production-live FRED | 中止；修正 closeout |
| 6 | `B2.5-O-05` 无 FRED-only 证据却关闭 | 中止；re-defer |
| 7 | WL 合并后 P0 列表移除已实现的 series | 停当前 §8 步；回 Plan 对齐 |
| 8 | 直接 commit registry 三件套 | 禁止；仅 proposed delta |

### 1.6 原计划归并

| 来源 | 内容 |
| ---- | ---- |
| `R3E_fred_authorized_sandbox_pilot.md` | AC、切片、验收、Red Flags |
| `PROMPT_04` | B2.5-O-05 staged 语义 |
| `018B` | production-live gate |
| `BATCH_01_*` | manifest、hardening、playbook |
| 纠偏 | FRED-05 → pilot-local health（非 data_health 主体） |

---

## 2. 预期结果（AC）

| ID | 预期结果 | 验证链 | 切片 |
| --- | --- | --- | --- |
| AC-FRED-01 | `fred` registry/capability：sandbox/disabled-by-default；非 production-live | §8.1 | FRED-01 |
| AC-FRED-02 | P0 series route preview：sandbox/raw-only；拒绝未列 series | §8.2 | FRED-02 |
| AC-FRED-03 | Mocked fetch 产出含 series_id/date/value/fetch_id/hash/as_of 的 manifest | §8.3 | FRED-03 |
| AC-FRED-04 | auth/network/schema/validation 失败 → 显式 `FRED_PILOT_*` 状态 | §8.4 | FRED-04 |
| AC-FRED-05 | pilot-local health 检出 stale/missing/malformed/missing hash | §8.5 | FRED-05 |
| AC-FRED-06 | `B2.5-O-05` 关闭或 re-defer 有 FRED-only 证据与 closeout | §8.6 | FRED-06 |
| AC-FRED-07 | 授权 live（若执行）尊重 caps；仅 sandbox 写；no-mutation proof | §8.7 | FRED-07 |

---

## 3. 范围

### 3.1 In scope

- `specs/datasource_registry/source_registry.yaml` — **fred 行**（proposed）
- `specs/datasource_registry/source_capabilities.yaml` — **fred 行**
- `backend/app/ops/fred_sandbox_pilot.py`（新建）或窄扩展 `staged_pilot.py`
- `backend/app/ops/fred_fetch_ports.py` 或 `staged_pilot_fetch_ports.py` 增 FRED port
- `backend/app/ops/fred_evidence_validator.py`（新建，pilot-local health）
- `tests/test_fred_source_registry.py` · `test_fred_sandbox_pilot.py` · `test_fred_staged_semantics.py`
- `execute-evidence/*`

### 3.2 Out of scope · defer

| 项 | Owner |
| --- | --- |
| `data_health.py` / v2 profiles | **B01-DH2** |
| `specs/model_inputs/**` 编写 | **B01-WL** |
| baostock/cninfo/akshare registry 行 | **B01-SP3** |
| production clean write | 禁止 |
| full FRED catalog / full history | 禁止 |

### 3.3 禁止修改

- `backend/app/ops/data_health.py` **主体**
- production DB / migration
- `macro_supplementary` 升级为 FRED primary
- frontend · Layer1 计算运行时

### 3.4 Boundary 表（playbook §2.6）

| Owns | Must not own |
| ---- | ------------ |
| `fred` registry 行（proposed） | clean write |
| FRED pilot/fetch 代码与测试 | `data_health.py` 主体 |
| task evidence | macro 替代 FRED |
| `fred_evidence_validator.py` | registry 三件套直接 commit |

### 3.5 B01-WL 依赖与只读引用策略

| 阶段 | P0 series SSOT | 动作 |
| ---- | -------------- | ---- |
| Plan（当前） | Layer1 axis specs + `R3D_model_input_whitelist.md` | 冻结 `DGS10,T10Y3M,VIXCLS,SP500,DFII10` |
| Execute（WL 未合并） | 同上 + `tests/fixtures/` 若 WL 已提供 | 路由/测试引用 axis indicator_id |
| Execute（WL 已合并） | `specs/model_inputs/layer1*.yaml` | 切换 SSOT；对齐 WL-01 字段 |
| Merge gate | Track A #1 WL → #3 FRED | **WL 必须先于 FRED 合 master** |

---

## 4. 代码地图

| 路径 | 操作 |
| ---- | ---- |
| `specs/datasource_registry/source_registry.yaml` | 修改 fred 段（proposed） |
| `specs/datasource_registry/source_capabilities.yaml` | 修改 fred 段 |
| `backend/app/ops/fred_fetch_ports.py` | 创建或窄扩展 fetch ports |
| `backend/app/ops/fred_sandbox_pilot.py` | 创建 orchestration |
| `backend/app/ops/fred_evidence_validator.py` | 创建 pilot-local health |
| `backend/app/datasources/route_planner.py` | 窄改 route preview（若 RED 需要） |
| `tests/test_fred_source_registry.py` | 创建 |
| `tests/test_fred_sandbox_pilot.py` | 创建 |

---

## 5. 测试契约

### 5.0 规范

1. 五字段 docstring（覆盖范围/测试对象/目的/验证点/失败含义）
2. 业务安全断言：FRED 非 production-live；macro 不关闭 B2.5-O-05
3. `test_ops_data_health.py`：**回归 only**，不改 `data_health.py`

### 5.1 测试文件路径

| 路径 | 目标 | 测试目的 | §8 步 |
| ---- | ---- | -------- | ----- |
| `tests/test_fred_source_registry.py` | registry yaml | fred sandbox/disabled | 8.1 |
| `tests/test_fred_sandbox_pilot.py` | fred_sandbox_pilot, ports, validator | fetch/evidence/health/failures | 8.3–8.5, 8.7 |
| `tests/test_fred_staged_semantics.py` | policy/docs | B2.5-O-05 语义（既有+扩展） | 8.6 |
| `tests/test_source_route_planner.py` | route_planner | P0 route preview | 8.2, 8.8 |
| `tests/test_source_capabilities.py` | capabilities | fred cap 回归 | 8.8 |
| `tests/test_ops_data_health.py` | data_health | **回归绿、无修改** | 8.8 |

### 5.2 成功/失败语义

| 能力 | 成功怎么测 | 失败怎么测 | 场景 |
| ---- | ---------- | ---------- | ---- |
| Registry guard | fred 非 production-live | 默认 enabled production → 拒绝 | S1 |
| Route preview | 白名单 series → sandbox plan | 未列 series → 拒绝 | S2 |
| Mock fetch | manifest 含 hash/fetch_id | 缺字段 → FAIL_SCHEMA | S3 |
| Failures | 各失败 → 对应 status | 静默 PASS → 拒绝 | S4 |
| Evidence health | 坏行 → WARN/FAIL | 坏 evidence 通过 → 拒绝 | S5 |
| Closeout | FRED-only 证据才允许 close | macro 证据关闭 → 拒绝 | S6 |

### 5.3 用例设计

| 测试文件 | `test_*` 名称 | 断言语义 | 场景 | RED 命令 |
| -------- | ------------- | -------- | ---- | -------- |
| `test_fred_source_registry.py` | `test_fredRegistry_disabledByDefault_notProductionLive` | fred sandbox 角色 | S1 | `pytest tests/test_fred_source_registry.py::test_fredRegistry_disabledByDefault_notProductionLive -v` |
| 同上 | `test_fredRegistry_exceedsMaxSeries_rejected` | 超 5 series 拒绝 | S1 | 同上模块 |
| `test_fred_sandbox_pilot.py` | `test_fredRoutePreview_whitelistedSeries_sandboxOnly` | dry-run plan | S2 | `pytest tests/test_fred_sandbox_pilot.py::test_fredRoutePreview_whitelistedSeries_sandboxOnly -v` |
| 同上 | `test_fredMockFetch_writesManifestWithHashAndFetchId` | manifest 字段 | S3 | 同上 |
| 同上 | `test_fredPilot_missingAuth_returnsFailAuth` | FAIL_AUTH | S4 | 同上 |
| 同上 | `test_fredEvidenceHealth_staleObservation_warnsOrFails` | health 检出 | S5 | 同上 |
| `test_fred_staged_semantics.py` | `test_macroSupplementary_cannotCloseB250o05` | macro ≠ FRED close | S6 | `pytest tests/test_fred_staged_semantics.py -q` |

### 5.4 四层测试

| 层 | 环境 | 命令 | 通过 | 证据 |
| --- | --- | --- | --- | --- |
| 单元 | local/ci | `pytest tests/test_fred_source_registry.py tests/test_fred_sandbox_pilot.py tests/test_fred_staged_semantics.py -q` | exit 0 | 8.x-green |
| 集成 | local/ci | `pytest tests/test_source_route_planner.py -q` | exit 0 | 8.8 |
| 管道 | prod-path | `pytest -q` | exit 0 | 8.8-green |
| E2E live | opt-in | FRED-07 + `FRED_API_KEY` | cap 内 evidence | 8.7-green |

---

## 6. 验证

| Tier | 环境 | 命令 | 场景 | 通过条件 | 勾 |
| ---- | ---- | ---- | ---- | -------- | --- |
| A | local/ci | playbook §8.5 块（见下） | S1–S6 | exit 0 | [ ] |
| B | prod-path | `uv run pytest -q` | 全回归 | exit 0 | [ ] |

### 6.0 Tier A — playbook §8.5 B01-FRED（冻结）

```bash
uv sync --locked
uv run pytest tests/test_source_capabilities.py tests/test_source_route_planner.py -q
uv run pytest tests/test_fred_source_registry.py tests/test_fred_sandbox_pilot.py tests/test_fred_staged_semantics.py -q
# 下列仅跑既有绿测，不得为 FRED 改 data_health 主体：
uv run pytest tests/test_ops_data_health.py -q
uv run ruff check backend/app/datasources backend/app/ops tests/test_fred_*.py
uv run pytest -q && uv run ruff check . && uv run python -m compileall backend scripts tests
```

**6.1 交接：** §9 证据齐 · §5.1 已建 · `validate-execute-handoff` 0

---

## 7. Red Flags

| 风险 | 预防 |
| ---- | ---- |
| 水平单 PR 实现全部切片 | §8 垂直切片 + 独立 evidence |
| FRED 默认启用 | registry测试 + FAIL_AUTH |
| 改 data_health 主体 | §3.3 forbidden + §1.5 #2 |
| macro 关闭 B2.5-O-05 | FRED-06 closeout 测试 |
| registry 直接 commit | proposed delta only |

---

## 8. 实现顺序（垂直切片冻结）

| 序 | ID | 交付物（完标准） | 依赖 | AC |
| --- | --- | --- | --- | --- |
| 1 | FRED-01 | fred registry/capability proposed + 测试绿 | WL 只读 | AC-FRED-01 |
| 2 | FRED-02 | route preview JSON + 拒绝未列 series | FRED-01 | AC-FRED-02 |
| 3 | FRED-03 | mocked manifest + fetch port | FRED-02 | AC-FRED-03 |
| 4 | FRED-04 | failure taxonomy report | FRED-03 | AC-FRED-04 |
| 5 | FRED-05 | `fred_evidence_validator` + health JSON | FRED-03 | AC-FRED-05 |
| 6 | FRED-06 | closeout + B2.5-O-05 决策 | FRED-03..05 | AC-FRED-06 |
| 7 | FRED-07 | 可选 live evidence + authorization.yaml | FRED-03 + auth | AC-FRED-07 |

---

## 9. 实现步骤（RED/GREEN · Execute）

### 9.0 Boot

> **必读路由：** §0.3 Execute 强制必读 + `research/integration-ledger.md` + `implement.jsonl` 全读（含原文任务卡 **必须读原文** 条目）。

| RED 命令 | GREEN 命令 | 证据 | 绑定 Execute Skill | 已执行 |
| -------- | ---------- | ---- | ------------------ | ------ |
| `uv run pytest tests/test_fred_staged_semantics.py -q` | 同上 | `9.0-red.txt` / `9.0-green.txt` | trellis-execute · gitnexus-impact | [ ] |

### 9.1 FRED-01 — Registry guard

| 字段 | 内容 |
| ---- | ---- |
| 切片 | FRED-01 |
| RED 命令 | `uv run pytest tests/test_fred_source_registry.py -q` |
| GREEN 命令 | 同上 |
| 证据 | `9.1-red.txt` / `9.1-green.txt` · `proposed_registry_delta.yaml` |
| 绑定 Execute Skill | test-driven-development · karpathy-guidelines · testing-guidelines |
| 通过 | RED FAIL；GREEN 0 |
| 已执行 | [ ] |

### 9.2 FRED-02 — Route preview

| 字段 | 内容 |
| ---- | ---- |
| 切片 | FRED-02 |
| RED 命令 | `uv run pytest tests/test_fred_sandbox_pilot.py::test_fredRoutePreview_whitelistedSeries_sandboxOnly -v` |
| GREEN 命令 | 同上 |
| 证据 | `9.2-red.txt` / `9.2-green.txt` · `route_preview_fred.json` |
| 绑定 Execute Skill | test-driven-development · incremental-implementation |
| 已执行 | [ ] |

### 9.3 FRED-03 — Mocked fetch

| 字段 | 内容 |
| ---- | ---- |
| 切片 | FRED-03 |
| RED 命令 | `uv run pytest tests/test_fred_sandbox_pilot.py::test_fredMockFetch_writesManifestWithHashAndFetchId -v` |
| GREEN 命令 | 同上 |
| 证据 | `9.3-red.txt` / `9.3-green.txt` · `fred_raw_manifest.json` |
| 绑定 Execute Skill | test-driven-development · karpathy-guidelines |
| 已执行 | [ ] |

### 9.4 FRED-04 — Failure taxonomy

| 字段 | 内容 |
| ---- | ---- |
| 切片 | FRED-04 |
| RED 命令 | `uv run pytest tests/test_fred_sandbox_pilot.py -k "FailAuth or Network or Schema or Validation" -v` |
| GREEN 命令 | 同上 |
| 证据 | `9.4-red.txt` / `9.4-green.txt` · `fred_pilot_status_report.json` |
| 绑定 Execute Skill | test-driven-development |
| 已执行 | [ ] |

### 9.5 FRED-05 — Pilot-local evidence health

| 字段 | 内容 |
| ---- | ---- |
| 切片 | FRED-05 |
| RED 命令 | `uv run pytest tests/test_fred_sandbox_pilot.py -k "EvidenceHealth" -v` |
| GREEN 命令 | 同上 |
| 证据 | `9.5-red.txt` / `9.5-green.txt` · `fred_evidence_health.json` |
| 绑定 Execute Skill | test-driven-development · ponytail |
| 通过 | **未改** `data_health.py` |
| 已执行 | [ ] |

### 9.6 FRED-06 — Registry closeout

| 字段 | 内容 |
| ---- | ---- |
| 切片 | FRED-06 |
| RED 命令 | `uv run pytest tests/test_fred_staged_semantics.py tests/test_fred_sandbox_pilot.py -k "Closeout or macroSupplementary" -v` |
| GREEN 命令 | 同上 |
| 证据 | `9.6-red.txt` / `9.6-green.txt` · `fred_pilot_closeout.json` |
| 绑定 Execute Skill | test-driven-development |
| 已执行 | [ ] |

### 9.7 FRED-07 — Authorized live fetch（可选）

| 字段 | 内容 |
| ---- | ---- |
| 切片 | FRED-07 |
| RED 命令 | `uv run pytest tests/test_fred_sandbox_pilot.py -k "LiveFetch" -v`（或无 key 时 explicit skip） |
| GREEN 命令 | 同上 |
| 证据 | `9.7-red.txt` / `9.7-green.txt` · `authorization.yaml` · `fred_live_fetch_evidence.json` |
| 绑定 Execute Skill | test-driven-development |
| 前置 | `execute-evidence/authorization.yaml` 与 §0 模板一致 |
| 已执行 | [ ] |

### 9.8 Tier B 回归

| 字段 | 内容 |
| ---- | ---- |
| 切片 | merge-gate |
| RED 命令 | playbook §8.5 全块 |
| GREEN 命令 | `uv run pytest -q && uv run ruff check .` |
| 证据 | `9.8-red.txt` / `9.8-green.txt` |
| 绑定 Execute Skill | incremental-implementation |
| 已执行 | [ ] |

---

## 10. Execute 交接 DoD

- [ ] §9 证据齐 · §5.4+§6 · `validate-execute-handoff` 0 · 未 finish-work

---

## 11. Execute Skill 冻结

| Skill | 本任务 | 绑定 | 已读 | 已执行 |
| ----- | ------ | ---- | ---- | ------ |
| trellis-execute | 必做 | Boot | [ ] | [ ] |
| test-driven-development | 必做 | §9 RED | [ ] | [ ] |
| incremental-implementation | 必做 | §9.8 | [ ] | [ ] |
| karpathy-guidelines | 必做 | GREEN | [ ] | [ ] |
| testing-guidelines | 必做 | 写测 | [ ] | [ ] |
| gitnexus-impact | 必做 | 改 symbol | [ ] | [ ] |
| systematic-debugging | 条件 | DEBUG | [ ] | [ ] |
| trellis-check | **不用** | → Audit A1 | — | — |

路径见 `execute-skill-paths.yaml`。
