# M-DATA-03 执行入口 — 路由地图（Execute SSOT）

> **角色：** 本任务 **唯一 Execute 读入口**  
> **任务目录：** `.trellis/tasks/m-data-03-tier-a-live/`  
> **活卡（包外）：** `docs/implementation_tasks/M_DATA_03_TIER_A_LIVE/M_DATA_03_TIER_A_LIVE.md`  
> **协议：** Plan v4.1 · `plan-skill-outputs.yaml`

---

## 1. 目的 · 价值 · 完成条件

| 维度         | 内容                                                                              |
| ------------ | --------------------------------------------------------------------------------- |
| **目的**     | 11 个 Tier A 源在隔离库 **真连网** incremental→clean→inspect 验收                 |
| **价值**     | 模块 v2 首票 P0；解锁 M-G1-03；MCR C3/D1/E1/E2/F0/B2 → R4                         |
| **前置**     | R3-DCP-05 CLOSED（replay 逻辑）；ADR-027/028                                      |
| **完成条件** | `to-issues-slices.md` 全切片绿 · S-ACCEPT 11/11 · `uv run pytest -q` · Audit PASS |
| **不在范围** | 新 DDL · Layer 建模 · Round4 · 主库 · Tier B/C cron                               |

---

## 2. 约束 · 规则

| 类别     | 约束                                           | 详述                                    |
| -------- | ---------------------------------------------- | --------------------------------------- |
| ADR-034  | 隔离 `DATA_ROOT` live 验收                     | `docs/decisions/ADR-034-*.md`           |
| ADR-027  | `QMD_ALLOW_LIVE_FETCH` 真网闸                  | `product_live_gate.py`                  |
| ADR-025  | Sync 必须 `datasource_service`                 | fail-closed                             |
| ADR-028  | clean 域 migration 015                         | 只读                                    |
| 参考采纳 | L 梯 **仅** `参考项目/**`；仓内 = **直接复用** | `reference-adoption-m-data-03.md` §0·§4 |
| 接口契约 | live 闸 / acceptance CLI exit 码               | `plan-spec.md` Interface Contract       |
| 主库     | 禁止 silent 写 canonical DB                    | ADR-034 · DEBT 惯例                     |
| GitNexus | impact + detect_changes                        | `gitnexus-summary.md`                   |
| 测试     | replay 默认绿 + network 可选 live              | `plan-spec.md`                          |

### 2.1 借鉴三等级速查（≠ 上下文 L1–L5）

| 等级           | 仅 `参考项目/**`         | 本票                         |
| -------------- | ------------------------ | ---------------------------- |
| L1 直接拷贝    | 粘贴外部源码到 qmd_owned | **0 项**                     |
| L2 拷贝后改造  | 借鉴片段 + 必改写        | **bis 窗参数**（§2.2 清单）  |
| L3 仅概念/架构 | 禁止粘贴参考代码         | OpenBB 三阶段、EasyXT 反例等 |
| 仓内直接复用   | **不适用借鉴梯**         | DCP-05 全部管道代码          |

详见 `reference-adoption-m-data-03.md` §0 · `plan-context.md` 命名澄清。

---

## 3. 验证命令

```bash
# 默认 CI
uv run pytest -q

# 单源 live（隔离库 + key）
export QMD_ALLOW_LIVE_FETCH=1
export DATA_ROOT=.audit-sandbox/m-data-03
uv run pytest tests/test_fred_macro_incremental_e2e.py -m network -q

# 11/11 验收
uv run python scripts/tier_a_live_acceptance.py --quick
uv run python scripts/tier_a_live_acceptance.py

uv run python scripts/loop_maintain.py
```

证据（v4.1 code-first）：`EXECUTION_INDEX.md` §1 · frozen §9 `[x]` · 对应 pytest/脚本路径

---

## 4. ADR 索引

