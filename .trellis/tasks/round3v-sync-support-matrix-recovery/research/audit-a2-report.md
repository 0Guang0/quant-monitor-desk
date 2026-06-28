# A2 Ponytail Audit — B3V-SYNC Sync Job Support Matrix & Crash-window Recovery

> **Task:** `round3v-sync-support-matrix-recovery` · Playbook `B3V-SYNC` / `B3V-C04`  
> **Agent:** audit-ponytail (A2) · **只读**  
> **Worktree:** `quant-monitor-desk-wt-b3v-sync` · branch `fix/round3v-sync-support-matrix-recovery`  
> **Authority:** `agents/audit-a2-ponytail.md` + `agents/audit-adversarial-authority.md` + `AUDIT.plan.md`  
> **Skills:** ponytail 梯级（`ponytail-review` / `doubt-driven-development` skill 文件不在 worktree；按 `.cursor/rules/ponytail.mdc` + MASTER §0.3a 内联应用）  
> **实现锚点 commit:** `fb1cf4c6`（`feat(sync): B3V-SYNC support matrix, deferred errors, and crash-window recovery`）  
> **AC 对照:** MASTER §2 / §4 / §8（AC-SYNC-001..002、REG、PLAYBOOK）

---

## Verdict: **PASS**

实现 commit 生产路径净增 **~89 行**（`contract.py` 新文件 + orchestrator/runners/YAML 薄改），测试净增 **~311 行**，与 AC-SYNC-002（矩阵 + deferred）、AC-SYNC-001（crash hook + recovery）、§5.3 冻结用例规模匹配。无 factory/registry 框架、无新依赖、无计划外抽象层。**阻塞项 0**；下列均为可选收缩（建议级）。

> **注：** 当前分支相对 `master` 仅含 Plan QC 文档提交；**代码审计以 `fb1cf4c6` 为准**（已合入 master）。worktree 另有 unstaged `tests/conftest.py` +13 行（R3G FRED bootstrap，**非本任务 scope**，见计划外 PO-04）。

---

## git diff --stat（A2 checklist）

### 实现 commit `fb1cf4c6` — MASTER §8 触及文件

| 文件                                            | +       | −      | net      |
| ----------------------------------------------- | ------- | ------ | -------- |
| `backend/app/sync/contract.py`                  | 48      | 0      | +48      |
| `backend/app/sync/orchestrator.py`              | 27      | 8      | +19      |
| `backend/app/sync/runners.py`                   | 8       | 0      | +8       |
| `specs/contracts/sync_job_contract.yaml`        | 14      | 0      | +14      |
| `tests/test_sync_orchestrator.py`               | 271     | 0      | +271     |
| `tests/test_r3x_residual_open_items_closure.py` | 40      | 8      | +32      |
| **合计（§8 组）**                               | **408** | **16** | **+392** |

**生产代码小计：** +97 / −8 → **net +89**

### 当前 worktree unstaged（非实现 commit）

| 文件                | net | 备注                                          |
| ------------------- | --- | --------------------------------------------- |
| `tests/conftest.py` | +13 | R3G FRED auth bootstrap — **B3V-SYNC 计划外** |

---

## DOUBT（≥20 行可简化？）

| 攻击                                               | 和解                                                                                                                                                                                          |
| -------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 「`contract.py` 新文件 +48 是否过度？」            | AC-SYNC-002 要求 `DeferredJobTypeError` + 常量 + YAML loader；`DeferredJobTypeError` 与 `sync_job_contract.yaml deferred_error` 双源 parity 为 ZO-05/06 闭合所必需                            |
| 「`raise_deferred_job_type` 是否多余 wrapper？」   | 原 3 处调用；B3F-SH 后仅剩 `run_full_load` 单调用 — **可内联 1 行**（未达 ≥20 行整块）                                                                                                        |
| 「crash/recovery 测试 +~80 行是否 setup 膨胀？」   | **是** — `test_syncJob_incremental_crashWindow_*` 与 `recoverStuckWriting_*` 共享 monkeypatch、`_orchestrator`、`_crash_after_write`、adapter/config 装配，结构重复 **~35–40 行**（见 A2-04） |
| 「`test_advA3_016` 三份 `SyncJobSpec` 是否重复？」 | **是** — 三份 12 字段 spec 仅 `job_type`/`job_id` 不同，可抽 helper 净减 **~25 行**（见 A2-05）                                                                                               |

**DOUBT 结论：** 至少 **1 处** ≥20 行可简化（crash-window 测试对重复 setup）；生产代码无 ≥20 行且无 AC 依据的整块可删。

