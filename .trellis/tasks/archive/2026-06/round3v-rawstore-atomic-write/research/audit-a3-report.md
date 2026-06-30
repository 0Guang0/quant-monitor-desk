# Audit A3 报告 — B3V-STOR RawStore Atomic Write

| 字段     | 值                                                                       |
| -------- | ------------------------------------------------------------------------ |
| 维度     | **A3** Security（静态威胁面 / 信任边界 / 本地 I/O）                      |
| 任务     | `round3v-rawstore-atomic-write` / Playbook **B3V-STOR**                  |
| Worktree | `C:/Users/Guang/Desktop/quant-monitor-desk-wt-b3v-stor`                  |
| 分支     | `fix/round3v-rawstore-atomic-write`                                      |
| 实现提交 | `f3281ad3` fix(storage): B3V-STOR atomic raw write with zero-open repair |
| 审计模式 | **只读**（不改码、不 commit、不写生产 `data/`）                          |
| 模板     | `agents/security-auditor.md` + `agents/audit-adversarial-authority.md`   |
| 日期     | 2026-06-28                                                               |

---

## 1. 审计范围

### 1.1 Trace Authority（AUDIT.plan §0 / §1 / §3）

| 来源                                   | 用途                                                   |
| -------------------------------------- | ------------------------------------------------------ |
| `AUDIT.plan.md` §2 A3                  | 通过条件：路径穿越/沙箱仍有效；既有校验测绿            |
| `MASTER.plan.md` §0 Batch 3V 边界      | owns / must-not（禁 production DB、禁 gate/sync 越界） |
| `B02_03_rawstore_atomic_write.md`      | 任务卡 §4 Forbidden scope                              |
| `BATCH_3V_HARDENING_RULES.md`          | 禁 production 写 / registry 直接 commit                |
| `research/gitnexus-rawstore-impact.md` | RawStore impact MEDIUM（GitNexus 替代查询）            |

### 1.2 Diff 文件（`f3281ad3` vs parent）

| 文件                                 | A3 相关性                                           |
| ------------------------------------ | --------------------------------------------------- |
| `backend/app/storage/path_compat.py` | 新增 `write_bytes_atomic`；temp 命名；fsync/replace |
| `backend/app/storage/raw_store.py`   | `save` 改调原子写；沙箱校验不变                     |
| `tests/test_raw_store.py`            | 路径穿越 / 原子写失败 / 幂等 安全相关用例           |

> 注：`git diff master...HEAD` 当前仅含 Plan 文档与 `tests/conftest.py`；**实现 diff** 以 `git diff f3281ad3^..f3281ad3` 为准（已合并入 master）。

---

## 2. A3 覆写通过条件核对

| 条件（AUDIT.plan §2 A3） | 结果     | 证据                                                                                                                           |
| ------------------------ | -------- | ------------------------------------------------------------------------------------------------------------------------------ |
| 路径穿越/沙箱仍有效      | **PASS** | `_safe_segment` + `is_relative_to_data_root` 未改动；`test_save_pathTraversal_raises` 等仍绿                                   |
| 既有校验测绿             | **PASS** | `uv run pytest tests/test_raw_store.py -q -k "pathTraversal or writeBytesAtomic or midWriteFailure or idempot"` → **8 passed** |
| 无 production DB 写      | **PASS** | diff 无 `WriteManager` / `INSERT` / `UPDATE` / `DELETE`                                                                        |
| 无 live fetch            | **PASS** | diff 无 `https?://`、`enable.qmt`、`enable.xqshare`                                                                            |
| 无密钥进 repo            | **PASS** | 仅 `secrets.token_hex(4)` 用于 temp 文件名熵，非凭据                                                                           |

**A3 覆写结论：PASS**

---

## 3. §3.3 安全发现

### 3.1 威胁面摘要

| 威胁类               | 本 diff 暴露面                     | 结论                                              |
| -------------------- | ---------------------------------- | ------------------------------------------------- |
| 路径穿越 / 任意写    | `RawStore.save` 入参 → `dest_path` | **受控** — 段校验 + `data_root` containment       |
| 半写证据污染         | 崩溃窗口直写目标                   | **缓解** — 同目录 temp + `os.replace`             |
| Temp 孤儿 / 信息泄露 | `.name.tmp.pid.hex` 残留           | **缓解** — `except` 中 `unlink`；runbook 已文档化 |
| 未授权写库           | —                                  | **无新增**                                        |
| SQL 注入             | —                                  | **N/A**（本 slice 无 SQL）                        |
| 密钥 / token 泄露    | —                                  | **无**                                            |
| Live / 外网 fetch    | —                                  | **未触及**                                        |
| 资源滥用（OOM）      | `MAX_RAW_FILE_BYTES` 256 MiB       | **既有护栏保留**                                  |

