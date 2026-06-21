# MASTER 计划 — Round 3 Batch 2.75 Production Live Pilot Gate

> **Execute 入口**  
> Execute：本文件 + `implement.jsonl`（第二条 = `trellis-execute/SKILL.md`）。Audit 见 `AUDIT.plan.md`。  
> **Gate：** PH-B0–PH-B6 阶段审计 PASS + §10 全绿后，Batch 3 方可引用 pilot source-shape facts（仍非 production-live release）。

---

## 0. 元信息

| 字段                      | 值                                                                                  |
| ------------------------- | ----------------------------------------------------------------------------------- |
| 任务 slug                 | `06-21-round3-batch2-75-live-pilot`                                                 |
| 原计划来源                | `018B_production_live_pilot_gate.md`（`R3-B2.75-PROD-LIVE-PILOT`）                  |
| 批次索引                  | `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §3 Batch 2.75、§4.2                            |
| 前置 gate                 | Batch 2.5 `06-20-round3-batch2-5-layer1-obs-ingest` archived PASS · **staged-only** |
| manifest_protocol_version | `3`                                                                                 |
| analysis_waiver           | `false`                                                                             |
| 默认 pilot 类型           | **raw-only sandbox**（`allow_clean_write=false`）                                   |
| 授权证据                  | `docs/quality/batch275_user_authorization_2026-06-21.md`                            |

### 0.1 原计划任务

| 字段          | 值                                                                                                               |
| ------------- | ---------------------------------------------------------------------------------------------------------------- |
| Round / Batch | Round 3 Batch 2.75                                                                                               |
| 原始任务      | `018B_production_live_pilot_gate.md`                                                                             |
| Item IDs      | `R3-B2.75-PROD-LIVE-PILOT`, `R3-B2.75-01`, `GLOBAL-P2-01`, `B2.5-O-05`, `R3-B25-PERF-BUDGET-01`, `R3-B25-HYG-03` |
| 排除          | Batch 3 建模、Batch 6 CLI/backfill、Migration 008、R2b–R2d split、前端 bundle、`qmd data` 生产 CLI               |

### 0.2 门控速查

- 实现目录：`backend/app/ops/`（新建 `live_pilot`）、窄扩展 `datasources/service.py` 调用方、`tests/`、`execute-evidence/` — **不得**在 `docs/`/`specs/` 写运行时代码。
- **禁止**直接写 `data/duckdb/quant_monitor.duckdb`。
- **禁止** fixture/staged fallback（`build_staged_fixture_service` / `StubFetchPort` / `capture_task_phase3_evidence` / Batch 2.5 `ingestion.py` staged micro-fetch）。
- 三请求授权见 `batch275_user_authorization_2026-06-21.md`；总 row cap ≤100（建议 ≤40）。
- 与 ingestion R2b–R2d **同 sprint 禁止**（`layer1_ingestion_refactor_rollback_plan.md` §6）。
- **`dry_run` 语义：** Phase 2 始终 `dry_run=true`（route preview only）；Phase 3 每个 live fetch 在 route `READY` + HITL 确认后于 sandbox 内设置 `dry_run=false`。
- **Route 硬停止码（任一即停止并记录失败证据）：** `DISABLED_SOURCE`, `CAPABILITY_MISSING`, `USER_AUTH_REQUIRED`, `RESOURCE_GUARD_PAUSED`, `route_status != READY`。
- **Request 3：** akshare `macro_supplementary` / `DGS10` 仅探测 shape；**不**关闭 `ENV-E1-DGS10` 的 FRED primary（`B2.5-O-05`）。
- 依赖：`uv sync --locked`（`runtime_versions.md`）。

**Sandbox 路径表（canonical）：**

| 用途                   | 路径                                      | 环境变量                           |
| ---------------------- | ----------------------------------------- | ---------------------------------- |
| Live pilot 数据根      | `.audit-sandbox/batch275-live-pilot/`     | `QMD_DATA_ROOT`（仅 pilot 子进程） |
| Perf smoke 隔离        | `.audit-sandbox/batch275-perf-smoke/`     | 脚本 `--data-root`                 |
| Execute prod-path 副本 | `.audit-sandbox/batch275-prod-equiv/`     | `AUDIT_PROD_ROOT`（Audit/§10）     |
| Audit sandbox          | `.audit-sandbox/r3b275-audit/`            | AUDIT §0                           |
| Audit prod-equiv       | `.audit-sandbox/r3b275-audit-prod-equiv/` | AUDIT §0                           |

### 0.4 上下文打包（协议 v3）

Execute 以 MASTER inline + `research/integration-ledger.md` 为准；`implement.jsonl` 每条 `extract: … | for: …` 为 must-read 原稿指针。Plan 分析溯源（`research/*` 除 ledger）Execute **默认不读**。

### 0.5 Handoff 权威文件

`research/execute-handoff.md`（Execute 会话交接；冻结时为空模板）。

### 0.3 Execute 强制必读清单

Phase 0 Boot **必须 Read `implement.jsonl` 每一条** + `research/integration-ledger.md`（v3）；记录 `execute-evidence/8.0-boot-reads.txt`。

```text
进入 Execute。MUST Read .cursor/skills/trellis-execute/SKILL.md。
按 §0.3 读 implement 全表 → §8.0 Boot → §8.1 Phase -1 → §8.2 Phase 0 → … → §8.8 → §9/§10 → validate-execute-handoff → §11 Audit。勿 finish-work。
HITL：§8.5a 首次真实网络 fetch 前须用户确认并产出 phase3_hitl_user_confirmation.md。
```

### 0.7 GLOBAL 与政策摘要（inline · 第一层已总结）

| 来源                            | 归并要点                                              |
| ------------------------------- | ----------------------------------------------------- |
| GLOBAL_EXECUTION_RULES          | 无 drive-by；不绕过 WriteManager；真实 API 须用户确认 |
| GLOBAL_TESTING_POLICY           | 语义断言；RED→GREEN                                   |
| GLOBAL_RESOURCE_LIMITS          | eco 默认；禁止全市场/全历史                           |
| production_live_pilot_policy.md | fail-closed；sandbox；raw-only first                  |
| PENDING_USER_DECISIONS D-11     | QMT 默认禁用                                          |
| BATCH3_STAGED_DOWNSTREAM_GATE   | Batch 3 在 pilot closeout 前保持 staged-only 宣称     |

### 0.6 Source Context Index（第三层追溯 · README 三层模型）

| Source path                                                                                                           | Type          | Used by              | Summary in plan? | Must read original? | Reason                  |
| --------------------------------------------------------------------------------------------------------------------- | ------------- | -------------------- | ---------------- | ------------------- | ----------------------- |
| `018B_production_live_pilot_gate.md`                                                                                  | original-task | Plan trace           | 是 §2/§8         | 否                  | 归并完成                |
| `batch275_user_authorization_2026-06-21.md`                                                                           | authorization | for:AC-P0            | 是 §0            | **yes**             | 授权证据原文            |
| `production_live_pilot_policy.md`                                                                                     | rule          | for:AC-P0            | 是 §0.7          | pointer             | 默认已 inline           |
| `PENDING_USER_DECISIONS.md`                                                                                           | decision      | extract:D-11         | 是 §0.7          | pointer             | QMT 禁用                |
| `layer1_ingestion_refactor_rollback_plan.md`                                                                          | architecture  | extract:§6           | 是 §3.2          | pointer             | R2b 互斥                |
| `018B` §3.1 business scope                                                                                            | business      | for:AC-P3-5          | 是               | no                  | 三请求+FRED 边界        |
| `source_registry.yaml`                                                                                                | registry      | for:AC-P2            | 部分             | **yes**             | primary/validation      |
| `source_capabilities.yaml`                                                                                            | registry      | for:AC-P2,P3         | 部分             | **yes**             | operations              |
| `source_capability_contract.yaml`                                                                                     | contract      | for:AC-P2            | 否               | **yes**             | capability gate         |
| `platform_source_matrix.yaml`                                                                                         | contract      | for:AC-P2            | 否               | **yes**             | QMT 矩阵                |
| `source_route_contract.yaml`                                                                                          | contract      | for:AC-P2            | 否               | **yes**             | READY / no fallback     |
| `datasource_service_contract.yaml`                                                                                    | contract      | for:AC-P3            | 否               | **yes**             | fetch 门面              |
| `ops_db_inspect_contract.yaml`                                                                                        | contract      | for:AC-P1,P3         | 否               | **yes**             | inventory               |
| `data_quality_rules.yaml`                                                                                             | contract      | for:AC-P4            | 否               | **yes**             | validation              |
| `resource_limits.yaml`                                                                                                | contract      | for:AC-P45           | 是 §10           | **yes**             | eco                     |
| `datasource_service.md`                                                                                               | design        | for:AC-P3            | 部分             | **yes**             | fetch 序列              |
| `source_route_plan.md`                                                                                                | design        | for:AC-P2            | 部分             | **yes**             | dry-run                 |
| `db_inspect_cli.md`                                                                                                   | ops           | for:AC-P1            | 部分             | **yes**             | 只读 inspect            |
| `service.py`                                                                                                          | wiring        | for:AC-P2,P3         | 否               | **yes**             | preview/fetch           |
| `route_planner.py`                                                                                                    | wiring        | for:AC-P2            | 否               | **yes**             | SourceRoutePlan         |
| `db_inspector.py`                                                                                                     | wiring        | for:AC-P1            | 否               | **yes**             | baseline                |
| `resource_guard.py`                                                                                                   | wiring        | for:AC-P2,P3         | 否               | **yes**             | guard                   |
| `data_quality.py`                                                                                                     | wiring        | for:AC-P4            | 否               | **yes**             | validator               |
| `ingestion_evidence.py`                                                                                               | wiring        | filtered             | —                | **no**              | staged only             |
| `integration-ledger.md`                                                                                               | rule          | for:§0.3             | 是               | **yes**             | v3 map                  |
| Batch 2.5 execute-evidence                                                                                            | evidence      | for:AC-PRE           | 是               | pointer             | staged 对照             |
| `docs/AUDIT_DEFERRED_REGISTRY.md`                                                                                     | registry      | for:AC-REG-1         | 否               | **yes**             | defer 不得 silent close |
| `docs/UNRESOLVED_ISSUES_REGISTRY.md`                                                                                  | registry      | for:AC-PM\*,AC-REG-1 | 否               | **yes**             | Phase -1 必读           |
| `docs/RESOLVED_ISSUES_REGISTRY.md`                                                                                    | registry      | for:AC-P5-3          | 否               | **yes**             | closeout 对齐           |
| `docs/quality/ROUND3_BATCH25_PENDING_FIX_REGISTRY.md`                                                                 | registry      | for:AC-PRE           | 否               | **yes**             | 不得误标 live PASS      |
| `ROUND3_BATCH_IMPLEMENTATION_MAP.md`                                                                                  | map           | for:AC-PM\*          | 部分 §0.2        | **yes**             | §4.2 bundle             |
| `docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md`                                                                       | gate          | for:AC-P5-4          | 部分 §11         | **yes**             | handoff 字段            |
| `docs/modules/data_sources.md`                                                                                        | design        | for:AC-P2            | 否               | **yes**             | baostock/akshare        |
| `docs/modules/source_capability_registry.md`                                                                          | design        | for:AC-P1-3          | 否               | **yes**             | capability snapshot     |
| `docs/modules/data_validation_and_conflict.md`                                                                        | design        | for:AC-P4-5          | 否               | **yes**             | conflict 规则           |
| `docs/modules/write_manager.md`                                                                                       | design        | for:AC-P4            | 否               | **yes**             | sandbox write           |
| `specs/contracts/write_contract.yaml`                                                                                 | contract      | for:AC-P4-2          | 否               | **yes**             | clean write gate        |
| `docs/quality/staged_acceptance_policy.md`                                                                            | policy        | filtered             | —                | pointer             | 不得 staged 冒充 live   |
| `backend/app/validators/source_conflict.py`                                                                           | wiring        | for:AC-P4-5          | 否               | **yes**             | conflict inspect        |
| `specs/contracts/source_conflict_rules.yaml`                                                                          | contract      | for:AC-P4-5          | 否               | **yes**             | Phase 4                 |
| `docs/implementation_tasks/ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/016F_define_prod_equivalent_scale_benchmark.md` | business      | for:AC-P45           | 部分 §8.7        | **yes**             | perf schema             |
| `specs/layer1_axes/restructured_axes_v1_1/environment_axis/environment_axis_indicator_spec.yaml`                      | spec          | for:AC-P3-5          | 部分             | **yes**             | ENV-E1-DGS10            |
| `backend/app/layer1_axes/ingestion.py`                                                                                | wiring        | filtered             | —                | **no**              | **禁止** live 复用      |
| `backend/app/layer1_axes/ingestion_evidence.py`                                                                       | wiring        | filtered             | —                | **no**              | staged only             |

### 0.8 证据清单（Execute 产出）

| Phase | 路径                                                    | 说明                         |
| ----- | ------------------------------------------------------- | ---------------------------- |
| -1    | `execute-evidence/phase-1-registry-read.txt`            | 四 registry 读证             |
| 0     | `execute-evidence/phase0_authorization_record.md`       | 授权 + source risk rationale |
| 1     | `execute-evidence/phase1_capability_snapshot.json`      | AC-P1-3                      |
| 2     | `execute-evidence/phase2_route_preview_matrix.json`     | dry_run route                |
| 3     | `execute-evidence/phase3_hitl_user_confirmation.md`     | HITL（§8.5a）                |
| 3     | `execute-evidence/phase3_raw_micro_fetch_evidence.json` | 三请求 raw                   |
| 4     | `execute-evidence/phase4_validation_report.json`        | validation                   |
| 4     | `execute-evidence/phase4_conflict_inspect.txt`          | AC-P4-5                      |
| 5     | `execute-evidence/phase45_perf_budget.json`             | perf re-defer schema         |
| 5     | `execute-evidence/final_registry_update.md`             | §11 handoff                  |

### 0.9 边界与反模式

- 不得将 Batch 2.5 staged 证据当作 live pilot PASS。
- 不得在同一 sprint 启动 ingestion R2b–R2d。
- `fred` 非注册 `source_id` — 不得 bypass gate。
- cninfo 可选：本 pilot **defer**（不在三请求内）。

### 0.10 进度（Plan 冻结时）

| §8   | VS   | 状态 |
| ---- | ---- | ---- |
| 8.0  | —    | Plan |
| 8.1  | VS-1 | Plan |
| 8.2  | VS-1 | Plan |
| 8.3  | VS-2 | Plan |
| 8.4  | VS-3 | Plan |
| 8.5a | VS-4 | Plan |
| 8.5b | VS-5 | Plan |
| 8.6  | VS-6 | Plan |
| 8.7  | VS-7 | Plan |
| 8.8  | VS-8 | Plan |

### 0.11 开放项（Plan 冻结）

| ID   | 项             | 负责    | 关闭条件                             |
| ---- | -------------- | ------- | ------------------------------------ |
| O-01 | 用户 HITL 确认 | User    | `phase3_hitl_user_confirmation.md`   |
| O-02 | 网络可达性     | Env     | Phase 3 fetch 或 `PILOT_FAIL_SOURCE` |
| O-03 | Perf budget    | Execute | `phase45_perf_budget.json`           |

## 1. 目标

### 1.1 一句话

交付受控 Batch 2.75 live pilot：三请求 sandbox raw-only 微抓取 + route/baseline/validation 证据 + perf budget 或 re-defer + `PILOT_*` registry closeout，**不**打开正式 production data access。

### 1.2 非目标

见 018B §2；另：不得关闭 `B2.5-O-06`、`R3-B25-HYG-01/02`、Batch 6 release gates。

### 1.3 子交付物表

| Item ID                                      | MASTER AC          | 说明                |
| -------------------------------------------- | ------------------ | ------------------- |
| `R3-B2.75-PROD-LIVE-PILOT`                   | AC-P0..P5, AC-GATE | 试点本体            |
| `R3-B2.75-01` / `GLOBAL-P2-01` / `B2.5-O-05` | AC-P3,P5           | live vs staged FRED |
| `R3-B25-PERF-BUDGET-01` / `R3-B25-HYG-03`    | AC-P45             | smoke 证据          |
| Batch 3 handoff                              | AC-P5-4            | `019` 可引用范围    |

---

## 2. 预期结果（A5 trace-ac）

| ID       | 预期结果                                                | 验证链                                 |
| -------- | ------------------------------------------------------- | -------------------------------------- |
| AC-PRE   | Batch 2.5 staged + policy tests green                   | §8.0                                   |
| AC-PM1   | 五 tracked ID 映射 AC                                   | §8.1 `phase_minus1_reconciliation.md`  |
| AC-PM2   | 不 reopen R3-B25-DOC-01 等                              | §8.1                                   |
| AC-PM3   | not-in-scope 注释                                       | §8.1                                   |
| AC-PM4   | sprint 未混 R2b–R2d                                     | §8.1                                   |
| AC-P0-1  | 授权文件 + 三请求参数                                   | §8.2                                   |
| AC-P0-2  | source risk rationale（baostock/akshare 低于 QMT/FRED） | §8.2 `phase0_authorization_record.md`  |
| AC-P0-2b | fail-closed 测试绿（无 network）                        | §8.2 gate tests                        |
| AC-P0-3  | QMT/Yahoo/FRED 未默认启用                               | §8.2                                   |
| AC-P0-4  | 无授权则 pilot 不继续                                   | §8.2                                   |
| AC-P1-1  | baseline inventory json/md                              | §8.3                                   |
| AC-P1-2  | Phase 1 零 mutation                                     | §8.3                                   |
| AC-P1-3  | source registry/capability snapshot                     | §8.3 `phase1_capability_snapshot.json` |
| AC-P2-1  | 三请求 route preview                                    | §8.4                                   |
| AC-P2-2  | 非 READY 则停止+证据                                    | §8.4                                   |
| AC-P2-3  | 无 fixture fallback                                     | §8.4                                   |
| AC-P3-1  | sandbox raw + fetch_log + file_registry                 | §8.5                                   |
| AC-P3-2  | content hash + 请求参数                                 | §8.5                                   |
| AC-P3-3  | production DB 不变                                      | §8.5                                   |
| AC-P3-4  | Request 2 不升 Primary                                  | §8.5                                   |
| AC-P3-5  | Request 3 不关闭 FRED primary                           | §8.5                                   |
| AC-P4-1  | validation report on raw                                | §8.6                                   |
| AC-P4-2  | severe 阻断 clean write                                 | §8.6                                   |
| AC-P4-3  | 默认无 clean write                                      | §8.6                                   |
| AC-P4-4  | production DB 仍不变                                    | §8.6                                   |
| AC-P4-5  | conflict report 或 explicit no-conflict                 | §8.6 `phase4_conflict_inspect.txt`     |
| AC-P45-1 | smoke 证据或 re-defer 行                                | §8.7                                   |
| AC-P45-2 | bounded + ResourceGuard                                 | §8.7                                   |
| AC-P45-3 | 不作 live 授权依据                                      | §8.7                                   |
| AC-P5-1  | 单一 `PILOT_*` 状态                                     | §8.8                                   |
| AC-P5-2  | 默认 `PILOT_PASS_RAW_ONLY` 若三请求 raw 成功            | §8.8                                   |
| AC-P5-3  | registry 三文件一致                                     | §8.8                                   |
| AC-P5-4  | Batch 3 handoff note                                    | §8.8                                   |
| AC-REG-1 | 未闭合项 DEFERRED 有 owner                              | §8.8                                   |
| AC-REG-2 | 四 registry closeout checklist 一致                     | §8.8, §11                              |
| AC-GATE  | §9–§10 全绿                                             | §8.8                                   |

---

## 3. 范围与边界

### 3.1 允许创建/修改

- `backend/app/ops/live_pilot.py`（**新建**）
- `tests/test_batch275_live_pilot_gate.py`（**新建**）
- `execute-evidence/phase*.md|json|txt`
- 窄改：`service.py` 仅当需显式 live-pilot 钩子（须 impact 分析 + Audit 批准）

### 3.2 Out of scope

| 项                          | 批次                |
| --------------------------- | ------------------- |
| `019` Layer 2               | Batch 3             |
| Migration 008 / `B2.5-O-06` | Batch 6 / migration |
| ingestion R2b–R2d           | 后置 PR             |
| `qmd data` CLI              | Batch 6             |
| sandbox clean write（默认） | 需单独授权修订      |

### 3.3 禁止与反复用（Batch 2.5 staged）

| 路径/模式                                                 | 原因                                               |
| --------------------------------------------------------- | -------------------------------------------------- |
| `build_staged_fixture_service`                            | staged fixture 非 live 证据                        |
| `StubFetchPort` / `capture_task_phase3_evidence`          | 禁止 fixture fallback                              |
| `backend/app/layer1_axes/ingestion.py`                    | Batch 2.5 orchestration — **不得** live pilot 复用 |
| `backend/app/layer1_axes/ingestion_evidence.py`           | staged evidence 默认路径                           |
| 将 Batch 2.5 `execute-evidence/phase3_*` 升级为 live PASS | staged ≠ production-live                           |
| 写 production `quant_monitor.duckdb`                      | sandbox only                                       |
| 同 sprint ingestion R2b–R2d split                         | sprint 互斥                                        |

### 3.4 Pilot 链路（示意）

```text
LivePilotRequest + authorization_evidence
  → validate_authorization (fail-closed)
  → Phase 1: DbInspector baseline (production read-only)
  → Phase 2: DataSourceService.preview_route × 3
  → ResourceGuard.check
  → Phase 3: sandbox QMD_DATA_ROOT + DataSourceService.fetch (real adapter, raw_only)
  → raw_store + fetch_log + file_registry (sandbox only)
  → Phase 4: DataQualityValidator on raw (no clean write default)
  → Phase 4.5: production_equivalent_smoke (bounded) OR re-defer
  → Phase 5: PILOT_* + registry + handoff
```

---

## 4. 代码地图

| 路径                                        | 操作                     |
| ------------------------------------------- | ------------------------ |
| `backend/app/ops/live_pilot.py`             | **创建** — orchestration |
| `tests/test_batch275_live_pilot_gate.py`    | **创建**                 |
| `backend/app/datasources/service.py`        | **调用** — preview/fetch |
| `backend/app/ops/db_inspector.py`           | **调用** — inventory     |
| `backend/app/validators/data_quality.py`    | **调用** — Phase 4       |
| `backend/app/validators/source_conflict.py` | **调用** — AC-P4-5       |

---

## 5. 实现切片（§8 · to-issues VS-1..VS-8）

见 `research/vertical-slices.md`：

| §8   | Slice | Phase      | 1:1 |
| ---- | ----- | ---------- | --- |
| 8.0  | —     | Boot       | —   |
| 8.1  | VS-1  | -1         | ✓   |
| 8.2  | VS-1  | 0          | ✓   |
| 8.3  | VS-2  | 1          | ✓   |
| 8.4  | VS-3  | 2          | ✓   |
| 8.5a | VS-4  | 3 HITL     | ✓   |
| 8.5b | VS-5  | 3 fetch    | ✓   |
| 8.6  | VS-6  | 4          | ✓   |
| 8.7  | VS-7  | 4.5        | ✓   |
| 8.8  | VS-8  | 5 closeout | ✓   |

---

## 6. 接口草图（api-and-interface-design · Plan 4）

```python
@dataclass(frozen=True)
class LivePilotRequest:
    source_id: str
    data_domain: str
    operation: str
    symbols_or_indicators: tuple[str, ...]
    date_window: str
    max_rows: int
    dry_run: bool = True
    raw_only: bool = True
    write_target: str = "sandbox"
    allow_clean_write: bool = False
    authorization_evidence: str  # path to batch275_user_authorization_*.md

class LivePilotOutcome(str, Enum):
    PILOT_PASS_RAW_ONLY = "PILOT_PASS_RAW_ONLY"
    PILOT_PASS_SANDBOX_CLEAN = "PILOT_PASS_SANDBOX_CLEAN"
    PILOT_FAIL_SOURCE = "PILOT_FAIL_SOURCE"
    PILOT_FAIL_VALIDATION = "PILOT_FAIL_VALIDATION"
    PILOT_REDEFERRED = "PILOT_REDEFERRED"

def validate_authorization(request: LivePilotRequest) -> None: ...
def preview_live_pilot(request: LivePilotRequest, *, con) -> dict: ...
def run_live_pilot_raw_only(request: LivePilotRequest, *, sandbox_root: Path) -> dict: ...
```

---

## 7. Red flags

- 网络失败时用 fixture 顶上 → `PILOT_FAIL_SOURCE` + 证据，禁止 fallback
- Request 3 成功后被表述为「FRED live PASS」→ 违反 AC-P3-5
- production DB 行数变化 → 立即 FAIL + 停止
- 同 PR 改 `ingestion.py` 拆分 → 违反 sprint 约束

---

## 8. 实现步骤（RED/GREEN）

> 垂直切片顺序：`research/vertical-slices.md`（VS-1..VS-8 · Plan 3.5 to-issues）。

### 8.0 Boot gate

| 字段       | 内容                                                                                                                                                                                                          |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 做什么     | 按 **§0.3** 读 `implement.jsonl` 全表 + `research/integration-ledger.md`；`uv sync --locked`；policy gate 基线                                                                                                |
| RED 命令   | `uv run python -c "import sys; from pathlib import Path; p=Path('.trellis/tasks/06-21-round3-batch2-75-live-pilot/research/execute-boot.md'); sys.exit(0 if p.is_file() else 1)"`                             |
| GREEN 命令 | 创建 `research/execute-boot.md` + `uv sync --locked` + `uv run pytest tests/test_production_live_pilot_policy.py tests/test_batch25_production_data_gate.py tests/test_round3_audit_registry_alignment.py -q` |
| RED 证据   | `execute-evidence/8.0-red.txt`                                                                                                                                                                                |
| GREEN 证据 | `execute-evidence/8.0-boot-reads.txt`, `execute-evidence/8.0-baseline.txt`                                                                                                                                    |
| Skill      | trellis-execute Phase 0                                                                                                                                                                                       |

### 8.1 Phase -1 reconciliation

| 字段       | 内容                                                                                                                                                                                     |
| ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 做什么     | 读四 registry（`AUDIT_DEFERRED`/`UNRESOLVED`/`RESOLVED`/`ROUND3_BATCH25_PENDING_FIX`）+ `ROUND3_BATCH_IMPLEMENTATION_MAP`；产出 `phase_minus1_reconciliation.md`                         |
| RED 命令   | `uv run pytest tests/test_batch275_live_pilot_gate.py::test_livePilot_phaseMinus1_registryReconciliationRequired -q`                                                                     |
| GREEN 命令 | `uv run pytest tests/test_batch275_live_pilot_gate.py -k "phaseMinus1 or missingAuthorization or disabledSource or routeNotReady or sandbox or rawOnly or productionDb or noFixture" -q` |
| RED 证据   | `execute-evidence/8.1-red.txt`                                                                                                                                                           |
| GREEN 证据 | `execute-evidence/phase_minus1_reconciliation.md`, `execute-evidence/phase-1-registry-read.txt`                                                                                          |
| 通过条件   | AC-PM1..4                                                                                                                                                                                |
| Skill      | test-driven-development, testing-guidelines                                                                                                                                              |
| **Audit**  | **PH-B0 PASS 后才能 §8.2**                                                                                                                                                               |

### 8.2 Phase 0 authorization

| 字段       | 内容                                                                                                                                 |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| 做什么     | Wire 授权文件；`LivePilotRequest` + `validate_authorization`；**必须**记录 source risk rationale（baostock/akshare 低于 QMT/FRED）   |
| RED 命令   | `uv run pytest tests/test_batch275_live_pilot_gate.py::test_livePilot_missingAuthorization_blocksBeforeFetch -q`                     |
| GREEN 命令 | `uv run pytest tests/test_batch275_live_pilot_gate.py -k "missingAuthorization or disabledSource or authorization" -q`（无 network） |
| RED 证据   | `execute-evidence/8.2-red.txt`                                                                                                       |
| GREEN 证据 | `execute-evidence/phase0_authorization_record.md`                                                                                    |
| 通过条件   | AC-P0-1..4                                                                                                                           |
| Skill      | test-driven-development, karpathy-guidelines                                                                                         |
| **Audit**  | PH-B0                                                                                                                                |

### 8.3 Phase 1 baseline

| 字段       | 内容                                                                                                                                                  |
| ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| 做什么     | 只读 production baseline + capability snapshot；`phase1_baseline_inventory.json/.md` + `phase1_capability_snapshot.json`                              |
| RED 命令   | `uv run pytest tests/test_batch275_live_pilot_gate.py::test_livePilot_phase1Baseline_readOnly -q`                                                     |
| GREEN 命令 | 实现 baseline + 上项测试绿                                                                                                                            |
| RED 证据   | `execute-evidence/8.3-red.txt`                                                                                                                        |
| GREEN 证据 | `execute-evidence/phase1_baseline_inventory.json`, `execute-evidence/phase1_no_mutation_proof.md`, `execute-evidence/phase1_capability_snapshot.json` |
| 通过条件   | AC-P1-1..3                                                                                                                                            |
| Skill      | test-driven-development                                                                                                                               |
| **Audit**  | **PH-B1 PASS 后才能 §8.4**                                                                                                                            |

### 8.4 Phase 2 route matrix

| 字段       | 内容                                                                                                      |
| ---------- | --------------------------------------------------------------------------------------------------------- |
| 做什么     | 三请求 route preview + capability + ResourceGuard；无 fetch                                               |
| RED 命令   | `uv run pytest tests/test_batch275_live_pilot_gate.py::test_livePilot_phase2RouteMatrix_threeRequests -q` |
| GREEN 命令 | `uv run pytest tests/test_batch275_live_pilot_gate.py -k phase2 -q`                                       |
| RED 证据   | `execute-evidence/8.4-red.txt`                                                                            |
| GREEN 证据 | `execute-evidence/phase2_route_preview_matrix.json`                                                       |
| 通过条件   | AC-P2-1..3                                                                                                |
| Skill      | test-driven-development, api-and-interface-design                                                         |
| **Audit**  | **PH-B2 PASS 后才能 §8.5**                                                                                |

### 8.5a Phase 3 HITL gate

| 字段       | 内容                                                                                                                                                 |
| ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| 做什么     | **首次真实网络 fetch 前**用户确认；产出 `phase3_hitl_user_confirmation.md`（含三请求摘要 + 风险确认）                                                |
| RED 命令   | `uv run python -c "import sys; from pathlib import Path; sys.exit(0 if Path('execute-evidence/phase3_hitl_user_confirmation.md').is_file() else 1)"` |
| GREEN 命令 | 用户签署 HITL 文件存在                                                                                                                               |
| RED 证据   | `execute-evidence/8.5a-red.txt`                                                                                                                      |
| GREEN 证据 | `execute-evidence/phase3_hitl_user_confirmation.md`                                                                                                  |
| 通过条件   | O-01 关闭                                                                                                                                            |
| Skill      | doubt-driven-development                                                                                                                             |
| **Audit**  | PH-B3a（HITL 存在性）                                                                                                                                |

### 8.5b Phase 3 raw-only live fetch

| 字段       | 内容                                                                                                               |
| ---------- | ------------------------------------------------------------------------------------------------------------------ |
| 做什么     | HITL 后 sandbox `dry_run=false` raw-only 三请求；**禁止** staged fixture                                           |
| RED 命令   | `uv run pytest tests/test_batch275_live_pilot_gate.py -k phase3 -q`                                                |
| GREEN 命令 | 同上 + 产出 evidence JSON（`@pytest.mark.slow` + network 标记见 §9）                                               |
| RED 证据   | `execute-evidence/8.5b-red.txt`                                                                                    |
| GREEN 证据 | `execute-evidence/phase3_raw_micro_fetch_evidence.json`, `execute-evidence/phase3_no_production_mutation_proof.md` |
| 通过条件   | AC-P3-1..5                                                                                                         |
| Skill      | test-driven-development, security-and-hardening                                                                    |
| **Audit**  | **PH-B3 PASS 后才能 §8.6**                                                                                         |

### 8.6 Phase 4 validation

| 字段       | 内容                                                                                                                 |
| ---------- | -------------------------------------------------------------------------------------------------------------------- |
| 做什么     | validation + `source_conflict` inspect on raw；**默认无 clean write**；`PILOT_PASS_SANDBOX_CLEAN` 分支须单独授权修订 |
| RED 命令   | `uv run pytest tests/test_batch275_live_pilot_gate.py::test_livePilot_phase4Validation_noCleanWriteByDefault -q`     |
| GREEN 命令 | `uv run pytest tests/test_batch275_live_pilot_gate.py -k phase4 -q`                                                  |
| RED 证据   | `execute-evidence/8.6-red.txt`                                                                                       |
| GREEN 证据 | `execute-evidence/phase4_validation_report.json`, `execute-evidence/phase4_conflict_inspect.txt`                     |
| 通过条件   | AC-P4-1..5                                                                                                           |
| Skill      | test-driven-development                                                                                              |
| **Audit**  | **PH-B4 PASS 后才能 §8.7**                                                                                           |

### 8.7 Phase 4.5 perf budget

| 字段       | 内容                                                                                                                                                                                                                                              |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 做什么     | bounded smoke 或 registry re-defer；`phase45_perf_budget.json` **必须**含 `owner`, `phase`, `closure_test`, `status`（`PASS`/`RE_DEFERRED`）                                                                                                      |
| RED 命令   | `uv run python -c "import sys,json; from pathlib import Path; p=Path('execute-evidence/phase45_perf_budget.json'); sys.exit(0 if p.is_file() and all(k in json.loads(p.read_text()) for k in ('owner','phase','closure_test','status')) else 1)"` |
| GREEN 命令 | `uv run python scripts/production_equivalent_smoke.py --data-root .audit-sandbox/batch275-perf-smoke` **或** 写入 re-defer 行到 `AUDIT_DEFERRED_REGISTRY` + JSON                                                                                  |
| RED 证据   | `execute-evidence/8.7-red.txt`                                                                                                                                                                                                                    |
| GREEN 证据 | `execute-evidence/phase45_perf_budget.json`                                                                                                                                                                                                       |
| 通过条件   | AC-P45-1..3                                                                                                                                                                                                                                       |
| Skill      | testing-guidelines                                                                                                                                                                                                                                |
| **Audit**  | **PH-B5 PASS 后才能 §8.8**                                                                                                                                                                                                                        |

### 8.8 Phase 5 closeout

| 字段       | 内容                                                                                                                                                                                                                                                                                                                     |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 做什么     | `PILOT_*` + registry + Batch 3 handoff + §10 全量                                                                                                                                                                                                                                                                        |
| RED 命令   | `uv run pytest -q`（若有回归红则 fail）                                                                                                                                                                                                                                                                                  |
| GREEN 命令 | `uv run pytest tests/test_batch275_live_pilot_gate.py tests/test_production_live_pilot_policy.py tests/test_batch25_production_data_gate.py tests/test_round3_audit_registry_alignment.py tests/test_datasource_service.py tests/test_source_route_planner.py tests/test_ops_db_inspector.py -q` 然后 `uv run pytest -q` |
| RED 证据   | `execute-evidence/8.8-red.txt`                                                                                                                                                                                                                                                                                           |
| GREEN 证据 | `execute-evidence/final_pilot_closeout.md`, `execute-evidence/final_registry_update.md`, `execute-evidence/final_pytest_output.txt`                                                                                                                                                                                      |
| 通过条件   | AC-P5-\*, AC-REG-1, AC-GATE                                                                                                                                                                                                                                                                                              |
| Skill      | incremental-implementation, verification-before-completion                                                                                                                                                                                                                                                               |
| **Audit**  | **PH-B6** + A1–A8                                                                                                                                                                                                                                                                                                        |

---

## 9. 四层测试

| 层      | 范围                                                                  |
| ------- | --------------------------------------------------------------------- |
| L1 单元 | `test_batch275_live_pilot_gate.py` fail-closed                        |
| L2 集成 | route + sandbox fetch（`@pytest.mark.slow` + `@pytest.mark.network`） |
| L3 契约 | policy + batch25 gate + registry alignment                            |
| L4 E2E  | 三请求 evidence JSON 端到端                                           |

**Network 标记：** Phase 3 live fetch 测试须 `@pytest.mark.network`；CI 默认 skip，本地 Execute 显式 `-m network` 或 `--run-network`。

---

## 10. Tier 验收

| Tier      | 命令                                                                                                                                                                                          | Execute    |
| --------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| A quick   | `uv run pytest tests/test_batch275_live_pilot_gate.py tests/test_production_live_pilot_policy.py tests/test_batch25_production_data_gate.py tests/test_round3_audit_registry_alignment.py -q` | 必跑       |
| B service | `uv run pytest tests/test_datasource_service.py tests/test_source_route_planner.py tests/test_ops_db_inspector.py -q`                                                                         | 必跑       |
| C full    | `uv run pytest -q`                                                                                                                                                                            | 交接前必跑 |
| D lint    | `uv run ruff check .` + `uv run ruff format --check .`                                                                                                                                        | 必跑       |
| E compile | `uv run python -m compileall -q backend scripts tests`                                                                                                                                        | 必跑       |
| F gate    | `uv run python scripts/production_gate.py` + `uv run python scripts/check_doc_links.py`                                                                                                       | 必跑       |
| G cov     | `uv run pytest -q --cov=backend --cov-fail-under=85`                                                                                                                                          | 交接前     |

**prod-path：** 复制 `data/` → `.audit-sandbox/batch275-prod-equiv/`；验证 production DB hash 不变；在副本上跑 Tier B。

---

## 11. Audit 交接

- Audit **不得**将本 MASTER 视为 source completeness 的唯一权威。A1/A5/A8 必须对照 `AUDIT.plan.md` Trace Authority Set 中的原始任务卡、项目地图、轮次地图、implementation task index、unresolved coverage 与 registry 验证本 MASTER 是否完整继承。
- 产出 `research/gitnexus-execute-summary.md`（Execute 7.pre 前）
- `validate-execute-handoff` exit 0
- Batch 3 handoff 写入 `final_registry_update.md`（模板）：

```text
Layer 1 observation ingestion bridge: PASS|FAIL
Ingestion type: staged | user-authorized live | production live
Allowed downstream use: yes/no
Allowed indicator scope: <list e.g. ENV-E1-DGS10 shape only>
Allowed as_of window: <window>
Remaining data limitations: <list incl. B2.5-O-05 FRED primary deferred>
Pilot closeout state: PILOT_PASS_RAW_ONLY | PILOT_PASS_SANDBOX_CLEAN | PILOT_FAIL_* | PILOT_REDEFERRED
Reference: docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md until explicit production-live closeout
```

- AC-REG-2 closeout checklist：`UNRESOLVED`/`AUDIT_DEFERRED`/`RESOLVED`/`ROUND3_BATCH25_PENDING_FIX` 四文件一致；未闭合项须有 owner + phase

---

## 12. Execute Skill 冻结

| Skill                          | 本任务 | 绑定 §8      | 触发            |
| ------------------------------ | ------ | ------------ | --------------- |
| trellis-execute                | 必做   | Boot         | 每步            |
| test-driven-development        | 必做   | §8.1–8.6     | RED→GREEN       |
| testing-guidelines             | 必做   | 全程         | 每步            |
| karpathy-guidelines            | 必做   | 实现前       | 每步 GREEN 前   |
| incremental-implementation     | 必做   | §8.2–8.6     | 多文件          |
| api-and-interface-design       | 必做   | §8.4, §6     | route/fetch API |
| verification-before-completion | 必做   | §8.8         | closeout        |
| systematic-debugging           | 条件   | pytest RED   | RED 时          |
| security-and-hardening         | 条件   | §8.5b        | live network    |
| doubt-driven-development       | 条件   | §8.5a HITL   | 授权边界        |
| GitNexus impact                | 必做   | 改 symbol 前 | AGENTS.md       |
| GitNexus detect_changes        | 必做   | commit 前    | AGENTS.md       |
| trellis-check                  | 不用   | —            | Audit 替代      |
| trellis-before-dev             | 不用   | —            | Plan 5c 已完成  |

---

## 13. 原计划归并表

| 018B §        | MASTER            |
| ------------- | ----------------- |
| §0 ledger     | §1.3, §2          |
| §3.1 requests | §0.2, AC-P0, §8.5 |
| §4–11 phases  | §8.1–8.8          |
| §12 registry  | §8.8, AC-REG-1    |
| §13 verify    | §9–§10            |

Annex：`research/original-plan-trace.md`
