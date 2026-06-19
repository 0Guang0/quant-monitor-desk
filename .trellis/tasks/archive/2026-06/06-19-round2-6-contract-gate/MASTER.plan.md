# MASTER 计划 — Round2.6 Phase B Contract Gate

> **Execute 入口**  
> Execute：本文件 + `implement.jsonl`。Audit 见同目录 `AUDIT.plan.md`（Execute 不读）。  
> Gate：本任务 PASS 后才能启动 `06-19-round2-6-routing-service-gate`；两者 PASS 后才能启动 Round3 `017`。

---

## 0. 元信息

| 字段 | 值 |
|---|---|
| 任务 slug | `06-19-round2-6-contract-gate` |
| 原计划 Round | `docs/implementation_tasks/ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/` |
| 原计划任务卡 | `016A`–`016F`（见 `research/original-plan-trace.md`） |
| Audit 计划 | `.trellis/tasks/06-19-round2-6-contract-gate/AUDIT.plan.md` |
| 分析豁免 | `analysis_waiver: false`；Execute 仍必须做 GitNexus Phase 0 |
| Plan 冻结自检 | `plan.freeze.md` |

### 0.1 门控速查

- Execute 开始前必须读 `.cursor/skills/trellis-execute/SKILL.md`。
- Execute Phase 0 必须读 `implement.jsonl` 每条路径并产出 `research/execute-boot.md`。
- 本任务仅做 contract/tests/checks/doc reconciliation；不得实现生产 `DataSourceService` 或 route persistence。
- 每个 §8 步必须有 RED/GREEN 证据文件。
- Execute 交接 Audit 前必须跑 §9/§10 并执行 `validate-execute-handoff`。

---

## 1. 目标

### 1.1 一句话目标

把 Round2.6 Phase A 的设计契约转化为可执行 contract tests、静态边界检查和 deferred registry 对齐，确保 Phase C 实现不会漏读或偏离设计。

### 1.2 非目标

- 不实现 `backend/app/datasources/capability_registry.py` 的生产逻辑，除非测试需要最小 parser helper；生产实现留给 Task 2。
- 不实现 `DataSourceService` / `SourceRoutePlanner` 生产路径。
- 不改 sync runner fetch 架构。
- 不新增 schema migration。
- 不启用 QMT / qmt_xqshare / Yahoo。
- 不实现 FastAPI diagnostics 或前端 UI。
- 不删除根目录 `ROUND2_6_PHASE_A_SELF_CHECK.md`，除非内容已迁移且用户/Task 2 计划确认。

### 1.3 原计划归并

| 来源 | 进入本任务的内容 |
|---|---|
| `016A` | capability/source_registry domain alignment tests；adapter-domain mismatch test |
| `016B` | route/service contract tests；direct adapter factory boundary tests |
| `016C` | module-boundary checker and tests |
| `016D` | data CLI dry-run/route-preview/error-doc tests |
| `016E` | platform/qmt_xqshare disabled tests |
| `016F` | benchmark requirements handed off to Task 2 |
| `ROUND2_6_PHASE_A_SELF_CHECK.md` | domain mismatch finding and cleanup decision |
| `docs/AUDIT_DEFERRED_REGISTRY.md` | stale deferred rows reconciliation |

---

## 2. 预期结果（A5 trace-ac 追溯用）

| ID | 预期结果 | 验证链 |
|---|---|---|
| AC-B1 | `source_registry.yaml` 中每个 source allowed_domain 都在 `source_capabilities.yaml` 声明，测试覆盖缺失/未知 source。 | §8.1；`tests/test_source_capabilities.py`; §10 Tier A |
| AC-B2 | adapter `supported_domains` 旧命名不再被隐藏：测试明确要求统一到 registry domain 或存在显式 compatibility map。 | §8.2；`test_adapterSupportedDomains_reconciled...`; §10 Tier A |
| AC-B3 | RoutePlan contract tests 覆盖 disabled source、no available source、fallback quality flag、selected_source_id nullness。 | §8.3；`tests/test_source_route_planner.py`; §10 Tier A |
| AC-B4 | DataSourceService boundary tests 覆盖 fetch 前 route/capability/ResourceGuard 顺序，并约束生产代码 direct adapter factory usage。 | §8.4；`tests/test_datasource_service.py`; §10 Tier A |
| AC-B5 | `scripts/check_module_boundaries.py` 与 `tests/test_module_boundaries.py` 能发现契约禁止的 import。 | §8.5；§10 Tier A/B |
| AC-B6 | Data CLI/dependency contract tests 覆盖 dry-run/route-preview no-write、error_code/docs_anchor、默认依赖不含 QMT/xqshare。 | §8.6；§10 Tier A |
| AC-B7 | Platform matrix tests 证明 qmt_xtdata 非 Windows默认不可调度、qmt_xqshare 缺 env/授权不可调度且不 auto-probe。 | §8.7；§10 Tier A |
| AC-B8 | `docs/AUDIT_DEFERRED_REGISTRY.md` 已把当前实现已关闭项改为 RESOLVED，仍未实现项挂到 Task 1/Task 2/Round3/Round4 明确 hook。 | §8.8；docs diff；§10 Tier A |
| AC-B9 | Phase D benchmark/prod-equivalent requirements 明确传递给 Task 2，不在本任务实现。 | §8.9；Task 2 input references |
| AC-B10 | `ROUND2_6_PHASE_A_SELF_CHECK.md` 关键信息迁移到 Trellis research；是否删除留给 Task 2 cleanup gate。 | §8.10；research file exists |