### 3.2 分级发现表

| ID  | 等级 | BLOCKING | 威胁 | 发现              | 证据           |
| --- | ---- | -------- | ---- | ----------------- | -------------- |
| —   | —    | —        | —    | **无 P0/P1 发现** | 见 §4 静态扫描 |

### 3.3 信任边界（对抗性）

#### `write_bytes_atomic`（`path_compat.py:49-71`）

- **契约：** docstring 明确要求 caller 在调用前验证 path containment（repair 已闭合 A3-P3-01）。
- **实现：** 同目录 temp → `flush` + `os.fsync` → `os.replace`；`except BaseException` 清理 temp。
- **熵：** `secrets.token_hex(4)` + `os.getpid()` 降低 temp 碰撞与可预测性。
- **天花板（ponytail）：** 无 parent-dir fsync；全 payload 在 RAM；断电场景目录元数据可能滞后 — 已注释。

#### `RawStore.save`（`raw_store.py:46-84`）

- `_SEGMENT` 正则拒绝 `..`、`/` 等穿越片段（`source` / `data_domain` / `as_of`）。
- `dest_path.resolve()` 后 `is_relative_to_data_root(dest_path, self.data_root)` — Windows 长路径兼容。
- **唯一生产调用点** 将 containment 校验置于 `write_bytes_atomic` 之前（`L72-74`）。
- `write_bytes_atomic` **未**被其他生产模块 import（仅 `raw_store.py` + 测试）。

---

## 4. DOUBT 静态扫描（可复现）

在实现 diff 生产文件执行 `security-auditor.md` 基线：

```text
# 密钥 / URL
rg -n 'https?://|api[_-]?key|secret|token|password' backend/app/storage/path_compat.py backend/app/storage/raw_store.py
→ path_compat.py:6 import secrets
→ path_compat.py:57 secrets.token_hex(4)   # temp 熵，非凭据

# SQL 拼接
rg -n 'execute\(f|f".*SELECT|f'"'"'.*SELECT' backend/app/storage/path_compat.py backend/app/storage/raw_store.py
→ 0 matches

# 写库 / 迁移
rg -n 'writer\(|apply_migrations|INSERT |UPDATE |DELETE ' backend/app/storage/path_compat.py backend/app/storage/raw_store.py
→ 0 matches

# 危险执行
rg -n 'subprocess|os\.system|eval\(|exec\(' backend/app/storage/path_compat.py backend/app/storage/raw_store.py
→ 0 matches

# Live 源
rg -n 'enable\.qmt|enable\.xqshare|--enable-qmt' backend/app/storage/
→ 0 matches
```

### 4.1 DOUBT 三类对抗搜索

| 类                    | 搜索范围                          | 结果             |
| --------------------- | --------------------------------- | ---------------- | -------------- | ------------------------------------ |
| 1. 硬编码 URL 变体    | `path_compat.py` + `raw_store.py` | **无发现**       |
| 2. JWT / API key 模式 | 同上 + `jwt                       | bearer           | Authorization` | **无发现**（`secrets` 仅 temp 命名） |
| 3. SQL 拼接           | 两 py 文件                        | **N/A / 无发现** |

---

## 5. GitNexus / 影响面

| 项         | 值                                                                                                       |
| ---------- | -------------------------------------------------------------------------------------------------------- |
| 查询       | `research/gitnexus-rawstore-impact.md`（MCP `context(write_bytes_atomic)` 索引未命中，以 Plan 研究为准） |
| Target     | `RawStore` upstream                                                                                      |
| Risk       | **MEDIUM**                                                                                               |
| d=1 调用方 | `ingestion.py`、`file_registry.py`、adapters、`staged_pilot.py`、`interface_probe.py`、测试              |
| A3 结论    | 原子写封装在 `path_compat`；`save` 单行替换；**未扩大信任边界**                                          |

