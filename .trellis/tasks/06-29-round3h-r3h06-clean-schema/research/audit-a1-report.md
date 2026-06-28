# Audit A1 — trellis-check / Trace Authority / GitNexus · R3H-06

> **维度：** A1（audit-spec）  
> **分支：** `feature/round3h-r3h06-clean-schema`  
> **权威：** `agents/audit-a1-spec.md` · `agents/audit-adversarial-authority.md` · `AUDIT.plan.md` · `frozen/R3H_06_CLEAN_SCHEMA.md`  
> **复核日期：** 2026-06-29（独立复核；推翻/确认前次 Ask 模式结论）  
> **模式：** 只读审计 + **本报告落盘**

---

## 总裁决

**PASS_WITH_FIXES**

实现侧（工作区）已对齐冻结卡 Wave 1 目标：migration 013/014、三域路由 `clean_write_targets.py`、OHLCV、cninfo 公告形、upsert 幂等、`market_bar_clean` 实现路径清零；A8 子集 pytest 与 `loop_maintain.py` 在本轮审计中 **exit 0**。  
**但** 存在 3 项 **BLOCKING** 流程/文档缺口（与独立复核前次结论一致）：路线图 §5.0.0 与 §5.0.1 自相矛盾、核心交付未 commit、9.1–9.9 缺 RED 证据。主会话须在 merge 前闭合，否则不得 `finish-work`。

---

## §3.1 trellis-check 证据表

| 检查项                  | 结果                 | 证据                                                                                                                                                                                                                                                                                                                                                                  |
| ----------------------- | -------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1. 变更范围**         | PASS（范围已识别）   | `git branch --show-current` → `feature/round3h-r3h06-clean-schema`；`git log --oneline master..HEAD` → **空**（分支 tip = `master`）；`git diff master --shortstat` → `28 files changed, 667 insertions(+), 187 deletions(-)`（仅已跟踪）；未跟踪核心：`013_clean_domain_tables.sql`、`014_stg_bar_ohlcv.sql`、`clean_write_targets.py`、`test_r3h06_clean_schema.py` |
| **2. 任务工件**         | PASS                 | `prd.md` L6–9 与 frozen §1 一致；`frozen/R3H_06_CLEAN_SCHEMA.md` 存在且冻结；无独立 `design.md` / `implement.md`（v4 以 frozen + INDEX 代）                                                                                                                                                                                                                           |
| **3. 包上下文**         | PASS                 | `uv run python ./.trellis/scripts/get_context.py --mode packages` → `Spec layers: backend`                                                                                                                                                                                                                                                                            |
| **4. Spec Quality**     | PASS（触及 backend） | `.trellis/spec/backend/index.md` Quality 指针已读；migration / WriteManager / pytest 惯例与 `database-guidelines.md` 方向一致                                                                                                                                                                                                                                         |
| **5. 项目检查**         | PASS（子集）         | `uv run pytest tests/test_r3h06_clean_schema.py tests/test_round3g_limited_production_clean_write.py tests/test_migration_coverage.py -q --basetemp=.audit-sandbox/pytest` → **65 passed, exit 0** @ 2026-06-29；`uv run python scripts/loop_maintain.py` → `OK: loop maintain`                                                                                       |
| **6. 跨层（≥3 层）**    | PASS                 | Storage：`migrations/013_*.sql`、`014_*.sql`；Service：`rehearsal_loader.py`、`limited_production_entry.py`、`clean_write_targets.py`；Tests：`test_r3h06_clean_schema.py`（13 测）+ round3g 回归；无 import 环（新模块仅被 ops 消费）                                                                                                                                |
| **7. manifest vs diff** | PASS_WITH_GAP        | `check.jsonl` / `audit.jsonl` 点名 frozen、INDEX、schema、MIGRATION_COVERAGE、ROADMAP；diff 含计划外 `db_inspector.py`、`ops_db_inspect_contract.yaml`（A2 已标必要涟漪）；**registry 三件套未改**（`git status` 无 `source_registry.yaml` / `source_capabilities.yaml` / `source_route_contract.yaml`）                                                              |
| **§9.8 rg 门禁**        | PASS                 | `rg market_bar_clean backend/ scripts/ tests/ specs/ docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/` → backend/scripts/tests/specs **零匹配**（历史 research/R3G 文档除外，符合 INDEX §1.1）                                                                                                                                                           |
| **禁止主库**            | PASS（设计+测）      | frozen §8 / INDEX §2.1 Tier D；本 diff 无 `data/duckdb/quant_monitor.duckdb` 写入路径                                                                                                                                                                                                                                                                                 |
| **Wave 2+ DDL**         | PASS                 | 仅 013/014；无额外 migration 文件                                                                                                                                                                                                                                                                                                                                     |