---

## 3. 范围与边界

### 3.1 本任务允许修改

- `tests/test_source_capabilities.py`
- `tests/test_source_route_planner.py`
- `tests/test_datasource_service.py`
- `tests/test_module_boundaries.py`
- `tests/test_platform_source_matrix.py`
- `tests/test_data_cli_contract.py`
- `tests/test_dependency_extras_contract.py`
- `scripts/check_module_boundaries.py`
- `docs/AUDIT_DEFERRED_REGISTRY.md`
- Trellis research / evidence files under this task directory

### 3.2 本任务仅在必要时可读/轻改

- `docs/implementation_tasks/ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/*`：只在发现计划遗漏时补链接，不改方向。
- `specs/contracts/*`：只修明显 YAML/contract typo，不扩大 scope。

### 3.3 本任务禁止修改

- `backend/app/datasources/service.py`、`route_planner.py`、`capability_registry.py` 生产实现（Task 2）。
- `backend/app/sync/runners.py` 生产 refactor（Task 2）。
- `backend/app/db/migrations/**`。
- `frontend/src/**`。
- `pyproject.toml`、`frontend/package.json`、`frontend/package-lock.json`。
- `specs/datasource_registry/source_registry.yaml` 中启用 qmt/xqshare。

---

## 4. 代码地图

| 路径 | 操作 |
|---|---|
| `tests/test_source_capabilities.py` | 创建 |
| `tests/test_source_route_planner.py` | 创建 contract tests（可先使用 test-only dataclasses/helpers；生产实现 Task 2） |
| `tests/test_datasource_service.py` | 创建 boundary/contract tests |
| `tests/test_module_boundaries.py` | 创建 |
| `scripts/check_module_boundaries.py` | 创建静态 import checker |
| `tests/test_platform_source_matrix.py` | 创建 |
| `tests/test_data_cli_contract.py` | 创建 |
| `tests/test_dependency_extras_contract.py` | 创建 |
| `docs/AUDIT_DEFERRED_REGISTRY.md` | 修改，reconcile stale rows |
| `.trellis/tasks/06-19-round2-6-contract-gate/research/phase-a-self-check.md` | 创建，迁移 root self-check 关键内容 |

---

## 5. 模式与约束

- 测试必须断言业务语义：domain coverage、route_status、quality_flags、disabled_reason、no-write、import violation。
- 允许 mock 文件系统/HTTP/DB 外部 I/O；不 mock domain validation 逻辑。
- RED tests 必须先失败；GREEN 可通过最小检查实现，不得伪绿或删除断言。
- Any direct factory boundary scan must distinguish tests/test-only factories from production imports.
- Default install/dependency tests must read project manifests; do not modify dependency files in this task.

---

## 6. 接口/契约

本任务冻结以下契约为测试源：

- `specs/contracts/source_capability_contract.yaml`
- `specs/contracts/source_route_contract.yaml`
- `specs/contracts/datasource_service_contract.yaml`
- `specs/contracts/module_boundary_contract.yaml`
- `specs/contracts/platform_source_matrix.yaml`
- `specs/contracts/data_cli_contract.yaml`
- `specs/contracts/dependency_extras_contract.yaml`
- `specs/contracts/reference_adoption_guardrails.yaml`

---

## 7. Red Flags

