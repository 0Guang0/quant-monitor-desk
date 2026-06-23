# 对抗性 Plan 审计 — 06-24-round3-021-layer3-snapshot

**审计模式：** Plan-only（只读；未改 MASTER/AUDIT/plan.freeze）  
**审计日期：** 2026-06-24  
**对照：** `021_implement_layer3_snapshot_builder.md`（无独立 `PROMPT_21_*.md`）、020 MASTER、`ROUND3_BATCH_IMPLEMENTATION_MAP.md` §4.2 Batch 4、020 `pre-execute-adversarial-audit.md`  
**门禁复跑：** `python .trellis/scripts/task.py validate-plan-freeze` → exit 0（2× authority_graph WARN 非阻塞）

---

## Verdict

**PLAN_NEEDS_FIX**

**BLOCKING 计数：** 4

主会话在 `task.py start` / Execute 前须修订 MASTER（及必要时 §5.3 / §6）；当前计划骨架扎实、defer 边界优于 020 冻结前，但 **lineage AC 与测试断言脱节**、**快照产物字段契约未冻结**、**工程纪律条文不完整**，足以让 Execute 实现分叉或 Audit A1/A5 争议。

---

## 对抗性检查矩阵

| #   | 检查项                                                                   | 结论                                                                                                                                                                            |
| --- | ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | PROMPT_21 AC → MASTER §2 / §8                                            | **PASS** — 权威为 `021_implement_layer3_snapshot_builder.md`；`source-index.md` / `original-plan-trace.md` 七项 AC 均映射 §8.2–8.6 / §10                                        |
| 2   | 权威文档 / API / layer3_chains specs                                     | **PARTIAL** — lineage contract、module §8.12.6、L2 模式已索引；缺 **快照行 / mapping view 冻结 schema**；Map §4.2 部分 Bundle 未进 implement.jsonl                              |
| 3   | ADV-R3X-LINEAGE-001 / R3Y 执行者上下文                                   | **PASS** — §3.2 + 停止条件 #7 明确；优于 020 冻结前                                                                                                                             |
| 4   | §8 测试策略充分性                                                        | **FAIL** — AC-021-2 断言窄于 AC 文案；缺 `agent_outputs_not_source`；`incrementalRebuild` 已 defer 且登记                                                                       |
| 5   | AUDIT 维度 / A6 SKIP                                                     | **PASS** — A1–A8 齐；A6「无 hot path」合理                                                                                                                                      |
| 6   | forbidden/allowed vs Map                                                 | **PASS** — `worktree-slices.md` ≡ MASTER §3.3；与 Map Batch 4 staged fixture 策略一致                                                                                           |
| 7   | B-19 / α-2 / registry                                                    | **PARTIAL** — `R3-B23A` 前置已写；**未声明与并行轨 B-19（staged pilot v2）无文件冲突**；`ADV-R3X-LINEAGE-001` 仍缺三 registry 行（已 defer 至 hygiene slice，Execute 不得误关） |
| 8   | 工程纪律（karpathy / testing / TDD / ponytail / 中文注释 / full pytest） | **PARTIAL** — §0.3a + §11 覆盖大部分；**缺**「不得弱化测试目的」「修复后 full pytest」显式条文；中文注释字段名与项目惯例不完全一致                                              |
| 9   | validate-plan-freeze                                                     | **PASS** exit 0；`context_pack.json` **空壳** 不触发校验错误                                                                                                                    |
| 10  | 快照产物 interface/schema                                                | **FAIL** — §6.2 API 示意有；**行级字段 / mapping view 结构未冻结**                                                                                                              |

---

## 发现清单

