# A6 audit-perf — B3V-STOR RawStore Atomic Write 性能审计

> **维度：** A6 · performance-engineer + doubt-driven-development  
> **任务：** `round3v-rawstore-atomic-write`（B3V-STOR · Manifest `B3V-C03`）  
> **Worktree：** `quant-monitor-desk-wt-b3v-stor`  
> **日期：** 2026-06-28  
> **模式：** Audit（只读，无 commit、无改码）

---

## 总判定

| 项                   | 值                                           |
| -------------------- | -------------------------------------------- |
| **verdict**          | **SKIP**                                     |
| **BLOCKING**         | 0                                            |
| **NON-BLOCKING**     | 2（NB-1/NB-2 → repair-evidence 已闭合）      |
| **AUDIT.plan §1 A6** | **SKIP** — 本地 I/O helper 小 diff           |

---

## Scorecard（静态审计 + pytest durations 参考）

| 指标               | 值           | 来源                    | 阈值（Plan 冻结） | 状态        |
| ------------------ | ------------ | ----------------------- | ----------------- | ----------- |
| LCP / INP / CLS    | not measured | —                       | CWV               | —（无 Web） |
| smoke 端到端耗时   | not measured | Plan 未挂载             | —                 | SKIP        |
| ResourceGuard 触发 | not measured | RawStore 路径未挂 guard | —                 | SKIP        |
| 原子写相关最慢 call | 0.06s        | pytest `--durations=15` | 未冻结            | 参考 only   |
| `test_save_repeatedSameContent_isIdempotent` | 0.02s | 同上 | 未冻结 | 参考 only |
| `test_save_midWriteFailure_whenTargetExists_preservesOriginalBytes` | 0.02s | 同上 | 未冻结 | 参考 only |
| 全模块最慢 call    | 0.56s        | 同上（registry 测）     | 未冻结            | 参考 only   |

> **Artifacts used:** `uv run pytest tests/test_raw_store.py -q --basetemp=.audit-sandbox/pytest --durations=15` → **31 passed**, exit 0（2026-06-28 A6 复跑）  
> **Stack detected:** Python 单机 pipeline；RawStore 证据落盘 helper；无 API 热路径、无批调度器挂载

---

## 1. 权威层级（`audit-adversarial-authority.md`）

| 级别   | 来源                                                                                         | 与本维结论                                                                 |
| ------ | -------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| 第一级 | `B02_03_rawstore_atomic_write.md` §4、`resource_limits.yaml` 邻接、`path_compat.py` ponytail 注释 | 原子写正确性优先；禁止 POSIX-only 目录 fsync；`MAX_RAW_FILE_BYTES` 256 MiB 上界 |
| 第二级 | `agents/performance-engineer.md` checklist、`AUDIT.plan.md` §1                               | A6 显式 **SKIP**；验收 = 任务卡 §7 pytest 子集（委托 A5/A8）              |
| 第三级 | `MASTER.plan.md` §2.5 设计决策、`§10` Execute DoD                                              | flush+fsync 为设计意图；**§10 无 perf 冻结行**（仅 pytest exit 0）        |

**对抗性注记：** MASTER §10 仅列 `uv run pytest -q` / ruff / validate-handoff，**未**定义 `production_equivalent_smoke.py`、`ResourceGuard`、fsync 延迟上限或 `--durations` 门禁。按 performance-engineer 模板无法填可 PASS/FAIL 的「指标 | 阈值 | 实测」perf 表；SKIP 为 Plan 冻结决策，非遗漏。

---

## 2. SKIP 理由（§3.6 等价 · 与 AUDIT.plan §1 A6 / §2.2 一致）

> Plan 原文：**「本地 I/O helper 小 diff」** — 本任务为 `write_bytes_atomic` + `RawStore.save` 单调用点切换，无生产 SLA、无冻结 perf 阈值。

### 2.1 五条证实

1. **无 hot path / SLA** — `write_bytes_atomic` 仅经 `RawStore.save` 调用；生产调用方为 adapter fetch 成功路径（`skeleton_base.py`）、ops probe（`interface_probe.py`、`tdx_manual_probe.py`），均为**低频证据落盘**，非用户可见 API 延迟面。
2. **有界 I/O 面** — 单次写：`len(content) ≤ MAX_RAW_FILE_BYTES`（256 MiB）；同目录 temp + `os.replace`；无循环批写、无 DuckDB 全表扫。
3. **任务卡 scope 排除 perf 优化** — `B02_03` §4：不改 content_hash 语义、不加外部依赖、不做 Windows POSIX-only 目录 fsync；**无**时长/吞吐 AC。
4. **fsync 为设计意图非回归** — MASTER §2.5：flush+fsync（平台支持）→ `os.replace` 为原子性契约；代价已在 repair `perf-tradeoff-note.md` 登记，属正确性换延迟的显式权衡。
5. **MASTER / AUDIT 无 perf 冻结行** — 通过条件为 pytest exit 0（A5/A8）；无 smoke/ResourceGuard/内存峰值数字可供 A6 PASS/FAIL。

