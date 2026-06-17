# Audit Report — 06-17-round2-batch-b-adapters

## 1. 元信息

| 字段 | 值 |
|------|-----|
| slug | `06-17-round2-batch-b-adapters` |
| GitNexus 刷新 | 2026-06-17 · 7.pre |
| 摘要文件 | `research/gitnexus-audit-summary.md` |
| Execute handoff | `validate-execute-handoff` exit 0 |
| Audit 模型 | composer-2.5-fast（A1–A8） |

---

## 2. 维度验证汇总（AUDIT.plan §2 · 7.0）

| 维 | 验证命令/检查 | 环境 | 隔离 | 结果 | 证据 |
|----|---------------|------|------|------|------|
| A1 | trellis-check + check.jsonl + DECISIONS §9 + F01/F02 | local | 无写 | **PASS** | §3.1 · 25 pytest + ruff 绿 |
| A2 | ponytail-review `adapters/` | — | — | **PASS** | §3.2 · net -11 lines optional |
| A3 | grep WriteManager/requests/httpx/secret | local | 无写 | **PASS** | §3.3 · P0 清洁 |
| A4 | code-review SkeletonAdapterBase + PortError | — | — | **PASS** | §3.4 · 五轴无阻塞 |
| A5 | AC-1..10 trace-ac + audit-sandbox FileRegistry | local / audit-sandbox | 独立 DATA_ROOT | **PASS** | §3.5 · 最低分 4 |
| A6 | SKIP — skeleton 无 perf SLA | — | — | **SKIP** | §3.6 |
| A7 | init_db×2 + ci_ingestion_smoke | audit-sandbox | `.audit-sandbox/data` | **PASS** | §3.7 · 幂等 exit 0 |
| A8 | pytest test_adapter_skeletons 全文件 | audit-sandbox | `.audit-sandbox/pytest` | **PASS** | §3.8 · 25/25 |

### Execute §10 证据索引（只读引用）

| Tier | Execute 证据路径/摘要 |
|------|----------------------|
| A | cov 93.72% · ruff 0 · grep WriteManager 0 · `research/execute-evidence/8.6-green.txt` |
| B | init_db×2 幂等 · ci_ingestion_smoke ok @ `data/` |
| C | prod-path pytest 200 passed |

---

## 3. 分维度详情（A1–A8）

### 3.1 A1 · Spec — **PASS**

| 检查项 | 结果 | 证据 |
|--------|------|------|
| trellis-check Steps 1–6 | PASS | diff 12 文件 + adapters 未跟踪包 |
| DECISIONS §9 Batch B 偿还 | PASS | F01 FileRegistry · F02 cninfo EMPTY |
| adversarial F01/F02 | PASS | skeleton_base register + UnpublishedPort |
| pytest + ruff | PASS | 25 passed · ruff 0 |
| GitNexus create_adapter | PASS | 仅 2 测试 caller · 无 ghost 依赖 |

### 3.2 A2 · 过度工程 — **PASS**

| Finding | 严重度 |
|---------|--------|
| `_utc_now_iso()` 与 base_adapter 重复 | Info · **可修复** |
| `UnavailableClientPort` 薄包装 | Info · **可修复** |
| `UnpublishedPort` 薄包装 | Info · **不修复**（MASTER §6.4 冻结） |

**net: -11 lines possible** → Repair 后约 -8 lines（保留 UnpublishedPort）

### 3.3 A3 · 安全 — **PASS**

| 检查 | 结果 |
|------|------|
| WriteManager/requests/httpx/secret grep | 0 命中 |
| 硬编码 URL / SQL | 0 |
| 路径穿越 | RawStore._safe_segment 缓解 |

**观察项（不修复 · 真实 Port 阶段）：** PortError.message 透传凭证风险；生产须显式注入 FetchPort + env 密钥。

### 3.4 A4 · 代码质量 — **PASS**

PortError 六态 → FetchResult.status → fetch_log.error_type 映射正确；模板 fetch 无真实 HTTP。

**Nit（不修复）：** PortErrorStatus vs FetchStatus 独立 Literal — Batch C 类型统一。

### 3.5 A5 · 完成情况 — **PASS**

| AC# | 分数 | 备注 |
|-----|------|------|
| AC-1..7, AC-9 | 5 | 完整追溯链 |
| AC-8 | 4 | Execute 8.6 证据；Audit 未 fresh 全库 cov |
| AC-10 | 4 | cninfo 测缺 fetch_log 显式断言 · **可修复** |

audit-sandbox：`pytest -k FileRegistry` exit 0。

### 3.6 A6 · 性能 — **SKIP**

理由：skeleton 层无 hot path / SLA（AUDIT.plan §2.2）。

### 3.7 A7 · 运维 — **PASS**

