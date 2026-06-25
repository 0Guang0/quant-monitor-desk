# MASTER 计划 — B3F-SH Source Health & Quality Runners

> **Execute 入口** — Batch6 source health；**不得**声称 production-live readiness。  
> 索引：`research/source-index.md` · `context_pack.json` · Audit：`AUDIT.plan.md`  
> **必须读原文：** `R3F_verified_audit_ops_perf_hygiene.md`、`014_implement_data_sync_orchestrator.md`、Playbook §3.5

---

## 0. 元信息

| 字段 | 值 |
| ---- | --- |
| 任务 slug | `round3-source-health-and-quality-runners` |
| Playbook ID | B3F-SH · Round 3F.3 |
| 分支 | `feature/round3-source-health-and-quality-runners` |
| Worktree | `../quant-monitor-desk-wt-b3f-sh` |
| 模型 | `composer-2.5` |
| 前置 | DH2 `round3-readonly-data-health-v2` on master |
| manifest_protocol_version | `3` |
| analysis_waiver | `false` |
| 原计划 | `research/source-index.md` · `research/original-plan-trace.md` |

### Batch 3F 边界（Playbook §2.5 / §2.6）

| Owns（B3F-SH 可写） | Must not own |
| ------------------- | ------------ |
| `source_health_snapshot` 表语义 ADR、writer、非 DH2 persist 路径 | `backend/app/db/migrations/**` 新 SQL（**B3F-MIG**；SH-01 先 ADR/测试骨架） |
| `run_revision_audit` / `run_data_quality` orchestrator 实现 | DH2 只读 profile 建表 |
| source readiness rollup 持久化 | Eastmoney/AkShare false-close |
| FRED live primary 跟踪（**须授权 YAML**） | 无授权 live；TDX/QMT/xqshare/Yahoo |
| `tests/test_source_health_snapshot.py` 等本任务测试 | ResourceGuard / Layer1 perf（B3F-HYG） |
| `backend/app/ops/data_health.py` writer 扩展（非 DH2 建表路径） | registry 三件套直接 RESOLVED commit |

### Failure modes / 回滚

| 场景 | 处理 |
| ---- | ---- |
| 无 MIG 协调写入 migration SQL | 停止 SH-01 SQL；保留 ADR + isolated test |
| DH2 路径 CREATE snapshot | 中止；revert writer 接线 |
| 无授权 FRED live | 停止 SH-06；不勾 GREEN |
| 改 forbidden 文件组 | revert |

### 0.1 门控速查

| 项 | 值 |
| --- | --- |
| 怎么测 | §9 RED→GREEN；`test_source_health_snapshot.py` + `test_b3f_quality_runners.py` + DH2 回归 |
| 怎么验收 | §10 + Playbook §8.4 |
| 什么叫过 | AC-SH-01..07 全部 |
| prod-path | Tier B：`uv run pytest -q` |
| 6.pre | `research/gitnexus-execute-summary.md`（Execute 例外可读） |

### 0.3 Execute 强制必读

Phase 0 **逐条 Read `implement.jsonl`**；再 Read `research/integration-ledger.md`。

### 0.3a Ponytail

MUST Read `.cursor/rules/ponytail.mdc`；复用 DH2 `data_health.py`；writer 独立最小模块。

### 0.3b 测试纪律

五字段 docstring；RED 必须先 FAIL；禁止削弱 DH2 只读边界测试目的。

### Source Context Index（Playbook §3.1 + §3.5）

#### §3.1 共用底座

| 路径 | 摘要 | implement |
| ---- | ---- | --------- |
| `BATCH_3F_COORDINATOR_PLAYBOOK.md` | §2.5 锁、§8.4 PASS | [x] |
| `BATCH_3F_TASK_CARD_MANIFEST.md` | B3F-SH owns | [x] |
| `BATCH_3F_HARDENING_RULES.md` | live/validation 硬约束 | [x] |
| `BATCH_3F_PLAYBOOK_ADVERSARIAL_AUDIT.report.md` | B3F-PB-011 MIG/SH 串行 | [x] |
| `PROJECT_IMPLEMENTATION_ROADMAP.md` | R3F-SH-01..07 | [x] |
| GLOBAL×4 | 全局纪律 | [x] |
| `production_live_pilot_policy.md` | FRED live 门 | [x] |
| Registry 三件套 | **只读**；proposed delta only | [x] |