| Red Flag | 预防 |
|---|---|
| 实现了完整 DataSourceService | §1.2/§3.3 禁止；Task 2 拥有 |
| qmt_xqshare 被加入 enabled source | AC-B7 只允许 disabled/authorization tests |
| Tests 只检查文件存在 | §5 要求业务断言 |
| Adapter domain mismatch 被 xfail 掩盖 | AC-B2 必须明确 fail 或形成 compatibility map test |
| 修改依赖或 schema migration | §3.3 禁止 |
| Deferred registry 未更新 | AC-B8 + §8.8 |
| `check_doc_links.py` allowlist blocked 后声称全绿 | 记录残余风险；可用 `pytest tests/test_documentation_index.py` 替代但不得冒充链接全检 |

---

## 8. 实现步骤（逐步 RED/GREEN + 证据）

### 8.1 Source capability domain coverage

| 字段 | 内容 |
|---|---|
| 做什么 | 创建 `tests/test_source_capabilities.py`，读取 `source_registry.yaml` 与 `source_capabilities.yaml`，断言每个 allowed_domain 有 capability 声明。 |
| 绑定 §12 Skill | test-driven-development, testing-guidelines |
| RED 命令 | `pytest tests/test_source_capabilities.py::test_everyAllowedDomain_hasCapabilityDeclaration -q` |
| RED 证据 | `research/execute-evidence/8.1-red.txt` |
| GREEN 命令 | `pytest tests/test_source_capabilities.py -q` |
| GREEN 证据 | `research/execute-evidence/8.1-green.txt` |
| 通过条件 | 测试至少断言缺失 domain 列表为空；包含 unknown/proposed source 处理。 |
| 环境 | local |
| 已执行 | [x] |

### 8.2 Adapter domain reconciliation contract

| 字段 | 内容 |
|---|---|
| 做什么 | 在 `tests/test_source_capabilities.py` 增加 adapter supported_domains reconciliation 测试；明确旧 domain 必须统一或被 compatibility map 覆盖。 |
| RED 命令 | `pytest tests/test_source_capabilities.py::test_adapterSupportedDomains_reconciledToCapabilityRegistryOrCompatibilityMap -q` |
| RED 证据 | `research/execute-evidence/8.2-red.txt` |
| GREEN 命令 | 同上 + `pytest tests/test_adapter_skeletons.py -q` |
| GREEN 证据 | `research/execute-evidence/8.2-green.txt` |
| 通过条件 | 不允许 silent mismatch；若使用 compatibility map，map 必须被测试且不启用新源。 |
| 环境 | local |
| 已执行 | [x] |

### 8.3 SourceRoutePlan contract tests

| 字段 | 内容 |
|---|---|
| 做什么 | 创建 `tests/test_source_route_planner.py`，先定义 contract expectations；可用 test-only minimal planner if production planner not yet in Task 1 scope。 |
| RED 命令 | `pytest tests/test_source_route_planner.py::test_qmtDisabled_routePlanShowsSkipReason -q` |
| RED 证据 | `research/execute-evidence/8.3-red.txt` |
| GREEN 命令 | `pytest tests/test_source_route_planner.py -q` |
| GREEN 证据 | `research/execute-evidence/8.3-green.txt` |
| 通过条件 | route_status/selected_source_id/candidates/quality_flags/disabled_reason 有业务断言。 |
| 环境 | local |
| 已执行 | [x] |

### 8.4 DataSourceService boundary tests

| 字段 | 内容 |
|---|---|
| 做什么 | 创建 `tests/test_datasource_service.py`，验证 contract boundary：production caller 不得直接用 adapter factory；fetch gate 顺序必须在 Task 2 实现。 |
| RED 命令 | `pytest tests/test_datasource_service.py::test_apiAndAgentCannotImportAdapterFactory -q` |
| RED 证据 | `research/execute-evidence/8.4-red.txt` |
| GREEN 命令 | `pytest tests/test_datasource_service.py -q` |
| GREEN 证据 | `research/execute-evidence/8.4-green.txt` |
| 通过条件 | 明确区分 test-only `create_test_adapter` 与 production import；不得要求 Task 1 实现 service。 |
| 环境 | local |
| 已执行 | [x] |

### 8.5 Module boundary checker

| 字段 | 内容 |
|---|---|
| 做什么 | 创建 `scripts/check_module_boundaries.py` 和 `tests/test_module_boundaries.py`，读取 `module_boundary_contract.yaml`，扫描 forbidden imports。 |
| RED 命令 | `pytest tests/test_module_boundaries.py::test_checkModuleBoundaries_detectsForbiddenImportFixture -q` |
| RED 证据 | `research/execute-evidence/8.5-red.txt` |
| GREEN 命令 | `pytest tests/test_module_boundaries.py -q && python scripts/check_module_boundaries.py` |
| GREEN 证据 | `research/execute-evidence/8.5-green.txt` |
| 通过条件 | 能检测临时 fixture 违规；真实代码扫描 exit 0 或列出需在 Task 2 修复的违规。 |
| 环境 | local |
| 已执行 | [x] |

