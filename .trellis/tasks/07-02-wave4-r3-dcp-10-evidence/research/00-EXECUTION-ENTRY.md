# R3-DCP-10 执行入口 — 路由地图（Execute SSOT）

> **任务目录：** `.trellis/tasks/07-02-wave4-r3-dcp-10-evidence/`  
> **活卡：** `EXTERNAL-INDEX.md` → `R3_DCP_10_LAYER5_EVIDENCE_BINDING.md`  
> **协议：** Plan v4.1

---

## 1. 目的 · 价值 · 完成条件

| 维度 | 内容 |
| --- | --- |
| **目的** | 一条 P0 factual evidence：真 fetch bundle → Layer5 provenance 可断言 |
| **价值** | Wave 4 G5 绑真源；`ACC-LAYER-E2E-LIVE-001` **G5 子集** |
| **P0 竖切** | `cn_equity_daily_bar` · `mootdx` · `sh.600519` · `security_bar_1d` |
| **完成条件** | S00–S03 绿 · Audit PASS · `uv run pytest -q` |
| **不在范围** | 全 instrument 矩阵 · evidence_chain DB · L3/L4 全链 · web_search 真 API |

---

## 2. 约束 · 规则

| 类别 | 约束 |
| --- | --- |
| ADR-031 | P0 锚点 + provenance 字段映射表 |
| ADR-028/027 | clean 表 · live env-gate |
| 金路径 | raw → clean → Layer5；WriteManager only |
| 参考 | `reference-adoption-dcp10.md`；禁止 EasyXT fallback |
| GitNexus | impact + detect_changes |

---

## 3. 验证命令

```bash
uv run pytest tests/test_layer5_evidence_foundation.py tests/test_mootdx_incremental_e2e.py -q
uv run pytest -q
python .trellis/scripts/task.py validate-plan-freeze .trellis/tasks/07-02-wave4-r3-dcp-10-evidence
```

Execute 证据：`research/execute-evidence/sNN-green.txt`

---

## 4. ADR 索引

| ADR | 标题 | 切片 |
| --- | --- | --- |
| `docs/decisions/ADR-031-dcp10-layer5-evidence-provenance-binding.md` | Layer5 provenance P0 + mapping | S01–S03 |
| `docs/decisions/ADR-028-dcp05-tier-a-clean-domain-extension.md` | clean 表 SSOT | S02 |
| `docs/decisions/ADR-027-r3h08-product-live-env-gate.md` | live 门控 | optional |

---

## 5. Research manifest

### §5.1 Bundle 文件（全部 research/*.md）

| 文件 | 用途 |
| --- | --- |
| `plan-boot.md` | P0 boot |
| `project-overview.md` | 架构概览 |
| `gitnexus-summary.md` | impact |
| `reference-adoption-dcp10.md` | L1/L2/L3 + **provenance 映射表 §4** |
| `to-issues-slices.md` | 切片 AC |
| `plan-task-breakdown.md` | 任务分解 |
| `plan-spec.md` | 功能规格 |
| `plan-context.md` | must-read manifest |
| `plan-doubt-review.md` | 质疑记录 |
| `integration-audit.md` | Plan 5d |
| `plan-consolidation.md` | 5e 打包 |
| `plan-audit-dcp10.md` | Plan 对抗审计 |
| `EXTERNAL-INDEX.md` | 包外索引 |
| `00-EXECUTION-ENTRY.md` | 本文件 |

### §5.2 Execute must-read（硬门禁）

§5.1 全部 + EXTERNAL-INDEX §A + ADR-031 + 活卡 §1–§5 + `to-issues-slices.md` 当前切片

### §5.3 执行情境路由

| 情境 | 路由 |
| --- | --- |
| 改 provenance 映射 | `reference-adoption-dcp10.md` §4 · ADR-031 |
| 改 bundle helper | `evidence_bundle.py` · S01 |
| 写 e2e | `to-issues-slices.md` S02 · `test_mootdx_incremental_e2e.py` |
| 读 raw/bundle | `cn_market.py` · `raw_store.py` |
| 改 foundation/lineage | `foundation.py` · `lineage.py` · gitnexus impact |
| 台账 G5 | `待修复清单.md` · S03 |
| Trellis | `plan-consolidation.md` · validate-execute-handoff |

---

## 6. GAP

| GAP | 交付 |
| --- | --- |
| `frozen/*.md` | freeze-task-card |
| `execute-evidence/*` | 各切片 GREEN |
| `execute-reference-read-evidence.md` | S01 RED 前 |

---

## 7. 下一刀

`to-issues-slices.md` § **S00-BOOT** → **S01-PROVENANCE-MAP**

## D. 机器路由

权威数据在 **`context_pack.json`**（本任务根目录）。 由 `context_router.py --task` 写入；本段不重复列举。