#### §3.5 B3F-SH 专用

| 路径 | 摘要 | implement |
| ---- | ---- | --------- |
| `R3F_verified_audit_ops_perf_hygiene.md` | VR-DATAHEALTH-001 | [x] |
| `014_implement_data_sync_orchestrator.md` | runner 矩阵 | [x] |
| `backend/app/ops/data_health.py` | DH2 基线 + writer 扩展点 | [x] |
| `backend/app/sync/orchestrator.py` | defer entrypoints | [x] |
| `docs/modules/data_sources.md` | snapshot 列 SSOT | [x] |
| `fred_live_authorization_2026-06-25.yaml` | **SH-06 授权** | [x] |
| `docs/quality/batch3f_fred_live_pilot_authorization_2026-06-25.md` | 用户授权 MD | [x] |
| `PROMPT_04_debt_r3b275_fred_staged_semantics.md` | B2.5-O-05 | [x] |
| `tests/test_ops_data_health.py` · `test_data_health_v2.py` | DH2 回归 | [x] |
| `tests/test_sync_orchestrator.py` | defer 基线 | [x] |

---

## 1. 目标

实现 Batch 3F.3：`source_health_snapshot` writer、quality runners、readiness rollup 持久化、FRED live primary（授权）、硬约束 no-false-close。

### 1.3 约束

- 无 production clean write；live 仅 SH-06 + 授权 YAML
- SH-01 migration SQL：**依赖 B3F-MIG 合并或主会话书面协调**

### 1.5 停止条件

| # | 事件 | 处理 |
| --- | ---- | ---- |
| 1 | Plan 未 freeze | 禁止 start |
| 2 | production DB mutation（非 isolated test） | 中止 |
| 3 | 无 MIG 协调提交 migration SQL | 停止 SH-01 SQL 部分 |
| 4 | RED 非本步全库红 | 停当前 §9 步 |
| 5 | 无 `fred_live_authorization_*.yaml` 却 live fetch | 停止 SH-06 |
| 6 | DH2 路径 CREATE `source_health_snapshot` | 中止；revert |
| 7 | AkShare/Eastmoney sidecar 关 REQ2-EM | 停止；修正 SH-07 |

### 1.6 原计划归并

| 来源 | 内容 |
| ---- | ---- |
| `PROJECT_IMPLEMENTATION_ROADMAP.md` R3F-SH-01..07 | 七切片 + gate |
| `R3F_verified_audit_ops_perf_hygiene.md` | VR-DATAHEALTH-001 |
| `014_implement_data_sync_orchestrator.md` | revision_audit / data_quality |
| `BATCH_3F_COORDINATOR_PLAYBOOK.md` §3.5 | 必读索引 |
| `research/vertical-slices.md` | Phase 3.5 /to-issues 冻结 |

---

## 2. 预期结果（AC）

| ID | 维度 | PASS 条件 | 验证链 |
| --- | ---- | --------- | ------ |
| AC-SH-PLAN | Plan | `validate-plan-freeze` exit 0 | freeze |
| AC-SH-01 | Snapshot | writer + isolated pytest；ADR 存在 | §9.1 |
| AC-SH-02 | Revision audit | `run_revision_audit` 非 defer | §9.2 |
| AC-SH-03 | Data quality | `run_data_quality` 非 defer | §9.3 |
| AC-SH-04 | Rollup persist | rollup → snapshot 行 | §9.4 |
| AC-SH-05 | DH2 boundary | DH2 不建表 | §9.5 |
| AC-SH-06 | FRED live | 授权 YAML + sandbox evidence | §9.6 |
| AC-SH-07 | No false close | AkShare/EM 不得 sidecar 关闭 | §9.7 |
| AC-SH-PLAYBOOK | Playbook | §8.4 命令绿 | §10 |

---

## 3. 需求与场景矩阵

