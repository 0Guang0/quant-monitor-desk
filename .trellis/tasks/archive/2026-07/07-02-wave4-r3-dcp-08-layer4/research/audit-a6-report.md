# Audit A6 — Eastmoney Taxonomy Notes（R3-DCP-08）

> **维：** A6 eastmoney taxonomy notes（AUDIT.plan §2 主会话覆写；**非** performance SKIP）  
> **协议：** plan_protocol_version 4.1  
> **模板：** `agents/performance-engineer.md`（任务维覆写为 taxonomy/registry SSOT）  
> **日期：** 2026-07-02  
> **焦点：** S08-REG-EM · `ACC-EASTMONEY-TAXONOMY-001` 部分关账 · **不关** `R3-B2.75-REQ2-EM`

---

## 维度证据

### Boot / 范围

| 项                                     | 证据                                                                                                     |
| -------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| AUDIT.plan §2 A6                       | eastmoney taxonomy notes                                                                                 |
| AUDIT.plan §3 台账                     | 关 `ACC-EASTMONEY-TAXONOMY-001`(部分)；**不关** `R3-B2.75-REQ2-EM`                                       |
| S08-REG-EM AC（`to-issues-slices.md`） | eastmoney capabilities/registry notes + ops 产品路径 SSOT；`rg ACC-EASTMONEY specs/datasource_registry/` |
| ADR-033 §Decision #6                   | extend registry/capabilities notes + ops SSOT only；**do not** enable hist live or close REQ2-EM         |
| 并行政策                               | registry 三件套主会话 merge；本轨 `registry_proposed_delta.yaml`                                         |

### `rg ACC-EASTMONEY specs/datasource_registry/`

```text
source_registry.yaml:319   … ACC-EASTMONEY-TAXONOMY-001: bar incremental via baostock/mootdx …
source_capabilities.yaml:1261 … ACC-EASTMONEY-TAXONOMY-001: bar incremental via baostock/mootdx …
```

→ **2/2 命中**（DCP-05 S13 基线 notes 仍在）

### ops 文档（DCP-08 增量）

| 工件                                                       | 裁决                                                                                                                                |
| ---------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `docs/ops/data_sync_quick_reference.md` §ACC-EASTMONEY     | **PASS** — 含 DCP-08 边界、产品 bar 路径（baostock/mootdx · ADR-033 双轨）、`sector_board`/`capital_flow` 独立 domain、不关 REQ2-EM |
| `git diff master -- docs/ops/data_sync_quick_reference.md` | +2 行 taxonomy（产品 bar 路径 · eastmoney 域分离）；「DCP-05 仅登记」→「DCP-08 登记 registry proposed delta + 本文档」              |

### registry 三件套 vs `registry_proposed_delta.yaml`

| 检查项                                                                              | 预期（proposed delta）                                                                       | 实测（live YAML）                                       | 裁决            |
| ----------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- | ------------------------------------------------------- | --------------- |
| `source_registry.yaml` eastmoney notes 含 R3-DCP-08 taxonomy SSOT 三 bullet         | sector_board/capital_flow 独立域 · bar hist validation-only · 不关 REQ2-EM                   | 仅 DCP-05 短注释；**无** `R3-DCP-08 taxonomy SSOT` 字样 | **GAP**         |
| `source_capabilities.yaml` eastmoney notes 含 Product bar path / Validation domains | `Product bar path: NOT eastmoney`；`cn_index, sector_board, capital_flow` 勿与 bar hist 混用 | 与 registry 同版 DCP-05 短注释；**无** domain 分离明细  | **GAP**         |
| merge gate（`registry_proposed_delta.yaml` §Merge gate）                            | coordinator apply 后勾 [x]                                                                   | `[ ]` 未勾                                              | **OPEN**        |
| `git diff master` registry 两文件                                                   | DCP-08 应有 delta                                                                            | **无 diff**                                             | **仅 ops 已改** |

### REQ2-EM 硬约束

