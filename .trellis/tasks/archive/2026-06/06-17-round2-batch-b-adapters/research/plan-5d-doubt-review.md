# Phase 5d — doubt-driven-development 对抗审查

> 主会话 · CLAIM → DOUBT → RECONCILE · 2026-06-17

---

## Step 1 — CLAIM

**CLAIM:** Batch B skeleton 通过 `FetchPort` 注入 + `SkeletonAdapterBase` 统一 RawStore 写盘，可在不联网、不新增依赖的前提下满足 contract rule 2，且不与 Batch A `BaseDataAdapter.fetch` 模板冲突。

**WHY:** 若 skeleton 各自实现 raw 路径或绕过 `fetch()`，将破坏 fetch_log 不变量并重复 Batch A 已测逻辑。

---

## Step 2 — ARTIFACT + CONTRACT

**ARTIFACT:** MASTER §6 `SkeletonAdapterBase` + `FetchPort` 设计；§8.1–8.5 逐步切片。

**CONTRACT:**

- 继承 `BaseDataAdapter`；禁止 WriteManager
- SUCCESS 必有 raw 文件证据
- 测试 mock 仅外部 port；registry 用真实 YAML/fixture
- pytest 全绿；无新依赖

---

## Step 3 — DOUBT（对抗清单）

| # | 质疑 | 严重度 |
|---|------|--------|
| D1 | `RawStore.save` 用 `as_of` 段 — request 无 as_of 时默认值是否稳定？ | P1 |
| D2 | 五 adapter 复制粘贴 `_fetch_impl` | P2 |
| D3 | factory 在 import 时拉 heavy 依赖 | P1 |
| D4 | SUCCESS raw 文件未清理导致 tmp_path 泄漏 | P2 |
| D5 | QMT AUTH 与 SUCCESS 双路径测试遗漏 | P1 |
| D6 | yahoo `validation_only` 生产误用 Primary | P2 |

---

## Step 4 — RECONCILE

| 发现 | 处置 | MASTER 修订 |
|------|------|-------------|
| D1 | `_resolve_as_of(req)` 冻结：优先 `req.end_time[:10]`，否则 UTC 日 | §6.2 |
| D2 | 共享 `SkeletonAdapterBase` 单一 `_fetch_impl` | §6.1 |
| D3 | factory lazy import 各类 | §6.3 |
| D4 | 测试用 `tmp_path` data_root；不依赖 prod `data/` | §8.0 conftest |
| D5 | §8.3 强制 AUTH + SUCCESS 两测 | §8.3 |
| D6 | §8.5 断言 registry `validation_only` + 文档注释 | §8.5 |

**Verdict:** PASS_WITH_FIXES — 已全部写入 MASTER v1.0

---

## Step 5 — STOP

三轮内无新 P0；停止对抗循环。