---

## §3.2 候选删改表

| 候选删改（file:line）                                                                                                                           | ponytail 梯级                                                             | 是否阻塞       |
| ----------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- | -------------- |
| `tests/test_sync_orchestrator.py:1329-1410` — crashWindow 与 recoverStuckWriting 重复 monkeypatch + `_crash_after_write` + incremental run 装配 | 梯级 2（共享 `@pytest.fixture` 或 `_run_incremental_until_crash` helper） | 建议           |
| `tests/test_r3x_residual_open_items_closure.py:352-381` — 三份 `SyncJobSpec` 仅 job_type 不同                                                   | 梯级 2（复用 `_reserved_job_spec` 或模块级 factory）                      | 建议           |
| `backend/app/sync/contract.py:45-46` — `raise_deferred_job_type` 现仅 `run_full_load` 单调用                                                    | 梯级 5（内联 `raise DeferredJobTypeError(...)`）                          | 建议           |
| `tests/test_sync_orchestrator.py:1245-1261` — `_assert_deferred_job_type_error` 现仅 `full_load` 单测使用                                       | 梯级 5（内联断言或保留以备 reserved 扩展）                                | 建议           |
| `backend/app/sync/contract.py:40-42` — `load_sync_job_contract` 用 `open()`；仓库惯例为 `read_text(encoding="utf-8")`                           | 梯级 3（stdlib 一致风格）                                                 | 建议           |
| `backend/app/sync/orchestrator.py:281-297` — `recover_stuck_writing_job` 缺 `ponytail:` 天花板注释（MASTER §2.4 要求单函数无框架）              | 梯级 7（应标注 ADR-001 窗口假设与升级路径）                               | 建议           |
| `tests/test_b3f_quality_runners.py:14-28` — `_reserved_job_spec` 与 `test_sync_orchestrator.py:1200-1214` 重复                                  | 梯级 2（抽到 `tests/sync_helpers.py` 或 conftest）                        | 建议           |
| `tests/conftest.py:72-81`（unstaged）— `_ensure_r3g_fred_authorization_bootstrap`                                                               | 梯级 1（YAGNI — 非 B3V-SYNC scope，应独立 ticket/worktree）               | 建议（计划外） |
| `backend/app/sync/contract.py` 全文件 +48                                                                                                       | 梯级 1（AC-SYNC-002 / VR-SYNC-002 显式交付）                              | **不算**       |
| `specs/contracts/sync_job_contract.yaml:3-19` — matrix + deferred_error 段                                                                      | 梯级 1（AC-SYNC-002 契约 SSOT）                                           | **不算**       |
| `backend/app/sync/runners.py:501-506` — `post_write_pre_complete_hook` + pytest guard                                                           | 梯级 1（AC-SYNC-001 / ZO-07 fail-closed）                                 | **不算**       |

---

## 计划外发现（对抗性搜索）

已读：`contract.py`、`orchestrator.py`（`run_full_load` / `recover_stuck_writing_job`）、`runners.py`（hook 段）、`sync_job_contract.yaml`、`test_sync_orchestrator.py`（§B3V 段）、`test_r3x_residual_open_items_closure.py`（advA3_016）、`B02_04_sync_job_support_and_recovery.md`（via MASTER trace）、`repair-evidence/zero-open-signoff.md`。

| ID    | 发现                                                                                                                                                                                         | 与 MASTER 关系                                         | 阻塞                     |
| ----- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ | ------------------------ |
| PO-01 | B3F-SH 合并后 `data_quality`/`revision_audit` 已从 reserved→implemented；原三 reserved deferred 测试改为 completion 测试 — **矩阵语义正确演进**，但 MASTER §9.3 文案仍写三 reserved deferred | 后续 batch 合法闭包；Plan 文档滞后                     | 非 A2                    |
| PO-02 | `raise_deferred_job_type` 退化为单调用 wrapper（仅 `run_full_load`）                                                                                                                         | 计划写三 reserved deferred；现仅 `full_load` 仍 defer  | 建议（A2-03）            |
| PO-03 | `recover_stuck_writing_job` 无幂等/并发 guard — 重复调用可能重复 transition                                                                                                                  | MASTER §2.4 ponytail 单函数；ADR-001 假定 ops 手动恢复 | 非 A2（语义 → A4/A5）    |
| PO-04 | worktree unstaged `conftest.py` R3G FRED bootstrap +13 行混入 B3V-SYNC worktree                                                                                                              | 计划 in-scope 不含 R3G auth 物化                       | 建议（应拆 commit/分支） |

