# A2 Ponytail Audit — B3V-STOR RawStore Atomic Write

> **Task:** `round3v-rawstore-atomic-write` · Playbook `B3V-STOR` / `B3V-C03`  
> **Agent:** audit-ponytail (A2) · **只读**  
> **Worktree:** `C:\Users\Guang\Desktop\quant-monitor-desk-wt-b3v-stor`  
> **Branch:** `fix/round3v-rawstore-atomic-write`  
> **Authority:** `agents/audit-a2-ponytail.md` + `agents/audit-adversarial-authority.md`  
> **Skills:** ponytail ladder（`.cursor/rules/ponytail.mdc` + MASTER §0.3a）  
> **AC 对照:** B02_03 · MASTER §2 AC-STOR-01..04 · §8 触及文件  
> **审计日期:** 2026-06-28

---

## Verdict: **PASS**

生产路径净增 **~28 行**（`path_compat.py` +26、`raw_store.py` 接线 ~+2 net），与 MASTER「一处 helper + save 最小一行替换」完全一致。无新依赖、无单调用 wrapper factory、无计划外抽象层。**阻塞项 0**；下列均为可选收缩或计划外 scope 注记（建议级）。

Repair 已闭合首轮 A2-NB-01（顶行 `import raw_store`）与 A2-NB-02（`ponytail:` 天花板注释）；本审独立复验后维持 PASS。

---

## git diff --stat（A2 checklist）

### 任务实现提交 `f3281ad`（生产 + 测试，相对父提交）

| 文件                                 | Δ 行                   | A2 备注                                   |
| ------------------------------------ | ---------------------- | ----------------------------------------- |
| `backend/app/storage/path_compat.py` | **+26**                | `write_bytes_atomic`（AC-STOR-01 交付物） |
| `backend/app/storage/raw_store.py`   | +8 / −6（**net ~+2**） | `write_bytes` → `write_bytes_atomic` 接线 |
| `tests/test_raw_store.py`            | **+188**               | S1–S4 + repair 增补；五字段注释占比较大   |
| Trellis / loop / docs（任务包）      | +2001 / −226           | 任务轨道工件，非生产 bloat                |
| **生产小计**                         | **~+28 net**           | 符合 ponytail 最小 diff                   |

### 当前分支相对 `master`（`master...HEAD`）

| 文件                                                           | Δ 行                     |
| -------------------------------------------------------------- | ------------------------ |
| `.trellis/tasks/.../research/plan-gate-evidence-2026-06-28.md` | +95                      |
| `.trellis/tasks/.../research/plan-qc-report.md`                | +50 / −16                |
| `.trellis/tasks/.../research/wave0-ssot-alignment.md`          | +47                      |
| `tests/conftest.py`                                            | **+18**                  |
| `MASTER.plan.md`                                               | ±2                       |
| **合计**                                                       | **+196 / −16，net +180** |

### 工作区未提交

| 文件                | Δ 行                                                                 |
| ------------------- | -------------------------------------------------------------------- |
| `tests/conftest.py` | +13（`_ensure_r3g_fred_authorization_bootstrap` 与分支提交重叠部分） |
| `task.json`         | 状态/metadata 格式化                                                 |

**MASTER §8 触及文件：** `path_compat.py`、`raw_store.py`、`test_raw_store.py` — 与 `f3281ad` 生产 diff 一致；**`conftest.py` 不在 §8 allowed 列表**（见计划外 PO-STOR-01）。

---

## DOUBT（≥20 行可简化？）

