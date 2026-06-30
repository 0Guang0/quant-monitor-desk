# A1 Spec / Trace Authority — B3V-STOR RawStore Atomic Write

> **角色：** Audit-A1（audit-spec）  
> **Worktree：** `C:/Users/Guang/Desktop/quant-monitor-desk-wt-b3v-stor`  
> **分支：** `fix/round3v-rawstore-atomic-write`  
> **实现提交：** `f3281ad3`（repair + zero-open）· merge `2a496af7`  
> **审计日期：** 2026-06-28  
> **模型：** composer-2.5  
> **权威：** `agents/audit-a1-spec.md` · `agents/audit-adversarial-authority.md` · `AUDIT.plan.md` · `B02_03_rawstore_atomic_write.md`

---

## 总裁决

| 字段         | 值                                                        |
| ------------ | --------------------------------------------------------- |
| **Verdict**  | **PASS**                                                  |
| **Owned VR** | `VR-STOR-001`（proposed delta only，符合 MASTER §0 边界） |
| **阻塞项**   | 0                                                         |

---

## §3.1 trellis-check 证据表

| 检查项              | 结果             | 证据                                                                                                                                                                           |
| ------------------- | ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1. 变更范围         | PASS             | `git show f3281ad3 --name-only` 仅含 `path_compat.py` · `raw_store.py` · `test_raw_store.py` + 任务工件；**无** `validation_gate.py` · `backend/app/sync/**` · registry 三件套 |
| 1b. 工作区脏文件    | NON-BLOCKING     | `git status`：`tests/conftest.py` 未提交改动为 R3G FRED bootstrap（`_ensure_r3g_fred_authorization_bootstrap`），**不在** B3V-STOR owns 表；建议主会话勿混入 STOR merge        |
| 2. 任务工件         | PASS             | `prd.md` · `MASTER.plan.md` · `research/source-index.md` · `execute-evidence/9.*` 齐全                                                                                         |
| 3. 包上下文         | PASS             | 触及 `backend/app/storage/`；`write_bytes` 保留（`path_compat.py:45-46`），仅 `RawStore.save` 切 atomic（`raw_store.py:74`）                                                   |
| 4. Spec Quality     | PASS（N/A 细项） | `.trellis/spec/` 无 storage 专用 index；实现符合 MASTER §2.1–§2.2 与 B02_03 §4 forbidden                                                                                       |
| 5. 项目检查         | PASS             | `uv run pytest tests/test_raw_store.py -q` → **31 passed**, exit 0；`uv run ruff check backend/app/storage tests/test_raw_store.py` → All checks passed                        |
| 6. 跨层             | PASS（≤2 层）    | Storage 单层 + 测试；未触及 Service/API/UI；`is_relative_to_data_root` 沙箱校验未改（`raw_store.py:72-73`）                                                                    |
| 7. manifest vs diff | PASS             | `audit.jsonl` / `check.jsonl` 点名文件均在 `f3281ad3` 或任务目录；diff 无 manifest 外生产代码                                                                                  |

---

## STOR-01..05 ↔ AC 追溯

| 切片    | AC         | 实现 / 测试                                                                                                                                                                          | 证据                                                                      | 结果     |
| ------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------- | -------- |
| STOR-01 | AC-STOR-01 | `write_bytes_atomic` `path_compat.py:49-71`；`test_writeBytesAtomic_writesCompleteFile` · `test_writeBytesAtomic_replaceFailure_*` · `test_writeBytesAtomic_writeFailure_cleansTemp` | `execute-evidence/9.1-green.txt`                                          | **PASS** |
| STOR-02 | AC-STOR-02 | `RawStore.save` → `write_bytes_atomic(dest_path, content)` `raw_store.py:74`；`_EXT_MAP` / `content_hash` 路径布局未变                                                               | `execute-evidence/9.2-green.txt`                                          | **PASS** |
| STOR-03 | AC-STOR-03 | `test_save_midWriteFailure_*` + helper `test_writeBytesAtomic_preexistingTarget_replaceFailure_preservesOriginalBytes`（repair 闭合 A4 BLOCKING）                                    | `execute-evidence/9.3-green.txt` · `repair-evidence/zero-open-signoff.md` | **PASS** |
| STOR-04 | AC-STOR-04 | `test_save_repeatedSameContent_isIdempotent`                                                                                                                                         | `execute-evidence/9.4-green.txt`                                          | **PASS** |
| STOR-05 | AC-STOR-05 | `research/registry_proposed_delta.yaml` 含 `VR-STOR-001` · `commit_policy: proposed_only_no_direct_registry_commit`                                                                  | `registry_proposed_delta.yaml` L4-27                                      | **PASS** |

### 实现语义核对（`write_bytes_atomic` + `RawStore.save`）

