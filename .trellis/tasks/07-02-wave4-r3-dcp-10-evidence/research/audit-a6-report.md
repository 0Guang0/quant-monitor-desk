# Audit A6 — Performance（R3-DCP-10 Layer5 证据绑真源）

> **维：** A6 · performance-engineer  
> **任务：** `07-02-wave4-r3-dcp-10-evidence`  
> **协议：** plan_protocol_version 4.1  
> **Worktree：** `quant-monitor-desk-wt-dcp10`  
> **日期：** 2026-07-02  
> **模式：** Audit（只读；无 commit、无改码）

---

## 维度证据

### Boot / 权威对照

| 级别 | 来源 | 与本维结论 |
| --- | --- | --- |
| 第一级 | `docs/modules/layer5_security_evidence.md` · ADR-031 · `specs/contracts/layer5_evidence_contract.yaml` | provenance 映射与 fail-closed 契约；**无**时长/内存/吞吐 SLA |
| 第二级 | `AUDIT.plan.md` §2 · `EXECUTION_INDEX.md` §2.1 · `to-issues-slices.md` · `agents/performance-engineer.md` | **无冻结 perf 阈值**；验收委托 pytest 正确性（A5/A8） |
| 第三级 | `frozen/R3_DCP_10_LAYER5_EVIDENCE_BINDING.md` · `research/00-EXECUTION-ENTRY.md` | 薄指针 + 切片 AC；scope = provenance bridge + mootdx e2e |

### AUDIT.plan §2 A6 与 perf 维度关系

| 项 | 内容 |
| --- | --- |
| AUDIT.plan §2 A6 原文 | `K1 layer5 plan 对齐（可选 note）` — **非** smoke/ResourceGuard/延迟门禁 |
| ENTRY §2.1 复验命令 | 仅 `uv run pytest …` + `loop_maintain.py --fix`；**无** `production_equivalent_smoke.py`、内存峰值、`--durations` 冻结行 |
| 活卡 / slices AC | S01 provenance 映射 · S02 mootdx e2e · S03 ACC G5 台账；**零条** perf AC |
| PASS 门槛（AUDIT.plan §1） | provenance e2e 绿 · 三哈希对齐 bundle · pytest 全绿 — **正确性**，非性能 |

**结论：** 本票 perf 维度无可对照的冻结指标；按派发指令「无 perf AC 可 SKIP」及 `performance-engineer.md` DOUBT 纪律，A6 perf **SKIP**。

### SKIP 五条证实

1. **无 hot path / SLA** — 交付为 `layer5_evidence/provenance.py` 桥接 + `bundle_layer5_provenance` 字段扩展；无 FastAPI 路由、无调度热环、无 `production_equivalent_smoke_budget.yaml` 挂载点。
2. **桥接路径 O(1)** — `build_source_provenance_from_bundle` 仅 dict 取值 + 元组构造；无 DB 扫描、无网络、无 DataFrame 分配。
3. **e2e 有界 I/O** — S02 测单标的 `sh.600519` 单日增量 replay；`tmp_path` 隔离；raw bundle 经 `glob` 取末条 JSON（fixture 级目录）。
4. **任务卡 scope 排除 perf 优化** — `plan-spec.md` / `to-issues-slices.md` 禁止 bypass WriteManager、禁止无 ADR migration；**未**要求 smoke 基线或 ResourceGuard 新阈值。
5. **INDEX / AUDIT 无 perf 冻结行** — §2.1 仅列 pytest 复验；无法填可 PASS/FAIL 的「指标 \| 阈值 \| 实测」perf 表。

### 实现路径 vs 性能特征（计划外扫描）

| 组件 | 触发时机 | I/O / CPU | 数据量级上界 |
| --- | --- | --- | --- |
| `build_source_provenance_from_bundle` | Layer5 记录构造 | 纯 Python；常量级字段映射 | 单 bundle dict |
| `bundle_layer5_provenance` | 同上 | 4 条 dataset id 字符串拼接 | 单 bundle |
| `test_layer5_provenance_bridge.py` | pytest | 读 replay fixture JSON 一次 | 固定 fixture |
| `test_mootdxBarClean_layer5Provenance_*` | pytest e2e | 单次 incremental + 单行 clean SELECT + 单 raw JSON | P0 竖切 1 标的 1 日 |
| ResourceGuard | e2e 测 | `monkeypatch` → `(OK, "")` **仅测试** | 不改动产线 guard 语义 |

### performance-engineer checklist

| 检查项 | 状态 | 说明 |
| --- | --- | --- |
| Baseline 有证据来源 | **N/A** | Plan 未冻结 perf 命令 |
| EXPLAIN/profile/smoke | **N/A** | 桥接无 SQL；无 smoke 挂载 |
| 优化后同一命令对比 | **N/A** | 无优化项 |
| sandbox 数据量级与 Plan 一致 | **PASS** | replay fixture + tmp_path；与 P0 竖切一致 |
| 全量 pytest 无无关回归 | **委托 A8** | 本维 durations 参考 only |

### §3.6 证据表（参考 · 非门禁）

| 指标 | 阈值（Plan 冻结） | 实测 | 证据 |
| --- | --- | --- | --- |
| `test_layer5_provenance_bridge.py` | exit 0（A8） | 3 passed | Execute `s01-green.txt` |
| `test_layer5_mootdx_bar_clean_e2e.py` | exit 0（A8） | 1 passed | Execute `s02-green.txt` |
| 两模块合并 `--durations=10` | **未冻结** | 4 passed；最慢 call **1.68s** | `uv run pytest tests/test_layer5_provenance_bridge.py tests/test_layer5_mootdx_bar_clean_e2e.py --durations=10 -q` → exit 0 |
| `production_equivalent_smoke.py` | **未冻结** | **未测** | Plan 未挂载 |
| 内存峰值 / ResourceGuard HARD_STOP | **未冻结** | **未测** | 桥接未改 guard 契约；e2e 测 monkeypatch |

---

## §维度裁决

**SKIP**

**SKIP 理由：** R3-DCP-10 为 Layer5 provenance 绑真源（正确性 / 追溯契约）；`AUDIT.plan` §2 A6 为 layer5 plan 对齐备注，**非** performance 冻结阈值；`EXECUTION_INDEX` §2.1、`to-issues-slices`、活卡均无 perf AC。无法建立可 PASS/FAIL 的 perf 对照表，故 perf 维 SKIP（非遗漏）。

---

## 计划内问题

| ID | P | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | --- | --- | --- | --- | --- |
| — | — | 无 | — | — | — | — |

---

## 计划外发现

| ID | P | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | --- | --- | --- | --- | --- |
| — | — | 无 | — | — | — | — |

已对抗搜索：`backend/app/layer5_evidence/provenance.py` · `evidence_bundle.py` `bundle_layer5_provenance` · `tests/test_layer5_provenance_bridge.py` · `tests/test_layer5_mootdx_bar_clean_e2e.py` · `AUDIT.plan.md` §1–§2 · `EXECUTION_INDEX.md` §2.1 · `to-issues-slices.md` · ADR-031 · `plan-spec.md` Never 边界 · pytest `--durations=10` 独立复跑。

**扫描结论：** 无新增生产 hot path；桥接无全表扫/无界 fetch；e2e ResourceGuard bypass 仅限 pytest。最慢 call 1.68s 为单标的 replay 增量，**无冻结基线**，仅作参考，**不构成 finding**。
