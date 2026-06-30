# Audit A7 报告 — B3V-STOR RawStore Atomic Write

| 字段       | 值                                                                                                                     |
| ---------- | ---------------------------------------------------------------------------------------------------------------------- |
| 维度       | **A7** Ops / DBA / 本地数据路径                                                                                        |
| 任务       | `round3v-rawstore-atomic-write` · Playbook `B3V-STOR` · Manifest `B3V-C03`                                             |
| Owned VR   | `VR-STOR-001`                                                                                                          |
| Worktree   | `C:/Users/Guang/Desktop/quant-monitor-desk-wt-b3v-stor`                                                                |
| 分支       | `fix/round3v-rawstore-atomic-write`（实现已 merge `2a496af7`；分支领先 master 仅 Plan QC 文档 + `conftest` bootstrap） |
| 实现提交   | `f3281ad3` fix(storage): B3V-STOR atomic raw write with zero-open repair                                               |
| 模式       | **只读 Audit**（不改代码、不 commit、不写 production 路径）                                                            |
| Agent 模板 | `agents/database-administrator.md`                                                                                     |
| 对抗权威   | `agents/audit-adversarial-authority.md`                                                                                |
| 审计日期   | 2026-06-28                                                                                                             |

---

## 1. AUDIT.plan §1 A7 / §2 验证矩阵

| 项                       | 冻结要求                | 审计结论                                                                                  |
| ------------------------ | ----------------------- | ----------------------------------------------------------------------------------------- |
| A7 验证类型              | cli-sandbox             | **已执行** — 见 §3.7                                                                      |
| 环境                     | local                   | sandbox `basetemp`                                                                        |
| 通过条件                 | **无 production DB 写** | **PASS** — 实现仅改文件系统 I/O helper；`RawStore.save` 无 DuckDB 连接                    |
| migration / init         | 未在 AUDIT.plan 单列    | **PASS（静态）** — `f3281ad3` 未触及 `specs/schema/`、`migrations/`、`scripts/init_db.py` |
| kill-migrate walkthrough | 标准 DBA 模板默认项     | **N/A** — 本任务无 migration 面；以 raw 写失败恢复 + migration 回归 pytest 替代           |

**DOUBT（DBA）：** 第二次 init 是否仅「不报错」而数据已损坏？→ 本 diff **无 schema 变更**；`test_schema_migration.py` 10/10 间接覆盖 migration 幂等（§3.7）。

**DOUBT（DBA）：** kill 后 `schema_version` 与 migration 表是否一致？→ **不适用**；本任务异常面为 **SIGKILL 后孤儿 temp**（§4 F1），非 DB migration 中途失败。

---

## 2. Diff 范围核对（schema / registry / 数据面）

### 2.1 实现变更（`f3281ad3`）

| 文件                                 | 类别                      | A7 相关                                                      |
| ------------------------------------ | ------------------------- | ------------------------------------------------------------ |
| `backend/app/storage/path_compat.py` | 新增 `write_bytes_atomic` | 同目录 temp + flush/fsync + `os.replace`；失败 `unlink` temp |
| `backend/app/storage/raw_store.py`   | 接线                      | `write_bytes` → `write_bytes_atomic`（L74）                  |
| `tests/test_raw_store.py`            | 测试                      | sandbox `tmp_path`；无 production `QMD_DATA_ROOT`            |

### 2.2 分支相对 master 额外 diff（非 STOR 实现）

| 文件                                 | A7 判定                                                                                        |
| ------------------------------------ | ---------------------------------------------------------------------------------------------- |
| `tests/conftest.py`                  | **计划外** — R3H/R3G authorization YAML bootstrap；与 STOR 原子写无关；不引入 production DB 写 |
| `.trellis/tasks/.../plan-qc-*.md` 等 | 文档 only                                                                                      |

### 2.3 显式未触及路径（对抗性 diff + grep）

