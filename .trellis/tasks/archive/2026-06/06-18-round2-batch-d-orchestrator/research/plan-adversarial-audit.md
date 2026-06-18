# Plan Adversarial Audit — Batch D (Agent 2)

> 2026-06-18 · 独立对抗审计 · 方法：MASTER/AUDIT/REPAIR/plan.freeze + 014/DECISIONS + GitNexus query/context + 代码 grep/Read  
> Agent 1 已补 `plan-doc-gap-report.md`；本报告为 **第二轮** 对抗审查。

---

## 摘要

| 严重度 | 发现数 | 已修复（Plan 内） | 遗留 |
|--------|--------|-------------------|------|
| **P0** | 3 | 3 | 0 |
| **P1** | 9 | 9 | 0 |
| **P2** | 5 | 5 | 0 |

`validate-plan-freeze`：修订后 **exit 0**（见文末）。

---

## P0 — Execute 阻断 / AC 缺口

### ADV-P0-1 — AC-2 六种 job_type 缺测试 tracer

| 字段 | 内容 |
|------|------|
| **ID** | ADV-P0-1 |
| **声称** | MASTER §2 AC-2 要求六种 `job_type` 各有语义测试；`orchestrator-tests.md` 仅覆盖 incremental/backfill/reconcile，**无** `full_load` / `revision_audit` / `data_quality` |
| **证据** | `sync_job_contract.yaml` L4–9 列六种类型；MASTER §4.2 L189 要求「各 1 条语义测」；`orchestrator-tests.md` §8.2 仅通用状态机测，无 job_type 维度 |
| **修复** | `orchestrator-tests.md` §8.2 追加三条 tracer；MASTER §8.2 注明 AC-2 骨架覆盖；AUDIT §2 A4 增加六种 type 抽检 |

### ADV-P0-2 — Adapter fetch 必须接 writer 连接（fetch_log 落库）

| 字段 | 内容 |
|------|------|
| **ID** | ADV-P0-2 |
| **声称** | MASTER §4 流水线未写明 `adapter.fetch(..., con=writer_con, job_id=...)`；Execute 易漏接 `ConnectionManager.writer()`，导致 fetch_log 不写、违反 DECISIONS §5 与 `data_sync_orchestrator.md` §13.1 |
| **证据** | `base_adapter.py` L64–71：`FetchLogWriter.write(con, ...)` 在 `fetch()` 内；`implement.jsonl` 缺 `fetch_log.py` / `base_adapter.py` / `connection.py` |
| **修复** | MASTER §4 流程 + 新增 §6.5 接线契约；`implement.jsonl` 追加 Batch C 写路径模块；§8.5 显式要求 writer `con` |

### ADV-P0-3 — `data_quality` job_type 与 DataQualityValidator 易混读

| 字段 | 内容 |
|------|------|
| **ID** | ADV-P0-3 |
| **声称** | 契约 `job_type=data_quality` 指 **独立抽样审计 job**（`data_sync_orchestrator.md` §13.4.6）；Execute 可能误当成 pipeline 内 VALIDATING 阶段或重复实现 Layer 3 全量审计 |
| **证据** | `grill-with-docs-session.md` Q3 有结论但未写入 MASTER §6；AC-2 与 §4.2 表述不足 |
| **修复** | MASTER §4.2 + §6.6 冻结语义：`create_job` + 状态转移 + 可选委托 `DataQualityValidator.validate_table` 抽样；**不**做 Layer 1–5 建模 |

---

## P1 — 高 misread 风险 / AUDIT 洞

### ADV-P1-1 — ResourceGuard 结果 → job 状态未冻结

| 字段 | 内容 |
|------|------|
| **ID** | ADV-P1-1 |
| **声称** | `RESOURCE_GUARD_PAUSED` **不是** `sync_job_contract` 合法 status；AC-5 写「event/message」但 orchestrator-tests / AUDIT A7 写 `FAILED_RETRYABLE`，Execute 可能发明非法 status 或永不转移 |
| **证据** | `resource_guard.py` L232–246 `format_pause_event` 输出 `RESOURCE_GUARD_PAUSED` 到 stderr；契约 statuses 无此项 |
| **修复** | MASTER §4.4 + §7 + orchestrator-tests §8.4：`Decision.PAUSE|HARD_STOP` → `FAILED_RETRYABLE`，`job_event_log.message` 含 `RESOURCE_GUARD_PAUSED` 前缀；AUDIT A7 对齐 |

### ADV-P1-2 — FullLoad 断点续跑 vs Batch D 骨架边界不清

| 字段 | 内容 |
|------|------|
| **ID** | ADV-P1-2 |
| **声称** | `data_sync_orchestrator.md` §13.4.1「必须支持断点续跑」；MASTER 仅 defer 调度频率，未 defer resume/checkpoint 字段 |
| **证据** | 模块 spec L194；MASTER §4.2 无 resume 说明 |
| **修复** | MASTER §3.2 defer 表增加 FullLoad checkpoint/resume → Round 3；§4.2 注明 Batch D 仅 `create_job`+最小转移 |

### ADV-P1-3 — Backfill 分片失败语义缺测试

| 字段 | 内容 |
|------|------|
| **ID** | ADV-P1-3 |
| **声称** | MASTER §4.3「失败不吞已完成 task」无 tracer；Execute 可能只测分片数 |
| **证据** | `orchestrator-tests.md` §8.6 仅两条测；无 mid-shard fail 断言 |
| **修复** | `orchestrator-tests.md` 追加 `test_backfillJob_midShardFailure_preservesCompletedTasks`；MASTER §8.6 引用 |

