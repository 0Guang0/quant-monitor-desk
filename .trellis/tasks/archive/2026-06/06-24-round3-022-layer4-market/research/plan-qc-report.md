# Plan 质检报告 — 022 Layer 4 Market Structure

> **Agent-2** · Wave C · 模型 `composer-2.5` · 2026-06-24  
> 任务：`06-24-round3-022-layer4-market` · worktree `quant-monitor-desk-wt-022-layer4`

---

## 0. 结论摘要

| 项                         | 结果                                                                                                                                         |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| **遗留项数**               | **0**                                                                                                                                        |
| **`validate-plan-freeze`** | **exit 0**（Agent-2 复检通过）                                                                                                               |
| **§3.1 21 行**             | 零遗漏                                                                                                                                       |
| **§3.3 21 行**             | 零遗漏（含 2 项路径纠偏已登记）                                                                                                              |
| **可否派发 Execute**       | **是** — Plan 冻结合格；Execute 与 C-20 **可并行**                                                                                           |
| **Audit 派发**             | **否（暂）** — playbook §4.3：C-20 与 022 的 Audit 链主会话**串行**；须等 C-20 Execute 完成并先进入 Audit 链（或 022 先完成则 022 先 Audit） |

---

## 1. playbook §3.6 核对清单

| 检查项                                                      | 状态                                   |
| ----------------------------------------------------------- | -------------------------------------- |
| §3.1 共用底座每一行已索引或 MASTER 标明                     | ✅                                     |
| §3.3 022 专属每一行已索引或纠偏登记                         | ✅                                     |
| `authority_graph` / `context_pack.json` 含 `layer4_markets` | ✅                                     |
| 任务卡 §3 输入与 playbook §3.3 无缺口                       | ✅                                     |
| 发现项已写回 MASTER / manifest 并修复                       | ✅（`integration-audit.md` 待跑→已跑） |
| playbook §2.2 / §2.2.1 / §2.2.2 / §2.3 已入 MASTER          | ✅ §0.3a–0.3b                          |
| playbook §8.2 子 AC → MASTER §2.1                           | ✅                                     |
| MAP §2.2 worktree / allowed / forbidden                     | ✅ MASTER §1.2–§1.3 / §3.3             |

---

## 2. SCI-A — playbook §3.1（21 行）

