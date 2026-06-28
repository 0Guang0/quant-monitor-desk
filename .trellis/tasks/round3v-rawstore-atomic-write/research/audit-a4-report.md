# A4 audit-quality — B3V-STOR RawStore Atomic Write

> Dimension: Code Quality (A4 only)  
> Scope: `f3281ad3` 实现 diff + 当前 `fix/round3v-rawstore-atomic-write` 分支 HEAD  
> Worktree: `../quant-monitor-desk-wt-b3v-stor`  
> Skills: `code-review-and-quality` + `doubt-driven-development`  
> Authority: `agents/code-reviewer.md` · `agents/audit-adversarial-authority.md` · `B02_03_rawstore_atomic_write.md`  
> Mode: **只读**（无代码修复）

---

## Verdict: **PASS**

`write_bytes_atomic` 与 `RawStore.save` 接线符合任务卡 §2–§6：`same-dir temp` → `flush`/`fsync` → `os.replace`；失败路径清理 temp；既有路径布局与 `content_hash` 命名未变。先前 A4 **BLOCKING**（`test_save_midWriteFailure_whenTargetExists` 用不同 content 导致不同 hash 路径）已在 `f3281ad3` zero-open repair 闭合：现用**同 content 二次 save + replace fail**，helper 层亦有预置 dest 覆盖失败单测。`tests/test_raw_store.py` 31 项全绿；触及文件 ruff 通过。无 P0 逻辑/质量阻塞。

---

## 审查范围

| 文件 | 变更摘要 |
|------|----------|
| `backend/app/storage/path_compat.py` | 新增 `write_bytes_atomic`；保留非原子 `write_bytes` |
| `backend/app/storage/raw_store.py` | `save` 改调 `write_bytes_atomic`（单行替换） |
| `tests/test_raw_store.py` | +8 用例：helper 成功/三失败路径、save crash、幂等、csv |
| `tests/test_path_compat.py` | 未改；仍用 `write_bytes` 测 extended path（非证据链） |
| `tests/conftest.py`（分支 HEAD） | bootstrap fixture 直写 `.audit-sandbox`（非 STOR 生产路径） |

**实现提交：** `f3281ad3` · **合并：** `2a496af7`

---

## 轴评分（1–5）

| 轴 | 分 | 理由 |
|----|----|------|
| Correctness | 5 | 原子写语义正确；crash/覆盖失败/幂等路径有分层单测；Windows extended path 经 `to_extended_path` 贯穿 temp 与 dest |
| Readability | 5 | 单行接线 + ponytail 天花板注释；import 分组清晰 |
| Architecture | 5 | helper 放 `path_compat`、校验留 `RawStore`；未扩散全仓替换 `write_bytes`（符合 gitnexus 策略） |
| Error handling | 4 | 主异常路径 temp 清理完整；次级 `unlink` 失败静默（见 A4-02） |
| Test quality | 4 | 新增用例五字段中文齐全；parquet `file_type` 落盘仍无专属用例（见 A4-05） |

---

## §3.4 发现表

| 轴 | ID | 发现 | 阻塞? | 证据 |
|----|-----|------|-------|------|
| Correctness | A4-01 | **已闭合** — 首轮 A4 BLOCKING：`whenTargetExists` 测不同 content → 不同 hash 路径，未覆盖「同路径 replace 失败」；repair 后同 content 二次 save + monkeypatch `os.replace` | — | `tests/test_raw_store.py:648-670`；`f3281ad3` |
| Error handling | A4-02 | `write_bytes_atomic` 清理 temp 时 `except OSError: pass`（`path_compat.py:69-70`）会吞掉次要 unlink 失败；主异常仍 re-raise，可接受 ponytail 取舍 | NON-BLOCKING | `path_compat.py:66-71` |
| Resource / I/O | A4-03 | ponytail 已声明天花板：无 parent-dir fsync；断电窗口可能遗留 `.name.tmp.pid.hex` 孤儿文件（显式命名=quarantine，非半写目标） | NON-BLOCKING | `path_compat.py:53-54`；`B02_03` §6 |
| Architecture | A4-04 | `write_bytes`（非原子）仍存在且 `test_path_compat.py` 仍使用；证据落盘仅经 `RawStore.save`→atomic，符合 Playbook「最小面」 | NON-BLOCKING | `path_compat.py:45-46`；`test_path_compat.py:57` |
| Test | A4-05 | `_EXT_MAP` 含 `parquet`，但全库无 `file_type="parquet"` 的 `RawStore.save` 单测；实现类型无关，回归风险低 | NON-BLOCKING | `raw_store.py:16`；对抗搜索 `tests/**` 无 parquet save |
| Test | A4-06 | 无并发双进程同路径写入单测；`os.replace` 同内容竞态末写仍同字节，计划未要求 | NON-BLOCKING | 计划外边界 |
| Maintainability | A4-07 | `except BaseException` 宽于 `Exception`，确保 KeyboardInterrupt 等也触发 temp 清理后 re-raise；符合 fail-safe 意图 | 信息性 | `path_compat.py:66` |