| Command | exit |
|---------|------|
| `QMD_DATA_ROOT=.audit-sandbox/data python scripts/init_db.py` ×2 | 0 · applied none |
| `QMD_DATA_ROOT=.audit-sandbox/data python scripts/ci_ingestion_smoke.py` | 0 · fetch_log + source_registry |

### 3.8 A8 · 测试缺口 — **PASS**

全文件 25/25；Red Flags 均有测试或跨维覆盖（A3 grep · A7 smoke）。

---

## 4. 风险与结论（A9 · 主会话）

### 4.1 Repair 项评估（可修复 vs 不修复）

#### 可修复（本 Repair 执行）

| ID | 来源 | 问题 | 修复方案 | 风险 |
|----|------|------|----------|------|
| R-1 | A2/A4 | `_utc_now_iso()` 重复 | skeleton_base 从 base_adapter 导入 | **低** — 同模块私有 helper |
| R-2 | A2 | `UnavailableClientPort` yagni | 删除类；QMT 测试改用 `FailingPort(AUTH_FAILED, …)` | **低** — 仅测试引用 |
| R-3 | A5/A8 | cninfo 测缺 fetch_log.error_type | 补 assert `EMPTY_RESPONSE` + `empty` | **低** — 纯测试增强 |

#### 不修复（记录原因）

| ID | 来源 | 问题 | 不修复理由 | 风险若强改 |
|----|------|------|------------|------------|
| D-1 | A2 | 删除 `UnpublishedPort` | **MASTER §6.4 / AC-10 冻结语义命名**；grill-me + 对抗审计 F02 显式要求 | 破坏 DECISIONS GPT-NOT-PUBLISHED 可读性 |
| D-2 | A4 | PortErrorStatus ↔ FetchStatus 共享类型 | Batch C 架构决策；当前测试已防 drift | 过早抽象、跨层耦合 |
| D-3 | A3 | 真实 Port 凭证/错误消息策略 | skeleton 无 outbound 网络；Batch C/D vendor Port 阶段 | 防御性 wrapper 违背「修根因」 |
| D-4 | A3/A4 | `_resolve_as_of` ISO 日期校验 | RawStore._safe_segment 已防路径穿越；畸形日期为业务语义 | 额外校验可能误拒合法输入 |
| D-5 | A5 | AC-8 fresh 全库 cov 在 Audit 重跑 | Execute 8.6-green 已有 200 passed / 93.72%；Repair 复验 §10 即可 | 重复劳动，非代码债 |

### 4.2 结论

- [x] **PASS** — Repair R-1..R-3 已关闭 · §5 复验 PASS · Phase 9 Finish
- [ ] **FAIL**
- [ ] **PASS**（无 §4.3）

### 4.3 修复项（→ Repair 执行）

| ID | 维度 | 问题 | 根因修复 | 优先级 | 状态 |
|----|------|------|----------|--------|------|
| R-1 | A2/A4 | `_utc_now_iso` 重复 | 导入 base_adapter | P3 | **已关闭** |
| R-2 | A2 | UnavailableClientPort yagni | 删类 + FailingPort | P3 | **已关闭** |
| R-3 | A5/A8 | cninfo fetch_log 断言缺口 | 补测试 assert | P3 | **已关闭** |

### 4.4 Deferred（用户批准 · 不修复）

| ID | 问题 | 理由 | 后续任务 |
|----|------|------|----------|
| D-1 | UnpublishedPort 保留 | MASTER §6.4 冻结 | — |
| D-2 | 类型别名统一 | Batch C | 013 Batch C |
| D-3 | Port 密钥/错误消息 | 无真实 HTTP | vendor Port 实现 |
| D-4 | as_of ISO 校验 | RawStore 已够 | 按需 Batch C |
| D-5 | Audit fresh cov | Execute 证据充分 | — |

---

## 5. Repair 复验（Phase 8）

| 项 | 结果 | 证据 |
|----|------|------|
| §4.3 R-1..R-3 全部关闭 | **PASS** | skeleton_base 删重复 helper；fetch_port 删 UnavailableClientPort；cninfo 测补 fetch_log |
| audit-sandbox A7 | **PASS** | init_db×2 `applied none` · ci_ingestion_smoke exit 0 @ `.audit-sandbox/data` |
| audit-sandbox A8 | **PASS** | `pytest test_adapter_skeletons --basetemp=.audit-sandbox/pytest` → **25 passed** |
| **MASTER §10 Tier A** | **PASS** | pytest 200 passed · cov **93.78%** ≥75% · ruff 0 · WriteManager grep 0 |
| **MASTER §10 Tier B** | **PASS** | `data/` init_db×2 幂等 · ci_ingestion_smoke exit 0 |
| **MASTER §10 Tier C** | **PASS** | `QMD_DATA_ROOT=data pytest -q` exit 0 |

**GitNexus detect_changes（Repair 后）：** 变更符号仍限于 adapters + conftest + 测试；无新增 ghost 依赖。

**复验 PASS → Phase 9 Finish 就绪**
