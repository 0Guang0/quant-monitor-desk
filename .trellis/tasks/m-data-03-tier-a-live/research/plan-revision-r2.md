# M-DATA-03 Plan Revision R2（2026-07-03）

> **状态：** Plan 生效中 · **取代：** Plan R1 partial F0 + SKIP 终态  
> **权威顺序：** `docs/` + `specs/` > 借鉴三等级（`参考项目/**`）> 仓内未成熟实现  
> **⚠️ 本文件 §2 AC 为用户锁定口径，Plan/Execute 不得修改**

## 1. 为何重写

| 问题      | R1 Plan                        | R2 口径（用户 + 活卡 + ROADMAP）                             |
| --------- | ------------------------------ | ------------------------------------------------------------ |
| F0 health | partial + SKIP 可过            | 每源 canonical `qmd data health`；**禁止 SKIP 当过关**       |
| B2        | 旁路抽查                       | 11 源 clean 后 **DataQualityValidator 主路径**；MCR B2→R4    |
| 证据      | 依赖仓内 hash bundle           | **`specs/contracts/live_tier_a_evidence_v1.yaml` SSOT**      |
| dispatch  | `_live_sync_registry` ponytail | **全量去重**；live 走 DCP-05 + DataSourceService 金路径      |
| CI        | 仅本地 11/11                   | nightly `--quick` + `workflow_dispatch` 全量 + JSON artifact |
| 失败      | 未分类                         | `FAIL_FIXABLE` 必修 · `FAIL_EXTERNAL` 须 ADR                 |
| 验收层    | 源间口径不一                   | **11 源同一验收层**（统一信封 + 分域规则）                   |

## 2. R2 完成条件（AC — 用户锁定）

1. `live_tier_a_evidence_v1.yaml` 实现闭合：11 源落盘 + acceptance 读取
2. 11 源统一验收报告 JSON；每源 `failure_class` 明确；**无 SKIP**
3. F0：`run_data_health_profile` 支持 `market_bar_p0` · `layer1_observation_p0` · `disclosure_p0` · `crypto_derivative_p0`
4. B2：每源 `validate_table` 按 `source_bindings` 跑通
5. E2：`DbInspector.inspect()` 非 FAIL
6. dispatch 重构完成；mootdx 纳入 `platform_source_matrix.yaml`；无 acceptance bypass
7. CI：nightly quick + manual 11/11；失败 artifact
8. `uv run pytest -q` exit 0；11/11 live exit 0（或 FAIL_EXTERNAL 全 ADR）
9. MCR：C3/D1/E1/E2/F0/B2 诚实 R4 sandbox scope
10. Execute 关账证据齐备（非 Plan 产物；Execute 阶段写入 `archive/non-plan/execute/`）

## 3. 切片 SSOT

见 `research/to-issues-slices.md` § R2 依赖图。

## 4. 借鉴三等级（R2）

| 能力                          | 等级         | 来源                                                |
| ----------------------------- | ------------ | --------------------------------------------------- |
| bar/macro health profile 扩展 | L2           | EasyXT integrity_checker / smart_data_detector 类别 |
| 宏观 API 窗                   | L2           | digital-oracle bis 窗参数（仓内已实现）             |
| Fetch 三阶段                  | L3           | OpenBB Fetcher 概念                                 |
| 结构化验收 JSON               | L3           | JQ2PTrade report 形状                               |
| silent fallback               | forbidden    | EasyXT unified_data_interface                       |
| sync/clean 管道               | 仓内直接复用 | DCP-05（R2 去重包装层）                             |

## 5. 归档（非 Plan 产物）

| 路径                                   | 内容                                    |
| -------------------------------------- | --------------------------------------- |
| `research/archive/plan-r1-superseded/` | R1 Plan 审计报告 · 旧 doubt logs        |
| `research/archive/non-plan/execute/`   | R1 live 证据 · execute 参考读           |
| `research/archive/non-plan/audit/`     | Audit 维度报告 · gitnexus-audit-summary |
| `research/archive/non-plan/repair/`    | Repair ledger · doubt repair            |
| `archive/audit/`                       | AUDIT.plan 旧版 · audit.report · jsonl  |
| `archive/repair/`                      | REPAIR.plan                             |
| `archive/execute/`                     | loop_manifest · evidence_index          |
