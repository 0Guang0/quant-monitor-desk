# A6 audit-perf — B3V-SYNC Sync Support Matrix & Crash-window Recovery 性能审计

> **维度：** A6 · performance-engineer + doubt-driven-development  
> **模型：** composer-2.5  
> **任务：** `round3v-sync-support-matrix-recovery`（B3V-SYNC · Manifest `B3V-C04`）  
> **Worktree：** `quant-monitor-desk-wt-b3v-sync`  
> **日期：** 2026-06-28  
> **模式：** Audit（只读，无 commit、无改码）

---

## 总判定

| 项                   | 值                         |
| -------------------- | -------------------------- |
| **verdict**          | **SKIP**                   |
| **BLOCKING**         | 0                          |
| **NON-BLOCKING**     | 2                          |
| **AUDIT.plan §1 A6** | **SKIP** — 无 hot path SLA |

---

## Scorecard（静态审计 + 参考 pytest durations）

| 指标                | 值           | 来源                    | 阈值（Plan 冻结） | 状态        |
| ------------------- | ------------ | ----------------------- | ----------------- | ----------- |
| LCP / INP / CLS     | not measured | —                       | CWV               | —（无 Web） |
| smoke 端到端耗时    | not measured | Plan 未挂载             | —                 | SKIP        |
| ResourceGuard 触发  | not measured | 既有路径未改 guard 语义 | —                 | SKIP        |
| 最慢单测 call       | 2.82s        | pytest `--durations=15` | 未冻结            | 参考 only   |
| B3V crash-window 测 | 0.80s        | 同上                    | 未冻结            | 参考 only   |
| B3V recovery 测     | 0.91s        | 同上                    | 未冻结            | 参考 only   |
| §9.6/9.7 子集       | 1.82s / 2项  | execute-evidence        | exit 0（A8）      | 委托 A8     |

> **Artifacts used:** `uv run pytest tests/test_sync_orchestrator.py -q --basetemp=.audit-sandbox/pytest-a6 --durations=15` → **33 passed**, exit 0  
> **Execute evidence:** `research/execute-evidence/9.6-green.txt`（1 passed）、`9.7-green.txt`（2 passed）  
> **Stack detected:** Python 单机 pipeline + DuckDB/SQLite；sync orchestrator 批作业；无 API 延迟 SLA；非 Web 应用

---

## 1. 权威层级（`audit-adversarial-authority.md`）

| 级别   | 来源                                                                                 | 与本维结论                                                                  |
| ------ | ------------------------------------------------------------------------------------ | --------------------------------------------------------------------------- |
| 第一级 | `B02_04_sync_job_support_and_recovery.md` §4–§7、`sync_job_contract.yaml`、`ADR-001` | 契约矩阵 + 稳定 deferred；crash-window 为正确性/恢复语义，非吞吐优化        |
| 第二级 | `agents/performance-engineer.md` checklist、`AUDIT.plan.md` §1                       | A6 显式 **SKIP**；验收 = Playbook §8.4 pytest 子集 + 全量 pytest（委托 A8） |
| 第三级 | `MASTER.plan.md` §9–§10、`implement.jsonl`                                           | §10 为 Execute DoD（证据齐 / validate-handoff）；**无 perf 冻结行**         |

**对抗性注记：** MASTER §10 仅列 §9 证据、`validate-execute-handoff`、VR 关账；**未**定义 `production_equivalent_smoke.py`、内存峰值、`--durations` 门禁或 p95 延迟。按 performance-engineer 模板无法填可 PASS/FAIL 的「指标 | 阈值 | 实测」perf 表；SKIP 为 Plan 冻结决策，非遗漏。

---

## 2. SKIP 理由（§3.6 等价 · 与 AUDIT.plan §1 A6 一致）

> Plan 原文：**「无 hot path SLA」** — 本任务为 sync job 支持矩阵显式化、稳定 deferred 错误与 crash-window **运维恢复** utility，无生产调度/API 热路径，无冻结 SLA。

### 2.1 五条证实

1. **无 hot path / SLA** — 变更落在 `contract.py` 常量、`sync_job_contract.yaml` 矩阵、`raise_deferred_job_type`、`recover_stuck_writing_job`；无 FastAPI 路由、无用户可见延迟面、无 `production_equivalent_smoke.py` 挂载点。
2. **恢复路径 O(1)** — `recover_stuck_writing_job` 仅 `SELECT status, write_id … LIMIT 1`（单行）+ `transition(COMPLETED)`；`kind=utility`、非 schedulable `job_type`。
3. **deferred 零 I/O** — `raise_deferred_job_type` 直接抛 `DeferredJobTypeError`；`full_load` reserved 路径无 adapter/fetch/write。
4. **任务卡 scope 排除重 I/O** — `B02_04` §4：禁止 production clean write；禁止把 reserved 暴露为可用；crash-window 为注入测试或 handoff，非批吞吐优化。
5. **MASTER / AUDIT 无 perf 冻结行** — 通过条件为 pytest exit 0（A8）+ VR 关账（A5）；无时长/内存数字可供 A6 PASS/FAIL。