---

## 计划外发现

| ID | 场景 | 若只按 MASTER §8 / §9 用例测会漏什么 | 严重度 |
|----|------|----------------------------------------|--------|
| OP-01 | 进程在 `fsync` 后、`os.replace` 前断电 | 目标仍 absent/旧内容；可能留孤儿 temp（非截断目标） | NON-BLOCKING（ponytail 已文档化） |
| OP-02 | 调用方跳过 `is_relative_to_data_root` 直接调 `write_bytes_atomic` | helper 不校验沙箱；当前唯一生产调用方 `RawStore.save` 已校验 | NON-BLOCKING |
| OP-03 | `conftest` bootstrap 用 `Path.write_bytes` 物化 fixture | 非 RawStore 证据链；与 STOR AC 无关 | 信息性 |
| OP-04 | 全量 `pytest -q` 在 worktree 有 R3G 等无关失败（见 execute-evidence） | STOR 子集绿 ≠ prod-path 全绿；属 A5 门禁 | 信息性（非 A4 阻断） |

**对抗搜索声明：** 已对照 `f3281ad3` diff、`B02_03` §4 forbidden、`path_compat.write_bytes_atomic` 全分支、`RawStore.save` 校验链、新增 8 测 + 既有 save 回归、gitnexus-summary MEDIUM blast radius 调用方列表、首轮 BLOCKING 修复 diff。

---

## DOUBT（对抗性）

| Claim | Attack | Result |
|-------|--------|--------|
| 「写中途失败不留半写目标」 | monkeypatch `os.replace` / `open.write` 抛错 | **成立** — helper 三失败路径 + save 集成测绿 |
| 「已有目标时 replace 失败不损坏原字节」 | 曾用不同 content 测错路径 | **repair 后成立** — `test_writeBytesAtomic_preexistingTarget_*` + `test_save_midWriteFailure_whenTargetExists_*` |
| 「同 content 重复 save 幂等」 | 第二次仍全量 atomic 写（无 skip） | **成立** — 同路径同字节；符合 AC-STOR-04 语义 |
| 「Windows 长路径仍可用」 | 仅 NT 测 `test_save_windowsLongPath_*` | **成立**（本机非 NT 时 skip） |
| 「temp 失败必清理」 | unlink 二次失败 | **部分成立** — 主异常可见；孤儿 temp 仅当 unlink 全失败（极罕见） |

**必选 DOUBT 结论（file:line）：** `path_compat.py:53-54` — 无 parent-dir fsync 时，断电可留**完整 temp 副本**而非半写目标；任务卡 §6 要求「temp 清理或 quarantine 显式命名」，当前 `.hash.json.tmp.pid.hex` 满足 quarantine，但运维需知孤儿文件可安全删除。不构成 BLOCKING；若需更强 durability 须后续 slice 加 dir fsync（任务卡 §4 禁止 Windows 依赖 POSIX-only dir fsync）。

---

## Checklist（code-reviewer.md）

- [x] 无 P0 逻辑/安全阻塞
- [x] 错误处理可观测（失败 re-raise；temp glob 断言无残留）
- [x] 风格与邻近模块一致（ponytail 注释、stdlib、无新依赖）
- [x] 测试变更保留 purpose（中文五字段）
- [x] 判定基于 diff 与 pytest，非覆盖率 KPI

---

## 验证结果

| 检查 | 命令 | 结果 |
|------|------|------|
| Pytest 子集 | `uv run pytest tests/test_raw_store.py -q --basetemp=.audit-sandbox/pytest` | **PASS**（31 passed） |
| Ruff | `uv run ruff check backend/app/storage/raw_store.py backend/app/storage/path_compat.py tests/test_raw_store.py` | **All checks passed** |

---

## 做得好的地方

- 最小 diff：`RawStore.save` 仅一行 `write_bytes`→`write_bytes_atomic`；blast radius 可控。
- temp 命名含 `pid` + `secrets.token_hex(4)`，同目录并发冲突概率低且可识别。
- `to_extended_path` 同时用于 temp 与 dest，Windows 深路径与原子写一致。
- ponytail 天花板注释诚实标注 RAM 全载与无 dir fsync，避免过度承诺。
- 测试分层：helper 三失败路径 + `RawStore.save` 集成，覆盖 AC-STOR-01..04。
- zero-open repair 精准修复首轮 A4 测错路径，未削弱断言意图。

---

## A4 门控结论

| 项 | 值 |
|----|-----|
| 维度 | A4 Code Quality |
| 结论 | **PASS** |
| BLOCKING 计数 | 0（首轮 1 项已 repair 闭合） |
| 建议跟进 | A4-05 parquet save 回归可并入 A8 或后续 hardening；A4-03 孤儿 temp 可写入 ops runbook（可选） |

*审计时间：2026-06-28 · 只读 · 未修改生产代码*
