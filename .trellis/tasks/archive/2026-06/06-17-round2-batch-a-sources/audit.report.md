# Audit Report — 06-17-round2-batch-a-sources

> **状态：** Phase 7 Audit 完成（A1–A8 + A9）· 待 Phase 8 Repair（可选 §4.3）→ Phase 9 Finish  
> **模型：** 各维子 agent 均使用 **Composer 2.5 fast**（`composer-2.5-fast`）

## 1. 元信息

| 字段 | 值 |
|------|-----|
| GitNexus 刷新 | 2026-06-17 · MCP query/context（7.pre） |
| 摘要文件 | `research/gitnexus-audit-summary.md` |
| Execute DATA_ROOT | `data/`（只读索引） |
| Audit sandbox | `.audit-sandbox/data` |
| A5 fresh pytest | **160 passed**, exit 0（主会话 2026-06-17 复跑） |
| A7 fresh init_db | run1: 001–004 applied；run2: `none (up to date)` |

---

## 2. 维度验证汇总（7.0 · A9）

| 维 | 验证命令/检查 | 环境 | 隔离 | 结果 | 证据 |
|----|---------------|------|------|------|------|
| A1 | trellis-check + DECISIONS + check.jsonl | local | 无写 | **PASS** | §3.1 |
| A2 | ponytail-review datasources/ | — | — | **PASS** | §3.2 |
| A3 | WriteManager grep + SQL/YAML 静态 | local | 无写 | **PASS** | §3.3 |
| A4 | code-review-and-quality | — | — | **PASS** | §3.4 |
| A5 | AC-1..8 追溯 + pytest -q | local | 无写 | **PASS** | §3.5 |
| A6 | N/A（无 hot path SLA） | — | — | **SKIP** | §3.6 |
| A7 | init_db ×2 @ audit-sandbox | audit-sandbox | 独立 | **PASS** | §3.7 |
| A8 | pytest -k Legacy/NETWORK/disabled | audit-sandbox | tmp | **PASS** | §3.8 |

**总判定：** **PASS**（无 P0/P1 阻塞；§4.3 含 P2 可选项）

### Execute §10 证据索引（只读）

| Tier | Execute 证据摘要 |
|------|-------------------|
| A | pytest **160/160**；ruff datasources 绿（Execute 补账） |
| B | init_db @ `.audit-sandbox/data` 幂等；004 在 schema_version |
| C | Batch A 无独立 smoke；schema + contract 测试覆盖 prod-path 代理 |

---

## 3. 分维度详情

### 3.1 A1 — audit-spec（Composer 2.5 · trellis-check）

**结论：PASS**

- check.jsonl 六项对照：DECISIONS §4、data_adapter_contract、data_sources §5.3–5.6 均一致
- Ghost 依赖：datasources 仅 yaml/pydantic/stdlib/项目内模块；无 WriteManager/vendor SDK
- GitNexus：`SourceRegistry` 5 importers；`BaseDataAdapter` 仅测试子类 extend
- Spec 偏离：无未授权偏离（`fetch(con=...)` keyword-only 与 MASTER §6.5 一致）

### 3.2 A2 — audit-ponytail（Composer 2.5 · ponytail-review）

**结论：PASS**

**ponytail-review：**

```
base_adapter.py:L13-14: shrink: _utc_now_iso 可内联 (~3 lines)
source_registry.py:L79-99: shrink: _record_to_db_row 可内联 (~8 lines)
fetch_result.py:L9-17: shrink: FetchStatus 别名 (~7 lines)
fetch_log.py:L30: yagni: 无状态类 — MASTER §6.4 冻结类名，非必删
```

**net:** ~8–12 行 optional shrink。**无 §4.3 必删 bloat。**

### 3.3 A3 — audit-security（Composer 2.5 · security-and-hardening）

**结论：PASS**（1× P2 防御缺口，不阻塞）

| 检查 | 结果 |
|------|------|
| `grep WriteManager` in datasources | 0 match ✅ |
| sync_to_db / fetch_log INSERT | 全参数化 ✅ |
| yaml.safe_load | ✅ |
| **P2** SourceRegistry.load 无 path confinement | 对比 raw_store 有 `is_relative_to` ⚠️ |

**§4.3 可选：** SEC-A3-1 — `load()` 增加 `resolve()` + specs 根目录约束 + 回归测

### 3.4 A4 — audit-quality（Composer 2.5 · code-review-and-quality）

**结论：PASS**

- 模板方法：`fetch` 成功/失败/异常均 1 条 fetch_log；pre-impl 失败 0 条
- LegacyRoleError：Shadow/Emergency + top-level key
- registry + adapter 测试 **43/43** 绿
- 非阻塞：`get_domain_roles` 仍抛 KeyError；primary allowed_domains 未在 loader 校验

