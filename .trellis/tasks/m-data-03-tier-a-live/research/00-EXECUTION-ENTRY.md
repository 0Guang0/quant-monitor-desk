# M-DATA-03 执行入口 — 路由地图（Plan R2 · Execute SSOT）

> **唯一 Execute 读入口** · **用户口径 SSOT：** `research/plan-revision-r2.md`  
> **协议：** Plan v4.1 · `plan-skill-outputs.yaml`

---

## 1. 目的 · 价值 · 完成条件

| 维度         | 内容                                                              |
| ------------ | ----------------------------------------------------------------- |
| **目的**     | 11 源隔离库 **R4 真网** 完整验收：统一信封 + F0 + B2 + 无 SKIP    |
| **价值**     | M-G1-03；MCR C3/D1/E1/E2/F0/B2 → R4                               |
| **完成条件** | `plan-revision-r2.md` §2 全满足 · `to-issues-slices.md` R2 全 [x] |
| **不在范围** | 新 DDL · Layer · Round4 · 主库 · 阶段外置                         |

---

## 2. 约束 · 规则

| 类别     | 约束                                                 | 详述                              |
| -------- | ---------------------------------------------------- | --------------------------------- |
| 证据     | `live_tier_a_evidence_v1.yaml`                       | 11 源统一信封 + `source_bindings` |
| F0/B2    | `data_quality_rules.yaml` · `data_cli_contract.yaml` | 四族 profile；禁 SKIP             |
| 权威     | docs/specs > 参考项目 > 仓内                         | `plan-revision-r2.md`             |
| 真网     | `QMD_ALLOW_LIVE_FETCH` + 隔离 `DATA_ROOT`            | ADR-034 · ADR-027                 |
| 失败     | fixable 必修 · external 须 ADR                       | contract `failure_class`          |
| GitNexus | dispatch 改前 `impact()`                             | `gitnexus-summary.md`             |

---

## 3. 验证命令

```bash
uv run pytest -q
uv run python scripts/loop_maintain.py
QMD_ALLOW_LIVE_FETCH=1 DATA_ROOT=.audit-sandbox/m-data-03/<run> \
  uv run python scripts/tier_a_live_acceptance.py --report /tmp/tier-a-r2.json
```

---

## 4. ADR 索引

| ADR                                                                                        | 标题                  | 切片          |
| ------------------------------------------------------------------------------------------ | --------------------- | ------------- |
| [ADR-034](../../../../docs/decisions/ADR-034-m-data-03-tier-a-live-acceptance.md)          | Tier A live 隔离验收  | S-R2-ACCEPT   |
| [ADR-027](../../../../docs/decisions/ADR-027-r3h08-product-live-env-gate.md)               | Product live env gate | 全片          |
| [ADR-025](../../../../docs/decisions/ADR-025-r3h10-sync-fail-closed-datasource-service.md) | Sync fail-closed      | S-R2-DISPATCH |
| [ADR-028](../../../../docs/decisions/ADR-028-dcp05-tier-a-clean-domain-extension.md)       | Clean domain          | 基线          |

**契约：** `specs/contracts/live_tier_a_evidence_v1.yaml`

---

## 5. 执行包阅读规则

### 5.1 包内文件地图（Plan 产物 only）

| 文件                              | Skill                       | 摘要                   |
| --------------------------------- | --------------------------- | ---------------------- |
| `00-EXECUTION-ENTRY.md`           | trellis-plan 5e             | 本路由                 |
| `EXTERNAL-INDEX.md`               | trellis-plan 5e             | 包外 §A/B/C/E          |
| `plan-revision-r2.md`             | Plan R2                     | **用户口径 · AC 锁定** |
| `to-issues-slices.md`             | to-issues                   | **切片 AC SSOT**       |
| `plan-spec.md`                    | spec-driven-development     | 技术规格 R2            |
| `plan-task-breakdown.md`          | planning-and-task-breakdown | R2 任务分解            |
| `plan-context.md`                 | context-engineering         | L1–L5 · 路由           |
| `plan-doubt-review.md`            | doubt-driven-development    | 怀疑审查               |
| `plan-consolidation.md`           | trellis-plan 5e             | Skill 对照             |
| `plan-boot.md`                    | P0 Boot                     | 复述                   |
| `reference-adoption-m-data-03.md` | trellis-research            | 借鉴梯                 |
| `tier-a-live-inventory.md`        | trellis-research            | 11 源触点              |
| `tier-a-live-eligibility.md`      | trellis-research            | KEY 矩阵               |
| `project-overview.md`             | GitNexus 1a                 | 子系统                 |
| `gitnexus-summary.md`             | GitNexus 1b                 | 冲击面                 |
| `parallel-dispatch-protocol.md`   | Plan 并行                   | R2 派发协议            |
| `integration-audit.md`            | Plan 5d                     | 集成审计               |

**归档（非 Plan · 只读）：** `research/archive/` — `plan-r1-superseded/` · `non-plan/{audit,repair,execute}/`

### 5.2 切片开工前必读

1. 本文件 §1–§4
2. `plan-revision-r2.md` §2（**禁止改 AC**）
3. `to-issues-slices.md` 当前 R2 切片
4. `live_tier_a_evidence_v1.yaml`
5. `reference-adoption-m-data-03.md` §0 + 当前源
6. ADR-034 · ADR-027
7. `plan-spec.md` Interface Contract
8. `EXTERNAL-INDEX.md` §A 全表

### 5.3 执行情境路由

| 情境               | 再读                                                    |
| ------------------ | ------------------------------------------------------- |
| S-R2-EVIDENCE      | contract `envelope` · `source_bindings`                 |
| S-R2-F0            | `data_health_cli.md` · 四族 profile · **禁 SKIP**       |
| S-R2-B2            | `data_validation_and_conflict.md`                       |
| S-R2-DISPATCH      | `gitnexus-summary.md` · `parallel-dispatch-protocol.md` |
| S-R2-CI            | `plan-spec.md` CI · workflow 模板                       |
| S-R2-ACCEPT        | `plan-spec.md` pipeline · `--report` schema             |
| 改 fetch port      | `EXTERNAL-INDEX.md` §E                                  |
| FAIL_EXTERNAL      | ADR 路径 · `failure_class`                              |
| 历史 Execute/Audit | `research/archive/non-plan/`                            |

---

## 6. Execute 顺序

`S-R2-EVIDENCE` → (`S-R2-F0` ∥ `S-R2-B2`) → `S-R2-DISPATCH` → `S-R2-ACCEPT` → `S-R2-CI`

合并强制顺序见 `to-issues-slices.md` · `parallel-dispatch-protocol.md` §2。

## D. 机器路由

`context_pack.json`（任务根目录）