| 工件                                                    | 状态                                   |
| ------------------------------------------------------- | -------------------------------------- |
| `docs/UNRESOLVED_ISSUES_REGISTRY.md` `R3-B2.75-REQ2-EM` | **DEFERRED** · `No`（未误关）          |
| registry/capabilities notes                             | 均含 `does not close R3-B2.75-REQ2-EM` |
| ops §ACC-EASTMONEY                                      | 明确「不关闭 REQ2-EM 硬约束」          |

### 台账 / loop

| 命令                                                         | 结果                                                        |
| ------------------------------------------------------------ | ----------------------------------------------------------- |
| `uv run python scripts/loop_maintain.py`                     | exit 0                                                      |
| `docs/quality/待修复清单.md` §4 `ACC-EASTMONEY-TAXONOMY-001` | 仍写「DCP-05 S13 **部分**」；**未**登记 DCP-08 ops 扩展证据 |

### Execute 证据对照

| 路径                                             | 自述                           | 独立复验                                        |
| ------------------------------------------------ | ------------------------------ | ----------------------------------------------- |
| `research/execute-evidence/s08-reg-em-green.txt` | ops doc ACC-EASTMONEY extended | ops diff **确认**；registry **无** DCP-08 delta |

---

## §维度裁决

**FAIL**

---

## 计划内问题

| ID        | P   | 标题                                   | 锚点                                                                                                                | 根因                                                                                                                    | 修复方案                                                                                             | 验证                                                                                                                       |
| --------- | --- | -------------------------------------- | ------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| A6-P2-001 | P2  | DCP-08 eastmoney registry delta 未落地 | ADR-033 §6 · `registry_proposed_delta.yaml` L63–83 · `source_registry.yaml` L319 · `source_capabilities.yaml` L1261 | S08-REG-EM 仅改 ops doc；proposed delta 仍 COORDINATOR-QUEUED；live YAML 无 `R3-DCP-08 taxonomy SSOT` / domain 分离明细 | 主会话 coordinator 按 proposed delta apply eastmoney notes 至 registry + capabilities；勾 merge gate | `rg "R3-DCP-08 taxonomy\|sector_board.*capital_flow" specs/datasource_registry/` 命中 eastmoney 两行；`git diff` 含两 YAML |
| A6-P3-001 | P3  | 待修复清单未反映 DCP-08 部分关账       | `docs/quality/待修复清单.md` §4 L90 `ACC-EASTMONEY-TAXONOMY-001`                                                    | 关闭条件仍仅写 DCP-05 S13 partial                                                                                       | 更新 §4 行：追加「DCP-08 ops taxonomy ✅；registry delta 待 coordinator」；保持 REQ2-EM open         | `rg "DCP-08" docs/quality/待修复清单.md` 命中 ACC-EASTMONEY 行                                                             |

---

## 计划外发现

| ID        | P   | 标题                                  | 锚点                                                                   | 根因                                                                          | 修复方案                                                                         | 验证                                                                  |
| --------- | --- | ------------------------------------- | ---------------------------------------------------------------------- | ----------------------------------------------------------------------------- | -------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| A6-P3-002 | P3  | ops/registry capabilities SSOT 不对称 | `data_sync_quick_reference.md` L35 vs `source_capabilities.yaml` L1261 | ops 已写 `sector_board`/`capital_flow` 独立 domain；capabilities notes 未镜像 | apply proposed delta 时在 capabilities notes 追加 domain 分离句（与 ops 同语义） | 人工 diff ops §ACC-EASTMONEY 与 capabilities eastmoney notes 语义对齐 |

已对抗搜索：`specs/datasource_registry/**` · `registry_proposed_delta.yaml` · `docs/ops/data_sync_quick_reference.md` · `docs/quality/待修复清单.md` §4 · `docs/UNRESOLVED_ISSUES_REGISTRY.md` · `git diff master` registry/ops · `loop_maintain` 实跑。