---

## Trace Authority（AUDIT.plan §0.1）

| 条目                       | 核对问题                                             | 结果                | 证据                                                                                                                                                                                                     |
| -------------------------- | ---------------------------------------------------- | ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 原始任务卡                 | scope/AC/Red Flags 已进入 frozen 或 explicit defer？ | **PASS**            | 活卡 `docs/.../R3H_06_CLEAN_SCHEMA.md` + `frozen/R3H_06_CLEAN_SCHEMA.md` §1–§15；Red Flags §13 与测对齐（cninfo 非 bar、upsert、无 VIEW）                                                                |
| PASS 计划                  | Wave 1 / DDL 独占一致？                              | **PASS**            | `R3H_PASS_EXECUTION_PLAN.md` L70–90 Wave 1 = R3H-06；L118「仅 R3H-06 拥有 DDL」                                                                                                                          |
| 3G gaps                    | G3–G6 闭合路径可追溯？                               | **PASS**            | `R3G_MASS_REHEARSAL_OPEN_GAPS.md` 经 INDEX §3 must-read；`original-plan-trace.md` §5.0.1 映射 9.1–9.7                                                                                                    |
| schema SSOT                | DDL 与 migration 一致？                              | **PASS**（工作区）  | `specs/schema/schema.sql` + `013_clean_domain_tables.sql` 含 `security_bar_1d` / `cn_announcement_clean`；`MIGRATION_COVERAGE.md` L38–82 标 013/014 **DONE**                                             |
| migration 矩阵             | 013 DONE 有文档？                                    | **PASS**            | `MIGRATION_COVERAGE.md` §「Round 3H clean domain」L105–110 rollback 说明                                                                                                                                 |
| 执行索引                   | manifest 血缘完整？                                  | **PASS**            | `EXECUTION_INDEX.md` §0.1 AC↔Step、§1 证据路径、§3 manifest 24+ 条                                                                                                                                       |
| omission-check             | 地图倒查无遗漏？                                     | **PASS_WITH_DEFER** | `research/project-map-omission-check.md` L17–20：`BATCH_3H_TASK_CARD_MANIFEST` / README 由 **coordinator merge 时补** — explicit defer，非 Execute 阻塞                                                  |
| integration-audit          | 5d 对抗闭环？                                        | **PASS**（Plan 期） | `research/integration-audit.md` B01–B10 fixed；Execute 后测已绿                                                                                                                                          |
| `research/source-index.md` | A1 模板 §A–§C？                                      | **DEFER**           | 本任务 **无** `source-index.md`；以 `EXECUTION_INDEX.md` §3 + `context_pack.json` + `adversarial-audit-report.md` 替代血缘（搜索范围：`.trellis/tasks/06-29-round3h-r3h06-clean-schema/research/` glob） |

---

## §5.0.1 交叉项追溯

| ID                          | 冻结要求                             | Step / 测                                             | 实现证据（工作区）                                                                                                                           | 文档/流程                                                           | 判定                     |
| --------------------------- | ------------------------------------ | ----------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------ |
| **SCHEMA-G3G4**             | 分表 + OHLCV + PK                    | 9.1+9.3+9.5；`-k bar_ddl` / `ohlcv` / `domain_router` | `013_clean_domain_tables.sql` L18–34 PK 含 `adjustment_type`；`014_stg_bar_ohlcv.sql`；`clean_write_targets.py` L27–32 bar→`security_bar_1d` | ROADMAP §5.0.1 L325 **CLOSED** vs §5.0.0 L307 **仍开放** → **矛盾** | **IMPL PASS / DOC FAIL** |
| **CNINFO-DISCLOSURE-SHAPE** | 公告原生形 + capabilities ⊆ DDL      | 9.2+9.4+9.6                                           | `cn_announcement_clean` §6.1 列 @ `013` L36+；`test_disclosure_ddl_*`；`test_cninfo_no_bar_*`                                                | 同上 §5.0.1 L326 CLOSED                                             | **IMPL PASS / DOC FAIL** |
| **G6-IDEMPOTENCY**          | `upsert_by_pk` 重复 promote 行数不变 | 9.7；`-k idempotency`                                 | `clean_write_targets.py` 全域 `write_mode="upsert_by_pk"`；`test_idempotency_duplicatePromote_rowCountStable`                                | §5.0.1 L327「R3H-06+3V CLOSED」；§5.0.0 L307 仍写 G6 开放           | **IMPL PASS / DOC FAIL** |

