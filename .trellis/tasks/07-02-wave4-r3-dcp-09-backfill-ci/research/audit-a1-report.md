# Audit A1 Report — R3-DCP-09 Spec / Trace Authority / ENTRY / ADR-030

> **维：** A1 · **任务：** `07-02-wave4-r3-dcp-09-backfill-ci` · **plan_protocol_version:** 4.1  
> **工作目录：** `quant-monitor-desk-wt-dcp09` · **分支：** `feature/wave4-r3-dcp-09-backfill-ci`（未提交变更）  
> **日期：** 2026-07-02 · **审计员：** trellis-check A1（readonly）

---

## 维度证据 §3.1

### Boot 与 trellis-check

| 检查项 | 结果 | 证据 |
| ------ | ---- | ---- |
| `task.json` plan_protocol_version | PASS | `task.json` L27 `"plan_protocol_version": "4.1"` |
| AUDIT.plan §0.1 Trace Authority 路径登记 | PASS | `audit.jsonl` 3 行 + INDEX §5 追溯集 |
| git status / diff 范围 | PASS | `git status --short`：核心变更 `backend/app/sync/jobs.py`、`backend/app/cli/data_commands.py`、`specs/contracts/bounded_backfill_cap.yaml`、7× 新测、`.github/workflows/nightly.yml`、`docs/decisions/ADR-030-*.md` |
| `check.jsonl` manifest vs diff | PASS | `check.jsonl` 点名 `frozen/` + `EXECUTION_INDEX.md`；diff 覆盖 manifest 核心 + Execute 交付物 |
| `implement.jsonl`（manifest 点名行） | PASS | 4 行：frozen · ENTRY · context_pack · trellis-execute SKILL |
| 包上下文 | PASS | `uv run python ./.trellis/scripts/get_context.py --mode packages` → `Spec layers: backend` |
| DCP-09 定向 pytest | PASS | `uv run pytest tests/test_bounded_backfill_cap.py tests/test_qmd_data_backfill_cli.py tests/test_nightly_ci_manifest.py tests/test_r3_dcp09_registry_closure.py -q` → 9 passed, exit 0 |
| 全量 pytest | PASS | `uv run pytest -q --tb=no` → exit 0（~344s） |
| `gitnexus-audit-summary.md`（Boot #15） | **缺口** | `.trellis/tasks/07-02-wave4-r3-dcp-09-backfill-ci/research/` 下 **无** 该文件 |

### GitNexus（≥1 query / context）

| 检查项 | 结果 | 证据 |
| ------ | ---- | ---- |
| `query` bounded backfill | PASS（邻域） | `query({search_query:"bounded backfill cap plan_backfill_shards max_shards CLI", repo:"quant-monitor-desk"})` → `plan_backfill_shards` definition + `BackfillShardRunner.run` 流程 |
| `context` plan_backfill_shards | PASS | callers：`BackfillShardRunner.run`、`production_equivalent_smoke._collect_scale_metrics`、`test_backfillJob_largeRange_splitsIntoTasks` |
| `context` run_backfill | PASS | callers 含 `test_sync_orchestrator` backfill 套件；outgoing `_default_pipeline_config` |
| 新 CLI 符号索引 | **缺口** | `query({search_query:"cmd_backfill data_commands backfill CLI", repo:"quant-monitor-desk"})` **未**返回 `data_commands` backfill handler；索引可能陈旧（见 §计划外） |

### ADR-030 ↔ Bundle ↔ 契约

| 锚点 | ADR-030 / 活卡 | ENTRY / to-issues / yaml / 代码 | 结果 |
| ---- | -------------- | ------------------------------- | ---- |
| 31 天/片 | `ECO_MAX_BACKFILL_DAYS_PER_TASK` = 31 | `bounded_backfill_cap.yaml` L10；`jobs.py` `ECO_MAX_BACKFILL_DAYS_PER_TASK` | PASS |
| 默认 max_shards | `DEFAULT_MAX_BACKFILL_SHARDS` = 3 | yaml L11；`jobs.py` L51 | PASS |
| 硬顶 | `ABSOLUTE_MAX_BACKFILL_SHARDS` = 12 | yaml L12；`jobs.py` L52；CLI 校验 L546–551 | PASS |
| `--truncate-to-cap` | ADR-030 §1 | yaml L13；`plan_backfill_shards(..., truncate_to_cap=)` L154–186 | PASS |
| 金路径 CLI → orchestrator | ADR-030 §2 · 活卡 §3 | ENTRY §2；`data_commands.py` → `run_backfill` | PASS |
| nightly 分层 | ADR-030 §3 | ENTRY §2 CI 行；`to-issues` S04；`nightly.yml` | PASS |
| 四台账 ID | ADR-030 Context | `to-issues` S03–S06 · INDEX §2.1 四行齐 | PASS |
| 不在范围 | 活卡 §6 · ADR Alternatives | ENTRY §1「不在范围」四行一致 | PASS |
| 活卡 Red Flags | 活卡 §3（bypass / silent 写 / 无 cap FullLoad） | ENTRY §2 金路径 · 有界 · 真网 gate | PASS |