| ADR                                                                                     | 标题                  | 切片                                         |
| --------------------------------------------------------------------------------------- | --------------------- | -------------------------------------------- |
| [ADR-034](../../../docs/decisions/ADR-034-m-data-03-tier-a-live-acceptance.md)          | 隔离库 live 验收      | **S00-INFRA** · **S-LIVE-\*** · **S-ACCEPT** |
| [ADR-027](../../../docs/decisions/ADR-027-r3h08-product-live-env-gate.md)               | Product live env gate | 全 live 切片                                 |
| [ADR-025](../../../docs/decisions/ADR-025-r3h10-sync-fail-closed-datasource-service.md) | Sync fail-closed      | 全片                                         |
| [ADR-028](../../../docs/decisions/ADR-028-dcp05-tier-a-clean-domain-extension.md)       | clean 域 015          | 只读                                         |

---

## 5. 执行包阅读规则

### 5.1 包内文件地图

| 文件                              | Skill                       | 摘要                                      |
| --------------------------------- | --------------------------- | ----------------------------------------- |
| `00-EXECUTION-ENTRY.md`           | trellis-plan 5e             | 本路由                                    |
| `EXTERNAL-INDEX.md`               | trellis-plan 5e             | 包外 §A/B/C                               |
| `plan-boot.md`                    | P0                          | Boot 复述                                 |
| `tier-a-live-inventory.md`        | trellis-research            | 设计权威倒查                              |
| `tier-a-live-eligibility.md`      | S00                         | 11 源资格矩阵                             |
| `to-issues-slices.md`             | to-issues                   | **切片 AC SSOT**                          |
| `plan-task-breakdown.md`          | planning-and-task-breakdown | 任务/CP                                   |
| `plan-spec.md`                    | spec-driven-development     | 技术规格                                  |
| `plan-context.md`                 | context-engineering         | 上下文/路由                               |
| `plan-doubt-review.md`            | doubt-driven-development    | 怀疑审查                                  |
| `reference-adoption-m-data-03.md` | trellis-research            | 借鉴三等级（仅参考项目）+ 仓内直接复用 §4 |
| `parallel-dispatch-protocol.md`   | trellis-channel             | 并行派发                                  |
| `project-overview.md`             | GitNexus 1a                 | 子系统                                    |
| `gitnexus-summary.md`             | GitNexus 1b                 | 冲击面                                    |
| `plan-consolidation.md`           | trellis-plan 5e             | 分流对照                                  |

### 5.2 切片开工前必读

1. 本文件 §1–§4
2. `to-issues-slices.md` 当前切片 §
3. `reference-adoption-m-data-03.md` **§0 等级定义** + 本源 §3 行
4. `plan-spec.md`（live 切片：Interface Contract + Official API）
5. `tier-a-live-inventory.md` §6–§8
6. ADR-034 · ADR-027
7. `EXTERNAL-INDEX.md` §A · §E（live 切片）

### 5.3 执行阶段情境路由

| 情境                      | 路由                                                                               |
| ------------------------- | ---------------------------------------------------------------------------------- |
| 改 fetch port live        | `source-driven-development` + `plan-spec.md` Official API + `EXTERNAL-INDEX.md` §E |
| 借鉴 L2（bis）            | `reference-adoption-m-data-03.md` §2.2 改造清单                                    |
| 仓内 orchestrator/service | **直接复用**；`gitnexus-summary.md`；禁止标借鉴 L1                                 |
| 并行 worktree             | `parallel-dispatch-protocol.md`                                                    |
| inspect/health 红         | EXTERNAL-INDEX §B · F0/E2                                                          |
| registry merge            | S-MERGE 仅 coordinator                                                             |

---

## 6. GAP

| GAP                                    | 时机                    |
| -------------------------------------- | ----------------------- |
| `frozen/*.md`                          | `freeze-task-card` 后   |
| `implement.jsonl`                      | `generate-manifests` 后 |
| `execute-reference-read-evidence-*.md` | Execute 每切片 RED 前   |

---

## 7. 当前切片指针

Plan 完成态：从 `to-issues-slices.md` § **S00-ELIGIBILITY** 起 Execute。

## D. 机器路由

权威数据在 **`context_pack.json`**（任务根目录）。
