# R3-DCP-07 执行入口 — 路由地图（Execute SSOT）

> **任务目录：** `.trellis/tasks/07-02-wave4-r3-dcp-07-layer2/`  
> **活卡：** `EXTERNAL-INDEX.md` → `R3_DCP_07_LAYER2_CROSS_ASSET.md`  
> **协议：** Plan v4.1

---

## 1. 目的 · 价值 · 完成条件

| 维度         | 内容                                                                      |
| ------------ | ------------------------------------------------------------------------- |
| **目的**     | 单 P0 cross-asset 传感器从 Tier A **clean** 读入并产出 snapshot + lineage |
| **价值**     | Wave 4 DCP-07；G2 R3→R4；`ACC-LAYER-E2E-LIVE-001` **L2 子集**             |
| **完成条件** | S00–S02 绿 · Audit PASS · pytest 全绿                                     |
| **不在范围** | L2 全矩阵 · L3–L5 全链 · FRED live primary · 新 migration                 |

---

## 2. 约束 · 规则

| 类别     | 约束                                                |
| -------- | --------------------------------------------------- |
| ADR-032  | P0 = L2-VIX / VIXCLS / axis_observation             |
| ADR-028  | clean 表映射（macro → axis_observation）            |
| 参考     | `reference-adoption-dcp07.md`；禁止 EasyXT fallback |
| 数据     | replay 隔离库；禁止 silent 主库写                   |
| GitNexus | impact + detect_changes                             |

---

## 3. 验证命令

```bash
uv run pytest tests/test_layer2_sensor_loader.py -q
uv run pytest tests/test_layer2_vix_clean_e2e.py -q
uv run pytest -q
uv run python scripts/loop_maintain.py
python .trellis/scripts/task.py validate-plan-freeze .trellis/tasks/07-02-wave4-r3-dcp-07-layer2
```

Execute 切片绿证据：`research/execute-evidence/sNN-green.txt`

---

## 4. ADR 索引

| ADR                                                             | 标题                | 切片    |
| --------------------------------------------------------------- | ------------------- | ------- |
| `docs/decisions/ADR-032-dcp07-layer2-vix-clean-read.md`         | L2-VIX clean 读绑定 | S00–S02 |
| `docs/decisions/ADR-028-dcp05-tier-a-clean-domain-extension.md` | clean 表 SSOT       | S00     |
| `docs/decisions/ADR-029-dcp06-layer1-five-axis-clean-read.md`   | VIXCLS 先例         | S01     |

---

## 5. Research manifest

### §5.1 Bundle 文件

| 文件                          | 用途               |
| ----------------------------- | ------------------ |
| `plan-boot.md`                | P0                 |
| `project-overview.md`         | 架构概览           |
| `gitnexus-summary.md`         | impact             |
| `reference-adoption-dcp07.md` | L1/L2/L3           |
| `to-issues-slices.md`         | 切片 AC            |
| `plan-task-breakdown.md`      | 任务分解           |
| `plan-spec.md`                | 功能规格           |
| `plan-context.md`             | must-read manifest |
| `plan-doubt-review.md`        | 质疑记录           |
| `integration-audit.md`        | Plan 5d            |
| `plan-consolidation.md`       | 5e 打包            |
| `plan-audit-dcp07.md`         | Plan 对抗审计      |
| `EXTERNAL-INDEX.md`           | 包外索引           |
| `00-EXECUTION-ENTRY.md`       | 本文件             |

### §5.2 Execute must-read

§5.1 全部 + EXTERNAL-INDEX §A + ADR-032 + 活卡 §1–§5

### §5.3 执行情境路由

| 情境        | 再读                                                                                  |
| ----------- | ------------------------------------------------------------------------------------- |
| S00 core    | `plan-spec.md` · `layer1_axes/clean_observation_reader.py`（模式参考，勿 import）     |
| S01 VIX e2e | `test_fred_macro_incremental_e2e.py` 种子 · `test_layer2_sensor_loader.py` lineage 测 |
| S02 台账    | `待修复清单.md` §4 ACC-LAYER-E2E-LIVE-001                                             |

---

## 6. 切片路由

| Step | 切片  | 证据                         |
| ---- | ----- | ---------------------------- |
| 1    | S00   | `execute-evidence/s00-*.txt` |
| 2    | S01   | `s01-*.txt`                  |
| 3    | S02   | `s02-*.txt`                  |
| 4    | Audit | `audit-a*-report.md`         |

AC SSOT：`to-issues-slices.md`

## D. 机器路由

权威数据在 **`context_pack.json`**（本任务根目录）。