| 攻击                                                                       | 和解                                                                                                                                                                                         |
| -------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 「`write_bytes_atomic` +26 行是否过度？」                                  | B02_03 §2 明确要求 same-dir temp + flush/fsync + `os.replace` + fail cleanup；已复用 `to_extended_path`（梯级 2），非平行新 I/O 栈                                                           |
| 「`test_raw_store.py` +188 是否 setup 膨胀？」                             | 8 项原子/crash 测 × 五字段 docstring ≈ 40 行属项目测试规范；**replace 失败类 4 测重复 `_boom` + `monkeypatch.setattr(os, "replace", ...)` 样板约 20 行可参数化/小 fixture 收缩**（见 A2-03） |
| 「`test_writeBytesAtomic_writeFailure_cleansTemp` ~35 行 open 猴子补丁？」 | 覆盖 write 阶段失败（非 replace），与 A8-D01 对齐；缩短会削弱「写一半再抛错」语义，**保留**                                                                                                  |
| 「分支 `conftest.py` +18？」                                               | 第三份 `_ensure_*_bootstrap` 拷贝粘贴模式，**非 B3V-STOR scope**（PO-STOR-01）                                                                                                               |

**DOUBT 结论：** 生产代码 **无** ≥20 行且无 AC 依据的整块可删；测试层 **1 处** 可选收缩（replace-fail 样板，估 −20~25 LOC）。**不构成 A2 阻塞。**

---

## §3.2 候选删改表

| 候选删改（file:line）                                                                                                     | ponytail 梯级                                                         | 是否阻塞                       |
| ------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- | ------------------------------ |
| `path_compat.py:49-71` — `write_bytes_atomic` 整函数                                                                      | 梯级 1（B02_03 / AC-STOR-01 **必须建**）                              | **不算**                       |
| `raw_store.py:74` — `write_bytes_atomic(dest_path, content)` 单行接线                                                     | 梯级 6（已最小）                                                      | **不算**                       |
| `path_compat.py:53-54` — `ponytail:` 天花板注释                                                                           | 梯级 7（repair 已闭合 A2-NB-02）                                      | **不算**（已满足）             |
| `tests/test_raw_store.py:531,548,571,597` — 4 处函数内 `from ... import write_bytes_atomic`                               | 梯级 5（可顶行合并 1 import）                                         | 建议（~4 LOC，未达 20）        |
| `tests/test_raw_store.py:552-555,577-580,637-640,664-667` — 4× 相同 `_boom` + `monkeypatch.setattr(os, "replace", _boom)` | 梯级 2（`@pytest.fixture` 或 `_fail_replace(monkeypatch, msg)` 复用） | 建议                           |
| `tests/test_raw_store.py:539-583` — `replaceFailure` 与 `preexistingTarget_replaceFailure` 结构相似                       | 梯级 2（`@pytest.mark.parametrize` 合并 dest 预置/断言分支）          | 建议（估 −20~25 LOC）          |
| `tests/conftest.py:72-81` — `_ensure_r3g_fred_authorization_bootstrap`                                                    | 梯级 2（与 `_ensure_prediction_live_*` 同模式；应归 R3G 切片非 STOR） | 建议（**scope 注记**）         |
| `path_compat.py:66-71` — `except BaseException` + temp unlink 嵌套 try                                                    | 梯级 3（stdlib 无更短等价；与 A4 错误模型一致）                       | 建议（与 A4 交叉，非 A2 阻塞） |

---

## 计划外发现（对抗性搜索）

已读：`path_compat.py`、`raw_store.py`、`test_raw_store.py`（524–710 原子段）、`B02_03_rawstore_atomic_write.md` §4 forbidden、`MASTER.plan.md` §8、`repair-evidence/zero-open-signoff.md`、分支 `conftest.py` diff、`test_path_compat.py`（仍用非原子 `write_bytes`，符合 scope）。

| ID         | 发现                                                                                          | 与 MASTER 关系                                             | 阻塞                                                   |
| ---------- | --------------------------------------------------------------------------------------------- | ---------------------------------------------------------- | ------------------------------------------------------ |
| PO-STOR-01 | 分支 `tests/conftest.py:72-81` 新增 R3G FRED auth bootstrap — **不在** B3V-STOR allowed files | MASTER §8 仅列三文件；属并行 R3G 环境便利                  | **NON-BLOCKING**（scope 泄漏；合并前应剥离或单开切片） |
| PO-STOR-02 | `write_bytes()` 仍保留且 `test_path_compat.py` 直用 — RawStore 已走 atomic                    | 任务卡未要求全局替换 `write_bytes`                         | NON-BLOCKING                                           |
| PO-STOR-03 | 无 parquet 原子写专项测                                                                       | A8 已 defer；非 ponytail bloat                             | NON-BLOCKING                                           |
| PO-STOR-04 | `secrets.token_hex(4)` temp 命名 — 极端并发同 pid 碰撞理论存在                                | ponytail 注释已声明天花板；`orphan-tmp-runbook.md` 闭合 A7 | NON-BLOCKING                                           |