| 场景# | Given | When | Then | AC | 测试 | Tier |
| ----- | ----- | ---- | ---- | -- | ---- | ---- |
| S1 | isolated test DB | writer insert snapshot | 行可读 | AC-SH-01 | snapshot pytest | B |
| S2 | orchestrator + job spec | `run_revision_audit` | SyncJobResult 非 defer | AC-SH-02 | quality runners | A |
| S3 | orchestrator + job spec | `run_data_quality` | SyncJobResult 非 defer | AC-SH-03 | quality runners | A |
| S4 | DH2 rollup bundle | persist API | snapshot 行含 rollup 字段 | AC-SH-04 | snapshot pytest | B |
| S5 | DH2 read-only path | health check | 无 CREATE TABLE | AC-SH-05 | ops_data_health | A |
| S6 | 授权 YAML 存在 | FRED live pilot | sandbox evidence；no prod write | AC-SH-06 | fred_live_closeout | B |
| S7 | OPEN registry rows | sidecar evidence | 不得 RESOLVED AkShare/EM | AC-SH-07 | hard_constraints | A |

**3.1 需求说明：** Batch6 source health 持久化 + runner 闭包；非 production-live 证明。  
**3.2 范围：** in §3.5 索引 · out MIG SQL、HYG perf、registry commit

### 3.3 禁止修改

- `backend/app/db/migrations/**`（无 MIG 协调）
- `backend/app/layer1_axes/**` ingestion split
- registry 三件套直接闭合
- DH2 profile 内 DDL

---

## 4. 代码地图

| 路径 | 操作 |
| ---- | ---- |
| `backend/app/ops/source_health_writer.py`（或同级） | 创建 — snapshot writer |
| `backend/app/ops/data_health.py` | 窄扩展 — persist 入口（非 DH2 DDL） |
| `backend/app/sync/orchestrator.py` | 实现 run_revision_audit / run_data_quality |
| `docs/decisions/ADR-024-source-health-snapshot-boundary.md` | 创建 — SH-01 ADR |
| `tests/test_source_health_snapshot.py` | 创建 |
| `tests/test_b3f_quality_runners.py` | 创建 |
| `tests/test_fred_live_primary_closeout.py` | 创建 |
| `tests/test_b3f_sh_hard_constraints.py` | 创建 |

---

## 5. 测试契约

### 5.0 规范

1. 五字段 docstring
2. 断言业务语义（defer、DDL、授权），非仅 import 成功

### 5.1 测试文件路径

| 路径 | 目标 | 测试目的 | §9 |
| ---- | ---- | -------- | -- |
| `tests/test_source_health_snapshot.py` | writer | snapshot insert/read | 9.1, 9.4 |
| `tests/test_b3f_quality_runners.py` | orchestrator | runner 非 defer | 9.2, 9.3 |
| `tests/test_ops_data_health.py` | data_health | DH2 不建表 | 9.5 |
| `tests/test_fred_live_primary_closeout.py` | live pilot | FRED 授权闭包 | 9.6 |
| `tests/test_b3f_sh_hard_constraints.py` | registry guard | no-false-close | 9.7 |

### 5.2 成功/失败语义

| 能力 | 成功怎么测 | 失败怎么测 | 场景 |
| ---- | ---------- | ---------- | ---- |
| Snapshot writer | isolated DB 有行 | 无 writer / insert 失败 | S1 |
| Revision audit | job 完成 | DeferredJobTypeError | S2 |
| Data quality | job 完成 | DeferredJobTypeError | S3 |
| Rollup persist | 字段匹配 | 无 persist | S4 |
| DH2 boundary | 无 DDL import | CREATE 出现在 DH2 路径 | S5 |
| FRED live | YAML + sandbox json | 无 YAML live 成功 | S6 |
| Hard constraint | OPEN 保持 | sidecar 关 EM/AkShare | S7 |

### 5.3 用例设计

