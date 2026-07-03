# M-DATA-03 — 11 源 Tier A 真网增量（隔离库验收）

> **Module ID：** C3, D1, E1, E2, F0, B2（主）；评级目标 **R3→R4 真网 scope**  
> **活规划：** `PROJECT_IMPLEMENTATION_ROADMAP.md` §3.1 · §1.8  
> **Trellis：** `.trellis/tasks/m-data-03-tier-a-live/` · Plan v4.1  
> **前置：** Wave 4 R3-DCP-05 CLOSED（11 源 replay incremental + clean 逻辑）  
> **用户裁决 @ 2026-07-02：** 11/11 源须真网；无 ADR 例外（路线图 §0.3.4）

---

## 1. 目的

在 **隔离库**（`.audit-sandbox` / 专用 `DATA_ROOT`）内，让 11 个 Tier A 主数据源每一条都完成：

```text
真连网 → incremental sync → clean 写库 → inspect/health 绿
```

Wave 4 DCP-05 已证明 **replay/mock 金路径**；本票把 **真网** 变成验收主路径，禁止用全 mock e2e 冒充模块完成。

## 2. 价值

- 解锁 **M-G1-03**（五轴需要宏观/行情真 clean 输入）
- 诚实抬升 C3/D1/E1/E2/F0/B2 至 **R4 真网 scope**（`MODULE_COMPLETION_RATING.md`）
- 为 **M-PASS-01** 清单第 1 项提供可复验证据

## 3. 不在范围

- 新 migration DDL（R3H-06 / ADR-028 已封板；新 DDL → Batch6）
- Layer1/2/4/5 建模（→ M-G1/G2/G4/G5-FULL）
- Round4 产品面（API/前端/Agent）
- 24 源 Tier B/C 全自动 cron 矩阵
- `web_search` 真 API（post-Round4）
- 主库 `data/duckdb/` 写入（**零主库污染**）

## 4. 约束

| 约束        | SSOT                                                              |
| ----------- | ----------------------------------------------------------------- |
| Sync 金路径 | ADR-025 · `DataSourceService` + `run_incremental`                 |
| 真网闸      | ADR-027 · `QMD_ALLOW_LIVE_FETCH=1` + `product_live_gate`          |
| Clean 域    | ADR-028 · migration 015 · `clean_write_targets.py`                |
| 隔离验收    | ADR-034 · 本票新建                                                |
| 参考采纳    | `reference_adoption_guardrails.yaml` · L 梯仅 `参考项目/**`       |
| 仓内承接    | DCP-05 增量逻辑 **不标 L 梯**；Execute 复用 `ops/*_incremental_*` |

## 5. 验收（AC）

> **Plan R2（2026-07-03）：** 下列 R1 条目已被 Trellis `research/plan-revision-r2.md` §2 **完全取代**（用户锁定口径）。Execute 关账 **只认** R2 §2 + `specs/contracts/live_tier_a_evidence_v1.yaml`，不得按本节 R1 泛化表述过关。

### 5.1 R2 验收（SSOT · 取代下列 R1 枚举）

见 `.trellis/tasks/m-data-03-tier-a-live/research/plan-revision-r2.md` §2（10 条）：证据契约 · 统一 JSON 报告 · 四族 F0 · B2 主路径 · E2 inspect · dispatch 去重 · CI · 禁 SKIP · MCR R4。

### 5.2 R1 历史条目（已由 R2 §2 取代 · 只读对照）

1. `research/tier-a-live-eligibility.md`：11/11 源资格矩阵（仍有效作 KEY 参考）
2. 每源 live pytest — R2 改为统一 acceptance 层 + 契约 manifest
3. `tier_a_live_acceptance.py` 11/11 — R2 须含 F0/B2/E2 全门控 + `--report` JSON
4. inspect/health — R2 须四族 `run_data_health_profile`；**禁止 SKIP**
5. `uv run pytest -q` + Audit — 仍适用
6. MCR R4 — R2 §2#9；证据 `archive/non-plan/execute/r2-tier-a-live-accept-evidence.md`

## 6. 参考项目与借鉴三等级（Execute RED 前读 `reference-adoption-m-data-03.md` §0）

```yaml
# 借鉴梯（仅 参考项目/**）
adoption_ladder:
  L1_direct_copy: 无 — 本票 0 项
  L2_copy_and_rewrite:
    - 参考项目/digital-oracle/.../bis.py L54–66 → 仓内 bis_incremental_* 窗参数
  L3_architecture_or_concept_only:
    - OpenBB fetcher 三阶段
    - EasyXT 日期窗/交易日概念（非拷贝）
  forbidden:
    - EasyXT unified_data_interface silent fallback
    - sys.path / runtime import 参考树
    - OpenBB Provider/Fetcher runtime 拷贝

# 仓内（不进借鉴梯）
qmd_internal_reuse:
  - backend/app/sync/orchestrator.py
  - backend/app/ops/*_incremental_*.py
  - backend/app/datasources/product_live_*.py
  - backend/app/datasources/service.py
  label: 直接复用  # 禁止写 L1
```

## 7. Trellis 路由

- **Execute entry：** `research/00-EXECUTION-ENTRY.md`
- **切片 SSOT：** `research/to-issues-slices.md`
- **并行协议：** `research/parallel-dispatch-protocol.md`
