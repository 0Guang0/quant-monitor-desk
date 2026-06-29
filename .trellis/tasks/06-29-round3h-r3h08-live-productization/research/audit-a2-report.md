# Audit A2 — Ponytail / 可读性 · R3H-08 live productization

> **维度：** A2（ponytail-review）  
> **任务：** `06-29-round3h-r3h08-live-productization`  
> **协议：** `plan_protocol_version: 4.1`  
> **模板：** `agents/audit-a2-ponytail.md`  
> **diff 范围：** `git diff 2f75a035^..2f75a035`  
> **焦点文件：** `product_live_gate.py` · `live_tier_router.py` · `product_live_ports.py` · `fetch_ports/*`  
> **日期：** 2026-06-30

---

## 维度证据

### git diff --stat（A2 checklist）

| 文件组                  | 文件数 | +       | −      | net      |
| ----------------------- | ------ | ------- | ------ | -------- |
| `fetch_ports/*`         | 11     | ~388    | ~20    | ~+368    |
| `live_tier_router.py`   | 1      | 61      | 0      | +61      |
| `product_live_gate.py`  | 1      | 38      | 0      | +38      |
| `product_live_ports.py` | 1      | 304     | 0      | +304     |
| **合计**                | **14** | **712** | **20** | **+692** |

### ponytail 梯级记录（§3.2 候选删改）

| 候选删改（file:line）                                                                  | ponytail 梯级                     | 备注                                 |
| -------------------------------------------------------------------------------------- | --------------------------------- | ------------------------------------ |
| `product_live_ports.py:23-57` 四套 `TIER_*_08x_SOURCES`                                | 梯级 2（复用 `live_tier_router`） | 与 ADR-027 SSOT 双轨                 |
| `product_live_ports.py:88-212` 14× `_xxx_port` + 4 dict                                | 梯级 1 YAGNI / 2 复用 `create_*`  | architecture §3.3 直调 port          |
| `product_live_ports.py:64-77,221-261` 双重 gate                                        | 梯级 2                            | 工厂 assert + `ProductLiveGatedPort` |
| `fetch_ports/{cftc_cot,us_treasury,world_bank}_port.py` mock-delegate `*LiveFetchPort` | 梯级 2                            | ~44 行无网络增量                     |
| `fetch_ports/{cninfo,mootdx,baostock}_port.py` replay-first ProductLive 类             | 梯级 2                            | ~45 行同构                           |
| `kalshi_port.py:107-118` / `polymarket_port.py` 同类 gate 分支                         | 梯级 2                            | 与工厂 gate 三重叠加                 |
| `product_live_gate.py` 全文件 +38                                                      | —                                 | ADR-027 显式交付，**不算**           |
| `live_tier_router.py` 全文件 +61                                                       | —                                 | ADR-027 显式交付，**不算**           |
| `bis_port.py:113-188` `BisLiveFetchPort` +86                                           | —                                 | L2 cite · 真网络路径，**不算**       |
| `deribit_port.py:80-152` `DeribitLiveFetchPort` +74                                    | —                                 | 真 API，**不算**                     |

### DOUBT（≥20 行可简化）

**已找到。** 搜索范围：`product_live_ports.py` 全文、`live_tier_router.py`、`fetch_ports/{baostock,cninfo,mootdx,cftc_cot,us_treasury,world_bank,sec_edgar,kalshi,polymarket}_port.py` diff 段。至少 3 处独立 ≥20 行块（工厂 ~125 行、tier 双轨 ~35 行、mock-delegate + CN replay ~78 行）。

### 与 A4 交叉引用

| A2 项                                                    | A4 可能接续                 |
| -------------------------------------------------------- | --------------------------- |
| 三重 `assert_product_live_allowed`                       | gate 失败码/消息一致性      |
| `SecEdgarLiveFetchPort` USER_AGENT 检查在类内 vs factory | `USER_AUTH_REQUIRED` 双路径 |
| `bis_port` `PortError("NETWORK_ERROR")` / `urllib` 样板  | 错误模型与重试策略          |

### A2 checklist

- [x] `git diff --stat` 已记录（14 files · net +692）
- [x] 每候选附 file:line + ponytail 梯级
- [x] A4 交叉引用（gate / auth / network 错误）
- [x] P0–P3 已区分（无 BLOCKING/NON-BLOCKING 措辞）

---

## §维度裁决

**FAIL**