| 测试文件 | test_* | 断言语义 | 场景 | RED 命令 |
| -------- | ------ | -------- | ---- | -------- |
| `test_source_health_snapshot.py` | `test_sourceHealthSnapshot_writer_insertsRow` | 行存在 | S1 | `pytest tests/test_source_health_snapshot.py::test_sourceHealthSnapshot_writer_insertsRow -v` |
| `test_b3f_quality_runners.py` | `test_b3fQualityRunners_revisionAudit_notDeferred` | 非 defer | S2 | `pytest tests/test_b3f_quality_runners.py::test_b3fQualityRunners_revisionAudit_notDeferred -v` |
| `test_b3f_quality_runners.py` | `test_b3fQualityRunners_dataQuality_notDeferred` | 非 defer | S3 | `pytest tests/test_b3f_quality_runners.py::test_b3fQualityRunners_dataQuality_notDeferred -v` |
| `test_source_health_snapshot.py` | `test_sourceHealthSnapshot_rollupPersist_fields` | rollup 字段 | S4 | `pytest tests/test_source_health_snapshot.py::test_sourceHealthSnapshot_rollupPersist_fields -v` |
| `test_ops_data_health.py` | `test_opsDataHealth_dh2Path_noSnapshotDdl` | 无 DDL | S5 | `pytest tests/test_ops_data_health.py::test_opsDataHealth_dh2Path_noSnapshotDdl -v` |
| `test_fred_live_primary_closeout.py` | `test_fredLivePrimary_requiresAuthorizationYaml` | 无 YAML 失败 | S6 | `pytest tests/test_fred_live_primary_closeout.py::test_fredLivePrimary_requiresAuthorizationYaml -v` |
| `test_b3f_sh_hard_constraints.py` | `test_b3fShHardConstraints_akshareNotClosedBySidecar` | OPEN 保持 | S7 | `pytest tests/test_b3f_sh_hard_constraints.py::test_b3fShHardConstraints_akshareNotClosedBySidecar -v` |

### 5.4 四层测试

| 层 | 命令 | 通过 |
| --- | ---- | ---- |
| 单元 | `uv run pytest tests/test_source_health_snapshot.py tests/test_b3f_quality_runners.py -q` | exit 0 |
| 集成 | `uv run pytest tests/test_ops_data_health.py tests/test_data_health_v2.py -q` | exit 0 |
| 管道 | `uv run pytest -q` | exit 0 |
| E2E | N/A — 无 frontend | SKIP |

---

## 6. 验证

| Tier | 命令 | 通过 |
| ---- | ---- | ---- |
| A | `uv run pytest tests/test_source_health_snapshot.py tests/test_b3f_quality_runners.py tests/test_ops_data_health.py -q` | exit 0 |
| B | `uv run pytest -q` | exit 0 |
| C | `uv run ruff check backend/app/ops backend/app/sync tests/test_source_health_snapshot.py tests/test_b3f_quality_runners.py` | exit 0 |

**6.1 交接门槛：** §9 证据齐 · §5.1 文件已建 · §1.5 未触发

---

## 7. Red Flags

| 风险 | 预防 |
| ---- | ---- |
| MIG/SH migration 冲突 | SH-01 标注；无协调不写 SQL |
| DH2 建表 | SH-05 grep + 停损 #6 |
| 无授权 live | YAML 双路径 §9.6 |
| 水平吞切片 | §8 七行独立 evidence |

---

## 8. 实现顺序（垂直切片 · Phase 3.5 /to-issues）

| 序 | ID | 交付物（完标准） | 依赖 | AC |
| --- | --- | --- | --- | --- |
| 1 | R3F-SH-01 | ADR + writer + isolated pytest；**migration SQL 等 B3F-MIG** | Boot | AC-SH-01 |
| 2 | R3F-SH-02 | `run_revision_audit` 实现 | SH-01 契约只读 | AC-SH-02 |
| 3 | R3F-SH-03 | `run_data_quality` 实现 | SH-02 模式 | AC-SH-03 |
| 4 | R3F-SH-04 | rollup → snapshot persist | SH-01 writer | AC-SH-04 |
| 5 | R3F-SH-05 | DH2 路径不建表测试 | DH2 基线 | AC-SH-05 |
| 6 | R3F-SH-06 | FRED live + `fred_live_authorization_2026-06-25.yaml` | SH-03 + 授权 | AC-SH-06 |
| 7 | R3F-SH-07 | no-false-close registry guard | SH-06 隔离 | AC-SH-07 |

---

## 9. 实现步骤（RED/GREEN）

### 9.0 Boot

| 字段 | 内容 |
| ---- | ---- |
| Boot | Phase 0 逐条 Read `implement.jsonl`（§0.3）；再 Read `research/integration-ledger.md` |
| RED 命令 | `uv run pytest tests/test_sync_orchestrator.py -q --tb=no` |
| GREEN 命令 | 同上（基线绿） |
| 绑定 Execute Skill | trellis-execute · test-driven-development · gitnexus-impact |
| 证据 | `execute-evidence/9.0-red.txt` / `9.0-green.txt` |
| 已执行 | [x] |

### 9.1 R3F-SH-01 — Snapshot ADR + writer