**计划外 bloat：** 未发现计划外新模块、新依赖或 ≥20 行无 AC 依据的生产抽象层。测试 setup 重复是唯一达 ≥20 行阈值的收缩点。

---

## 与 A4 交叉引用

| A2 项                                                                               | A4 可能接续                                                                                                 |
| ----------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| `DeferredJobTypeError` 字段与 YAML `deferred_error` 双源维护                        | 契约单源 vs runtime 常量漂移（A4 已有 `test_syncJobContract_deferredErrorYaml_parityWithRuntimeConstants`） |
| `recover_stuck_writing_job` 用 `KeyError`（unknown job）vs `ValueError`（非法状态） | 错误模型一致性 / 调用方可观测性（A4）                                                                       |
| `post_write_pre_complete_hook` guard 复用 `sync_adapter_bypass_allowed()` 命名      | bypass 语义与 hook 守卫是否同义（A4 脆弱耦合）                                                              |
| crash 测试 `except RuntimeError: pass` 吞掉非模拟异常                               | 断言是否过宽（A4/A8）                                                                                       |

---

## 做得好的地方（ponytail 合规）

- **梯级 2：** `recover_stuck_writing_job` 复用既有 `_jobs.transition` + `_cm.reader()`，未新建 recovery 框架（对齐 MASTER §2.4）。
- **梯级 2：** deferred 错误对齐 Round 3F `WriteManager` deferred 文案模式（MASTER §0.3a）。
- **梯级 3：** YAML loader 用 stdlib `yaml.safe_load`；hook guard 用既有 `sync_adapter_bypass_allowed()`。
- **梯级 1：** 未引入 CLI、新依赖或 registry 主文件直接 commit。
- **梯级 7：** hook 有显式 `pytest-only` 文案；recovery 函数体短小。
- **YAGNI：** `runners.py` 仅 +8 行（type alias + 6 行 hook 块），无 speculative pipeline 抽象。

---

## §4.3 / 阻塞队列（A2 贡献）

| ID  | Priority | Blocks finish-work? |
| --- | -------- | ------------------- |
| —   | —        | **No**              |

全部 A2 项为 P3 可选收缩或它维（PO-03 → A4/A5；PO-04 → 分支卫生）。**§4.3 count (A2): 0**

---

## 建议收缩（Audit 不应用）

1. **A2-04：** 提取 `_crash_window_fixture(tmp_path, monkeypatch, job_id)` 或 `_simulate_post_write_crash(orch, spec)`，合并 crash/recovery 两测重复段（估 −30~35 LOC）。
2. **A2-05：** `test_advA3_016` 用 `_reserved_job_spec(job_type, job_id=...)` 替代三份内联 `SyncJobSpec`（估 −25 LOC）。
3. **A2-03：** `run_full_load` 内联 `raise DeferredJobTypeError(...)`，删除 `raise_deferred_job_type`（−2 LOC 生产 + import）。
4. **A2-06：** `recover_stuck_writing_job` 加 `ponytail:` 注释说明单函数 recovery 天花板（无幂等、无分布式锁）。
5. **A2-07：** 将 `_reserved_job_spec` 提升到共享 test helper，消除 `test_b3f_quality_runners.py` 重复。
6. **A2-08：** 勿在 B3V-SYNC worktree 提交 `conftest.py` R3G bootstrap — 独立 R3G ticket。

**估 optional shrink：** ~55–65 LOC（主要为测试），占实现 commit net +392 的 **~15%**。

---

## Verification（A2 维度）

| Check                   | Result                                                   |
| ----------------------- | -------------------------------------------------------- |
| `git diff --stat`       | 已记录（`fb1cf4c6` §8 组 + worktree unstaged）           |
| 每候选 file:line + 梯级 | 已列 §3.2                                                |
| 与 A4 交叉              | 已列                                                     |
| 阻塞 vs 建议            | 阻塞 **0** / 建议 **8**                                  |
| Build / pytest          | **未跑**（A2 只读；A8 负责 Playbook §8.4 + 全量 pytest） |

---

## A2 checklist

- [x] `git diff --stat` 已记录 Lxx / net lines
- [x] 每候选附 `file:line` + ponytail 梯级
- [x] 与 A4 过度抽象交叉引用（已列）
- [x] 阻塞 vs 建议已区分

---

_A2 only · 未执行 A1/A3–A8 · 未改代码_
