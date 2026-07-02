# Audit A1 Report — M-DATA-03 Tier A Live

## 元信息

| 字段                    | 值                                                            |
| ----------------------- | ------------------------------------------------------------- |
| 维度                    | A1 — audit-spec（trellis-check · Trace Authority · GitNexus） |
| 任务                    | `.trellis/tasks/m-data-03-tier-a-live`                        |
| `plan_protocol_version` | 4.1                                                           |
| 模板                    | `agents/audit-a1-spec.md`                                     |
| 审计日期                | 2026-07-03                                                    |
| 模型                    | composer-2.5                                                  |
| 验证                    | git diff + 独立 pytest + 代码 Read（不信文档自述）            |

---

## 维度证据

### trellis-check（步骤 1–7）

| 检查项              | 结果                 | 证据                                                                                                                                                                   |
| ------------------- | -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1. 变更范围         | PASS                 | `git diff --name-only`：27 条已跟踪修改 + 未跟踪 `backend/app/ops/tier_a_live_*.py`、`scripts/tier_a_live_acceptance.py`、`.trellis/tasks/m-data-03-tier-a-live/**` 等 |
| 2. 任务工件         | PASS（薄索引）       | `prd.md` 为 thin-index；无 `design.md`/`implement.md`（v4.1 正常）                                                                                                     |
| 3. 包上下文         | SKIP                 | `python ./.trellis/scripts/get_context.py --mode packages` 无可用输出（沙箱限制）；改用手动 Read `backend/app/ops/`                                                    |
| 4. Spec Quality     | PASS（无专用 index） | `.trellis/spec/ops/**/index.md` 不存在；对照 `plan-spec.md` Interface Contract + ADR-034/027                                                                           |
| 5. 项目检查         | PASS                 | `uv run pytest -q --tb=no` **exit 0**（~373s）；`uv run pytest tests/test_tier_a_live_harness.py tests/test_tier_a_live_dispatch.py -q` **exit 0**                     |
| 6. 跨层             | PASS                 | Storage→ops dispatch→`DbInspector`→CLI；`product_live_gate` 横切；无环 import 迹象                                                                                     |
| 7. manifest vs diff | **FAIL**             | `implement.jsonl` 仅 6 行；`check.jsonl` 2 行；diff 含 30+ 路径未登记                                                                                                  |

### Trace Authority（AUDIT.plan §0.1）

| 条目                      | 结果        | 证据                                                                                                                                                                    |
| ------------------------- | ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 活卡 scope/AC             | **PARTIAL** | 活卡 §5 AC#4 含 **data health**；`plan-spec.md` Interface Contract 仅 `sync→clean→inspect`（L49–50）；`l4-tier-a-live-accept-evidence.md` L30 口头收窄 health → nightly |
| task README / input index | PASS        | `docs/implementation_tasks/M_DATA_03_TIER_A_LIVE/` + `EXTERNAL-INDEX.md` §A 已路由                                                                                      |
| unresolved coverage       | PASS        | `integration-audit.md` doc-gap 已在 Execute 代码闭合（harness/acceptance/dispatch 存在）                                                                                |
| round map                 | PASS        | `to-issues-slices.md` 依赖图与 ENTRY §1 一致（11 源）                                                                                                                   |
| source-index              | PASS        | `EXTERNAL-INDEX.md` §C 十一源 port/ops/e2e 表与 diff 对齐                                                                                                               |
| omission-check            | **FAIL**    | `to-issues-slices.md` L11–12 要求 `execute-evidence/sNN-*.txt`；目录 **不存在**                                                                                         |
| integration-ledger        | **PARTIAL** | `plan-doubt-review.md` Cycle 10 声称 F0/E2 已进 slices；`plan-spec` Interface Contract **未同步**                                                                       |

### A1 checklist

| 项                                    | 结果                                    |
| ------------------------------------- | --------------------------------------- |
| trellis-check 1–7 有证据              | PASS（#3 SKIP 已说明）                  |
| diff vs audit/check manifest          | **FAIL**（implement.jsonl 不全）        |
| Trace Authority 继承或 explicit defer | **FAIL**（data health 未 formal defer） |
| 无 Plan omission                      | **FAIL**（execute-evidence、§2.1 Tier） |
| GitNexus 已查                         | **PARTIAL**（索引陈旧，见下）           |

### GitNexus