**对抗结论：** 若审计员只读 §5.0.1 表会误判三项已 CLOSED；若只读 §5.0.0 表会误判仍 OPEN。须 coordinator 统一 ROADMAP §5.0.0 L307（及 L281 摘要行 G3–G5）与 §5.0.1，并待 **commit + merge** 后方可标 CLOSED。

---

## GitNexus

| 动作                                                                                 | 结果                                                                                                            |
| ------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------- |
| `query({search_query: "clean_write_targets domain router promote security_bar_1d"})` | 返回 interface_probe / live_pilot 等流程；**未索引** `clean_write_targets.py`（未跟踪新文件，索引 stale）       |
| `context({name: "limited_production_entry"})`                                        | 未执行（MCP 审批阻断）；以 `grep` + 文件读取代：`limited_production_entry.py` 消费 `resolve_clean_write_target` |

**声明：** 已执行 ≥1 次 `query`；新 SSOT 文件需 merge 后 `node .gitnexus/run.cjs analyze` 刷新索引。

---

## DOUBT（对抗 scope / Red Flags / unresolved）

| 追问                         | 搜索范围                                         | 结论                                                                             |
| ---------------------------- | ------------------------------------------------ | -------------------------------------------------------------------------------- |
| Red Flags 是否进测？         | `test_r3h06_clean_schema.py` 13 测；round3g 回归 | **是** — 无 `market_bar_clean`、cninfo 不增 bar 行、upsert 幂等                  |
| 继续三源同表？               | `rg market_bar_clean` + `clean_write_targets.py` | **否**                                                                           |
| append_only 叠行？           | `clean_write_targets.py` 全 `upsert_by_pk`       | **否**（rehearsal_runner bar rehearsal 仍 append 有意分叉 — A2 O4 NON-BLOCKING） |
| 改 registry 无 coordinator？ | `git status` registry 三件套                     | **未改**                                                                         |
| 宣称主库 promote？           | diff + frozen §8                                 | **无**                                                                           |
| TDD 每步 RED？               | `execute-evidence/*-red.txt`                     | **否** — 仅 9.0-red（见 BLOCKING A1-B03）                                        |
| 核心交付可 merge？           | `git log master..HEAD`                           | **否** — 零 commit（见 BLOCKING A1-B02）                                         |

---

## 计划外发现

> 对抗搜索：设计边界 + 契约 scope vs diff；任务卡 Red Flags；计划未索引路径。搜索：`git diff master --name-only`、frozen §4/§8、`rg market_bar_clean`、A2 报告交叉。

| ID  | 发现                                                                                                    | 严重度 | 阻塞                                  |
| --- | ------------------------------------------------------------------------------------------------------- | ------ | ------------------------------------- |
| O1  | `db_inspector.py` + `ops_db_inspect_contract.yaml` L5 表迁出 `future_phase_key_tables` — frozen §4 未列 | LOW    | NON-BLOCKING（013 状态涟漪，A2 已审） |
| O2  | `BATCH_3H_TASK_CARD_MANIFEST.md` / `R3H_PASS_EXECUTION_PLAN.md` Wave 表更新 — coordinator 文档          | LOW    | NON-BLOCKING                          |
| O3  | FRED promote 走 `axis_observation`，部分 round3g 测仍断言 bar 形 staging（A2-001 交叉）                 | MEDIUM | NON-BLOCKING                          |
| O4  | `execute-evidence/9.*-green.txt` 多为单行摘要，非完整 pytest 日志 — 不利 CI 复现                        | LOW    | NON-BLOCKING                          |
| O5  | `research/execute-evidence/` 与 `execute-evidence/` 双份 9.0 证据 — 易漂移                              | LOW    | NON-BLOCKING                          |
| O6  | `research/source-index.md` 缺失 — A1 模板默认路径无文件                                                 | LOW    | NON-BLOCKING（INDEX §3 已替代）       |
| O7  | 实现路径 `market_bar_clean` 零残留                                                                      | —      | **计划外负向检查 PASS**               |