### 2.2 实现路径 vs 性能特征

| 组件                    | 触发时机              | I/O / CPU 特征                                      | 数据量级上界              |
| ----------------------- | --------------------- | --------------------------------------------------- | ------------------------- |
| `write_bytes_atomic`    | 每次 `RawStore.save`  | temp 写 + flush + `os.fsync` + `os.replace`        | 单次 ≤256 MiB（RAM 缓冲） |
| `RawStore.save`         | adapter/probe 证据写  | 上述 + sha256 + mkdir                               | 同上                      |
| `write_bytes`（保留）   | 非本任务路径          | 无 fsync；未改行为                                  | —                         |
| registry 相关测（最慢） | pytest fixture        | DuckDB/SQLite 启动主导 0.56s                        | fixture 级                |

**结论：** 变更落在 **单次证据文件落盘** 的微型路径；fsync 增加延迟但符合原子写契约；与 AUDIT.plan「本地 I/O helper 小 diff」一致。

### 2.3 performance-engineer checklist（Audit 模式）

| 检查项                       | 状态        | 说明                                          |
| ---------------------------- | ----------- | --------------------------------------------- |
| Baseline 有证据来源          | **N/A**     | Plan 未冻结 perf 命令                         |
| EXPLAIN/profile/smoke        | **N/A**     | 无 SQL hot path；无 smoke 挂载点              |
| 优化后同一命令对比           | **N/A**     | 无优化项（正确性加固，非 perf 优化任务）      |
| sandbox 数据量级与 Plan 一致 | **PASS**    | 测试 payload KB 级；`MAX_RAW_FILE_BYTES` 既有 |
| 全量 pytest 无无关回归       | **委托 A5** | 本维仅 `test_raw_store.py` durations 参考     |

---

## 3. 计划外 perf 风险扫描

> 按 `audit-adversarial-authority.md` A6：**即使 SKIP，仍须扫描** hot path、无界 I/O、批大小/内存尖峰。

### 3.1 Hot path

| 路径                                   | 是否 hot   | 证据                                      | 风险                         |
| -------------------------------------- | ---------- | ----------------------------------------- | ---------------------------- |
| `RawStore.save` @ adapter fetch        | **否**     | 每 SUCCESS fetch 一次证据写；非 API 路由  | 无生产 SLA                   |
| `RawStore.save` @ ops probe            | **否**     | 手动/探测路径                             | 偶发                         |
| 批量 micro-fetch / 多 worker           | **未涉及** | MASTER 单机 pipeline；gitnexus d=1 共 6  | 未来高频写须复评 → NB-2      |
| `production_equivalent_smoke.py`       | **未挂载** | diff 未改 smoke 脚本                      | 无                           |

**结论：** 当前分支**不存在**可观测的生产 hot path；SKIP 合理。

### 3.2 无界 I/O

| 面                     | 扫描                     | 发现                                           | 评级       |
| ---------------------- | ------------------------ | ---------------------------------------------- | ---------- |
| 单文件大小             | `raw_store.py` L18       | `MAX_RAW_FILE_BYTES = 256 * 1024 * 1024` 硬顶  | **无**     |
| temp 文件泄漏          | `write_bytes_atomic`     | except 路径 `unlink(missing_ok=True)`          | **无**     |
| 目录遍历 / 全盘扫      | 任务边界                 | 单目标路径写                                   | **无**     |
| 父目录 fsync           | `path_compat.py` ponytail | **故意省略**（Windows 兼容）；见 NB-1 备忘    | NB-1 子项  |
| 网络 / live fetch      | 任务边界                 | 禁止 production DB 写                          | **无**     |

### 3.3 批大小 / 内存尖峰

| 面                           | 行为                         | 当前量级     | 计划外风险                                      |
| ---------------------------- | ---------------------------- | ------------ | ----------------------------------------------- |
| 全 payload RAM 缓冲          | `write_bytes_atomic` 入参 bytes | ≤256 MiB   | 超大文件内存尖峰；已有 cap + ponytail 注释      |
| 每写 fsync                   | `os.fsync(handle.fileno())`  | 单次         | 高频小文件 burst → 吞吐瓶颈 → NB-2              |
| temp 命名                    | pid + token_hex(4)           | 同目录       | 冲突概率极低；A7 孤儿 temp runbook 已闭合       |
| SHA256 全内容哈希            | `RawStore.save` L65          | ≤256 MiB     | 与既有行为一致；非本 diff 新增                  |

**结论：** 当前证据落盘频率与规模下 CPU/延迟**可接受**；结构性备忘见 NB-1/NB-2（repair 已闭合）。

### 3.4 与 deferred perf 项交叉