### ADV-P1-4 — `SyncJobSpec` 缺 `adapter_id` 与 schema 漂移

| 字段 | 内容 |
|------|------|
| **ID** | ADV-P1-4 |
| **声称** | `schema.sql` L84 `adapter_id` 列；`SyncJobSpec` 未含字段，persist 层易漏列或硬编码 |
| **证据** | MASTER §4.1 L159–172 vs `schema.sql` L73–99 |
| **修复** | `SyncJobSpec` 增加 `adapter_id: str | None`；§6.1 注明可空、fetch 后回填 |

### ADV-P1-5 — implement.jsonl 缺 migration / init 触点

| 字段 | 内容 |
|------|------|
| **ID** | ADV-P1-5 |
| **声称** | §8.1 要求改 migrate runner；`implement.jsonl` 无 `migrate.py` / `init_db.py`，GitNexus impact 前易漏读 |
| **证据** | MASTER §8.1 Skill 行；`validate_plan_freeze` 不强制 migrate 路径 |
| **修复** | `implement.jsonl` + `check.jsonl` 追加 |

### ADV-P1-6 — AUDIT A5 prod-path 环境验证命令错误

| 字段 | 内容 |
|------|------|
| **ID** | ADV-P1-6 |
| **声称** | AUDIT §2 A5 使用 `from app.config import Config`；仓库实际为 `backend.app.config.DATA_ROOT` |
| **证据** | `config.py` L18；`tests/test_backend_smoke.py` import 模式 |
| **修复** | AUDIT §2 A5 改为 `from backend.app.config import DATA_ROOT` |

### ADV-P1-7 — AUDIT A3 缺可执行 init/migrate CLI

| 字段 | 内容 |
|------|------|
| **ID** | ADV-P1-7 |
| **声称** | 协议 §2.10 要求 A7/A3 替换 `{{init/migrate CLI}}`；AUDIT A3 仅 prose「init_db twice」 |
| **证据** | `audit-skill-registry.md` L81；AUDIT.plan §2 A3 |
| **修复** | A3 追加 `QMD_DATA_ROOT=... python scripts/init_db.py` ×2 + 006 表存在性 SQL |

### ADV-P1-8 — ci_ingestion_smoke 扩展断言不足

| 字段 | 内容 |
|------|------|
| **ID** | ADV-P1-8 |
| **声称** | AC-9 / §8.9 仅「输出含 orchestrator ok」；当前 smoke 只验 004 两表（L32–37），Execute 可能只 print 不改断言 |
| **证据** | `scripts/ci_ingestion_smoke.py` 全文 42 行 |
| **修复** | MASTER §8.9 冻结：应用 006 后 `data_sync_job`/`job_event_log` 存在 + 跑一次 orchestrator incremental smoke + stdout 含 `orchestrator_smoke: ok` |

### ADV-P1-9 — 状态机合法转移未指向权威

| 字段 | 内容 |
|------|------|
| **ID** | ADV-P1-9 |
| **声称** | `sync_job_contract.yaml` 列 status 枚举但无转移表；`test_syncJob_invalidTransition_raises` 无正向路径清单，Execute 可能过宽或过窄 |
| **证据** | 契约 L10–28；`data_sync_orchestrator.md` §13.2 有主路径图 |
| **修复** | MASTER §6.2 追加：happy path 以 §13.2 为准；非法跳迁拒绝；terminal 不可出 |

---

## P2 — 已关闭（Plan 修订 2026-06-18）

| ID | 原遗留 | 关闭方式 |
|----|--------|----------|
| **ADV-P2-1** | DECISIONS §9 GPT-P2-2 与代码漂移 | `DECISIONS.md` §9 更新 + §已偿还 `GPT-P2-2-tombstone` |
| **ADV-P2-2** | GPT-P1-5-DB fetch_log DB CHECK | MASTER §6.7 + DECISIONS §9 改为「维持 app 层」 |
| **ADV-P2-3** | AUDIT 维度与 registry 映射 | AUDIT §0.1 维度映射说明 |
| **ADV-P2-4** | FakeAdapter 位置 | MASTER §6.8 + `implement.jsonl` 已有 `test_data_adapter_contract.py` |
| **ADV-P2-5** | 生产 CLI defer | MASTER §3.2 已有 `quant_monitor.sync` → Round 3 |

---

## GitNexus / 代码验证摘要

| 查询 | 结论 |
|------|------|
| `query("DataSyncOrchestrator sync job orchestration")` | 无既有 Orchestrator 实现；Batch C wiring（`sync_to_db`, validators, `WriteManager._write_audit`）已索引 |
| `context("ResourceGuard")` | 仅测试/smoke 引用；Batch D 为首次生产路径集成 |
| `backend/app/sync/*` | **不存在**（符合 Plan 预期） |
| `006_*.sql` | **不存在**（Execute 创建） |

---

## 修订文件（Agent 2）

- `research/plan-adversarial-audit.md`（本文件）
- `MASTER.plan.md` — §3.2, §4, §6, §7, §8.2/8.5/8.6/8.9, §13
- `AUDIT.plan.md` — §2 A3/A4/A5/A7
- `research/orchestrator-tests.md` — §8.2/8.4/8.6
- `implement.jsonl` — +6 接线模块
- `check.jsonl` — +2 spec 触点
- `research/original-plan-trace.md` — 输入表 + AC-2 注记

---

## validate-plan-freeze

```bash
python .trellis/scripts/task.py validate-plan-freeze .trellis/tasks/06-18-round2-batch-d-orchestrator
# → Plan freeze validation passed (exit 0)
```