---

## 全部发现项汇总

### BLOCKING

| ID         | 严重度     | 发现                                                                                                                                                                                                                                  | 修复建议                                                                                                                           |
| ---------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| **A1-B01** | **HIGH**   | `PROJECT_IMPLEMENTATION_ROADMAP.md` **§5.0.0 L307** 写「G3/G4/G6 … ❌ **仍开放**」且落点「R3H-05 + schema」；**§5.0.1 L325–327** 同三项标 **CLOSED @ R3H-06**。§4.6 L281 摘要亦写「G3–G5 仍开放」。审计无法单一 SSOT 判定 PASS 门禁。 | 主会话/coordinator 更新 §5.0.0 表行 307（及 L281）为「✅ R3H-06 闭合」或标 `IN_PROGRESS` 直至 merge；与 §5.0.1 对齐后再标 CLOSED。 |
| **A1-B02** | **HIGH**   | **核心交付未 commit**：`git log master..HEAD` 为空；未跟踪 `backend/app/db/migrations/013_*.sql`、`014_*.sql`、`clean_write_targets.py`、`tests/test_r3h06_clean_schema.py`；分支名存在但无 R3H-06 提交。                             | 按切片 commit（建议：migration+schema → routing+loader → tests+docs）；merge 前 `detect_changes()`。                               |
| **A1-B03** | **MEDIUM** | **TDD RED 证据缺失**：`EXECUTION_INDEX.md` §1 要求每步 `9.x-{red,green}.txt`；`frozen` §8「每步先 RED」；实际仅 `execute-evidence/9.0-red.txt`（ModuleNotFound），**无** `9.1-red` … `9.9-red`。                                      | 补跑 RED 命令并落盘，或主会话书面 waive（须引用 GLOBAL_TESTING_POLICY 例外条款）；否则 Execute handoff 不合规。                    |

### NON-BLOCKING

| ID      | 严重度 | 发现                                                 | 修复建议                                 |
| ------- | ------ | ---------------------------------------------------- | ---------------------------------------- |
| A1-NB01 | LOW    | `omission-check` 登记 manifest/README 待 coordinator | merge 时补 `BATCH_3H_TASK_CARD_MANIFEST` |
| A1-NB02 | LOW    | GitNexus 未索引 `clean_write_targets.py`             | merge 后 analyze                         |
| A1-NB03 | LOW    | `9.10-full.txt` 仅一行「exit 0」无计数               | 补全库 pytest 摘要行数                   |
| A1-NB04 | MEDIUM | ponytail 重复路径（A2-001–006）                      | debt-lite 跟进，不阻 merge               |
| A1-NB05 | LOW    | `prd.md` L10 仍写「待用户批准」— 状态陈旧            | Execute 完成后改 thin-index 状态         |

---

## A1 checklist（模板）

- [x] trellis-check 步骤 1–7 有证据（上表 §3.1）
- [x] diff vs audit/check manifest（§3.1 行 7）
- [x] Trace Authority 已核对或 explicit defer（上表）
- [x] Plan omission — coordinator defer 已登记（NB01）
- [x] GitNexus `query` 已执行；新文件索引 stale 已说明

---

## 与下游维度交接

| 维  | A1 移交要点                                                                         |
| --- | ----------------------------------------------------------------------------------- |
| A2  | ponytail 重复项见 A2 报告 A2-001–008；本维确认 scope 内实现成立                     |
| A3  | registry 未改；cninfo 无 bar 形写入 — 请 A3 复核 promote mutation proof             |
| A7  | 013/014 无 down migration — `MIGRATION_COVERAGE.md` rollback 文字已存在             |
| A8  | 子集 65 测已绿；全库以 `9.10-full.txt` 声称绿 — 建议 A8 独立复跑 `uv run pytest -q` |

---

## Verification Story（A1 维）

| 项                | 状态                                          |
| ----------------- | --------------------------------------------- |
| trellis-check 1–7 | **已执行**（本报告 §3.1）                     |
| A8 子集 pytest    | **已执行** — 65 passed                        |
| loop_maintain     | **已执行** — OK                               |
| 全库 pytest       | **未独立复跑** — 依赖 Execute `9.10-full.txt` |
| 代码修改          | **无**（只读审计）                            |

---

**A1 维裁决：PASS_WITH_FIXES** — 实现质量可接受，**3 BLOCKING 须在 merge / finish-work 前闭合**。