| ID        | 级别         | Finding                                                                                                                                                                                                                                                                                                                                                                                                                                           | Plan section              | Required plan fix                                                                                                                                                                                                                  |
| --------- | ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| AA-021-01 | **BLOCKING** | **AC-021-2** 要求 lineage envelope 含 **contract 全部必需字段**；§5.3 `test_snapshotLineageContainsSourceHashes` 断言语义仅写「`source_content_hashes` 非空」。L2 同名测试遍历 `LINEAGE_REQUIRED_FIELDS`（`test_layer2_sensor_loader.py`）。Execute 可按窄断言实现，Audit A1 将以 contract yaml 判 FAIL。                                                                                                                                         | §2 AC-021-2；§5.3；§8.2   | §5.3 将 AC-021-2 断言改为：对 `LINEAGE_REQUIRED_FIELDS` 逐字段 `is not None`（`rebuild_reason` 可空）；或增 `test_layer3Snapshot_lineageRequiredFieldsComplete` 并绑定 §8.2 RED。引用 `assert_lineage_fields_complete` / L2 模式。 |
| AA-021-02 | **BLOCKING** | **`IndustryChainDailySnapshotRow` 字段子集未冻结**。`layer3_industry_shock_anchor.md` SQL 含 `pct_change_1d/5d`、`amount`、`open_interest`、`latest_event_*`、`quality_flags` 等；MASTER §6 仅 API 签名，§8.1 无 staged 子集表。Execute 与 Audit A1 对「021 必须填哪些列」无 SSOT。                                                                                                                                                               | §4；§6；§8.1              | 新增 **§6.3 Staged snapshot row 字段冻结表**（必填 / 可选 / event_only 禁止），显式引用 module §8.12.6–8.12.8 的 staged 子集；与 D-09「不复制 L1 全量字段」对齐。                                                                  |
| AA-021-03 | **BLOCKING** | **`Layer5MappingView` 结构未定义**。AC-021-5 仅测 `instrument_id + close`；Map §4.2 要求「Layer5 mapping view」可验收。缺 `volume`、`trade_date`、`as_of_timestamp` 等是否必填。                                                                                                                                                                                                                                                                  | §2 AC-021-5；§6           | 新增 **§6.4 Layer5MappingView 冻结**（字段名、类型、与 `manifest.yaml` bar 条目映射）；§5.3 断言与表对齐。                                                                                                                         |
| AA-021-04 | **BLOCKING** | **工程纪律条文不完整**（协调者/用户强制项）。§0.3a 有 ponytail + TDD 顺序；§11 列 skill；但 **未** 写：① 每步 GREEN 后 MUST Read `incremental-implementation`；② 代码修复后 MUST 跑 `uv run pytest -q`（或 §10 Tier B 时机）；③ **禁止**为通过测试而修改测试目的/弱化断言；④ 测试 docstring 须含 **覆盖范围 / 测试对象 / 目的**（§5.0 用 `purpose/target/verifies` 与仓库用户规则不一致）。020 §0.3a 另有「违反 ponytail → 停止当前步」021 缺失。 | §0.3a；§5.0；§11          | 见下文 **「建议追加 MASTER 条文」**；同步 §11 表注「GREEN 前 karpathy；GREEN 后 incremental-implementation + 当前步 pytest」。                                                                                                     |
| AA-021-05 | NON-BLOCKING | **`context_pack.json` 空壳**（`modules`/`source_authorities`/`tests` 均为 `[]`）。`implement.jsonl` slot 2 声明 `authority graph routing`，Execute Boot 无法从 pack 机器路由，只能回退全文 implement.jsonl。`validate-plan-freeze` 仍 exit 0。                                                                                                                                                                                                    | `context_pack.json`；§0.4 | Execute 前运行 `context_router.py --task <dir>` 填充 pack；或在 MASTER §0.4 写明「空 pack 时以 implement.jsonl 为唯一路由」以免双轨歧义。                                                                                          |
| AA-021-06 | NON-BLOCKING | **Map §4.2 Batch 4 Plan bundle 部分未进 implement.jsonl**：`layer3_loader_contract.yaml`、`ADR-0004`、`layer3_config_health_check.md`、`schema.sql`、`duckdb_and_parquet.md` 未列。021 不改 loader contract，但 A1 对照 loader 输入语义时 Execute 可能未读。                                                                                                                                                                                      | implement.jsonl；§1.6     | 在 implement.jsonl 增 pointer 行（`for: §8.3 loader 输入边界`）或在 MASTER §1.6 归并表声明「loader contract 只读继承 020，021 不扩硬规则」。                                                                                       |
| AA-021-07 | NON-BLOCKING | **无 `PROMPT_21_feature_round3_021_layer3_snapshot.md`**。Round 3 并行提示词索引止于 PROMPT_20；本任务用正式任务卡 + Trellis task，可接受。                                                                                                                                                                                                                                                                                                       | PLAN_BOOT                 | 在 `source-index.md` §A 注「无 PROMPT_21；权威 = 021 任务卡 + MASTER」。                                                                                                                                                           |
| AA-021-08 | NON-BLOCKING | **`price_proxy_needs_feed` / commodity 价锚**（module §8.12.5–6）未在 §3.2 defer。021 用 staged MSFT 类 fixture 可能不触发，但 Execute 读 module 全文可能超 scope。                                                                                                                                                                                                                                                                               | §3.2                      | §3.2 增一行：`price_proxy_needs_feed` 阻断逻辑 → defer `022`/live L5；021 staged fixture 不覆盖 commodity proxy。                                                                                                                  |
| AA-021-09 | NON-BLOCKING | **`test_incrementalRebuildPreservesAsOfBoundary`** 在 contract `validation_tests` 中，MASTER §3.2 已 defer Batch 5+。登记充分；建议在 §5.3 脚注「contract 第三条 validation_test 不在 021 Execute RED」。                                                                                                                                                                                                                                         | §3.2；§5.3                | 脚注一行即可。                                                                                                                                                                                                                     |
| AA-021-10 | NON-BLOCKING | **AUDIT A8「空 loader 结果」** 仅 Audit 补测，MASTER §5.3 未列（与 020 模式一致）。Acceptable；建议在 §5.3 脚注指向 A8。                                                                                                                                                                                                                                                                                                                          | §5.3；AUDIT §2 A8         | 可选：§5.3 增「Audit-only」行避免 Execute 与 Audit 责任混淆。                                                                                                                                                                      |
| AA-021-11 | NON-BLOCKING | **并行轨 B-19**（`06-24-round3-real-data-staged-pilot-v2`）与 021 无文件重叠，但 MASTER 未写「不得等待 B-19 merge」。                                                                                                                                                                                                                                                                                                                             | §1.2                      | §1.2 增一句：前置仅为 `020` merged + staged gate；**不**依赖 B-19 / registry hygiene slice 完成。                                                                                                                                  |
| AA-021-12 | NON-BLOCKING | **`agent_outputs_not_source`**：L1/L2/023A 有专测；021 lineage 计划未要求。contract `constraints` 含此条。                                                                                                                                                                                                                                                                                                                                        | §5.3；§8.2                | 建议 §8.2 增可选 RED：`source_dataset_ids` 含 agent 文案 → 拒绝（复用 `validate_source_dataset_ids`）。非阻塞若 A1 接受 staged fixture 不覆盖。                                                                                    |
| AA-021-13 | NON-BLOCKING | **integration-audit.md** 声称六类「无缺口」，未像 020 对抗审计那样质疑 §5.3 与 contract 粒度。                                                                                                                                                                                                                                                                                                                                                    | research                  | Plan 修订后刷新 integration-audit 一行 caveat。                                                                                                                                                                                    |