**计划外 bloat：** 未发现计划外新模块、新依赖或仅单调用 factory；**唯一 scope 外增量为 `conftest.py` bootstrap（PO-STOR-01）**。

---

## 与 A4 交叉引用

| A2 项                                                                   | A4 接续                                                  |
| ----------------------------------------------------------------------- | -------------------------------------------------------- |
| `except BaseException` 宽捕获 + pass `OSError` on unlink                | A4 错误模型：是否应窄化为 `Exception`（unlink 失败吞掉） |
| replace-fail 测已由 repair 闭合（helper 异 content + save 同 content）  | A4 首轮 BLOCKING 已 CLOSED；A2 不重复升格                |
| mock `os.replace` 非真实 errno                                          | 与 A8 §6.2 一致；ponytail 单元天花板                     |
| `write_bytes_atomic` docstring「caller must validate path containment」 | A3 路径沙箱；非 A2                                       |

---

## 做得好的地方（ponytail 合规）

- **梯级 1：** 未引入 pyarrow、watchdog 或外部 FS 库；未改 content_hash 命名。
- **梯级 2：** `write_bytes_atomic` 复用既有 `to_extended_path`；`RawStore.save` 仅改一行写调用。
- **梯级 3/4：** `os.replace` + `os.fsync` + `secrets`（stdlib / 已装依赖）。
- **梯级 7：** `ponytail:` 注释标明无 parent-dir fsync、全 payload RAM 天花板。
- **YAGNI：** 无 `AtomicWriter` class、无 registry 框架；`file_registry.py` 未触。
- **Repair 闭合：** `zero-open-signoff.md` A2-NB-01/02 与本审读一致。

---

## §4.3 / 阻塞队列（A2 贡献）

| ID  | Priority | Blocks finish-work? |
| --- | -------- | ------------------- |
| —   | —        | **No**              |

全部 A2 项为 P3 可选收缩或 scope 注记（PO-STOR-01 → 合并协调）。**§4.3 count (A2): 0**

---

## 建议收缩（Audit 不应用）

1. **A2-01：** 将 4 处函数内 `write_bytes_atomic` import 合并为文件顶行（与 `RawStore` import 并列）。
2. **A2-02：** 合并前从 STOR 分支移除或 revert `conftest.py` R3G bootstrap（PO-STOR-01）；由 R3G 切片自有 PR 携带。
3. **A2-03：** `@pytest.mark.parametrize` 或 `_patch_replace_fail(monkeypatch, match)` 合并 replace 失败类 3–4 测（估 −20~25 LOC）。

**估 optional shrink：** ~25–30 LOC（主要为测试样板），占 `test_raw_store.py` 原子段 ~15%；生产路径 **已最小**。

---

## Verification（A2 维度）

| Check                   | Result                                          |
| ----------------------- | ----------------------------------------------- |
| `git diff --stat`       | 已记录（`f3281ad` 生产 + `master...HEAD` 分支） |
| 每候选 file:line + 梯级 | 已列 §3.2                                       |
| A4 交叉                 | 已列                                            |
| 阻塞 vs 建议            | 阻塞 **0** / 建议 **4**                         |
| Build / pytest          | **未跑**（A2 只读；A5/A8 负责）                 |

---

## A2 checklist（模板）

- [x] `git diff --stat` 已记录 Lxx / net lines
- [x] 每候选附 `file:line` + ponytail 梯级
- [x] 与 A4 过度抽象交叉引用
- [x] 阻塞 vs 建议已区分

---

_A2 only · 未执行 A1/A3–A8 · 未改代码 · 2026-06-28_
