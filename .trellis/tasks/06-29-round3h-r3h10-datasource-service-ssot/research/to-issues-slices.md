# R3H-10 `/to-issues` 垂直切片

> **Execute 入口：** `research/00-EXECUTION-ENTRY.md`（路由地图）  
> **活卡：** `R3H_10_DATASOURCE_SERVICE_SSOT.md`  
> **外部路径：** `research/EXTERNAL-INDEX.md`  
> **Module：** **C2**（主）· **E4**（收敛）  
> **评级：** `R3_STAGED_FIXTURE_CLOSED` → `R4_SANDBOX_REAL_DATA_OR_REHEARSAL`  
> **状态：** 切片已冻结 @ 2026-06-29 · Plan freeze 已通过（`validate-plan-freeze`）  
> **映射：** Trellis frozen §9.x = S10-BOOT→`9.0` … S10-05→`9.5` · S10-CLOSE→Audit（无 `9.6` 业务步）

---

## 0. 切片原则

| 原则          | 本任务                                                                                                  |
| ------------- | ------------------------------------------------------------------------------------------------------- |
| Tracer bullet | 每切片 = 一条可验证端到端行为，非「只改契约」或「只加测试」                                             |
| 模块完整      | **R3H-10 关账前**不开工 R3H-07；切片内不拆「registry 一行」微活                                         |
| 已有守卫复用  | Sync `guard_production_adapter_bypass` + `test_r3ySync001_*` 已存在 — BOOT 先登记，再 **扩展** 覆盖缺口 |
| 不在范围      | R3H-08 真网 live 产品化；新 migration；Round4 API                                                       |

---

## 1. 切片总表

| 序  | ID            | 标题                                 | 阻塞           | Execute Step | 评级贡献   |
| --- | ------------- | ------------------------------------ | -------------- | ------------ | ---------- |
| 0   | **S10-BOOT**  | 入口旁路基线矩阵                     | —              | `9.0`        | —          |
| 1   | **S10-01**    | Sync 生产路径仅 service fetch        | BOOT           | `9.1`        | C2         |
| 2   | **S10-02**    | `qmd data` 与契约 SSOT 对齐          | BOOT           | `9.2`        | C2, E1     |
| 3   | **S10-03**    | Rehearsal 与产品路径文档化硬边界     | S10-01         | `9.3`        | E4         |
| 4   | **S10-04**    | 旁路负向守卫扩面                     | S10-01, S10-02 | `9.4`        | C2         |
| 5   | **S10-05**    | staged/live 双轨收敛到 `fetch_ports` | S10-03         | `9.5`        | C2, E4     |
| 6   | **S10-CLOSE** | STAGED-PILOT-SSOT 关账 + 证据        | S10-04, S10-05 | Audit        | C2→R4 登记 |

```text
S10-BOOT
  ├→ S10-01 ─→ S10-03 ─→ S10-05 ─┐
  └→ S10-02 ─→ S10-04 ────────────┴→ S10-CLOSE
```

---

## 2. S10-BOOT — 入口旁路基线矩阵

### What to build

盘点所有「拉数 / route preview / sync 计划」入口，标注是否 **必经 `DataSourceService.fetch` 或 `preview_route`**，产出可执行基线文档供后续切片 RED 引用。

### 交付物

- `research/bypass-baseline-matrix.md`（本任务目录）
- `execute-evidence/9.0-green.txt`：矩阵完成 + 当前全量 `pytest -q` 绿快照

### 验收

- [ ] 矩阵含 **Sync / CLI / staged_pilot / live_pilot / interface_probe / Layer1 ingestion** 六类入口
- [ ] 每行：`入口` · `当前是否经 service` · `旁路风险` · `目标切片`
- [ ] 标明 **已闭合**（如 `test_r3ySync001_*`）与 **OPEN** 项

### 基线快照（BOOT 起点，Execute 时复核）

| 入口                                                           | 当前                                          | 风险        | 目标切片        |
| -------------------------------------------------------------- | --------------------------------------------- | ----------- | --------------- |
| `orchestrator.run_incremental/backfill/reconcile` + `adapter=` | 生产 profile **已 fail-closed**               | 低          | S10-01 复核     |
| 同上 + `datasource_service=`                                   | **金路径**                                    | —           | S10-01 保持     |
| `qmd data route-preview` / `sync-plan`                         | **经 `_service()`**                           | 低          | S10-02          |
| `run_staged_pilot_raw_only`                                    | service + **`create_staged_fetch_port`** 注入 | **双轨**    | S10-05          |
| `run_live_pilot_raw_only`                                      | service + **`create_live_fetch_port`** 注入   | **双轨**    | S10-03, S10-05  |
| `run_interface_probe`                                          | **`interface_probe_fetch_ports`** 直连        | **旁路**    | S10-04, S10-05  |
| `Layer1ObservationIngestionService`                            | 可注入 `build_staged_fixture_service`         | staged 合法 | S10-03 文档边界 |
| `datasource_service_contract.yaml`                             | `status: draft_round2_6`                      | 契约未升格  | S10-02          |

