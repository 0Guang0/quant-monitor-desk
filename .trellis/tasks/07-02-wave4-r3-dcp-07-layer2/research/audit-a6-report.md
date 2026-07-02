# Audit A6 — Performance（R3-DCP-07 Layer2 跨资产真 clean）

> **维：** A6 · performance-engineer + doubt-driven-development  
> **协议：** plan_protocol_version 4.1  
> **任务：** `07-02-wave4-r3-dcp-07-layer2`  
> **Worktree：** `quant-monitor-desk-wt-dcp07`  
> **日期：** 2026-07-02  
> **模式：** Audit（只读，无 commit、无改码）

---

## 维度证据

### Boot / 范围

| 项 | 证据 |
| --- | --- |
| AUDIT.plan §2 A6 | **G2 MODULE_COMPLETION（主会话）** — 非 performance 维度 |
| EXECUTION_INDEX §2.1 | 仅 `uv run pytest …` 复验命令；**无** smoke / 内存 / `--durations` 冻结阈值 |
| ENTRY §1 完成条件 | S00–S02 绿 · Audit PASS · pytest 全绿 — **无 perf AC** |
| 活卡 §5 AC | clean 读 + lineage + pytest — **无** SLA / smoke / ResourceGuard 门禁 |
| AUDIT.plan §1 PASS 门槛 | L2-VIX clean e2e · lineage 可断言 · pytest 全绿 |

### 权威层级（`audit-adversarial-authority.md`）

| 级别 | 来源 | 与本维结论 |
| --- | --- | --- |
| 第一级 | `frozen/R3_DCP_07_LAYER2_CROSS_ASSET.md` · ADR-032 · `layer2_cross_asset_sensor.md` | 竖切正确性 / clean 绑定；未定义吞吐或延迟 SLO |
| 第二级 | `agents/performance-engineer.md` · `AUDIT.plan.md` §2 | A6 槽位已覆写为 **MODULE_COMPLETION 主会话**；perf 无冻结指标 → **SKIP** |
| 第三级 | `EXECUTION_INDEX.md` §2.1 · `implement.jsonl` | 验收 = pytest exit 0（委托 A8）；**无 perf 冻结行** |

**对抗性注记：** 活卡、ENTRY、INDEX §2.1 均未定义 `production_equivalent_smoke.py`、内存峰值、`ResourceGuard` 新语义或 p95 延迟。按 performance-engineer 模板无法填可 PASS/FAIL 的「指标 \| 阈值 \| 实测」perf 表；**SKIP** 为 Plan 覆写决策（A6 委派主会话），非遗漏。

### 实现路径 vs 性能特征（静态审阅）

| 组件 | 触发时机 | I/O / CPU 特征 | 数据量级上界 |
| --- | --- | --- | --- |
| `Layer2CleanObservationReader.read_observations` | e2e / 未来 replay | `WHERE indicator_id = ?` + `ORDER BY publish_timestamp ASC LIMIT ?` | `P0_ROW_CAPS["L2-VIX"]=120` |
| `resolve_read_limit` | reader 入口 | `min(requested, cap)` | 默认 120 行 |
| `CrossAssetSnapshotBuilder.build_daily_snapshots` | S01 e2e | 既有 `ResourceGuard`；本分支未改 guard 语义 | 单日观测子集 |
| `Layer2SnapshotWriter.write_daily_snapshot` | S01 e2e | 单 snapshot + lineage INSERT | 1 行级写 |
| Registry `production_clean_replay` | 测试加载 | YAML fixture 读；非调度热环 | P0 单资产 |

**SQL 片段（有界读）：**

```sql
SELECT … FROM axis_observation WHERE indicator_id = ? [AND publish_timestamp <= ?]
ORDER BY publish_timestamp ASC LIMIT ?
```

### 独立复验（pytest durations · 参考 only）

```text
uv run pytest tests/test_layer2_clean_reader.py tests/test_layer2_vix_clean_e2e.py -q \
  --basetemp=.audit-sandbox/pytest-a6 --durations=15
→ 6 passed, exit 0
```

| 测例 | call 耗时 | 说明 |
| --- | --- | --- |
| `test_layer2CleanReader_respectsRowCap` | 1.76s | seed 200 行；断言 ≤120 — cap 纪律测 |
| `test_layer2_vix_clean_e2e_*` | 1.20s | 40 行种子 + snapshot/lineage 写 |
| `test_layer2CleanReader_readsVixclsFromAxisObservation` | 1.14s | 40 行种子 |

> Plan **未冻结**单测耗时基线；上表仅供计划外扫描备忘，**不构成** PASS/FAIL 门禁。

### performance-engineer checklist（Audit 模式）