### 2.2 实现路径 vs 性能特征

| 组件                              | 触发时机              | I/O / CPU 特征                                     | 数据量级上界       |
| --------------------------------- | --------------------- | -------------------------------------------------- | ------------------ |
| `raise_deferred_job_type`         | `run_full_load` 调用  | 纯异常构造；零 DB/网络                             | 常量               |
| `recover_stuck_writing_job`       | 运维手动恢复          | 1× reader SELECT + 1× writer transition            | 单行               |
| `IMPLEMENTED_JOB_TYPES` 常量      | 测试/契约校验         | 内存 frozenset；运行时 orchestrator 不读 YAML 文件 | 6 类型             |
| `post_write_pre_complete_hook`    | pytest 注入 crash     | 测试专用；生产路径 gated                           | fixture 级         |
| `IncrementalJobRunner.run` 写路径 | 既有 incremental 作业 | 未改 `_finalize_staged` 批逻辑                     | ResourceGuard 既有 |

**结论：** 变更落在 **契约显式化 + 单次运维恢复 + 测试注入 hook**，非高频批处理或 SLA 敏感面；与 AUDIT.plan「无 hot path SLA」一致。

### 2.3 performance-engineer checklist（Audit 模式）

| 检查项                       | 状态        | 说明                                  |
| ---------------------------- | ----------- | ------------------------------------- |
| Baseline 有证据来源          | **N/A**     | Plan 未冻结 perf 命令                 |
| EXPLAIN/profile/smoke        | **N/A**     | recovery SQL trivial；无 smoke 挂载点 |
| 优化后同一命令对比           | **N/A**     | 无优化项                              |
| sandbox 数据量级与 Plan 一致 | **PASS**    | pytest tmp_path + 小 adapter fixture  |
| 全量 pytest 无无关回归       | **委托 A8** | 本维 durations 参考；正式门禁见 A8    |

---

## 3. 计划外 perf 风险扫描

> 按 `audit-adversarial-authority.md` A6：**即使 SKIP，仍须扫描** hot path、无界 I/O、批大小/内存尖峰。

### 3.1 Hot path

| 路径                                      | 是否 hot | 证据                                        | 风险                      |
| ----------------------------------------- | -------- | ------------------------------------------- | ------------------------- |
| `recover_stuck_writing_job`               | **否**   | utility ops；人工/脚本偶发调用              | 无 SLA                    |
| `raise_deferred_job_type` @ full_load     | **否**   | 立即 fail-fast；不应进入调度热环            | 无                        |
| `run_data_quality` / `run_revision_audit` | **否**   | 批作业 runner；与既有 incremental 同级      | 见 NB-1（scope 扩展备忘） |
| incremental/backfill 主路径               | **未改** | `_finalize_staged` / ResourceGuard 未动语义 | 预存在 perf 特征          |

**结论：** 本分支**不存在**新增可观测的生产 hot path；SKIP 合理。

### 3.2 无界 I/O

| 面                      | 扫描                      | 发现                                   | 评级    |
| ----------------------- | ------------------------- | -------------------------------------- | ------- |
| recovery 全表扫         | `orchestrator.py:283-287` | `WHERE job_id = ?` 主键点查            | **无**  |
| contract YAML 热读      | `contract.py` + grep      | `load_sync_job_contract()` 仅测试调用  | **无**  |
| deferred 触发网络 fetch | `run_full_load`           | 抛错前无 adapter                       | **无**  |
| crash-window 重复写     | recovery 测 + 实现        | recovery 仅 transition；不测二次 write | **无**  |
| backfill shard 循环     | `runners.py`              | 既有分片逻辑；B3V 未扩 shard 面        | 见 NB-2 |

### 3.3 批大小 / 内存尖峰

| 面                             | 行为                          | 当前量级    | 计划外风险                   |
| ------------------------------ | ----------------------------- | ----------- | ---------------------------- |
| recovery 双连接                | reader 块 + writer transition | 毫秒级      | 运维偶发；见 NB-2            |
| ADR-001 COMPLETED 事务外       | 写提交后 transition           | 设计既定    | 正确性非 perf；recovery 补偿 |
| backfill large range 测        | 多分片 fixture                | ~2.82s 最慢 | 预存在；无冻结基线 → NB-2    |
| ResourceGuard @ begin_fetching | 既有                          | 未改        | 无新增内存尖峰               |