### Trace Authority 逐步核对（AUDIT.plan §0.1）

| 条目 | 核对问题 | 结果 | 证据 |
| ---- | -------- | ---- | ---- |
| 原始任务卡 | scope/AC/Red Flags 进入 ENTRY/INDEX？ | **FAIL** | 活卡路径 `docs/implementation_tasks/.../R3_DCP_09_BOUNDED_BACKFILL_CI.md` 在 **本分支 worktree 不存在**（`docs/implementation_tasks` 下 grep `R3_DCP_09` 0 命中）；`frozen` L6 仍指向该路径 |
| task README / Plan 入口 | Plan v4.1 合规？ | PASS | `task.json` meta.execute_entry → `00-EXECUTION-ENTRY.md` |
| unresolved coverage | 未闭合项有 registry/defer？ | **FAIL** | `integration-audit.md` L33–37 doc-gap 仍写 S01/S04/S06 未交付；与 frozen §9 全 `[x]` 矛盾 |
| round map | batch/out-of-scope 与 ENTRY §2 一致？ | PASS | ENTRY §1 不在范围 = 活卡 §6 |
| source-index / EXTERNAL §A | manifest 血缘完整？ | **FAIL** | `R3_DCP_TO_ISSUES_INDEX.md` §6.3 L166 仅列 **3** 台账 ID，缺 `LIVE-NETWORK-GATE-001`（ADR-030 / S06 要求 4） |
| omission-check | 地图倒查无遗漏？ | **FAIL** | `EXTERNAL-INDEX.md` §C L42–43 仍写 `--quick` / findings gate「待 S03/S05」；`plan-consolidation.md` L25–29 Execute GAP 仍 open |
| integration-ledger | context packing 一致？ | PASS | `context_pack.json` 存在；`audit.jsonl` 与 AUDIT.plan §0.1 对齐 |

### DOUBT（活卡 / Red Flags / unresolved → Bundle）

| 怀疑点 | 搜索范围 | 结论 |
| ------ | -------- | ---- |
| 活卡 §5 `reference-adoption-dcp09.md` L1/L2/L3 | `research/reference-adoption-dcp09.md` §1 | **PASS** — 三等级表存在 |
| plan-doubt-review D5 参考树实读证据 | `research/execute-reference-read-evidence-dcp09.md` | **FAIL** — 文件缺失；`reference-adoption-dcp09.md` L28 要求 Execute 落盘 |
| to-issues RED→GREEN 规则 | `research/execute-evidence/` | **FAIL** — 仅有 `s00`–`s06-green.txt`，**无** `sNN-red.txt`（`to-issues-slices.md` L11） |
| 活卡 §7 Trellis 路径 | 活卡 L81 vs `task.json` slug | **漂移** — 活卡 `wave4-r3-dcp-09-backfill-ci` vs 实际 `07-02-wave4-r3-dcp-09-backfill-ci`（未在 ENTRY 显式 reconcile） |

### trellis-check 步骤摘要

1. **变更范围** — `git status` + 未提交文件列表 ✓  
2. **任务工件** — `prd.md` 无；frozen · ENTRY · to-issues · plan-spec 已读 ✓  
3. **包上下文** — `get_context.py` ✓  
4. **Spec Quality** — ADR-030 + `bounded_backfill_cap.yaml` 与 `jobs.py`/`data_commands.py` 一致 ✓  
5. **项目检查** — 全量 pytest exit 0 ✓  
6. **跨层** — CLI → orchestrator → runner；触及 sync/cli/specs/docs/ci（≥3 层）✓  
7. **manifest** — `check.jsonl` 2 行 vs diff 无冲突 ✓  

---

## §维度裁决

**FAIL**

（链 A 下沉丢失 / Bundle 与 Execute 完成态未 reconcile：6 项计划内 P2 + 1 项计划外 P3。ADR-030 与 ENTRY 核心约束对齐；全量 pytest 绿 **不能** 抵消 Trace Authority 缺口。）

**Finding count：** 6（计划内）+ 1（计划外）= **7**

---