---

## 建议追加 MASTER 条文（工程纪律 — 供主会话粘贴）

在 **§0.3a** 末尾追加（或替换为完整小节）：

```markdown
### 0.3b Execute 工程纪律 — 测试与回归（强制）

1. **TDD 不可跳过**：每个 §8.x 步 MUST 先 RED（失败）→ Read `karpathy-guidelines` + `testing-guidelines` → 再 GREEN；禁止先写实现再补测试。
2. **每步 GREEN 后** MUST Read `incremental-implementation`；仅跑当前步 RED 用例 + 已绿用例（§10）；**Tier B 全库 `uv run pytest -q` 仅 §8.6 一次**。
3. **任何代码修复后**（含测试调整、ruff、review fix）MUST 至少跑当前任务 L1：`uv run pytest tests/test_layer3_snapshot_builder.py -q`；§8.6 前不得跳过 Tier B。
4. **禁止弱化测试目的**：不得为通过测试而删除业务语义断言、降低 AC 覆盖面或改写测试目标；允许重构测试实现，但 `purpose`/`verifies` 所指 AC 不变。
5. **测试注释（中文）**：每个 `test_*` 须含 **覆盖范围**、**测试对象**、**目的**（可与 `purpose`/`target`/`verifies`/`failure_meaning` 并列，但三者必填）。
6. **ponytail 违规**：过度抽象、重复 L2 已有 helper、未请求新依赖 → **停止当前 §8 步**，删 bloat 后再 GREEN；GREEN 证据含 `ponytail: reused <symbol>` 或 `ponytail: no new helper`。
```

在 **§11** 表 `incremental-implementation` 行加注：`每步 GREEN 后必做（§0.3b-2）`。

---

## AC → §8 映射（复检 PASS）

| 任务卡 / AC           | MASTER   | §8 步    | 测试名                                                                   |
| --------------------- | -------- | -------- | ------------------------------------------------------------------------ |
| §1 snapshot + L5 view | AC-021-1 | 8.3      | `test_layer3Snapshot_buildsFromStagedLoaderAndL5_success`                |
| §15 lineage           | AC-021-2 | 8.2      | `test_snapshotLineageContainsSourceHashes`（**断言待加强 — AA-021-01**） |
| §15 as_of             | AC-021-3 | 8.4      | `test_snapshotRejectsFutureInput`                                        |
| §8.12.6 event_only    | AC-021-4 | 8.5      | `test_layer3Snapshot_eventOnly_skipsPriceFields`                         |
| §2 L5 mapping         | AC-021-5 | 8.3      | `test_layer3Snapshot_layer5MappingView_nonEventOnly`                     |
| §16 staged-only       | AC-021-6 | 8.3      | `test_layer3Snapshot_nonStagedL5Source_rejects`                          |
| §11 验收              | AC-021-7 | 10 / 8.6 | Tier A + batch3 gate                                                     |