### 3.5 A5 — audit-completion（Composer 2.5 · verification-before-completion）

**结论：PASS**（主会话 fresh 验证后）

| AC | 分数 | 判定 |
|----|------|------|
| AC-1..AC-8 | 均 ≥4 | PASS |

**Fresh evidence（主会话）：**

```text
pytest -q → 160 passed, exit 0
```

AC-8 Tier B 由 A7 init_db 证据补全。

### 3.6 A6 — audit-perf

**SKIP** — AUDIT §2.2：源注册/契约层无 hot path SLA。

### 3.7 A7 — audit-ops（Composer 2.5 · shell）

**结论：PASS**（主会话 fresh 验证）

```text
QMD_DATA_ROOT=.audit-sandbox/data
Run1: init_db: applied ['001_foundation', '002_registry_hardening', '003_resource_guard_metrics', '004_ingestion_sources']
Run2: init_db: applied none (up to date)
```

**表验证：** `source_registry`, `fetch_log` 存在于 `.audit-sandbox/data/duckdb/quant_monitor.duckdb`  
**schema_version：** 001–004 各一行，003 resource_guard 仍在链上。

### 3.8 A8 — audit-test-gap（Composer 2.5 · test-engineer）

**结论：PASS**

```text
pytest ... -k "Legacy or NETWORK or disabled" --basetemp=.audit-sandbox/pytest
→ 5 passed, 38 deselected
```

MASTER §7 八项 Red Flag 均有测试或 A3 静态覆盖。

**§4.3 建议补测（非阻塞）：**

- registry 级 `assert_domain_allowed` 经 `fetch()` 的 0-log 路径
- `get_domain_roles` 未知 domain 行为显式锁定
- 文档化 `.audit-sandbox/pytest` 目录需预建

---

## 4. A9 风险汇总与 §4.3 Repair 索引

| ID | 优先级 | 维度 | 描述 | 建议动作 |
|----|--------|------|------|----------|
| SEC-A3-1 | P2 | A3 | SourceRegistry.load 缺 path confinement | Batch A 可顺带；Batch B+ 若暴露 API 升为 P1 |
| QA-A8-1 | Medium | A8 | fetch + registry domain 拒绝 0-log 对称测 | 补 1 测 |
| QA-A8-2 | Low | A8 | get_domain_roles unknown domain | 补 1 测 |
| A2-shrink | Info | A2 | ~8–12 行 optional inline | Repair 可选，非必做 |

**无 P0/P1 阻塞项。** Phase 8 Repair 已完成（见 §5）。

---

## 5. Phase 8 Repair 复核（2026-06-17）

| ID | 动作 | 复核 |
|----|------|------|
| SEC-A3-1 | `_resolve_registry_path()` — YAML 须在 `PROJECT_ROOT` 下 | ✅ `test_load_pathOutsideProjectRoot_raises` |
| QA-A8-1 | `test_fetch_registryDomainNotAllowed_raisesBeforeImpl_andWritesNoFetchLog` | ✅ BroadDomainAdapter + fundamental 0-log |
| QA-A8-2 | `test_getDomainRoles_unknownDomain_raisesKeyError` | ✅ |
| A2-shrink | 跳过（Info 级 optional inline） | — |

**Repair 后验证：**

```text
pytest -q → 163 passed, exit 0
ruff check backend/app/datasources → All checks passed
QMD_DATA_ROOT=data init_db ×2 → applied none (up to date), exit 0
QMD_DATA_ROOT=.audit-sandbox/data init_db → up to date
```

---

## 6. Audit DoD

- [x] 7.pre → `research/gitnexus-audit-summary.md`
- [x] §2 各行（A6 SKIP）已执行
- [x] A9 §4 已写

---

## 7. 子 agent 派发记录

| 维 | Agent | Skill | 模型 | 子 agent 初判 | A9 终判 |
|----|-------|-------|------|---------------|---------|
| A1 | audit-spec | trellis-check | composer-2.5-fast | PASS | PASS |
| A2 | audit-ponytail | ponytail-review | composer-2.5-fast | PASS | PASS |
| A3 | audit-security | security-and-hardening | composer-2.5-fast | PASS | PASS |
| A4 | audit-quality | code-review-and-quality | composer-2.5-fast | PASS | PASS |
| A5 | audit-completion | verification-before-completion | composer-2.5-fast | FAIL* | **PASS** |
| A6 | — | — | — | SKIP | SKIP |
| A7 | audit-ops | — | composer-2.5-fast | FAIL* | **PASS** |
| A8 | audit-test-gap | — | composer-2.5-fast | PASS | PASS |

\* 子 agent Shell 无法采集 pytest/init_db 输出；主会话 A9 fresh 复跑后升格 PASS。
