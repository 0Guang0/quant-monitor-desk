# R3-DCP-10 — `/to-issues` 垂直切片

> **SSOT：** 切片 AC 仅本文件 · Plan v4.1  
> **P0 竖切：** `cn_equity_daily_bar` · `mootdx` · `sh.600519` · `security_bar_1d`

---

## 垂直切片规则

1. 每片 tracer-bullet：可独立 pytest 绿。
2. RED → GREEN 证据：`research/execute-evidence/sNN-red.txt` → `sNN-green.txt`
3. 禁止 bypass WriteManager；provenance 必须来自 **同 run** fetch bundle。
4. 默认 replay；live 仅 env-gate + 隔离库（非本票 AC）。

---

## 依赖图

```text
S00-BOOT (validate-execute-boot)
  → S01-PROVENANCE-MAP (bundle → SourceProvenance + schema_hash)
  → S02-MOOTDX-E2E (fetch → clean → Layer5 foundation + lineage)
  → S03-LEDGER (ACC-LAYER-E2E G5 子集关账)
```

---

## 切片总表

| Slice | What to build | Acceptance criteria | Blocked by | 测试 / 证据 |
| --- | --- | --- | --- | --- |
| **S00-BOOT** | Execute boot；读全包 + ADR-031 | `validate-execute-boot` exit 0 | — | boot 声明 |
| **S01-PROVENANCE-MAP** | 扩展 `bundle_layer5_provenance`；新增 layer5 provenance bridge 模块 | 单元测：给定 finalize bundle → SourceProvenance 三字段 + dataset ids 可断言 schema_hash | S00 | S01 新建 provenance bridge 单测模块 |
| **S02-MOOTDX-E2E** | mootdx replay incremental → `security_bar_1d` → 读 raw bundle → foundation + lineage | e2e：provenance 与 bundle 一致；非 staged 占位 | S01 | S02 新建 mootdx bar clean e2e 模块 |
| **S03-LEDGER** | `ACC-LAYER-E2E-LIVE-001` G5 子集关账 | `待修复清单.md` G5 行更新；L3–L5 全链仍阶段外置 | S02 | repair ledger + pytest 全绿 |

---

## Issue 骨架

```markdown
### [S02] mootdx bar clean → Layer5 provenance e2e

**What:** One P0 instrument factual evidence with real fetch bundle provenance
**AC:** mootdx bar clean e2e GREEN; source_fetch_id + content_hash + schema_hash match bundle
**Blocked by:** S01
**Verify:** uv run pytest tests/test_layer5_mootdx_bar_clean_e2e.py -q
```

---

## RED/GREEN 证据路径

| 切片 | RED | GREEN |
| --- | --- | --- |
| S01 | `execute-evidence/s01-red.txt` | `execute-evidence/s01-green.txt` |
| S02 | `execute-evidence/s02-red.txt` | `execute-evidence/s02-green.txt` |
| S03 | — | `execute-evidence/s03-green.txt` + 全量 pytest |

---

## 台账承接

| 台账 ID | 本票范围 | 关闭条件 |
| --- | --- | --- |
| `ACC-LAYER-E2E-LIVE-001` | **G5 子集** | S03：一条 mootdx bar → Layer5 provenance e2e 绿 |
| 全链 L1–L5 | **阶段外置** | Wave 5 `R3H-05-GATE` + DCP-07/08 余量 |