### 8.6 Data CLI and dependency contracts

| 字段 | 内容 |
|---|---|
| 做什么 | 创建 `tests/test_data_cli_contract.py` 和 `tests/test_dependency_extras_contract.py`。本任务不实现完整 CLI；先验证 contract/docs/manifests。 |
| RED 命令 | `pytest tests/test_data_cli_contract.py::test_routePreviewContract_isReadOnly -q` |
| RED 证据 | `research/execute-evidence/8.6-red.txt` |
| GREEN 命令 | `pytest tests/test_data_cli_contract.py tests/test_dependency_extras_contract.py -q` |
| GREEN 证据 | `research/execute-evidence/8.6-green.txt` |
| 通过条件 | dry-run/route-preview/error_code/docs_anchor/default dependency exclusion 有断言；未实现 CLI 时必须在 registry 标明确切 Task hook。 |
| 环境 | local |
| 已执行 | [x] |

### 8.7 Platform source matrix tests

| 字段 | 内容 |
|---|---|
| 做什么 | 创建 `tests/test_platform_source_matrix.py`，验证 qmt_xtdata/qmt_xqshare disabled/default/env/user-confirmation 行为。 |
| RED 命令 | `pytest tests/test_platform_source_matrix.py::test_qmtXqshareMissingEnvNotSchedulable -q` |
| RED 证据 | `research/execute-evidence/8.7-red.txt` |
| GREEN 命令 | `pytest tests/test_platform_source_matrix.py -q` |
| GREEN 证据 | `research/execute-evidence/8.7-green.txt` |
| 通过条件 | 不联网、不探测端口、不启用 source；断言 route disabled reason 或 matrix status。 |
| 环境 | local |
| 已执行 | [x] |

### 8.8 Deferred registry reconciliation

| 字段 | 内容 |
|---|---|
| 做什么 | 更新 `docs/AUDIT_DEFERRED_REGISTRY.md`：已由当前代码/测试闭环的 rows 转 RESOLVED；仍未完成 rows 绑定 Task 1/Task 2/Round3/Round4 hooks。 |
| RED 命令 | `pytest tests/test_documentation_index.py -q` + manual grep for stale R3-PARTIAL rows |
| RED 证据 | `research/execute-evidence/8.8-red.txt` |
| GREEN 命令 | `pytest tests/test_documentation_index.py -q` |
| GREEN 证据 | `research/execute-evidence/8.8-green.txt` |
| 通过条件 | No OPEN blocks 017 except intentional Round2.6 Task 2 gate; stale implemented items not left as deferred. |
| 环境 | local |
| 已执行 | [x] |

### 8.9 Benchmark handoff to Task 2

| 字段 | 内容 |
|---|---|
| 做什么 | Ensure Task 2 plan references `016F`, `production_equivalent_smoke.py`, fixture-scale, ResourceGuard thresholds. |
| RED 命令 | `test -f .trellis/tasks/06-19-round2-6-routing-service-gate/MASTER.plan.md` or Windows equivalent manual check |
| RED 证据 | `research/execute-evidence/8.9-red.txt` |
| GREEN 命令 | manual/check JSONL references after Task 2 plan exists |
| GREEN 证据 | `research/execute-evidence/8.9-green.txt` |
| 通过条件 | Task 2 exists and includes Phase D benchmark scope. |
| 环境 | local |
| 已执行 | [x] |

### 8.10 Phase A self-check migration

| 字段 | 内容 |
|---|---|
| 做什么 | Copy key findings from root `ROUND2_6_PHASE_A_SELF_CHECK.md` into `research/phase-a-self-check.md`; decide root cleanup in Task 2 final cleanup. |
| RED 命令 | `test -f .trellis/tasks/06-19-round2-6-contract-gate/research/phase-a-self-check.md` (should fail before creation) |
| RED 证据 | `research/execute-evidence/8.10-red.txt` |
| GREEN 命令 | manual grep for `adapter-domain residual gap documented` in Trellis research |
| GREEN 证据 | `research/execute-evidence/8.10-green.txt` |
| 通过条件 | Trellis research contains domain mismatch finding and cleanup decision. |
| 环境 | local |
| 已执行 | [x] |