| 字段 | 内容 |
| ---- | ---- |
| 切片 | R3F-SH-01 |
| MIG 依赖 | **依赖 B3F-MIG 合并或主会话书面协调** — 可先 ADR + 测试骨架；`migrations/*.sql` 禁止本步提交 |
| RED 命令 | `uv run pytest tests/test_source_health_snapshot.py::test_sourceHealthSnapshot_writer_insertsRow -q` |
| GREEN 命令 | 同上 |
| 绑定 Execute Skill | test-driven-development · karpathy-guidelines · testing-guidelines |
| 证据 | `execute-evidence/9.1-red.txt` / `9.1-green.txt` |
| 已执行 | [x] |

### 9.2 R3F-SH-02 — Revision audit runner

| RED 命令 | `uv run pytest tests/test_b3f_quality_runners.py::test_b3fQualityRunners_revisionAudit_notDeferred -q` |
| GREEN 命令 | 同上 |
| 绑定 Execute Skill | test-driven-development · incremental-implementation |
| 证据 | `execute-evidence/9.2-red.txt` / `9.2-green.txt` |
| 已执行 | [x] |

### 9.3 R3F-SH-03 — Data quality runner

| RED 命令 | `uv run pytest tests/test_b3f_quality_runners.py::test_b3fQualityRunners_dataQuality_notDeferred -q` |
| GREEN 命令 | 同上 |
| 绑定 Execute Skill | test-driven-development · incremental-implementation |
| 已执行 | [x] |

### 9.4 R3F-SH-04 — Rollup persist

| RED 命令 | `uv run pytest tests/test_source_health_snapshot.py::test_sourceHealthSnapshot_rollupPersist_fields -q` |
| GREEN 命令 | 同上 |
| 绑定 Execute Skill | test-driven-development · incremental-implementation |
| 已执行 | [x] |

### 9.5 R3F-SH-05 — DH2 boundary

| RED 命令 | `uv run pytest tests/test_ops_data_health.py::test_opsDataHealth_dh2Path_noSnapshotDdl -q` |
| GREEN 命令 | 同上 |
| 绑定 Execute Skill | test-driven-development · incremental-implementation |
| 已执行 | [x] |

### 9.6 R3F-SH-06 — FRED live primary

| 字段 | 内容 |
| ---- | ---- |
| 授权引用 | `.trellis/tasks/round3-source-health-and-quality-runners/execute-evidence/fred_live_authorization_2026-06-25.yaml` + `docs/quality/batch3f_fred_live_pilot_authorization_2026-06-25.md` |
| RED 命令 | `uv run pytest tests/test_fred_live_primary_closeout.py::test_fredLivePrimary_requiresAuthorizationYaml -q` |
| GREEN 命令 | 同上 |
| 绑定 Execute Skill | test-driven-development · incremental-implementation |
| 证据 | `execute-evidence/fred_live_fetch_evidence.json`（live 时） |
| 已执行 | [x] |

### 9.7 R3F-SH-07 — Hard constraints

| RED 命令 | `uv run pytest tests/test_b3f_sh_hard_constraints.py::test_b3fShHardConstraints_akshareNotClosedBySidecar -q` |
| GREEN 命令 | 同上 |
| 绑定 Execute Skill | test-driven-development · incremental-implementation |
| 已执行 | [x] |

---

## 10. Execute 交接 DoD

- [x] §9 证据齐 · Boot 产物齐 · §5.4+§6 证据 · §11 Skill 必做 `[x]` · `validate-execute-handoff` 0 · 未 finish-work

---

## 11. Execute Skill 冻结

| Skill | 本任务 | 绑定 | 已读 | 已执行 |
| ----- | ------ | ---- | ---- | ------ |
| trellis-execute | 必做 | Boot | [x] | [x] |
| test-driven-development | 必做 | §9 RED | [x] | [x] |
| incremental-implementation | 必做 | §9 SLICE | [x] | [x] |
| karpathy-guidelines | 必做 | GREEN | [x] | [x] |
| testing-guidelines | 必做 | 写测 | [x] | [x] |
| gitnexus-impact | 必做 | 改 symbol | [x] | [x] |
| systematic-debugging | 条件 | DEBUG | [ ] | [ ] |
| trellis-implement | inline | Execute | [x] | [x] |
| trellis-check | **不用** | → Audit A1 | — | — |

路径见 `execute-skill-paths.yaml`。Audit → `AUDIT.plan.md`。