### Blocked by

无

---

## 3. S10-01 — Sync 生产路径仅 service fetch

### What to build

生产语义下，**Incremental / Backfill** 两条 runner 仅接受 `datasource_service` 提供的 fetch（或由其绑定的 `fetch_callable`），`adapter=` 仅在 pytest 测试钩下允许；与 `datasource_service_contract.yaml` 的 `forbidden_direct_callers` 一致。

**Reconcile（R3H-10 范围外）：** `run_reconcile` 仍 `adapter=` 形参；生产 profile 经 `guard_production_adapter_bypass` fail-closed（`test_r3ySync001_reconcile_*`）。`datasource_service=` 金路径 **defer** → Wave 2 / R3H-08 或专用 reconcile 切片（ADR-025 §Reconcile defer）。

### 端到端行为

操作员或脚本调用 `DataSyncOrchestrator.run_incremental(spec)`（非测试环境）时，若未传 `datasource_service=`，**必须 fail-closed**（明确报错），**禁止**自动构造默认 production `DataSourceService`。**ADR @ 2026-06-29 已裁决**；与 `test_r3ySync001_*` 及 EasyXT `auto_data_updater` 第二条入口反例一致（见 `research/reference-adoption-r3h10.md` §3.2）。

### 验收

- [ ] `test_r3ySync001_incremental/backfill/reconcile_rejectsAdapterBypassInProductionProfile` 仍绿
- [ ] 新增或扩展：无 `datasource_service` 且无 `adapter=` 时 **fail-closed**（与 ADR 一致）
- [ ] `runners.guard_production_adapter_bypass` / `guard_runner_direct_adapter_bypass` 无生产 env 逃逸口（除 `PYTEST_CURRENT_TEST`）
- [ ] `execute-evidence/9.1-red.txt` → `9.1-green.txt`

### 建议测试（TDD）

| 测试文件                          | 目的                                                       |
| --------------------------------- | ---------------------------------------------------------- |
| `tests/test_sync_orchestrator.py` | 扩展现有 R3Y 守卫或新增 production-profile 无 service 用例 |
| `tests/test_vendor_fetch_e2e.py`  | 保持 `datasource_service=` 金路径绿                        |

### Blocked by

S10-BOOT

---

## 4. S10-02 — `qmd data` 与契约 SSOT 对齐

### What to build

`qmd data route-preview` / `sync-plan` 继续只读经 `DataSourceService`；将 `datasource_service_contract.yaml` 从 `draft_round2_6` 升格为 **active**，`required_tests` 与本仓库测试名对齐；`sync-plan` 输出显式声明 **非 product live**（`dry_run` 默认 true 守牢）。

### 端到端行为

`qmd data route-preview --data-domain market_bar_1d` 返回的 `route_plan` 与 service `preview_route` 一致，且 **side_effects_allowed: false**；契约扫描测试可 FAIL 若契约 status 仍为 draft。

### 验收

- [ ] `tests/test_data_cli_contract.py` 绿
- [ ] `tests/test_datasource_service.py` 契约 gate（`contract_gate_support`）绿
- [ ] `datasource_service_contract.yaml` status → `active`（或项目等价 active 枚举）
- [ ] `execute-evidence/9.2-red.txt` → `9.2-green.txt`

### Blocked by

S10-BOOT

---

## 5. S10-03 — Rehearsal 与产品路径文档化硬边界

### What to build

在 `production_live_pilot_policy.md`、`datasource_service.md`（或活卡 §）写死：

- **产品 fetch SSOT** = `DataSourceService` → `datasources/fetch_ports/*` / 内部 `create_adapter`
- **Rehearsal-only** = `ops/live_pilot_*`、`ops/staged_pilot_*`、`scripts/run_staged_pilot.py`、`--live-wire` — **不得**作为 R3H-08 产品 live 替身

代码侧：为 rehearsal 模块增加 **单一** `REHEARSAL_ONLY` 常量或模块 docstring 契约测试（不删模块）。

### 端到端行为

审计员读文档即可区分「 rehearsal 证据」与「产品路径」；测试可断言 `run_staged_pilot` 入口模块带 rehearsal 标记且 **不在** `sync_orchestrator` 默认 import 链上。