| 检查项 | 状态 | 说明 |
| --- | --- | --- |
| Baseline 有证据来源 | **N/A** | Plan 未冻结 perf 命令 |
| EXPLAIN/profile/smoke | **N/A** | 无 smoke 挂载点；SQL 为点查 + LIMIT |
| 优化后同一命令对比 | **N/A** | 无优化项 |
| sandbox 数据量级与 Plan 一致 | **PASS** | tmp_path 隔离库；种子 40/200 行 |
| 全量 pytest 无无关回归 | **委托 A8** | 本维仅跑 DCP-07 子集 |

### §3.6 证据表（SKIP 专用）

| 指标 | 阈值（Plan 冻结） | 实测 | 证据 |
| --- | --- | --- | --- |
| DCP-07 pytest 子集 | exit 0（委托 A8） | 6 passed | `uv run pytest tests/test_layer2_clean_reader.py tests/test_layer2_vix_clean_e2e.py -q` |
| 最慢 call（row cap 测） | **未冻结** | 1.76s | `--durations=15` 参考 |
| smoke 端到端 | **未冻结** | **未测** | SKIP |
| ResourceGuard 新语义 | **未冻结** | **未改** | 既有 `CrossAssetSnapshotBuilder` 路径 |
| 内存峰值 MB | **未冻结** | **未测** | fixture 级 |

---

## SKIP 理由（与 AUDIT.plan §2 A6 一致）

> Plan 原文：**「G2 MODULE_COMPLETION（主会话）」** — A6 审计槽位已委派主会话完成 G2 评级证据（`MODULE_COMPLETION_RATING.md` · S02 repair ledger），**非** performance-engineer 冻结阈值验收。

### 五条证实

1. **无 perf AC** — 活卡 §5、ENTRY §1、`to-issues-slices.md` S00–S02 均未列 smoke、内存、延迟或 batch perf gate。
2. **INDEX §2.1 无冻结行** — 仅三条 pytest 复验命令；与 DCP-05/06 同类竖切一致。
3. **A6 维度覆写** — AUDIT.plan §2 将 A6 标为 MODULE_COMPLETION 主会话职责；perf 子代理无 Plan 内 PASS/FAIL 标尺。
4. **scope 排除重 I/O** — 活卡 §6：非 L2 全矩阵、非 L3–L5 全链、非 FRED live primary；单传感器 replay e2e。
5. **实现为有界读** — `P0_ROW_CAPS` + SQL `LIMIT`；空行 fail-closed，无 EasyXT 式无界 fallback。

### 计划外 perf 风险扫描

> 按 `audit-adversarial-authority.md`：**即使 SKIP，仍须扫描** hot path、无界 I/O、批大小/内存尖峰。

| 面 | 扫描 | 发现 | 结论 |
| --- | --- | --- | --- |
| Hot path | `clean_observation_reader.py` · e2e 路径 | 单资产 replay；非 API/调度热环 | **无新增 hot path** |
| 无界 I/O | SQL + `resolve_read_limit` | `indicator_id` 过滤 + cap 120 | **无全表扫** |
| 批大小 / 内存 | 200 行 seed cap 测 | Python 循环 ≤120 `CrossAssetObservation` | **有界** |
| ResourceGuard | `snapshot_builder.py` | 本分支未改 guard 调用语义 | **无新增尖峰** |
| smoke / nightly | grep diff | 未挂载 `production_equivalent_smoke.py` | **与 Plan 一致** |

**结论：** 本分支不存在需登记为 finding 的计划外 perf 阻断项；SKIP 合理。

### DOUBT

| 疑点 | 结论 |
| --- | --- |
| SKIP 是否遗漏 smoke？ | **否** — AUDIT.plan §2 + INDEX §2.1 双重无 perf 阈值 |
| row_cap 120 是否在 live 量级不足？ | **阶段外** — 竖切 replay；与 Layer1 VIXCLS cap 对齐；扩资产时须随 K1 whitelist 升级 |
| 1.76s cap 测是否回归？ | **否** — 无冻结基线；200 行种子属边界测 intentionally |
| MODULE_COMPLETION 是否算 A6 perf？ | **否** — 主会话职责；本报告仅 perf 子维 |

---

## §维度裁决

**SKIP**

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

已对抗搜索：`AUDIT.plan.md` §2 A6 · `EXECUTION_INDEX.md` §2.1 · `research/00-EXECUTION-ENTRY.md` §1/§3 · `to-issues-slices.md` S00–S02 · `backend/app/layer2_sensors/clean_observation_reader.py`（`P0_ROW_CAPS` / SQL LIMIT）· `tests/test_layer2_clean_reader.py` · `tests/test_layer2_vix_clean_e2e.py` · `CrossAssetSnapshotBuilder` ResourceGuard 既有路径 · `production_equivalent_smoke` / `performance_limits` grep — **无 perf finding**。
