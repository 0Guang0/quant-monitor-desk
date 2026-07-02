# R3-DCP-08 执行入口 — 路由地图（Execute SSOT）

> **角色：** 本任务 **唯一 Execute 读入口**  
> **任务目录：** `.trellis/tasks/07-02-wave4-r3-dcp-08-layer4/`  
> **活卡（包外）：** `EXTERNAL-INDEX.md` → `R3_DCP_08_LAYER4_MARKET_STRUCTURE.md`  
> **协议：** Plan v4.1 · `plan-skill-outputs.yaml`  
> **P0 market_id：** `US_EQ`

---

## 1. 任务目的 · 价值 · 完成条件

| 维度         | 内容                                                                                                           |
| ------------ | -------------------------------------------------------------------------------------------------------------- |
| **目的**     | Layer4 **US_EQ** 从 Tier A clean + US 日历 → market breadth snapshot + lineage                                 |
| **价值**     | Wave 4 G4 最小竖切；关 ACC-MOOTDX · ACC-EASTMONEY(部分) · ACC-LAYER-E2E L4                                     |
| **评级**     | G4 `R3→R4`                                                                                                     |
| **完成条件** | S08-BOOT..CLOSE 全绿 · `test_layer4_us_equity_clean_e2e.py` GREEN · registry delta queued · `uv run pytest -q` |
| **不在范围** | CN_A full slice · Eastmoney hist live · REQ2-EM · L3/L5 全链                                                   |

**业务详述：** 活卡 `R3_DCP_08_LAYER4_MARKET_STRUCTURE.md` §1–§5

---

## 2. 约束 · 规则 · 铁律

| 类别         | 约束                                              | 详述                           |
| ------------ | ------------------------------------------------- | ------------------------------ |
| **ADR-033**  | P0 US_EQ · tier_a_clean · 无 migration            | §4 · `plan-doubt-review.md`    |
| **ADR-026**  | US 日历 SSOT                                      | `us_trading_calendar.py`       |
| **参考采纳** | L1/L2/L3 仅 `参考项目/**`                         | `reference-adoption-dcp08.md`  |
| **REQ2-EM**  | **禁止** 关 Eastmoney hist 真网                   | 活卡 §3 · §6                   |
| **Registry** | proposed delta → 主会话 merge                     | `registry_proposed_delta.yaml` |
| **TDD**      | RED→GREEN · 五字段                                | `/test-driven-development`     |
| **GitNexus** | impact before edit · detect_changes before commit | `gitnexus-summary.md`          |

---

## 3. 验证命令

```bash
uv run pytest tests/test_layer4_us_equity_clean_e2e.py -q
uv run pytest tests/test_layer4_market_structure.py -q
uv run pytest tests/test_qmd_data_sync_tier_a_router.py -k mootdx -q
uv run pytest -q
uv run python scripts/loop_maintain.py
python .trellis/scripts/task.py validate-execute-handoff .trellis/tasks/07-02-wave4-r3-dcp-08-layer4
```

证据：`research/execute-evidence/s08-NN-red.txt` → `s08-NN-green.txt`

---

## 4. ADR 索引

| ADR                                                                             | 标题                                                   | 绑定切片               |
| ------------------------------------------------------------------------------- | ------------------------------------------------------ | ---------------------- |
| [ADR-033](../../../../docs/decisions/ADR-033-dcp08-layer4-us-eq-clean-read.md)  | DCP-08 Layer4 US_EQ clean read + registry dual-primary | S08-E2E · S08-REG-\*   |
| [ADR-026](../../../../docs/decisions/ADR-026-r3h07-us-trading-calendar-ssot.md) | US trading calendar SSOT                               | S08-READ · S08-ADAPTER |

---

## 5. 执行包阅读规则

### 5.1 文件地图（全部 research/\*.md，除 plan-boot）

