# Plan Boot — R3-DCP-03 post-write inspect

> **任务目录：** `.trellis/tasks/06-30-wave3-r3-dcp-03-post-write-inspect`  
> **分支：** `feature/wave3-r3-dcp-03-post-write-inspect`  
> **协议：** debt-lite Phase 8D · Plan 增强（**参考项目** L1/L2/L3 调研先行；仓内只写「复用」）  
> **日期：** 2026-06-30

---

## 1. 上下文复述（自己的话）

### 做什么

在 **DCP-01 baostock 增量写库**（主路径）完成后，用 **E2 `DbInspector`** 与 **F0 `run_data_health_profile(market_bar_p0)`** 做写后抽检：重复增量跑行数不膨胀、`max(trade_date)` 可断言、`qmd_ops db-inspect` JSON smoke 绿。fred 幂等已在 DCP-02 e2e 覆盖；本轨 inspect 以 baostock + `security_bar_1d` 为主（INDEX 允许 baostock **或** fred）。

### 价值

- 闭合 Wave 3「读水位 → 增量 → 写库 → **抽检**」
- E2 从 staged fixture 升级到 **增量产品路径写后** 绑定
- 为 Wave 4 多源扩展提供可复制测试夹具（sync → inspect）

### 约束

| 约束     | 要求                                                                  |
| -------- | --------------------------------------------------------------------- |
| 只读抽检 | inspect / health **零写库**                                           |
| 复用     | `db_inspector.py`、`data_health_profiles`、`scripts/qmd_ops.py`       |
| 隔离     | `tmp_path` / `QMD_DATA_ROOT`；禁止 canonical 主库                     |
| 不扩域   | 不新 macro profile；不新 migration                                    |
| 边界     | 不改 DCP-01/02 sync/port/watermark（测试编排可 import 其 e2e helper） |

### 相关设计（上游 SSOT）

```text
活卡 R3_DCP_03_POST_WRITE_INSPECT.md
INDEX R3_DCP_TO_ISSUES_INDEX.md §3
docs/ops/db_inspect_cli.md + specs/contracts/ops_db_inspect_contract.yaml
backend/app/ops/db_inspector.py（KEY_TABLES 含 security_bar_1d、axis_observation）
backend/app/ops/data_health_profiles/__init__.py（market_bar_p0）
tests/test_baostock_incremental_e2e.py（增量写库先例）
tests/test_ops_db_inspector.py（DbInspector + CLI 契约）
DCP-01/02 归档 research/reference-adoption-dcp01/02.md
```

### 成功标准（活卡 §5 AC）

- [ ] 写后 row_count 稳定 + max(trade_date) 断言
- [ ] market_bar_p0 profile smoke
- [ ] db-inspect CLI JSON smoke
- [ ] 参考项目三等级表 + 仓内复用表齐（`reference-adoption-dcp03.md`）+ DEBT.plan 切片
- [ ] Audit Repair 关账 + pytest 全绿

### 完成条件

活卡 §5 全勾 → Wave 3 **CLOSED**（路线图 §3.4 Wave Done）。

---

## 2. 必读清单（阶段 0）

| #   | 文档 / 路径                                                           | 状态 |
| --- | --------------------------------------------------------------------- | ---- |
| 1   | `agent-toolchain.md` · Phase 8D                                       | [x]  |
| 2   | `R3_DCP_TO_ISSUES_INDEX.md` §3 + 活卡                                 | [x]  |
| 3   | `docs/ops/db_inspect_cli.md` · `ops_db_inspect_contract.yaml`         | [x]  |
| 4   | `db_inspector.py` · `test_ops_db_inspector.py`                        | [x]  |
| 5   | `data_health_profiles/__init__.py` · `test_data_health_profiles` 相关 | [x]  |
| 6   | `test_baostock_incremental_e2e.py` · DCP-02 fred e2e 幂等测           | [x]  |
| 7   | `reference_adoption_guardrails.yaml` adoption_ladder                  | [x]  |
| 8   | DCP-01/02 归档 `plan-boot.md` / `DEBT.plan.md`（模式对齐）            | [x]  |
| 9   | `MODULE_COMPLETION_RATING.md` E2/F0 行                                | [x]  |
| 10  | `PROJECT_IMPLEMENTATION_ROADMAP.md` §3.4 Wave 3 Done                  | [x]  |

---

## 3. 缺口摘要（Plan 结论）

| 仓内已有                                                | 本轨缺口（绿场交付）                                                                      |
| ------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| `DbInspector` key_tables 含 `security_bar_1d` row_count | **无**「增量跑两次 → inspect 行数稳定」集成测                                             |
| `run_data_health_profile(market_bar_p0)`                | **未**绑在 baostock incremental 写库之后                                                  |
| `qmd_ops db-inspect` CLI                                | **未**在 DCP 增量隔离库路径上 smoke                                                       |
| `max(trade_date)`                                       | contract **未**要求 inspect 输出该字段 → 测试内 read-only SQL 或极小扩展（需 ADR 级理由） |

**默认 ponytail：** `max(trade_date)` 在 `test_incremental_post_write_inspect.py` 内用 `ConnectionManager.reader()` 断言，**不**改 `DbInspector` 公共报告形状，除非 Plan-Audit 证明必须。

**三等级：** 仅 `参考项目/**`（见 `reference-adoption-dcp03.md` §2）；本轨 **无新增外部 L2 拷贝**（规则已在 R3FR-02 落地）。

---

## 4. Plan 产出物

| 文件                                          | 状态                                |
| --------------------------------------------- | ----------------------------------- |
| `research/plan-boot.md`                       | [x] 本文                            |
| `research/reference-adoption-dcp03.md`        | [x]                                 |
| `research/architecture-dcp03.md`              | [x]                                 |
| `DEBT.plan.md`                                | [x]                                 |
| `research/plan-adversarial-audit.md`          | [x] PASS（0 BLOCKING）              |
| `research/execute-reference-read-evidence.md` | [x] 占位；Execute RED 前填实读行    |
| `AUDIT.plan.md`                               | 待 Execute 前补（对齐 DCP-01 模板） |

---

## 5. 下一步（Plan 闸门后）

1. **Plan-Audit**（对抗审计 `research/plan-adversarial-audit.md`）— 0 BLOCKING 后进入 Execute
2. Execute：`DEBT.plan.md` S01→S03，TDD per slice
3. Audit A1–A8 → Repair → merge → 归档 → Wave 3 CLOSED
