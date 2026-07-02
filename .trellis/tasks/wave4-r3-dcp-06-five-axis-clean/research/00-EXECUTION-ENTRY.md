# R3-DCP-06 执行入口 — 路由地图（Execute SSOT）

> **任务目录：** `.trellis/tasks/wave4-r3-dcp-06-five-axis-clean/`  
> **活卡：** `EXTERNAL-INDEX.md` → `R3_DCP_06_LAYER1_FIVE_AXIS_CLEAN.md`  
> **协议：** Plan v4.1

---

## 1. 目的 · 价值 · 完成条件

| 维度         | 内容                                                          |
| ------------ | ------------------------------------------------------------- |
| **目的**     | 五轴从 Tier A **clean** 读入并 pytest 全绿（G12 PASS 硬门禁） |
| **价值**     | Wave 4 DCP-06；G1/K2 R3→R4；`ACC-LAYER-E2E-LIVE-001` L1 子集  |
| **完成条件** | S00–S06 绿 · §3.5.1 全 [x] · Audit PASS · pytest 全绿         |
| **不在范围** | B2.5-O-05 · L3–L5 全链 · tiingo 主路径 · 新 migration         |

---

## 2. 约束 · 规则

| 类别     | 约束                                                |
| -------- | --------------------------------------------------- |
| ADR-029  | P0 锚点 + clean 读路径                              |
| ADR-028  | clean 表映射（只读）                                |
| 参考     | `reference-adoption-dcp06.md`；禁止 EasyXT fallback |
| 数据     | replay 隔离库；禁止 silent 主库写                   |
| GitNexus | impact + detect_changes                             |

---

## 3. 验证命令

```bash
uv run pytest tests/test_layer1_axis_loader.py tests/test_layer1_observation_ingestion.py -q
uv run pytest -q
uv run python scripts/loop_maintain.py
python .trellis/scripts/task.py validate-plan-freeze .trellis/tasks/wave4-r3-dcp-06-five-axis-clean
```

Execute 切片绿证据：research/execute-evidence/sNN-green.txt（含新建 test*layer1*\*\_clean_e2e 模块）

---

## 4. ADR 索引

| ADR                                                             | 标题              | 切片    |
| --------------------------------------------------------------- | ----------------- | ------- |
| `docs/decisions/ADR-029-dcp06-layer1-five-axis-clean-read.md`   | 五轴 clean 读绑定 | S00–S06 |
| `docs/decisions/ADR-028-dcp05-tier-a-clean-domain-extension.md` | clean 表 SSOT     | S00     |

---

## 5. Research \_manifest

### §5.1 Bundle 文件

| 文件                            | 用途               |
| ------------------------------- | ------------------ |
| `plan-boot.md`                  | P0                 |
| `project-overview.md`           | 架构概览           |
| `gitnexus-summary.md`           | impact             |
| `reference-adoption-dcp06.md`   | L1/L2/L3           |
| `to-issues-slices.md`           | 切片 AC            |
| `plan-task-breakdown.md`        | 任务分解           |
| `plan-spec.md`                  | 功能规格           |
| `plan-context.md`               | must-read manifest |
| `plan-doubt-review.md`          | 质疑记录           |
| `integration-audit.md`          | Plan 5d            |
| `parallel-dispatch-protocol.md` | 并行 agent         |
| `plan-consolidation.md`         | 5e 打包            |
| `EXTERNAL-INDEX.md`             | 包外索引           |
| `00-EXECUTION-ENTRY.md`         | 本文件             |

### §5.2 Execute must-read

§5.1 全部 + EXTERNAL-INDEX §A + ADR-029 + 活卡 §1–§5

### 5.3 执行情境路由

| 情境           | 再读                                                             |
| -------------- | ---------------------------------------------------------------- |
| S00 core       | `plan-spec.md` FR-1..3 · `ingestion.py` staged 桥（勿破坏）      |
| 宏观轴 S01–S03 | `test_fred_macro_incremental_e2e.py` 种子模式 · ADR-028 macro 域 |
| 流动性 S04     | ADR-029 ponytail · alpha_vantage bar 先例                        |
| 情绪 S05       | cftc incremental e2e · COT 行映射                                |
| S06 台账       | `待修复清单.md` §4 ACC-LAYER-E2E-LIVE-001                        |

---

## D. 机器路由

## 权威数据在 **context_pack.json**（任务根目录）。

## 6. 切片路由

| Step | 切片    | 证据                         |
| ---- | ------- | ---------------------------- |
| 1    | S00     | `execute-evidence/s00-*.txt` |
| 2    | S01–S05 | `s01-` … `s05-`              |
| 3    | S06     | `s06-`                       |
| 4    | Audit   | `audit-a*-report.md`         |

AC SSOT：`to-issues-slices.md`

## D. 机器路由

权威数据在 **`context_pack.json`**（本任务根目录）。 由 `context_router.py --task` 写入；本段不重复列举。