| 文件                           | Skill                       | 内容摘要                            |
| ------------------------------ | --------------------------- | ----------------------------------- |
| `00-EXECUTION-ENTRY.md`        | trellis-plan 5e             | 本路由                              |
| `EXTERNAL-INDEX.md`            | trellis-plan 5e             | 包外 §A/B/C                         |
| `to-issues-slices.md`          | to-issues                   | 垂直切片 · AC · 证据                |
| `plan-task-breakdown.md`       | planning-and-task-breakdown | 任务分解 · 风险                     |
| `plan-spec.md`                 | spec-driven-development     | Spec · 边界                         |
| `plan-context.md`              | context-engineering         | 上下文 L1–L5 · 路由                 |
| `plan-doubt-review.md`         | doubt-driven-development    | 对抗审查 · US_EQ 定案               |
| `reference-adoption-dcp08.md`  | trellis-research            | 参考采纳 L1/L2/L3                   |
| `layer4-tier-a-research.md`    | trellis-research            | clean read 调研                     |
| `project-overview.md`          | gitnexus 1a                 | 模块地图                            |
| `gitnexus-summary.md`          | gitnexus 1b                 | impact 摘要                         |
| `registry_proposed_delta.yaml` | trellis-research            | registry COORDINATOR-QUEUED         |
| `integration-audit.md`         | trellis-plan 5d             | Plan 对抗 · PASS_WITH_GAPS          |
| `plan-audit-dcp08.md`          | plan-audit                  | Plan 对抗审计 · 4 findings 已修复   |
| `plan-consolidation.md`        | trellis-plan 5e             | 分流 · 对照 · **Phase 5e complete** |

### 5.2 切片开工前必读（硬门禁）

**每一次** S08-xx 切片开始前必须已 Read：

#### A. `research/` 包内（§5.1 全部 14 份，不含 plan-boot）

#### B. `EXTERNAL-INDEX.md` §A 全部

#### C. 当前切片

`to-issues-slices.md` 对应 § 精读

```text
开工检查：
[ ] research/ §5.1 14 份已读
[ ] EXTERNAL-INDEX §A 已读
[ ] 当前 S08-xx § 已读
→ 然后 RED
```

### 5.3 执行阶段情境路由

| 情境                      | 路由                                                                    |
| ------------------------- | ----------------------------------------------------------------------- |
| 改 breadth 聚合           | `layer4-tier-a-research.md` · `docs/modules/layer4_market_structure.md` |
| 改 US 日历 / 非交易日     | ADR-026 · `us_trading_calendar.py`                                      |
| 改 Builder staged 路径    | `market_structure.py` · 022 测不可回归                                  |
| mootdx dry-run / registry | `registry_proposed_delta.yaml` · `data_commands.py` · ACC-MOOTDX        |
| eastmoney taxonomy        | registry notes · ops doc · **不关 REQ2-EM**                             |
| 参考项目                  | `reference-adoption-dcp08.md`                                           |
| L4 e2e 台账               | `to-issues-slices.md` S08-L4-E2E-LEDGER                                 |

---

## 6. Execute 产出（Plan 后填）

| 路径                                              | 用途             |
| ------------------------------------------------- | ---------------- |
| `research/execute-evidence/s08-*.txt`             | RED/GREEN        |
| `research/execute-reference-read-evidence-s08.md` | 参考项目实读     |
| `research/l4-e2e-live-evidence.md`                | ACC-LAYER-E2E L4 |

---

## 7. 台账关账指针

| ID                          | Execute 切片                | 关账证据                             |
| --------------------------- | --------------------------- | ------------------------------------ |
| ACC-MOOTDX-DRYRUN-ROUTE-001 | S08-REG-MOOTDX              | router test + registry delta applied |
| ACC-EASTMONEY-TAXONOMY-001  | S08-REG-EM                  | notes/ops · REQ2-EM still open       |
| ACC-LAYER-E2E-LIVE-001 L4   | S08-E2E + S08-L4-E2E-LEDGER | clean e2e green + evidence md        |

## D. 机器路由

权威数据在 **`context_pack.json`**（本任务根目录）。 由 `context_router.py --task` 写入；本段不重复列举。