| 登记项                                   | 与 B3V-STOR 关系                  |
| ---------------------------------------- | --------------------------------- |
| `scripts/production_equivalent_smoke.py` | diff 未挂载；MASTER §10 无 smoke  |
| `tests/test_resource_guard.py`           | RawStore 路径未接入 ResourceGuard |
| Batch 6 perf budget / nightly            | **不阻塞** 本任务                 |
| `repair-evidence/perf-tradeoff-note.md`  | A6-NB-01/NB-02 **已闭合**         |

---

## 4. DOUBT（doubt-driven-development）

| 疑点                                      | 结论                                                                      |
| ----------------------------------------- | ------------------------------------------------------------------------- |
| SKIP 是否遗漏 smoke？                     | **否** — AUDIT.plan §1 + MASTER §10 双重无 perf 阈值                    |
| fsync 是否构成 BLOCKING perf 回归？       | **否** — 为 MASTER §2.5 设计意图；低频写；`perf-tradeoff-note.md` 已登记 |
| 256 MiB RAM 缓冲是否 BLOCKING？           | **否** — 既有 `MAX_RAW_FILE_BYTES`；ponytail 天花板已注释               |
| 省略父目录 fsync 是否 perf 问题？         | **否** — 属耐久性/正确性权衡（断电目录项），非吞吐；A2 已注释           |
| registry 测 0.56s 是否原子写回归？        | **否** — DuckDB fixture 主导；原子写相关测 ≤0.06s                       |
| repair 后 A6-NB 是否仍 OPEN？             | **否** — `zero-open-signoff.md` 登记 CLOSED                               |

---

## 5. §3.6 证据表（SKIP 专用）

| 指标                                                         | 阈值（Plan 冻结） | 实测                    | 证据                                                                 |
| ------------------------------------------------------------ | ----------------- | ----------------------- | -------------------------------------------------------------------- |
| `tests/test_raw_store.py`                                    | exit 0（A5/A8）   | **31 passed**, exit 0   | `uv run pytest tests/test_raw_store.py -q --basetemp=.audit-sandbox/pytest --durations=15` |
| 原子写 idempotent 测 call                                    | **未冻结**        | 0.02s                   | 同上                                                                 |
| 原子写 mid-failure 测 call                                   | **未冻结**        | 0.02s                   | 同上                                                                 |
| oversized content 测 call                                    | **未冻结**        | 0.06s                   | 同上                                                                 |
| smoke 端到端                                                 | **未冻结**        | **未测**                | SKIP                                                                 |
| ResourceGuard                                                | **未冻结**        | **未触及**              | 无 RawStore 调用路径                                                 |
| fsync 延迟 / 吞吐                                            | **未冻结**        | **未测**（设计权衡文档） | `repair-evidence/perf-tradeoff-note.md`                              |
| 内存峰值 MB                                                  | **未冻结**        | **未测**                | fixture KB 级；cap 256 MiB                                           |

---

## 6. 计划外发现

| ID   | 发现                                                                 | 严重度               | 说明 / 闭合状态                                                          |
| ---- | -------------------------------------------------------------------- | -------------------- | ------------------------------------------------------------------------ |
| NB-1 | 每次写入 **`flush` + `os.fsync`**；比 `write_bytes` 慢一个数量级     | **NON-BLOCKING**     | **CLOSED** — `repair-evidence/perf-tradeoff-note.md`；低频证据写可接受   |
| NB-2 | 若 sync 路径改为**高频小写 / 批量 micro-fetch**，fsync 成吞吐瓶颈    | **NON-BLOCKING**     | **CLOSED** — 同上；复评触发条件已写（组写/WAL/间隔 fsync）               |
| —    | hot path / 无界 I/O / ResourceGuard 缺失 / smoke 未挂载              | **无 BLOCKING 发现** | 已审阅 `path_compat.py`、`raw_store.py`、`B02_03` §4、MASTER §2.5/§10、`perf-tradeoff-note.md` |

**显式声明：** 已对照 `B02_03_rawstore_atomic_write.md`、`AUDIT.plan.md` §1 A6 / §2.2、`MASTER.plan.md` §2.5/§10、`agents/performance-engineer.md`、`agents/audit-adversarial-authority.md`、实现全文、repair signoff 及 pytest durations；**无 BLOCKING perf 项**。

---

## 7. 结论

**A6 审计判定：SKIP（维持）。**

理由摘要：B3V-STOR 是 **RawStore 证据文件原子写加固**（同目录 temp → flush/fsync → `os.replace`）；任务卡与 AUDIT.plan §1 均排除 perf SLA、smoke 与 ResourceGuard 门禁；**无**冻结 perf 阈值、**无**生产 hot path。fsync 延迟为正确性契约的一部分，已在 repair 文档化。计划外扫描登记 2 项 **NON-BLOCKING**（NB-1 fsync 代价、NB-2 高频写复评触发），**均已闭合**，**不阻断** B3V-STOR merge。