### 验收

- [ ] 文档与 `R3H_10` 活卡 §2 一致
- [ ] `tests/test_production_live_pilot_policy.py` 或新测：rehearsal 脚本 **不**声称 product-live ready
- [ ] `execute-evidence/9.3-green.txt`（文档+测，通常无 RED 若仅文档；有测则 RED→GREEN）

### Blocked by

S10-01（Sync 金路径先稳）

---

## 6. S10-04 — 旁路负向守卫扩面

### What to build

在 Sync 守卫之外，为 **interface_probe**、**直接 `create_adapter` 的生产包扫描** 补齐 fail-closed 负向测试；复用 `tests/test_datasource_service.py` 的 `scan_package_for_create_adapter` 模式，确保 `forbidden_direct_callers` 列表与实际 import 一致。

### 端到端行为

若 `backend.app.ops.interface_probe` 在生产 profile 下未经 service 拉网，测试 **RED**；修复方式为 probe **委托** `DataSourceService.fetch`（可仍用 sandbox + cap），而非删除 probe。

### 验收

- [ ] 新增负向测：`interface_probe` 或等价路径不能成为 silent product bypass
- [ ] `scan_package_for_create_adapter` / `test_apiAndAgentCannotImportAdapterFactory` 绿
- [ ] `execute-evidence/9.4-red.txt` → `9.4-green.txt`

### Blocked by

S10-01, S10-02

---

## 7. S10-05 — staged/live 双轨收敛到 `fetch_ports`

### What to build

`ops/staged_pilot_fetch_ports` / `ops/live_pilot_fetch_ports` 中 **已 READY 的源**（如 baostock、cninfo）改为 **薄委托** `backend.app.datasources.fetch_ports.*`，或标记 deprecated 并统一经 service 内部 adapter 构造；rehearsal 仍可注入 port，但 **port 实现** 不得与产品 `fetch_ports` 行为分叉（同一 `FetchPort` 类或显式 re-export）。

闭合 `docs/quality/round3h_real_data_production_entry_audit.md` 行 **STAGED-PILOT-SSOT** → CLOSED（proposed delta，主会话 reconcile registry）。

### 端到端行为

`run_staged_pilot_raw_only(baostock, …)` 与 `DataSourceService.fetch`（产品 staged_fixture_mode=false）使用 **同一 fetch port 实现类**；`tests/test_staged_pilot.py` 绿且无「双实现」漂移。

### 验收

- [ ] `tests/test_staged_pilot.py` 绿
- [ ] `tests/test_batch275_live_pilot_gate.py` 仍绿（rehearsal 边界未破坏）
- [ ] audit 表 STAGED-PILOT-SSOT = CLOSED（证据路径记入 `execute-evidence/`）
- [ ] `execute-evidence/9.5-red.txt` → `9.5-green.txt`

### Blocked by

S10-03

### Out of scope

- 删除 `staged_pilot` / `live_pilot` 模块（仅收敛实现，不删 rehearsal 能力）
- R3H-08 真网写 clean

---

## 8. S10-CLOSE — 关账与下游解锁

### What to build

- Trellis Audit（complex 任务卡流程）PASS
- `MODULE_COMPLETION_RATING.md` **C2** 行证据可更新（R4 路径说明）
- `R3H_PASS_EXECUTION_PLAN.md` §3.1 Wave 1a → CLOSED
- **解锁 R3H-07** Plan/Execute

### 验收

- [ ] 全量 `uv run pytest -q` 绿
- [ ] `STAGED-PILOT-SSOT` 无 UNRESOLVED 矛盾
- [ ] Wave 1 INDEX §3 checklist 对应项 [x]

### Blocked by

S10-04, S10-05

---

## 9. GitHub issue（整卡 1 票 · 已裁决）

单票 **[R3H-10] DataSourceService SSOT — C2 R3→R4**；上表 S10-BOOT..CLOSE 为票内 Step。发布到 tracker 时复制 `WAVE1_R3H10_THEN_R3H07_TO_ISSUES_INDEX.md` §1 issue 骨架。

---

## 10. 建议 Execute 顺序（用户逐步）

```text
1. S10-BOOT（只读矩阵，可不改业务代码）
2. S10-01 TDD RED→GREEN
3. S10-02 TDD RED→GREEN（可与 01 同 PR 若文件锁不撞）
4. S10-03 文档+测
5. S10-04 TDD RED→GREEN
6. S10-05 TDD RED→GREEN（最大 diff — 单独 PR 更稳）
7. S10-CLOSE 全量 pytest + Audit
```

每步完成后：**全量 pytest** → 再下一切片。