- `specs/schema/schema.sql`
- `backend/app/db/migrations/**`
- `scripts/init_db.py`
- `backend/app/db/write_manager.py` / `validation_gate.py`
- `specs/datasource_registry/source_registry.yaml`
- `backend/app/storage/file_registry.py`（实现体未改）

### 2.4 运行时数据路径影响

| 组件                  | 写 DuckDB？ | 写文件系统？                  | 说明                                                                                              |
| --------------------- | ----------- | ----------------------------- | ------------------------------------------------------------------------------------------------- |
| `RawStore.save`       | **否**      | **是**（`data_root/raw/...`） | 仅经 `write_bytes_atomic` 落盘；`content_hash` 命名不变                                           |
| `write_bytes_atomic`  | **否**      | **是**（caller 指定 path）    | caller 须自行做 `data_root` containment（docstring + `RawStore` 已有 `is_relative_to_data_root`） |
| `write_bytes`（遗留） | **否**      | 是                            | 仍供 `test_path_compat` 等；**RawStore 主路径已不走**                                             |

**Hardening §3：** Batch 3V 禁止 production clean write / production DB mutation — **符合**；变更限于本地 raw 证据原子写语义。

---

## 3. §3.7 运维证据表

### 3.1 Database Administrator（幂等 / schema / 数据污染面）

| 步骤                       | 命令                                                                                                                                | exit     | 关键输出 / 证据                                              |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | -------- | ------------------------------------------------------------ |
| 实现 scope 静态检查        | `git diff f3281ad3^..f3281ad3 --name-only -- backend/ specs/schema/ scripts/`                                                       | **0**    | 仅 `path_compat.py`、`raw_store.py`                          |
| migration 回归（间接幂等） | `uv run pytest tests/test_schema_migration.py -q --basetemp=.trellis/tasks/round3v-rawstore-atomic-write/.audit-sandbox/pytest-mig` | **0**    | `..........` **10 passed**                                   |
| init_db 两遍幂等           | —                                                                                                                                   | **SKIP** | 只读 Audit + 零 migration diff；由 migration pytest 间接覆盖 |
| kill migrate 异常          | —                                                                                                                                   | **N/A**  | 无 migration 改动                                            |

### 3.2 本地文件 I/O 可靠性（STOR 主判据）

| 步骤                          | 命令                                                                                                                     | exit  | 关键输出 / 证据                                                                             |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------ | ----- | ------------------------------------------------------------------------------------------- |
| RawStore 切片全绿             | `uv run pytest tests/test_raw_store.py -q --basetemp=.trellis/tasks/round3v-rawstore-atomic-write/.audit-sandbox/pytest` | **0** | **`31 passed`**（2026-06-28 本审计员独立复跑）                                              |
| 写失败不泄漏目标              | 含于上表                                                                                                                 | —     | `test_save_midWriteFailure_*`、`test_writeBytesAtomic_*`                                    |
| 同路径 replace 失败保留原字节 | 含于上表                                                                                                                 | —     | `test_writeBytesAtomic_preexistingTarget_*`、`test_save_midWriteFailure_whenTargetExists_*` |
| temp 清理                     | 含于上表                                                                                                                 | —     | `test_writeBytesAtomic_writeFailure_cleansTemp`；glob `.*.tmp.*` 为空                       |
| 同 content 幂等               | 含于上表                                                                                                                 | —     | `test_save_repeatedSameContent_isIdempotent`（Execute `9.4-green.txt` 一致）                |
| production DB 写探测          | 静态：`raw_store.py` 无 `duckdb`/`WriteManager`/`ConnectionManager` import                                               | —     | **无生产库写入口**                                                                          |

### 3.3 可恢复性 / 运维 runbook