## 计划内问题

| ID | P | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| A1-P2-001 | P2 | 活卡路径在本分支不可达 | `AUDIT.plan.md` §0.1 活卡行；`frozen/R3_DCP_09_BOUNDED_BACKFILL_CI.md` L6；`task.json` L31 `source_task_card` | Execute 未将 `docs/implementation_tasks/.../R3_DCP_09_BOUNDED_BACKFILL_CI.md` 纳入 feature branch；Trace Authority 第一级权威断链 | 将活卡提交至本分支（或更新 frozen/ENTRY 指向已提交的等价路径并登记 ADR/roadmap） | `Test-Path docs/implementation_tasks/.../R3_DCP_09_BOUNDED_BACKFILL_CI.md` 为真；`grep R3_DCP_09` 命中活卡 |
| A1-P2-002 | P2 | 参考项目实读证据缺失 | `reference-adoption-dcp09.md` L28；`plan-doubt-review.md` D5；`EXTERNAL-INDEX.md` §D | Bundle 规定 Execute RED 前落盘 `execute-reference-read-evidence-dcp09.md`，research 包无此文件 | 补写 `research/execute-reference-read-evidence-dcp09.md`（OpenBB/EasyXT 行号实读摘要 + 负向声明）或 grill 登记 blocker | `test -f .../execute-reference-read-evidence-dcp09.md` 且含 §D 两参考路径 |
| A1-P2-003 | P2 | integration-audit 与 Execute 完成态矛盾 | `integration-audit.md` L14–17 · L33–39 | Plan 5d 文档未在 S00–S06 后 reconcile；仍 `PASS_WITH_GAPS` + doc-gap 三项 open | 更新 integration-audit：契约/测试/运维类→PASS；doc-gap 标 CLOSED 或删行；结论改为 PASS（或注明 Execute 已闭合） | Read 文件无「`qmd data backfill` 未实现」「nightly workflow 未建」 |
| A1-P2-004 | P2 | EXTERNAL-INDEX §C 字典陈旧 | `EXTERNAL-INDEX.md` §C L42–43；`EXECUTION_INDEX.md` §1 全 `[x]` | Execute 后未回写包外字典「待 S03/S05」 | 将 §C 改为当前能力描述（`--quick` 已实现；findings gate 已实现）；删除「待 Sxx」 | grep §C 无 `待 S03` / `待 S05` |
| A1-P2-005 | P2 | Wave4 索引缺第四台账 ID | `R3_DCP_TO_ISSUES_INDEX.md` §6.3 L166；ADR-030 L16；`to-issues-slices.md` S06 AC | 上游索引仅列 3 ID，未下沉 `LIVE-NETWORK-GATE-001` | §6.3 承接台账补第四 ID；勾选项与 S04 nightly gate 对齐 | §6.3 含 `LIVE-NETWORK-GATE-001` 四 ID 全名 |
| A1-P2-006 | P2 | 切片 RED 证据文件缺失 | `to-issues-slices.md` L11；`EXECUTION_INDEX.md` §1 | 规则要求 `sNN-red.txt` → `sNN-green.txt`；`execute-evidence/` 仅 7 个 green | 按切片补 `s00-red.txt`…`s06-red.txt`（RED 阶段失败摘要）或 amend to-issues 规则并显式 defer（须绑任务） | 每切片 red+green 成对存在，或 INDEX 注明 defer 理由 |

---

## 计划外发现

| ID | P | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| A1-P3-001 | P3 | GitNexus 未索引新 backfill CLI 符号 | MCP `query` backfill CLI；`data_commands.py` L511+ | 索引未 re-analyze；`cmd_backfill` 类符号不出现在 query 结果 | Repair 或主会话跑 `node .gitnexus/run.cjs analyze`；复验 `context({name:"cmd_backfill", repo:"quant-monitor-desk"})` 或等价 handler 名 | GitNexus context/query 能解析 `data_commands` backfill 入口 |

已对抗搜索：`plan-consolidation.md` Execute GAP 列表（与 A1-P2-003/004 同源，已计入计划内）· 活卡 §5 checkbox 仍为 `[ ]`（上游活卡未更新；frozen `[x]` 与 ENTRY 切片表已覆盖 AC 语义，不单独立项）· `gitnexus-audit-summary.md` 缺失（Boot 7.pre 工件；建议 A9 补，不单独立 finding）· ADR-030 cap 数值与代码（PASS）· `reference-adoption-dcp09.md` L1/L2/L3 内容（PASS）· 全量 pytest（PASS，属 trellis-check 证据，非 Trace Authority 关账）。