| 调用                                                                            | 结果                                                                           |
| ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| `query("tier_a_live incremental dispatch acceptance", repo=quant-monitor-desk)` | 返回无关符号；**未命中** tier_a_live 新符号                                    |
| `context("tier_a_live_acceptance", repo=quant-monitor-desk)`                    | **Symbol not found**                                                           |
| `context("run_acceptance", repo=quant-monitor-desk)`                            | **Symbol not found**                                                           |
| `detect_changes(scope=compare, base_ref=master)`                                | 27 files changed，仅 3 symbols（`pytest_configure` 等）；**新 ops 模块未索引** |

**结论：** 已满足「≥1 query/context」纪律，但索引 stale；审计以 git diff + Read 源码为准。

### DOUBT 对抗核对

| 问题                                 | 结论                                                               |
| ------------------------------------ | ------------------------------------------------------------------ |
| 活卡 Red Flags（零主库、11/11 真网） | 已进 ENTRY §2 / slices；代码 `assert_isolated_live_data_root` 落地 |
| plan-doubt-review Cycle 10（F0/E2）  | slices 已写；**plan-spec Interface Contract 未下沉** → 链 A 丢义   |
| AUDIT.plan §1 PASS 门槛              | 活卡 §5 全勾 **不能**在 data health 缺口下成立                     |

### 代码锚点（spec 契约 vs 实现）

