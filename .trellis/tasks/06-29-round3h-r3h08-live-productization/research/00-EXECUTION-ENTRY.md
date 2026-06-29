# R3H-08 执行入口 — 路由地图（Execute SSOT）

> **任务目录：** `.trellis/tasks/06-29-round3h-r3h08-live-productization/`  
> **活卡：** `EXTERNAL-INDEX.md` → `R3H_08_LIVE_PRODUCTIZATION.md`  
> **协议：** Plan v4.1  
> **Execute 子 agent 双铁律 SSOT：** `research/execute-parity-contract.md`

---

## 0. Execute 子 agent 强制双铁律（派发必读）

| 铁律  | 内容                                                                                                                                              |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| **A** | 完整流程与**主会话亲自 Execute 完全一致**（`trellis-execute` SSOT）；**仅**禁止 commit/finish-work                                                |
| **B** | **每个切片 RED 前** Read `reference-adoption-r3h08.md` §7 + `EXTERNAL-INDEX.md` §D 的 `参考项目/**` 源码；严格 **L1/L2/L3**；**禁止不参考从零造** |

详表：`execute-parity-contract.md`（Boot 0b 全文必读）

---

## 1. 任务目的 · 价值 · 完成条件

| 维度         | 内容                                             |
| ------------ | ------------------------------------------------ |
| **目的**     | 闭合 **LIVE-PROD-24**；24 源 env-gated 产品 live |
| **价值**     | Round4 PASS Wave 2；Tier A/B/C 正确落库          |
| **完成条件** | S08-BOOT..05 绿 · pytest 全绿 · Audit PASS       |
| **不在范围** | web_search 真 API · 新 migration                 |

**调研/架构（Plan 前置必做）：** `reference-adoption-r3h08.md` · `live-tier-architecture.md`

---

## 2. 约束 · 规则 · 铁律

| 类别                  | 约束                                                                         | 出处                             |
| --------------------- | ---------------------------------------------------------------------------- | -------------------------------- |
| ADR                   | ADR-027 env gate + tier                                                      | §4                               |
| ADR                   | ADR-025 reconcile（S08-05）                                                  | R3H-10                           |
| 参考                  | L1/L2/L3 三等级                                                              | `reference-adoption-r3h08.md`    |
| **参考 Execute 门禁** | **RED 前必 Read `参考项目/**`源码（见 §2.1 · §5.2 ·`EXTERNAL-INDEX` §D）\*\* | **禁止不参考从零造**             |
| 边界                  | REHEARSAL_ONLY ≠ 产品                                                        | `rehearsal_boundary.py`          |
| GitNexus              | 改 symbol 前 impact                                                          | `gitnexus-summary.md`            |
| **Execute 同流程**    | **子 agent = 主会话亲自 Execute（trellis-execute 全文）**                    | **`execute-parity-contract.md`** |

### 2.1 Execute 参考项目门禁（铁律 B）

> 与 **铁律 A**（`execute-parity-contract.md`）同时生效，不可只遵守其一。

> **铁律：** Execute agent 必须根据 `reference-adoption-r3h08.md` 调研结论，在**每个切片 RED 之前**实际 Read `参考项目/**` 中登记的源码锚点，再写测试/改 QMD 代码。  
> **禁止：** 不打开参考项目源码、不从零臆造 port/编排/解析逻辑。  
> **禁止：** runtime import / sys.path / 执行期读取参考路径（guardrails P0）。  
> **等级：** L1 直拷须落 `qmd_owned` 路径；L2 拷改须对照源码后重写；L3 自研须文档写明「参考了哪段源码、采纳什么、拒绝什么」；`architecture_only` / `forbidden` 须 Read 后写清不拷贝理由。

**机械自检（每个切片 RED 前）：**

```text
[ ] 已 Read reference-adoption-r3h08.md §7 本切片行
[ ] 已 Read EXTERNAL-INDEX.md §D 列出的全部源码文件（全文或调研锚点段落）
[ ] 已在实现/测试注释或矩阵中 cite：参考路径 + 行号 + L1/L2/L3 等级
[ ] forbidden（EasyXT 等）已核对无 silent_fallback / bypass 语义渗入
→ 然后才允许 RED
```