| 要求（B02_03 / MASTER §2.1） | 代码                                                                                                          | 结果 |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------- | ---- |
| 同目录唯一 temp              | `.{dest.name}.tmp.{pid}.{token}` `path_compat.py:57`                                                          | PASS |
| flush + fsync                | `handle.flush()` + `os.fsync` `path_compat.py:63-64`                                                          | PASS |
| `os.replace` 原子替换        | `path_compat.py:65`                                                                                           | PASS |
| 失败清理 temp、目标不动      | `except BaseException` → `unlink(missing_ok=True)` `path_compat.py:66-71`                                     | PASS |
| 无 POSIX-only 目录 fsync     | ponytail 注释声明天花板 `path_compat.py:53-54`                                                                | PASS |
| Windows 长路径               | `to_extended_path` 用于 temp/dest `path_compat.py:58-59`；`test_save_windowsLongPath_writesSuccessfully` 仍绿 | PASS |
| 路径沙箱由 caller 负责       | docstring `path_compat.py:52`；`is_relative_to_data_root` 仍在 `save` 内                                      | PASS |

---

## Trace Authority（AUDIT.plan §0.1 / source-index §A–§C）

| 条目                      | 核对问题                                  | 结果 | 证据                                                                     |
| ------------------------- | ----------------------------------------- | ---- | ------------------------------------------------------------------------ |
| 原始任务卡 B02_03         | scope/AC/Red Flags 进入 MASTER §2/§3/§7？ | PASS | `research/original-plan-trace.md` · MASTER §2.5 AC 表                    |
| task README / input index | Plan 入口合规？                           | PASS | `research/source-index.md` §B manifest 完整                              |
| unresolved coverage       | VR-STOR-001 有 proposed closeout？        | PASS | `registry_proposed_delta.yaml`；未直接 commit 三件套（符合 §0 Must not） |
| round map                 | batch/out-of-scope 与 MASTER §4 一致？    | PASS | B3V-C03 · out: gate/sync/registry commit                                 |
| source-index              | manifest 血缘完整？                       | PASS | `source-index.md` §C 六类 `[x]`                                          |
| omission-check            | 地图倒查无遗漏？                          | PASS | `plan-qc-report.md` §12 对抗性审 PASS                                    |
| integration-ledger        | context packing 一致？                    | PASS | `research/integration-ledger.md` 与 MASTER §0.4 对齐                     |

---

## DOUBT（对抗性 scope）

| 攻击面                               | 搜索范围                                             | 结论                                                                                  | 严重度       |
| ------------------------------------ | ---------------------------------------------------- | ------------------------------------------------------------------------------------- | ------------ |
| 水平改 gate/sync                     | `f3281ad3` file list · grep `validation_gate`/`sync` | 无触及                                                                                | —            |
| production DB 写                     | hardening · `raw_store`/`path_compat` 无 DB import   | 无                                                                                    | —            |
| `content_hash` 命名语义变更          | `raw_store.py:65-70`                                 | 未改                                                                                  | —            |
| FileRegistry 语义变更                | `file_registry.py` 不在 diff                         | 未改                                                                                  | —            |
| 全仓库扩散 `write_bytes_atomic`      | grep backend                                         | 仅 `raw_store.save` 调用                                                              | PASS         |
| GitNexus `write_bytes_atomic` 未索引 | MCP `context`/`impact` → not found                   | Plan 阶段 `research/gitnexus-summary.md` 已记录 RawStore **MEDIUM**；本审计复用该结论 | NON-BLOCKING |

---

## 计划外发现

| ID           | 严重度       | 发现                                                                                                    | 建议                                           |
| ------------ | ------------ | ------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| A1-NB-WT-01  | NON-BLOCKING | 工作区未提交 `tests/conftest.py` R3G FRED bootstrap 不属于 B3V-STOR owns                                | 主会话单独提交或还原，勿与 STOR merge 混卷     |
| A1-NB-WT-02  | NON-BLOCKING | `uv run pytest -q` 全量仍有非 STOR 失败（`execute-evidence/full-pytest-2026-06-28.txt` R3G 对抗审计等） | A5 prod-path 项；**不降级** A1 scope PASS      |
| A1-NB-ADV-01 | NON-BLOCKING | 无 parquet 专项 crash smoke                                                                             | 继承 `adversarial-audit-report.md` ADV-STOR-01 |

**已对抗搜索；无 BLOCKING 计划外项。**

---

## A1 checklist

- [x] trellis-check 步骤 1–7 有证据（上表 + 命令 exit 0）
- [x] diff vs `audit.jsonl` / `check.jsonl` manifest
- [x] Trace Authority 已继承（source-index §A–§C）
- [x] 无 Plan omission（plan-qc §12 PASS）
- [x] GitNexus：MCP 未解析 `write_bytes_atomic`；Plan `gitnexus-summary.md` RawStore MEDIUM 已查并记录

---

## 独立复跑命令（本审计员）

```text
uv run pytest tests/test_raw_store.py -q          → 31 passed, exit 0
uv run ruff check backend/app/storage tests/test_raw_store.py  → exit 0
git show f3281ad3 --name-only                     → 仅 storage + 任务工件
```

---

**A1 裁决：PASS** — `path_compat.write_bytes_atomic` 与 `RawStore.save` 接线符合 B02_03 与 MASTER §2；STOR-01..05 切片可追溯且有 GREEN 证据；无 gate/sync/production DB scope 泄漏。