| 契约来源                       | 要求                               | 代码/文档实况                                                 |
| ------------------------------ | ---------------------------------- | ------------------------------------------------------------- |
| `plan-spec.md` L49–50          | exit 0 = sync→clean→**inspect** 绿 | `run_source_live_acceptance` 调 `DbInspector.inspect()` ✓     |
| 活卡 §5 AC#4 / slices S-ACCEPT | inspect **+ data health (F0)**     | `tier_a_live_acceptance.py` **无** data health 调用           |
| `plan-spec.md` L123 Boundaries | inspect/**health**                 | Interface Contract **无 health**                              |
| `tier-a-live-eligibility.md`   | 9 源无 KEY 槽位                    | 代码 `SOURCE_API_KEY_ENV["sec_edgar"]="SEC_EDGAR_USER_AGENT"` |

---

## §维度裁决

**FAIL**

（§计划内 + §计划外 findings 表均有非占位行。）

---

## §计划内问题

| ID        | P   | 标题                                                   | 锚点                                                                                                                                       | 根因                                                                                                 | 修复方案                                                                                                                                                                                                                                         | 验证                                                                                                                                                    |
| --------- | --- | ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A1-P1-001 | P1  | data health (F0) 未下沉至 plan-spec Interface Contract | 活卡 `M_DATA_03_TIER_A_LIVE.md` §5 AC#4 · `to-issues-slices.md` S-ACCEPT · `plan-spec.md` L43–56 · `l4-tier-a-live-accept-evidence.md` L30 | plan-doubt-review Cycle 10 只修了 slices；`plan-spec` CLI 契约仍仅 inspect；l4 证据未授权收窄 health | 在 `plan-spec.md` Interface Contract 补全 F0 data health 门槛（或 formal 阶段外置绑任务 ID）；同步修订 `l4-tier-a-live-accept-evidence.md` 与活卡/slices 一致；若本票 scope 含 health，在 `run_source_live_acceptance` 接入 `data_health` runner | `rg "data.?health" plan-spec.md` 命中 Interface Contract；`rg "data_health" backend/app/ops/tier_a_live_acceptance.py` 有调用；或两份登记文档路径可核对 |
| A1-P2-001 | P2  | execute-evidence RED/GREEN 路径缺失                    | `to-issues-slices.md` L11–12 · `00-EXECUTION-ENTRY.md` §3 L67 · `EXECUTION_INDEX.md` §1 `[x]`                                              | v4.1 code-first 与 slices 旧 txt 证据规则未 reconcile；`research/execute-evidence/` **不存在**       | 二选一：**(a)** 创建 execute-evidence 并补 sNN-red/green；**(b)** 修订 slices/ENTRY/INDEX 声明 v4.1 以 pytest+代码为证据，删除 txt 要求                                                                                                          | `test -d .trellis/tasks/m-data-03-tier-a-live/research/execute-evidence` 或 grep slices 无 sNN-green 要求                                               |
| A1-P2-002 | P2  | EXECUTION_INDEX 缺 §2.1 Tier 复验节                    | `agents/audit-boot-v4.1.md` L59/L68 · `EXECUTION_INDEX.md`                                                                                 | v4.1 Boot/A9 要求 INDEX §2.1 + `uv run pytest -q`；INDEX 仅 §2 无 §2.1                               | 在 `EXECUTION_INDEX.md` 增 §2.1 Tier（最弱 2 行复验命令 + exit 0 门槛）                                                                                                                                                                          | `rg "§2\\.1" EXECUTION_INDEX.md` 命中；按 §2.1 命令 exit 0                                                                                              |
| A1-P3-001 | P3  | eligibility 矩阵缺 SEC_EDGAR_USER_AGENT                | `tier-a-live-eligibility.md` L14 · `tier_a_live_acceptance.py` L21–25                                                                      | SEC fair-access 要求未下沉资格表；代码已强制 KEY                                                     | 在 `tier-a-live-eligibility.md` 增 `SEC_EDGAR_USER_AGENT` 行；对齐 `SOURCE_API_KEY_ENV`                                                                                                                                                          | harness `test_validateLiveAcceptanceEnv_rejectsMissing*` 覆盖 sec_edgar；eligibility 文档含该变量名                                                     |

---

## §计划外发现

| ID        | P   | 标题                           | 锚点                                                                      | 根因                                | 修复方案                                                                                         | 验证                                                                       |
| --------- | --- | ------------------------------ | ------------------------------------------------------------------------- | ----------------------------------- | ------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------- |
| A1-P3-002 | P3  | AUDIT.plan §3 陈旧「9 源」表述 | `AUDIT.plan.md` §3 L39                                                    | Plan GAP 文案未随 11 源 scope 更新  | 改为「11 源 live 变体」或删除过时 GAP 行                                                         | Read `AUDIT.plan.md` §3 与 `TIER_A_SOURCES` len=11 一致                    |
| A1-P3-003 | P3  | loop handoff 机器证据空        | `evidence_index.json` · `loop_manifest.json` `acs:[]`                     | Execute 未填充 loop 工件            | 跑 `loop_maintain.py --fix` 或 handoff 脚本填充 `evidence_index.json` / `loop_manifest.json` acs | `python .trellis/scripts/task.py validate-execute-handoff` exit 0          |
| A1-P3-004 | P3  | implement.jsonl manifest 不全  | `implement.jsonl`（6 行）vs `git diff`（30+ 路径）                        | `generate-manifests` 未覆盖整轮变更 | 重跑 manifest 生成，纳入 `tier_a_live_*.py`、`scripts/tier_a_live_acceptance.py`、11 e2e 等      | `implement.jsonl` 行数 ≥ 核心变更文件数；`validate-execute-handoff` exit 0 |
| A1-P3-005 | P3  | GitNexus 索引未收录新符号      | `gitnexus-audit-summary.md` · `context(tier_a_live_acceptance)` not found | 新文件未 analyze                    | `node .gitnexus/run.cjs analyze` 后 `context(tier_a_live_acceptance)` 成功                       | GitNexus context 返回 callers/callees                                      |

已对抗搜索：`backend/app/ops/tier_a_live*.py`、`scripts/tier_a_live_acceptance.py`、`tests/test_tier_a_live_*.py`、`.trellis/tasks/m-data-03-tier-a-live/research/*.md`、`grep data.?health|execute-evidence|SEC_EDGAR`、GitNexus query/context/detect_changes、全量 pytest。

---

### 已通过项（不计入 findings）

- `task.json` `plan_protocol_version: "4.1"` ✓
- ADR-034 已索引于 ENTRY §2/§4、INDEX §0 ✓
- 11 源均有 `@pytest.mark.network`（各 e2e 2 处）✓
- harness 负向 3 项（无 env 闸 / 主库拒绝 / 无 silent fallback）有单测 ✓
- `uv run pytest -q` exit 0 ✓
- 借鉴梯仅 `参考项目/**` 在 Bundle 中一致 ✓
- `test_catalog.yaml` 已登记 harness + dispatch（`scripts/` CLI 无 catalog 条目为仓库惯例）✓

---

**Repair 优先序：** A1-P1-001 → A1-P2-001/002 → A1-P3-\*。data health 缺口同时属 A5 执行偏差，A9 合并时须与 A5 台账去重。

[REDACTED]
