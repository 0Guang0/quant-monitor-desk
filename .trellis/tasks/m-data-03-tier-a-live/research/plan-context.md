# M-DATA-03 Context Engineering

## 命名澄清（防 Execute 混淆）

| 术语                       | 含义                               | 本任务                               |
| -------------------------- | ---------------------------------- | ------------------------------------ |
| **上下文 L1–L5**（本文件） | 信息层次：规则→设计→源码→契约→切片 | 见下表                               |
| **借鉴 L1/L2/L3**          | 仅 `参考项目/**` 外部源码采纳梯    | `reference-adoption-m-data-03.md` §0 |
| **仓内直接复用**           | QMD 已有代码（DCP-05/R3H-08）      | **不进**借鉴 L 梯                    |

**混淆禁令：** 不得写「L1 复用 orchestrator」— 应写「仓内直接复用 `sync/orchestrator.py`」。

---

## Context Hierarchy（L1–L5）

| Level       | 本任务映射                                              |
| ----------- | ------------------------------------------------------- |
| L1 项目意图 | `PROJECT_IMPLEMENTATION_ROADMAP.md` §3.1                |
| L2 模块设计 | `tier-a-live-inventory.md` §2                           |
| L3 源码触点 | §6 仓内表 + `EXTERNAL-INDEX.md` §C                      |
| L4 契约     | ADR-025/027/028/034 · `plan-spec.md` Interface Contract |
| L5 切片 AC  | `to-issues-slices.md`                                   |

## PROJECT CONTEXT（可复制给 Execute agent）

```text
任务：M-DATA-03 — 11 源隔离库真网 incremental→clean→inspect
仓内：DCP-05 管道直接复用（禁止标借鉴 L 梯）
借鉴：仅 参考项目/** — 本票 0×L1 · 1×L2(bis 窗) · 余 L3/forbidden
金路径：DataSourceService + run_incremental（ADR-025）
真网闸：QMD_ALLOW_LIVE_FETCH=1 + gate_live_fetch_port（ADR-027）
隔离：DATA_ROOT；禁止主库（ADR-034）
SDD：每源 live RED 前读 plan-spec.md Official API 表
完成：11/11 live + F0/E2 inspect 绿 + MCR R4
```

## Level 3 源码表

### 仓内直接复用（非借鉴梯）

| 组件         | 路径                                             |
| ------------ | ------------------------------------------------ |
| Orchestrator | `sync/orchestrator.py`                           |
| Watermark    | `sync/watermark.py`                              |
| Service      | `datasources/service.py`                         |
| Live gate    | `product_live_gate.py` · `product_live_ports.py` |
| 11 源 ops    | `ops/*_incremental_*.py`                         |
| CLI          | `cli/data_commands.py`                           |

### 按切片追加必读

| 切片            | 仓内 + 参考                                                       |
| --------------- | ----------------------------------------------------------------- |
| S00-INFRA       | `product_live_gate.py` · `test_r3h08_*` · `reference-adoption` §0 |
| S-LIVE-FRED     | `fred_port.py` · SDD FRED API · 借鉴 **L3**                       |
| S-LIVE-BIS      | `bis_incremental_*` · 借鉴 **L2** §2.2 改造清单                   |
| S-LIVE-BAOSTOCK | `baostock_port` · EasyXT **forbidden** 反例                       |
| S-LIVE-\* 其余  | §C port/ops/e2e · SDD §E · 借鉴 **L3**                            |
| S-MERGE         | registry 三件套                                                   |
| S-ACCEPT        | `tier_a_live_acceptance.py` · inspect/health CLI                  |

## 开工必读 vs 情境路由

### §5.2 开工必读

1. `00-EXECUTION-ENTRY.md` §1–§4
2. `reference-adoption-m-data-03.md` **§0 等级定义** + 本源 §3 行
3. `to-issues-slices.md` 当前切片
4. `plan-spec.md` Interface Contract + Official API（live 切片）
5. ADR-034 · ADR-027
6. `EXTERNAL-INDEX.md` §A · §E

### §5.3 情境路由

| 情境               | 读                                                       |
| ------------------ | -------------------------------------------------------- |
| 改 fetch port live | `source-driven-development` + plan-spec Official API     |
| bis 宏观窗         | `reference-adoption` §2.2 **L2 改造清单**                |
| 能否拷贝参考代码？ | §0：仅 L1/L2；本票无 L1；L2 必须改写                     |
| 仓内 orchestrator  | **直接复用**；GitNexus impact；禁止借鉴梯标注            |
| inspect/health 红  | `db_inspect_cli.md` · F0 引擎                            |
| silent fallback    | EasyXT unified_data_interface forbidden + harness 负向测 |