（§计划内 + §计划外 共 5 行非占位 finding）

---

## 计划内问题

| ID        | P   | 标题                                                     | 锚点                                                                 | 根因                                                                                                                                                      | 修复方案                                                                                                                                                                                          | 验证                                                                                                        |
| --------- | --- | -------------------------------------------------------- | -------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| A2-P1-001 | P1  | Tier 源表与 `live_tier_router` 双轨维护                  | `product_live_ports.py:23-57` · `live_tier_router.py:9-46`           | S08 子轨 frozenset 与 ADR-027 `resolve_live_tier` SSOT 重复登记 24 源                                                                                     | 删除 `TIER_A_08C/08A`、`TIER_B_08B`、`TIER_C_08D`；`create_product_live_fetch_port` 仅 `resolve_live_tier(source_id)` + 子轨→factory 小 dict（或 slice ID 参数）                                  | `uv run pytest tests/test_r3h08_live_productization.py -q`；`rg TIER_A_08 backend/app/datasources` 无重复表 |
| A2-P1-002 | P1  | `product_live_ports` 巨型工厂违背 architecture 直调 port | `product_live_ports.py:88-212`                                       | `live-tier-architecture.md` §3.3 要求 `create_<source>_fetch_port(..., use_mock=False)` 直构 service；Execute 叠 14 个 `_xxx_port` + 4 dict（净 ~125 行） | 缩为 `SOURCE_LIVE_DEFAULTS: dict[str, dict]` + 通用 `_import_create(source_id)`；或测试/CLI 直调各 `create_*_fetch_port`，本模块只保留 gate+tier 路由（目标 <120 行）                             | 同上；`wc -l product_live_ports.py` 显著下降且 24 源测仍绿                                                  |
| A2-P2-001 | P2  | ProductLiveGate 三重检查                                 | `product_live_ports.py:221-222,64-77,261` · `kalshi_port.py:107-118` | 工厂入口 `assert` + `ProductLiveGatedPort` 每次 fetch 再 assert + Tier C port 内第三道                                                                    | 保留**一处** fail-closed：推荐删 `ProductLiveGatedPort` 包装，仅在 `create_product_live_fetch_port` / CLI 入口 assert；kalshi/poly 保留 smoke 分支但去掉重复的 `is_product_live_fetch_allowed` 块 | `tests/test_r3h08_live_productization.py` 中 gate 负向/08C/08D 测仍绿                                       |

---

## 计划外发现

| ID        | P   | 标题                                  | 锚点                                                                                                                                                    | 根因                                                                                      | 修复方案                                                                                                                                                         | 验证                                                                                                  |
| --------- | --- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| A2-P2-002 | P2  | mock-delegate `*LiveFetchPort` 类膨胀 | `cftc_cot_port.py:75-83` · `us_treasury_port.py:117-130` · `world_bank_port.py:85-102` · `sec_edgar_port.py:130-147`（后两者含 auth 可留 factory 检查） | `use_mock=False` 仅新增 dataclass 委托 `MockFetchPort`，无网络/解析增量（合计 ~50–78 行） | `create_*` 在 `use_mock=False` 直接 `return XxxMockFetchPort(...)`；`ponytail:` 注释留在 factory；`SecEdgar` USER_AGENT guard 留在 `create_sec_edgar_fetch_port` | 各源 live opt-in 契约测 purpose 不变前提下 `uv run pytest tests/test_r3h08_live_productization.py -q` |
| A2-P2-003 | P2  | CN replay-first ProductLive 三份拷贝  | `baostock_port.py:100-118` · `cninfo_port.py:137-148` · `mootdx_port.py:134-145`                                                                        | 同构「replay fixture → MockFetchPort」仅类名不同                                          | 抽 `replay_first_mock_port(MockCls, ...)` 或 factory 内联 `return Mock(..., replay_path=REPLAY_FIXTURE)`；baostock 网络 fallback 保留在 factory 分支             | 08A 三源测（`test_r3h08` S08-02 段）仍绿；rehearsal 负向不受影响                                      |

已对抗搜索：`product_live_ports.py`、`live_tier_router.py`、`product_live_gate.py`、`fetch_ports/*` diff 全量；对照 `live-tier-architecture.md` §3、`ADR-027`、`to-issues-slices.md` S08-01–04 AC。`bis`/`deribit` 真 live 实现、`product_live_gate`/`live_tier_router` 薄模块判为计划内合理增量。