---

## 6. 计划外发现

> 对抗性搜索：若只跑 MASTER §9 用例，下列项仍可能被忽略。

| ID         | 等级 | BLOCKING     | 发现                                                     | 理由                                                                        | 建议                                                                       |
| ---------- | ---- | ------------ | -------------------------------------------------------- | --------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| A3-PLAN-01 | P2   | NON-BLOCKING | `write_bytes_atomic` 自身不 enforce sandbox，依赖 caller | 当前唯一生产 caller 为 `RawStore.save` 且已校验；未来直接调用可能任意路径写 | 保持 helper 为 package-internal；若对外暴露须内置 containment 或 lint 约束 |
| A3-PLAN-02 | P3   | NON-BLOCKING | `kill -9` 于 temp 已写、replace 前可留孤儿 `.tmp.*`      | 概率低；`orphan-tmp-runbook.md` 已闭合                                      | 运维按 runbook 清理；无需本 slice 改码                                     |
| A3-PLAN-03 | P3   | NON-BLOCKING | 无 parquet 专项原子失败测                                | json/csv helper 层已覆盖 replace-fail 语义                                  | 与 `ADV-STOR-01` 一致；parquet 增多时补 smoke                              |
| A3-PLAN-04 | P3   | NON-BLOCKING | mock `os.replace` 不覆盖磁盘满/权限 errno                | 单元级可接受；真实 errno 属集成/运维面                                      | 维持 ponytail 天花板文档                                                   |

**显式声明：** 已按计划外完成对抗搜索；**无 BLOCKING 项**。

---

## 7. 与任务卡 / 契约一致性

| 要求                             | 状态                                                                    |
| -------------------------------- | ----------------------------------------------------------------------- |
| B02 §4 禁止 production DB writes | 满足                                                                    |
| B02 §4 禁止改 content_hash 命名  | 满足（`{hash}.{ext}` 未变）                                             |
| B02 §4 禁止外部文件系统依赖      | 满足（仅 stdlib `os`/`secrets`）                                        |
| AC-STOR-01 原子 helper           | `write_bytes_atomic` + helper 测绿                                      |
| AC-STOR-03 写失败无半写目标      | `test_writeBytesAtomic_*` + `test_save_midWriteFailure_*`               |
| AC-STOR-04 幂等                  | `test_save_repeatedSameContent_isIdempotent`                            |
| 路径穿越防护                     | `test_save_pathTraversal_raises` + `test_save_invalidDataDomain_raises` |
| Repair A3-P3-01 docstring        | **CLOSED**（`path_compat.py:52`）                                       |

---

## 8. 验证结果（A3 静态）

| 项                                    | 结果                                                                                             |
| ------------------------------------- | ------------------------------------------------------------------------------------------------ |
| 静态 rg 基线                          | PASS                                                                                             |
| 路径沙箱 / 穿越测                     | PASS（8/8 子集绿）                                                                               |
| A3 覆写（沙箱有效 / 无 DB / 无 live） | PASS                                                                                             |
| 全量 `uv run pytest -q`               | **未执行**（归 A5 prod-path；首轮 adversarial 报告记录 host ResourceGuard 环境红，与 STOR 无关） |
| TypeCheck / Lint                      | **未执行**（只读 A3）                                                                            |

---

## 9. 总结

| 指标                      | 值                                          |
| ------------------------- | ------------------------------------------- |
| 审阅文件                  | 3（2 生产 py + 1 测试模块相关 diff）        |
| P0/P1 发现                | 0                                           |
| P2/P3 计划外              | 4（均 NON-BLOCKING）                        |
| Repair 开放项（A3 scope） | 0（`zero-open-signoff.md` A3-P3-01 CLOSED） |
| **A3 判定**               | **PASS**                                    |

本 slice 在本地 raw 证据 I/O 路径上符合 AUDIT.plan A3 覆写：路径沙箱与段校验未削弱，原子写降低半写污染风险，未引入 production DB 写、live fetch、SQL 面或密钥暴露。`write_bytes_atomic` 的 caller-trust 模型已由 docstring 与 `RawStore.save` 双重约束；剩余 P2/P3 为未来调用方纪律与运维 hygiene，不构成 merge 阻断。

---

_审计员角色：Audit-A3 · B3V-STOR · 只读_
