# Plan Document Gap Report — Batch D (Agent 1)

> 2026-06-18 · `06-18-round2-batch-d-orchestrator`  
> 方法：MASTER §1–3、DECISIONS、014 任务卡 §3/§5、P0o 必读表、`implement.jsonl` / `check.jsonl` / `original-plan-trace.md` 交叉核对；GitNexus `query`、CodeGraph 索引、`grep tombstone_missing`。

---

## 摘要

Plan 阶段已产出可冻结的 MASTER/AUDIT，但 **implement.jsonl 与 Batch C 同级任务相比偏薄**，遗漏了编排层必须接线的 Batch C 交付物、任务卡 §5 架构引用、以及 DECISIONS 漂移项（`sync_to_db` 已实现 `tombstone_missing`）。本次已 **追加 19 条 implement.jsonl、7 条 check.jsonl**，修订 MASTER §1.3/§3.2/§6.4/§8.0/§8.8、AUDIT §2 A1、`original-plan-trace.md`。

`validate-plan-freeze`：**exit 0**（修订前后均通过；修订为 Execute 防漂移补强，非门禁失败修复）。

---

## 缺口清单

| # | 路径 | 为何 Batch D Execute 需要 | 已补到哪里 |
|---|------|---------------------------|------------|
| G1 | `docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/README.md` | P0o 强制 Round README；批次顺序与 D 前置 | `implement.jsonl` |
| G2 | `docs/architecture/04_data_architecture.md` | 任务卡 §5；clean/staging 分层边界（AC-8） | `implement.jsonl`, `check.jsonl`, `original-plan-trace` |
| G3 | `docs/quality/final_package_rules.md` | 任务卡 §5 最终包规则 | `implement.jsonl`, `original-plan-trace` |
| G4 | `docs/modules/data_validation_and_conflict.md` | Batch C 模块规格；编排 VALIDATING 阶段 | `implement.jsonl`, `check.jsonl` |
| G5 | `docs/modules/data_sources.md` | `fetch_log` / registry 权威（C-C2） | `implement.jsonl`, `check.jsonl` |
| G6 | `docs/modules/write_manager.md` | job_id ↔ write_audit；禁止直写 clean | `implement.jsonl` |
| G7 | `specs/contracts/data_adapter_contract.md` | FETCHING 阶段 FetchRequest/Result | `implement.jsonl`, `check.jsonl` |
| G8 | `specs/contracts/data_quality_rules.yaml` | VALIDATING 规则（AC-6） | `implement.jsonl`, `check.jsonl` |
| G9 | `specs/contracts/source_conflict_rules.yaml` | Reconcile / severe conflict（§8.7） | `implement.jsonl`, `check.jsonl` |
| G10 | `scripts/ci_ingestion_smoke.py` | GPT-P3-6 扩展基线（AC-9） | `implement.jsonl` |
| G11 | `backend/app/datasources/source_registry.py` | `sync_to_db(tombstone_missing=True)` 已存在 | `implement.jsonl` |
| G12 | `backend/app/datasources/adapters/__init__.py` | `create_adapter` 工厂 | `implement.jsonl` |
| G13 | `backend/app/db/validation_gate.py` | DbValidationGate 接线 | `implement.jsonl` |
| G14 | `backend/app/db/write_manager.py` | 唯一 clean 写路径 | `implement.jsonl` |
| G15 | `backend/app/validators/data_quality.py` | VALIDATING 阶段 | `implement.jsonl` |
| G16 | `backend/app/validators/source_conflict.py` | Reconcile 委托（§4） | `implement.jsonl` |
| G17 | `backend/app/core/resource_guard.py` | FETCHING 前门禁（AC-5） | `implement.jsonl` |
| G18 | `tests/test_batch_c_validation_flow.py` | E2E 编排测试模板（§8.5） | `implement.jsonl` |
| G19 | `.trellis/tasks/06-17-round2-batch-c-validation-conflict/finish.md` | `READY_FOR_BATCH_D` 前置证据 | `implement.jsonl` |
| G20 | `specs/schema/schema.sql` | migration 006 列权威（AC-7） | `check.jsonl`（implement 已有） |
| G21 | MASTER §3.2 tombstone 行 | 仍写「最小 disabled 待实现」与代码漂移 | MASTER §3.2 → defer `registry_generation` 列 |
| G22 | MASTER §8.8 | 未指明调用既有 `tombstone_missing` API | MASTER §6.4 + §8.8 |
| G23 | MASTER §8.0 Boot 读清单 | 缺 Batch C 契约与模块 | MASTER §8.0 追加 |
| G24 | AUDIT §2 A1 | 未要求核对 tombstone / Batch C 接线 | AUDIT §2 A1 追加 |