### 2.2 Execute 与主会话同流程（铁律 A）

> 完整步骤见 **`execute-parity-contract.md` §2–§4**（= 主会话派发 Execute 模板全文）

---

## 3. 验证命令

```bash
uv run pytest -q
python .trellis/scripts/task.py validate-execute-handoff .trellis/tasks/06-29-round3h-r3h08-live-productization
```

---

## 4. ADR 索引

| ADR                                                                                        | 标题                         | 切片             |
| ------------------------------------------------------------------------------------------ | ---------------------------- | ---------------- |
| [ADR-027](../../../../docs/decisions/ADR-027-r3h08-product-live-env-gate.md)               | Product live env gate + tier | S08-BOOT, S08-05 |
| [ADR-025](../../../../docs/decisions/ADR-025-r3h10-sync-fail-closed-datasource-service.md) | Sync fail-closed             | S08-05           |

---

## 5. 执行包阅读规则

### 5.1 文件地图

| 文件                             | 用途                                         |
| -------------------------------- | -------------------------------------------- |
| `00-EXECUTION-ENTRY.md`          | 本路由                                       |
| `EXTERNAL-INDEX.md`              | 包外 §A/B/C                                  |
| `to-issues-slices.md`            | 垂直切片                                     |
| `live-tier-architecture.md`      | 架构 SSOT                                    |
| `reference-adoption-r3h08.md`    | 三等级调研                                   |
| `live-tier-baseline-matrix.md`   | BOOT 矩阵（Execute 产出）                    |
| `plan-spec-gap.md`               | Spec                                         |
| `plan-task-sizing.md`            | 规模                                         |
| `plan-context-pack.md`           | 上下文                                       |
| `plan-doubt-review.md`           | 对抗审查                                     |
| `plan-consolidation.md`          | 5e 对照                                      |
| `integration-audit.md`           | 5d                                           |
| `project-overview.md`            | GitNexus 1a                                  |
| `gitnexus-summary.md`            | GitNexus 1b                                  |
| **`execute-parity-contract.md`** | **子 agent = 主会话 Execute 同流程（强制）** |

### 5.2 Boot 开工必读

1. 上表全部（除 `plan-boot.md`）
2. **`execute-parity-contract.md` 全文（派发契约 · 与主会话零流程差）**
3. `EXTERNAL-INDEX.md` §A 每一行
4. `to-issues-slices.md` **当前切片 §**
5. **`reference-adoption-r3h08.md` §7（Execute 参考门禁）全文**
6. **`EXTERNAL-INDEX.md` §D — 当前切片登记的 `参考项目/**` 源码（RED 前必 Read）\*\*

**每个切片增量（RED 前重复）：** §D 当前切片行 + §7 对照表 + QMD 将改 `fetch_ports/*` 现有实现。

### 5.3 情境路由

| 情境               | 路由                                                                              |
| ------------------ | --------------------------------------------------------------------------------- |
| 改 tier / env gate | `live-tier-architecture.md` §3 · ADR-027                                          |
| 改 port live       | `fetch_ports/*` · `reference-adoption-r3h08.md` §4 · **§7 + §D 先 Read 参考源码** |
| Tier B 写库        | `limited_production_entry.py` L166-180                                            |
| rehearsal 边界     | `production_live_pilot_policy.md`                                                 |
| reconcile/probe    | `to-issues-slices.md` §7 · ADR-025                                                |

---

## 6. GAP

| GAP                            | 时机      |
| ------------------------------ | --------- |
| `frozen/` + INDEX              | freeze 后 |
| `live-tier-baseline-matrix.md` | S08-BOOT  |

---

## 7. 当前切片指针

默认：**S08-BOOT** · `to-issues-slices.md` §2

## D. 机器路由

权威：`context_pack.json`（`context_router.py --task`）
