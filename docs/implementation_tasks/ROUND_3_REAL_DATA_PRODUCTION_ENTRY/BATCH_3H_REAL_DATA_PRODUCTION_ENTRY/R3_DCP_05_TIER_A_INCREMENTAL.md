# R3-DCP-05 — Tier A 全源增量 + 产品真网 + 11/11 clean 写入

> **规划 ID：** R3-DCP-05  
> **Wave：** 4a · **并行按源**（见 Trellis `to-issues-slices.md`）  
> **Trellis：** `.trellis/tasks/wave4-r3-dcp-05-tier-a/` · Plan v4.1  
> **Module：** D1 Sync · E1 `qmd data` CLI · A2 schema（migration 015）  
> **评级：** D1/E1/C3 `R4→R5`；A2 批/3 +1  
> **用户裁决（2026-07-02）：** **11/11 Tier A 源必须 clean 表 upsert**，禁止 staging-only ponytail。

---

## 1. Goal（人话）

把 Wave 3 在 baostock + fred 上跑通的「读库水位 → 只拉新增 → 写 clean → CLI 可重复跑」，推广到 **全部 11 个 Tier A 主源**；并修 **baostock 产品 sync 永远 mock** 的硬伤。每个源增量写后必须落在 **R3H-06 契约下的 clean 表**（含本票新增表），不是只写 staging。

---

## 2. 价值

- Wave 4 主线 **R3-DCP-05** 硬交付；解锁 DCP-06 五轴「Tier A clean 真输入」
- 台账关账：`ACC-BAOSTOCK-NO-LIVE`；承接 `ACC-EASTMONEY-TAXONOMY-001`（文档/registry，不关 `R3-B2.75-REQ2-EM`）
- 验证 Tier A 增量模式可复制（Wave 5 PASS 前置）

---

## 3. 约束

| 约束        | 要求                                                                                             |
| ----------- | ------------------------------------------------------------------------------------------------ |
| 金路径      | `DataSourceService` + `run_incremental`；禁止 adapter bypass                                     |
| 真网        | `QMD_ALLOW_LIVE_FETCH=1` + 源级 key；默认 replay；隔离库 `--no-dry-run`                          |
| 主库        | 禁止 silent 写 canonical `data/duckdb/`                                                          |
| Schema      | **migration 015**（`us_disclosure_clean` · `crypto_derivative_clean` + staging）；见 **ADR-028** |
| 11/11 clean | 每源至少 1 个 registry primary domain → `resolve_clean_write_target` → clean upsert e2e 绿       |
| Registry    | 主会话排队 merge 三件套                                                                          |
| 参考项目    | Plan L1/L2/L3 **仅** `参考项目/**`；仓内 Wave 3 = 承接，不进借鉴梯                               |

---

## 4. 架构触点

```text
qmd data sync --source-id <tier_a> [--domain ...] [--no-dry-run]
  → product live gate + sandbox guard
  → read_*_watermark(clean)
  → build_*_incremental_service(use_mock=not live)
  → DataSyncOrchestrator.run_incremental
  → clean upsert（security_bar_1d | axis_observation | cn_announcement_clean | us_disclosure_clean | crypto_derivative_clean）
```

**Tier A（11）：** `fred` `us_treasury` `sec_edgar` `cftc_cot` `bis` `world_bank` `alpha_vantage` `deribit` `baostock` `cninfo` `mootdx`

---

## 5. Acceptance criteria

- [x] migration 015 应用；`test_schema_migration` / `test_migration_coverage` 绿
- [x] `clean_write_targets` 覆盖 11 源 canonical incremental domain（见 ADR-028 矩阵）
- [x] baostock：`QMD_ALLOW_LIVE_FETCH=1` 时 sync `use_mock=False`；`ACC-BAOSTOCK-NO-LIVE` 关
- [x] 11 源各有 watermark 单测 + replay 增量 e2e **写 clean** 测
- [x] 11 源 `qmd data sync`（或等价）dry-run 可审计
- [x] `research/reference-adoption-dcp05.md` 含参考项目 L1/L2/L3（非仓内代码）
- [x] 东财/校验口径 SSOT 文档/registry 更新（不关 REQ2-EM）
- [x] Plan v4.1 包齐；`validate-plan-freeze` exit 0
- [x] `uv run pytest -q` exit 0

> **AC 勾选证据（契约关账顺序 · 2026-07-02）：** 下列门禁均在本节 `[x]` 之前或同日跑绿：`uv run pytest -q` exit 0 · `python .trellis/scripts/task.py validate-plan-freeze .trellis/tasks/wave4-r3-dcp-05-tier-a` exit 0 · `validate-repair-close` exit 0。详见 `.trellis/tasks/wave4-r3-dcp-05-tier-a/research/contract-compliance-evidence.md`。

## 6. 非目标

- FRED **live primary** 关账（`B2.5-O-05`）
- 五轴 G12（DCP-06）、有界 backfill CI（DCP-09）
- Tier B/C 增量
- 新生产 cron 矩阵（Batch 6）

---

## 7. Trellis 入口

- **任务目录：** `.trellis/tasks/wave4-r3-dcp-05-tier-a/`
- **Execute 首读：** `research/00-EXECUTION-ENTRY.md`
- **INDEX：** `R3_DCP_TO_ISSUES_INDEX.md` §7