---

## 刻意未纳入（有理由）

| 路径 | 理由 |
|------|------|
| `scripts/sync_registry.py` | Execute §8.8 **新建**；冻结前不存在，不宜列入 implement 必读 |
| `specs/contracts/write_contract.yaml` | WriteManager 行为已由 `write_manager.md` + 代码覆盖 |
| `specs/contracts/runtime_flow_contract.yaml` | 与 `03_runtime_flows.md` 重叠；03 已在 implement |
| Layer 1–5 契约 YAML | MASTER §3.2 显式 defer Round 3 |
| `docs/modules/agent_module.md` 等 Round 4/5 | Out of scope AC-12 |

---

## DECISIONS 漂移修正

**发现：** `SourceRegistry.sync_to_db` 在 `source_registry.py:340` 已实现 `tombstone_missing: bool = True`（YAML 缺失源 → `is_enabled=false`）。

**修订：**

- MASTER §1.3：GPT-P2-2 改为「调用既有 API」
- MASTER §3.2：defer 项从「YAML tombstone 完整 generation」改为 `registry_generation` / `removed_from_yaml_at` **列**
- MASTER §6.4（新增）：registry sync 契约
- MASTER §8.8：禁止重复实现 tombstone；测试幂等与 disabled

DECISIONS.md §9 已同步（GPT-P2-2-tombstone → 已偿还；GPT-P1-5-DB → 维持 app 层）。

---

## 路径纠偏（再次确认）

| 任务卡 | 仓库实际 |
|--------|----------|
| `backend/sync/orchestrator.py` | `backend/app/sync/orchestrator.py` |
| `backend/sync/jobs.py` | `backend/app/sync/jobs.py` |

MASTER §3.3、AUDIT A1、implement 均已对齐。

---

## validate-plan-freeze

```bash
python .trellis/scripts/task.py validate-plan-freeze .trellis/tasks/06-18-round2-batch-d-orchestrator
# → Plan freeze validation passed (exit 0)
```

---

## 修改文件清单

- `implement.jsonl` — +19 entries
- `check.jsonl` — +7 entries
- `research/original-plan-trace.md` — 输入表去重 + GPT-P2-2 修订
- `MASTER.plan.md` — §1.3, §3.2, §6.4, §8.0, §8.8
- `AUDIT.plan.md` — §2 A1
- `research/plan-doc-gap-report.md` — 本文件

---

## 第二轮缺口（Execute 零遗漏复核 · 2026-06-18）

对照 MASTER §9.2/§9.3、Batch C `implement.jsonl`、`data_sync_orchestrator.md` 引用表、AUDIT A1 `check.jsonl` 要求，追加：

| # | 路径 | 为何需要 | 已补 |
|---|------|----------|------|
| G25 | `fetch_result.py` / `fetch_port.py` | FETCHING 阶段契约与 Port 错误映射 | implement |
| G26 | `004`/`005` migrations | C-C2 不可 ALTER 004；validation 表上下文 | implement + check |
| G27 | `source_registry.yaml` | §8.8 registry sync YAML 权威 | implement + check |
| G28 | `config.py` | QMD_DATA_ROOT / DATA_ROOT smoke | implement |
| G29 | `error_redaction.py` | MASTER §7 脱敏 | implement |
| G30 | §9.2 回归测试 ×5 | Tier B 不得回归破坏 | implement |
| G31 | `production_gate` / `check_doc_links` | Tier C 验收 | implement |
| G32 | `BATCH_B_REPAIR_STATUS` | DECISIONS §9 跨批延后台账 | implement + check |
| G33 | `07_project_directory_structure` | `backend/app/*` 路径归一化 | implement |
| G34 | `duckdb_and_parquet.md` | orchestrator 模块引用表 | implement |
| G35 | `quality-guidelines.md` | Trellis 禁止模式 | implement |
| G36 | `original-plan-trace` | Execute traceability + Audit A5 | implement（`plan-adversarial-audit` Plan-only，**不**进 implement） |
| G37 | MASTER **§0.3** | 强制逐条 Read implement.jsonl + `8.0-boot-reads.txt` | MASTER |
| G38 | `check.jsonl` +17 | A1 运行时/台账/接线/迁移 | check |