附加 fail-fast：`test_layer3Snapshot_missingL5Bar_rejects` → §8.3（非独立 AC，合理）。

---

## 测试覆盖评估（§8 策略）

| 能力                    | 计划覆盖      | 缺口                                        |
| ----------------------- | ------------- | ------------------------------------------- |
| staged builder 成功路径 | §8.3          | OK                                          |
| lineage contract        | §8.2          | **AA-021-01** 全字段                        |
| no_future_data          | §8.4          | OK；与 contract 测试名对齐                  |
| event_only              | §8.5          | OK                                          |
| staged-only L5          | §8.3          | OK；`manifest.source_mode` 机制 §6.1 已冻结 |
| 空 loader / 坏 manifest | A8 Audit-only | 可接受                                      |
| incremental rebuild     | defer §3.2    | 已登记                                      |
| registry VR (R3Y)       | defer §3.2    | 已登记；Execute 不改三 registry             |

---

## AUDIT.plan 维度完整性

| 维            | 状态     | 备注                                 |
| ------------- | -------- | ------------------------------------ |
| A1 spec       | 必做     | 依赖 §6 快照字段冻结（AA-021-02/03） |
| A2 ponytail   | 必做     | OK                                   |
| A3 security   | 必做     | staged + forbidden OK                |
| A4 quality    | 必做     | OK                                   |
| A5 completion | 必做     | AC trace + sandbox OK                |
| A6 perf       | **SKIP** | §2.2 理由充分：小 fixture、无 SLA    |
| A7 ops        | 必做     | 无 DB 写 OK                          |
| A8 test-gap   | 必做     | 空 loader 补测 OK                    |

---

## 相对 020 MASTER 模式 — 改进与退步

**改进：**

- §3.2 显式登记 `ADV-R3X-LINEAGE-001` / `R3Y-LINEAGE-VR-001`（020 冻结前对抗审计 Top3 之一）。
- §6.1 staged L5 `manifest.yaml` + `source_mode` 机制已冻结（020 曾缺 bundle mode 定义）。
- §5.3 与 §8 RED 命令用例名对齐（020 曾 §8.5 `-k cross_chain` 脱节）。

**退步 / 仍存：**

- lineage 测试粒度仍窄于 AC 文案（类同 020 contract 七条 vs §5.3 部分覆盖）。
- 产物 schema 冻结弱于 loader 阶段对 contract 七条的显式表格式。

---

## 主会话 Must-Fix 列表（按优先级）

1. **AA-021-01** — 加强 AC-021-2 / §5.3 / §8.2 lineage 全字段断言（对齐 L2 `LINEAGE_REQUIRED_FIELDS` 循环）。
2. **AA-021-02** — 冻结 `IndustryChainDailySnapshotRow` staged 字段子集（§6.3）。
3. **AA-021-03** — 冻结 `Layer5MappingView` 结构与 manifest 映射（§6.4）。
4. **AA-021-04** — 追加 §0.3b 工程纪律（测试回归、禁止弱化测试目的、中文覆盖范围/对象/目的、ponytail 停损）。

**建议修（非阻塞）：** AA-021-05 context_pack 填充；AA-021-06 Map bundle pointer；AA-021-08 price_proxy defer；AA-021-11 B-19 独立性声明。

---

## Post-audit fixes (2026-06-24)

| ID            | Status                                         |
| ------------- | ---------------------------------------------- |
| AA-021-01..04 | **FIXED** in MASTER §0.3b / §5.3 / §6.3 / §6.4 |
| Verdict       | **PLAN_READY**                                 |

- staged-only 边界、forbidden 列表、D-09、023A lineage contract 写权限与 020 一脉相承且更清晰。
- defer 登记表（§3.2）可直接防止 Execute 误关 ADV-R3X / 误改三 registry。
- §6.1 L5 staged bundle 协议具体可执行（`STAGED_LAYER3_L5_BARS_DIR`、`source_mode`、体量上限）。
- vertical-slices → §8.0–8.6 一一对应；Tier B 仅 §8.6 执行一次（§10 写死）。
- `test_catalog.yaml` 已登记 `test_layer3_snapshot_builder.py`；Plan skeleton 可 import。

---

## Verification Story

- **Tests reviewed:** 是 — `test_layer3_snapshot_builder.py` 为 Plan skip 骨架；§5.3 为 Execute 契约；对照 L1/L2 lineage 测试模式。
- **Build verified:** 否 — Plan-only。
- **Security checked:** 是（静态）— staged-only、无 prod DB、forbidden 路径充分。
- **validate-plan-freeze:** exit 0（2026-06-24 复跑确认）。