**结论：** B3V-SYNC 增量路径 CPU/内存**可忽略**；结构性备忘见 NB-1/NB-2。

### 3.4 与 deferred perf 项交叉

| 登记项                                   | 与 B3V-SYNC 关系                 |
| ---------------------------------------- | -------------------------------- |
| `scripts/production_equivalent_smoke.py` | diff 未挂载；MASTER §10 无 smoke |
| `tests/test_resource_guard.py`           | sync guard 语义未改              |
| Batch 6 perf budget / nightly            | **不阻塞** 本任务                |

---

## 4. DOUBT（doubt-driven-development）

| 疑点                                               | 结论                                                 |
| -------------------------------------------------- | ---------------------------------------------------- |
| SKIP 是否遗漏 smoke？                              | **否** — AUDIT.plan §1 + MASTER §10 双重无 perf 阈值 |
| recovery 是否引入双写 perf 风险？                  | **否** — 仅状态 transition；§9.7 测 clean 行数不变   |
| `data_quality`/`revision_audit` 升格实现是否 hot？ | **否** — 批作业；非 API；登记 NB-1 备忘              |
| crash hook 是否泄漏到生产？                        | **否** — `sync_adapter_bypass_allowed()` pytest gate |
| backfill 2.8s 测是否 B3V 回归？                    | **否** — 非 B3V slice 测；无冻结基线                 |

---

## 5. §3.6 证据表（SKIP 专用）

| 指标                                                 | 阈值（Plan 冻结） | 实测             | 证据                                                                    |
| ---------------------------------------------------- | ----------------- | ---------------- | ----------------------------------------------------------------------- |
| `tests/test_sync_orchestrator.py` 全模块             | exit 0（A8）      | 33 passed        | `uv run pytest … -q --basetemp=.audit-sandbox/pytest-a6 --durations=15` |
| §9.6 recovery smoke                                  | exit 0            | 1 passed / 1.4s  | `execute-evidence/9.6-green.txt`                                        |
| §9.7 crash-window + recovery                         | exit 0            | 2 passed / 1.82s | `execute-evidence/9.7-green.txt`                                        |
| 最慢 call（backfill large range）                    | **未冻结**        | 2.82s            | durations 参考                                                          |
| B3V `test_syncJob_incremental_crashWindow_*`         | **未冻结**        | 0.80s            | durations 参考                                                          |
| B3V `test_syncJob_incremental_recoverStuckWriting_*` | **未冻结**        | 0.91s            | durations 参考                                                          |
| smoke 端到端                                         | **未冻结**        | **未测**         | SKIP                                                                    |
| 内存峰值 MB                                          | **未冻结**        | **未测**         | fixture 级                                                              |

---

## 6. 计划外发现

| ID   | 发现                                                                                  | 严重度               | 说明                                                                                  |
| ---- | ------------------------------------------------------------------------------------- | -------------------- | ------------------------------------------------------------------------------------- |
| NB-1 | `data_quality` / `revision_audit` 从 reserved stub 升格为 **implemented runner**      | **NON-BLOCKING**     | 扩大可调度作业面；runner 复用 `QualityJobRunner` 既有模式；非 B3V perf SLA 范围       |
| NB-2 | **backfill 大区间分片** 测仍为模块最慢（~2.8s）；recovery 使用 reader+writer 两次连接 | **NON-BLOCKING**     | 预存在/运维偶发；无 Plan 冻结基线；未来若 nightly perf gate 须单独对标                |
| —    | hot path / 全表扫 / 无界 fetch / recovery 双写                                        | **无 BLOCKING 发现** | 已审阅 `orchestrator.py`、`contract.py`、`runners.py` hook 段、`B02_04` §4、`ADR-001` |

**显式声明：** 已对照 `B02_04_sync_job_support_and_recovery.md`、`AUDIT.plan.md` §1 A6、`MASTER.plan.md` §9–§10、`sync_job_contract.yaml`、`agents/performance-engineer.md`、实现全文、execute-evidence 及 pytest durations；**无 BLOCKING perf 项**。

---

## 7. 结论

**A6 审计判定：SKIP（维持）。**

理由摘要：B3V-SYNC 是 **sync job 支持矩阵显式化 + 稳定 deferred 错误 + crash-window 运维恢复 utility**；任务卡与 AUDIT.plan §1 均排除 production clean write 与 API 热路径；**无**冻结 perf 阈值。实现遵守 O(1) recovery 点查、deferred 零 I/O、pytest-only crash hook。计划外扫描登记 2 项 **NON-BLOCKING** 备忘，**不阻断** B3V-SYNC merge。