---

## 9. 测试层次（复杂任务四层全部必做）

| 层次 | 必做 | 环境 | 命令 | 通过条件 | 测试文件/路径 | Execute 证据 |
|---|---|---|---|---|---|---|
| 单元 | ✅ | local | `pytest tests/test_source_capabilities.py tests/test_platform_source_matrix.py tests/test_dependency_extras_contract.py -q` | exit 0；domain/matrix/dependency 业务断言通过 | tests | `research/execute-evidence/9-unit.txt` |
| 集成 | ✅ | local | `pytest tests/test_source_route_planner.py tests/test_datasource_service.py tests/test_module_boundaries.py tests/test_data_cli_contract.py -q` | exit 0；contract/boundary 断言通过 | tests + script | `research/execute-evidence/9-integration.txt` |
| 管道/集成链 | ✅ | prod-path | `python scripts/init_db.py --db .audit-sandbox/contract-gate/duckdb/quant_monitor.duckdb && pytest tests/test_source_registry.py tests/test_adapter_skeletons.py -q` | real config/schema path works; no production data pollution | scripts/tests | `research/execute-evidence/9-pipeline.txt` |
| E2E/smoke | ✅ | prod-path | `pytest tests/test_vendor_fetch_e2e.py tests/test_documentation_index.py -q` | fixture E2E remains green; docs index green | tests | `research/execute-evidence/9-e2e.txt` |

---

## 10. 验收 Tier 表（Execute 专用）

| Tier | 环境 | 命令 | 通过条件 | Execute 勾 |
|---|---|---|---|---|---|
| A | local | `pytest tests/test_source_capabilities.py tests/test_source_route_planner.py tests/test_datasource_service.py -q` | exit 0 | | [x] |
| A | local | `pytest tests/test_module_boundaries.py tests/test_platform_source_matrix.py tests/test_data_cli_contract.py tests/test_dependency_extras_contract.py -q` | exit 0 | | [x] |
| A | local | `python scripts/check_module_boundaries.py` | exit 0 or documented Task 2 fix items | | [x] |
| A | local | `pytest tests/test_documentation_index.py -q` | exit 0 | | [x] |
| A | local | `ruff check .` | exit 0 if available; if allowlist blocked, record exact blocker | | [x] |
| B | prod-path | `python scripts/init_db.py --db .audit-sandbox/contract-gate/duckdb/quant_monitor.duckdb` | creates/validates isolated DB; no repo pollution except `.audit-sandbox` | | [x] |
| C | prod-path | `pytest tests/test_vendor_fetch_e2e.py -q` | fixture vendor E2E still green | | [x] |
| C | docs | `python scripts/check_doc_links.py` | exit 0 if available; if allowlist blocked, record exact blocker and run docs index test | | [x] |

---

## 11. Execute 交接 DoD

- [x] §8 每步 RED/GREEN 证据齐全。
- [x] §9 四层证据齐全。
- [x] §10 Tier A/B/C 执行或阻塞记录齐全。
- [x] `docs/AUDIT_DEFERRED_REGISTRY.md` reconciliation 完成。
- [x] Task 2 plan exists and references Phase D benchmark handoff。
- [x] `task.py validate-execute-handoff` exit 0。
- [x] 未 finish-work，等待 Audit。

---

## 12. Execute Skill 冻结清单

| Skill | 本任务 | 绑定 §8 | 触发 | @ 指令 | 已执行 |
|---|---|---|---|---|---|
| test-driven-development | 必做 | 每个 §8 步 | RED/GREEN | 先写失败 tracer，再最小实现到绿。 | [x] |
| testing-guidelines | 必做 | 每个新增测试 | 写/改测试 | 每个测试至少一个业务语义断言。 | [x] |
| karpathy-guidelines | 必做 | GREEN 前 | 改代码/测试 | 最小清晰实现，不做抽象过度。 | [x] |
| incremental-implementation | 必做 | 每步 GREEN 后 | 每步 | 一步一验，不跨步批量改。 | [x] |
| systematic-debugging | 条件 | RED 非预期或 GREEN 失败 | 失败时 | 记录失败根因，不伪绿。 | [ ] |
| source-driven | 条件 | YAML/spec parser tests | 读取 contracts | 以 specs/contracts 为源，不凭记忆。 | [x] |
| GitNexus impact/context | 必做 | Phase 0 + 改 symbol 前 | 改任何代码 symbol 前 | 先查影响，再改。 | [x] |