| #   | 路径                                                          | MASTER §12 | implement.jsonl | 摘要                                  | 遗漏风险 |
| --- | ------------------------------------------------------------- | ---------- | --------------- | ------------------------------------- | -------- |
| 1   | `WAVE_C_MAIN_SESSION_COORDINATOR_PLAYBOOK.md`                 | ✅         | L7              | Wave C 派发、PASS、模型、测试铁律     | 无       |
| 2   | `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §2.2–§2.6                | ✅         | L42             | worktree、allowed/forbidden、验证命令 | 无       |
| 3   | `.trellis/spec/guides/round3-repair-debt-worktree-plan.md` §6 | ✅         | L43             | 一分支一核心文件组                    | 无       |
| 4   | `docs/AUDIT_DEFERRED_REGISTRY.md`                             | ✅         | L37             | defer ID 只读                         | 无       |
| 5   | `docs/UNRESOLVED_ISSUES_REGISTRY.md`                          | ✅         | L38             | 操作面 OPEN 项                        | 无       |
| 6   | `docs/RESOLVED_ISSUES_REGISTRY.md`                            | ✅         | L39             | 防重复打开                            | 无       |
| 7   | `docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md`  | ✅         | L40             | ID→分支映射                           | 无       |
| 8   | `docs/ROUND3_HANDOFF.md`                                      | ✅         | L36             | Round 3 staged-only 语境              | 无       |
| 9   | `docs/quality/staged_acceptance_policy.md`                    | ✅         | L23             | 分阶段验收                            | 无       |
| 10  | `docs/quality/production_live_pilot_policy.md`                | ✅         | L25             | 不得声称 production-live              | 无       |
| 11  | `docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md`               | ✅         | L24             | Batch 3 staged 门禁                   | 无       |
| 12  | `docs/quality/ROUND3_TEST_DOCSTRING_HYGIENE_PLAN.md`          | ✅         | L27             | 测试五字段 docstring                  | 无       |
| 13  | `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md`         | ✅         | L10             | docs/specs 非实现路径边界             | 无       |
| 14  | `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`          | ✅         | L11             | 语义测试 / RED-GREEN                  | 无       |
| 15  | `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md`         | ✅         | L12             | eco / ResourceGuard                   | 无       |
| 16  | `specs/contracts/runtime_versions.md`                         | ✅         | L33             | uv sync --locked 权威                 | 无       |
| 17  | `specs/contracts/write_contract.yaml`                         | ✅         | L34             | 写路径合约                            | 无       |
| 18  | `specs/contracts/resource_limits.yaml`                        | ✅         | L35             | 资源上限                              | 无       |
| 19  | `specs/contracts/snapshot_lineage_contract.yaml`              | ✅         | L32             | 快照血缘 required_fields              | 无       |
| 20  | `docs/architecture/module_boundary_matrix.md`                 | ✅         | L22             | 模块边界                              | 无       |
| 21  | `MIGRATION_MAP.md`                                            | ✅         | L41             | 实现目录与文档映射                    | 无       |

**§3.1 结论：** 21/21 已双索引（MASTER SCI-A + implement.jsonl）。

---

## 3. SCI-B — playbook §3.3（21 行）

| #   | 路径                                                                                                | MASTER §12 | implement.jsonl | 摘要                                 | 遗漏风险      |
| --- | --------------------------------------------------------------------------------------------------- | ---------- | --------------- | ------------------------------------ | ------------- |
| 1   | `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/022_implement_layer4_market_structure.md`        | ✅         | L8              | AC、验收、lineage §15、ResourceGuard | 无            |
| 2   | `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/README.md`                                       | ✅         | L15             | Layer 2–5 正式任务边界               | 无            |
| 3   | `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3Y_execution_discipline_addendum.md` | ✅         | L9              | TDD / ponytail 纪律                  | 无            |
| 4   | `docs/modules/layer4_market_structure.md`                                                           | ✅         | L16             | Layer 4 实现权威；含 §5 DDL          | 无            |
| 5   | `docs/modules/layer3_industry_shock_anchor.md`                                                      | ✅         | L17             | 上游 L3 接口语境                     | 无            |
| 6   | `docs/modules/duckdb_and_parquet.md`                                                                | ✅         | L18             | staging vs clean 分层                | 无            |
| 7   | `docs/modules/write_manager.md`                                                                     | ✅         | L19             | clean 写必经 WriteManager            | 无            |
| 8   | `docs/architecture/03_runtime_flows.md`                                                             | ✅         | L20             | Layer4 运行链路                      | 无            |
| 9   | `docs/architecture/04_data_architecture.md`                                                         | ✅         | L21             | 数据分层                             | 无            |
| 10  | `docs/quality/final_package_rules.md`                                                               | ✅         | L26             | 包与产出规则                         | 无            |
| 11  | `docs/quality/ROUND3_WAVE_B_PENDING_FIX_REGISTRY.md` §2                                             | ✅         | L28             | ADV-R3X defer 语境                   | 无            |
| 12  | `docs/adr/ADR-0004-layer3-shock-anchor-model.md`                                                    | ✅         | L30             | L3 模型依赖                          | 无            |
| 13  | `docs/decisions/` D-09 → **`docs/quality/PENDING_USER_DECISIONS.md` §D-09**                         | ✅ 纠偏    | L29             | L2–5 不复制 L1 全套标准化字段        | 无（见 §5.2） |
| 14  | `specs/contracts/layer4_market_contract.yaml`                                                       | ✅         | L31             | 主契约 models + quality_rules        | 无            |
| 15  | `specs/contracts/snapshot_lineage_contract.yaml`                                                    | ✅         | L32             | 血缘字段（与 SCI-A 共用）            | 无            |
| 16  | `specs/contracts/layer3_loader_contract.yaml`                                                       | ✅         | L54             | 上游 loader 口径                     | 无            |
| 17  | **`specs/schema/schema.sql`（仓库缺失）**                                                           | ✅ 纠偏    | — 不入 manifest | DDL → module §5 + contract models    | 无（见 §5.1） |
| 18  | `backend/app/layer3_chains/`（021 snapshot）                                                        | ✅         | L44–45, L50     | snapshot_builder + lineage + loader  | 无            |
| 19  | `backend/app/db/write_manager.py`                                                                   | ✅         | L49             | DuckDBWriteManager 写路径            | 无            |
| 20  | `tests/test_layer3_snapshot_builder.py`                                                             | ✅         | L58             | L3 回归不破坏                        | 无            |
| 21  | `tests/test_batch3_staged_downstream_gate.py`                                                       | ✅         | L53             | staged gate 回归                     | 无            |

**§3.3 结论：** 21/21 已覆盖；2 项缺失路径已在 MASTER + `source-index.md` §A 纠偏，替代口径充分。

---

## 4. 路径纠偏验证

### 4.1 `specs/schema/schema.sql` 缺失

| 检查                   | 结果                                                                                                                            |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| 仓库存在性             | **不存在**（全仓 glob 0 命中）                                                                                                  |
| MASTER 登记            | SCI-B 行 17 标明「仓库缺失」                                                                                                    |
| 替代路径 1             | `docs/modules/layer4_market_structure.md` **§5.1–5.5** 含 `market_registry` / `market_calendar` / `market_breadth_snapshot` DDL |
| 替代路径 2             | `specs/contracts/layer4_market_contract.yaml` models 字段                                                                       |
| 是否入 implement.jsonl | **否** — `validate-plan-freeze` 对缺失文件会报错；以 MASTER 纠偏行为准                                                          |
| **充分性判定**         | **PASS** — Execute 建表语义不依赖独立 schema.sql                                                                                |

### 4.2 `docs/decisions/` 缺失

| 检查            | 结果                                                                               |
| --------------- | ---------------------------------------------------------------------------------- |
| 仓库存在性      | **不存在**（目录 glob 0 命中）                                                     |
| playbook 原文   | 「`docs/decisions/` 中 D-09 相关条目（经 `PENDING_USER_DECISIONS.md` 索引）」      |
| 替代路径        | `docs/quality/PENDING_USER_DECISIONS.md` **§D-09** — L2–5 不全量复制 L1 标准化字段 |
| implement.jsonl | L29 `for: AC-022-7`                                                                |
| MASTER 映射     | AC-022-7 · §8.7 `test_marketSnapshot_noLayer5HistoryFields`                        |
| **充分性判定**  | **PASS**                                                                           |

---

## 5. 横切约束核对

### 5.1 staged-only

| 锚点                         | 覆盖                                                |
| ---------------------------- | --------------------------------------------------- |
| MASTER §0 staged limitations | BATCH3 gate + REQ2-EM DEFERRED + 无 prod DB writes  |
| AC-022-6                     | `test_marketAdapter_nonStagedSource_rejects` · §8.2 |
| §6.1 fixture 协议            | `manifest.yaml` `source_mode: staged_fixture_only`  |
| MAP §2.2 forbidden           | ops/staged 三文件、registry trio                    |
| Tier A                       | `test_batch3_staged_downstream_gate.py`             |

### 5.2 `as_of` / no-future-data

| 锚点        | 覆盖                                                                           |
| ----------- | ------------------------------------------------------------------------------ |
| 任务卡 §15  | `as_of_timestamp` 边界 + 测试证明                                              |
| AC-022-5    | `test_marketSnapshotRejectsFutureInput` · §8.6                                 |
| contract    | `snapshot_lineage_contract.yaml` + `layer4_market_contract.yaml` quality_rules |
| 停止条件 #5 | 未来 as_of → `Layer4MarketError`                                               |

### 5.3 lineage §15

| 锚点       | 覆盖                                                               |
| ---------- | ------------------------------------------------------------------ |
| 任务卡 §15 | `snapshot_id`、`as_of_timestamp`、`source_fetch_ids` 等            |
| AC-022-4   | `test_marketSnapshot_lineageRequiredFieldsComplete` · §8.4–8.5     |
| kernel     | `backend/app/core/snapshot_lineage.py` · `LINEAGE_REQUIRED_FIELDS` |
| defer 边界 | §3.2 ADV-R3X — 仅 L4 contract 子集，非全量跨层 DB 持久化           |
| forbidden  | 不得改 `snapshot_lineage_contract.yaml`                            |

### 5.4 ResourceGuard / eco

| 锚点                   | 覆盖                                      |
| ---------------------- | ----------------------------------------- |
| 任务卡 §7–§8           | 默认 eco；禁止全市场全历史扫描            |
| GLOBAL_RESOURCE_LIMITS | implement L12                             |
| resource_limits.yaml   | implement L35                             |
| AC-022-6               | staged fixture only → 不触发全市场扫描    |
| 停止条件 #8            | `RESOURCE_GUARD_PAUSED` 非预期 → 停损汇报 |
| playbook §8.2 测试行   | ResourceGuard / eco 默认未触发全市场扫描  |

---

## 6. MAP §2.2 对齐

| MAP §2.2 项                                                     | MASTER 映射  | 状态 |
| --------------------------------------------------------------- | ------------ | ---- |
| 分支 `feature/round3-022-layer4-market`                         | §0 元信息    | ✅   |
| worktree `../quant-monitor-desk-wt-022-layer4`                  | §1.2         | ✅   |
| allowed: `layer4_markets/**`, `test_layer4_market_structure.py` | §1.3 / §3.1  | ✅   |
| forbidden: ops/staged 三文件, registry trio                     | §3.3         | ✅   |
| 与 C-20 / α-3 / β-2 并行                                        | Wave C 四路  | ✅   |
| 验证: layer4 tests + batch3 gate + 全库 pytest                  | §10 Tier A/B | ✅   |

---

## 7. implement.jsonl 增补项（playbook 外，低风险）

| 路径                                         | 行     | 用途                           | 风险 |
| -------------------------------------------- | ------ | ------------------------------ | ---- |
| `.cursor/rules/ponytail.mdc`                 | L4     | §0.3a 全程强制                 | 无   |
| `research/vertical-slices.md`                | L6     | §8 顺序                        | 无   |
| `backend/app/layer2_sensors/*`               | L46–47 | L2 lineage/as_of 模式参考      | 无   |
| `specs/contracts/api_security_contract.yaml` | L55    | module_boundary 1-hop          | 无   |
| `tests/test_layer4_market_structure.py`      | L56    | Execute 创建目标（E11 豁免类） | 无   |
| `research/worktree-slices.md`                | L51    | allowed/forbidden 切片         | 无   |
| 021 archived MASTER                          | L52    | 前置 defer 延续                | 无   |

**条数：** 58（≥15 门禁满足）。

---

## 8. vertical-slices ↔ MASTER §8

| 切片            | MASTER §8 | AC         |
| --------------- | --------- | ---------- |
| SLICE-BOOT      | 8.0       | —          |
| SLICE-REGISTRY  | 8.1       | AC-022-1   |
| SLICE-ADAPTER   | 8.2       | AC-022-6   |
| SLICE-CAL-BREAD | 8.3       | AC-022-2,3 |
| SLICE-LINEAGE   | 8.4       | AC-022-4   |
| SLICE-ASOF      | 8.5–8.6   | AC-022-5   |
| SLICE-QUALITY   | 8.3/8.7   | AC-022-2,7 |
| SLICE-GATES     | 8.7 + §10 | AC-022-8   |

**结论：** `vertical-slices.md` 已冻结为 §8.0–8.7，无漂移。

---

## 9. 门禁复检

```text
$ python .trellis/scripts/task.py validate-plan-freeze .trellis/tasks/06-24-round3-022-layer4-market
Plan freeze validation passed (exit 0)
```

---

## 10. 派发建议（返回主会话）

| 轨道               | 建议                                                                                                 |
| ------------------ | ---------------------------------------------------------------------------------------------------- |
| **Execute（022）** | **可立即派发** — `composer-2.5` only；禁 `composer-2.5-fast`；入口 §0.5 开场白                       |
| **Audit（022）**   | **Execute 完成后**再派发；且须遵守 §4.3 与 C-20 **串行** — 若 C-20 先完成 Execute，C-20 Audit 链优先 |
| **主会话合并**     | 须 §6 + §8.2 全表 PASS + worktree 提交                                                               |

**Agent-2 签字：** Plan QC **PASS** · 遗留 **0** · `validate-plan-freeze` **exit 0**