| 检查项              | 结论                    | 证据                                                  |
| ------------------- | ----------------------- | ----------------------------------------------------- |
| 孤儿 temp 运维说明  | **已闭合（A7-NB-01）**  | `repair-evidence/orphan-tmp-runbook.md`               |
| fsync 性能权衡      | **已文档化（A6 交界）** | `repair-evidence/perf-tradeoff-note.md`               |
| Execute repair 验证 | 与审计一致              | `repair-evidence/repair-verification.txt` — 31 passed |
| Zero-open repair    | **0 OPEN**              | `repair-evidence/zero-open-signoff.md`                |

---

## 4. 计划外发现

| ID  | 发现                                                           | 严重度                 | 说明                                                                                                            |
| --- | -------------------------------------------------------------- | ---------------------- | --------------------------------------------------------------------------------------------------------------- |
| F1  | SIGKILL / 断电可能在 `unlink` 前留下 `.{name}.tmp.{pid}.{hex}` | **NON-BLOCKING**       | `write_bytes_atomic` 已 best-effort 清理；runbook §运维动作已覆盖；正常 replace 成功无残留                      |
| F2  | 未做父目录 fsync                                               | **NON-BLOCKING**       | ponytail 注释 + `perf-tradeoff-note.md`；B02_03 §4 禁止 Windows 依赖 POSIX-only directory fsync                 |
| F3  | `write_bytes` 非原子 API 仍存在                                | **NON-BLOCKING**       | RawStore 主路径已原子化；其他调用方（`test_path_compat`）非证据链主写路径；若未来生产写绕过 RawStore 须单独审计 |
| F4  | 分支 `conftest.py` 含 R3H/R3G bootstrap                        | **NON-BLOCKING（A7）** | 与 STOR scope 无关；仅写 `.audit-sandbox/` fixture YAML；建议主会话 merge 前拆分或标注来源                      |
| F5  | 全量 `uv run pytest -q` 环境红（ResourceGuard 等）             | **NON-BLOCKING（A7）** | `adversarial-audit-report.md` 已记录；**非** migration/raw 数据面；A5 负责全绿门禁                              |

**对抗搜索声明：** 已对照 `specs/schema/`、`migrations/`、`init_db.py`、`datasource_registry/`、`file_registry.py`、`write_manager`、`duckdb_and_parquet.md` §2.3 raw 路径、`backup_and_recovery.md`；除上表外无计划外 DB 污染或 migration 面。

---

## 5. 判定

| 维度                      | 判定             | 理由                                                            |
| ------------------------- | ---------------- | --------------------------------------------------------------- |
| **AUDIT.plan A7**         | **PASS**         | 无 production DB 写；变更限于 sandbox 可验证的 raw 文件原子 I/O |
| DBA migration adjunct     | **PASS（间接）** | 零 schema/migration diff；migration pytest 10/10                |
| 文件 I/O 可恢复性 adjunct | **PASS**         | 失败清理 + 同路径保护有测试；孤儿 temp runbook 已闭合           |
| **A7-NB-01**              | **CLOSED**       | `orphan-tmp-runbook.md`                                         |

### 移交主会话 / 其他维度

- **VR-STOR-001** registry 行闭合由 coordinator merge `registry_proposed_delta.yaml`（A7 不判 registry 三件套直接改动）。
- **F4** `conftest` 非 STOR diff — 建议 merge 协调时与 Plan QC 文档一并审阅。
- **F5** 全量 pytest — A5/A9 门禁；不阻塞 A7 PASS。

---

## 6. 参考命令（sandbox 复现）

```bash
cd quant-monitor-desk-wt-b3v-stor
SANDBOX=.trellis/tasks/round3v-rawstore-atomic-write/.audit-sandbox

# A7 静态：实现 scope
git diff f3281ad3^..f3281ad3 --name-only -- backend/ specs/schema/ scripts/

# RawStore 切片（主判据）
uv run pytest tests/test_raw_store.py -q --basetemp=$SANDBOX/pytest

# migration 间接回归
uv run pytest tests/test_schema_migration.py -q --basetemp=$SANDBOX/pytest-mig
```

---

_A7 只读审计完成。未修改仓库代码。_
