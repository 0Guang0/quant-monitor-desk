# Audit A1 Report — R3-DCP-10 Layer5 Evidence Binding

> **维：** A1 trellis-check · Trace Authority · GitNexus  
> **任务：** `.trellis/tasks/07-02-wave4-r3-dcp-10-evidence/`  
> **协议：** `plan_protocol_version: 4.1`  
> **工作目录：** `quant-monitor-desk-wt-dcp10`（分支 `feature/wave4-r3-dcp-10-evidence`）  
> **日期：** 2026-07-02  
> **审计员：** audit-spec (A1) subagent

---

## 维度证据 §3.1

| 检查项 | 结果 | 证据 |
| --- | --- | --- |
| trellis-check Step 1 变更范围 | PASS | `git status --short`：9 项（6 modified + 3 untracked 代码 + 任务目录）；`master...HEAD` 空（变更未 commit） |
| trellis-check Step 2 任务工件 | PASS | 已读 `prd.md`（薄索引）、`frozen/R3_DCP_10_LAYER5_EVIDENCE_BINDING.md`、`EXECUTION_INDEX.md`、`00-EXECUTION-ENTRY.md` |
| trellis-check Step 3 包上下文 | PASS | `uv run python .trellis/scripts/get_context.py --mode packages` → `Spec layers: backend` |
| trellis-check Step 4 Spec Quality | PASS（触及层） | 变更包：`layer5_evidence`、`datasources`；`bundle_layer5_provenance` 扩展与 ADR-031 映射表一致（`evidence_bundle.py:99-125`） |
| trellis-check Step 5 项目检查 | PASS | DCP-10 定向：`uv run pytest tests/test_layer5_evidence_foundation.py tests/test_mootdx_incremental_e2e.py tests/test_layer5_provenance_bridge.py tests/test_layer5_mootdx_bar_clean_e2e.py -q` → 15 passed；全量 `uv run pytest -q` → exit 0 |
| trellis-check Step 6 跨层 | PASS（2 层） | Storage(raw) → normalizers → layer5_evidence；未触及 ≥3 层，跳过深查 |
| trellis-check Step 7 manifest | PASS | `audit.jsonl` 6 行、`check.jsonl` 2 行与 AUDIT.plan §0.1 Trace Authority 对齐；`implement.jsonl` manifest 点名行已读（Boot 槽位，非行为全集） |
| Trace Authority / 活卡（frozen 指针） | PASS | `frozen/R3_DCP_10_LAYER5_EVIDENCE_BINDING.md` 薄指针 → ENTRY §1/§2 + `to-issues-slices.md`；S00–S03 均 `[x]` |
| Trace Authority / 原始任务卡（活卡路径） | **FAIL** | `EXTERNAL-INDEX.md` §A + `task.json` `meta.source_task_card` 指向 `docs/implementation_tasks/.../R3_DCP_10_LAYER5_EVIDENCE_BINDING.md`；worktree `Test-Path` = **False**（主仓只读对照存在，worktree 不可达） |
| Trace Authority / ENTRY §1 P0 竖切 | PASS | `cn_equity_daily_bar` · `mootdx` · `sh.600519` · `security_bar_1d` — 与 ADR-031 §Decision-1 一致 |
| Trace Authority / ADR-031 映射表 | PASS | `build_source_provenance_from_bundle` + `bundle_layer5_provenance` 实现 ADR-031 §2 六行映射；`test_layer5_provenance_bridge.py:36-54` 断言 schema/domain/clean dataset ids |
| Trace Authority / 不在范围 | PASS | ENTRY §1「不在范围」= 活卡 §6 非目标 = ADR-031 §5 G5 子集 + L3–L4 阶段外置；`to-issues-slices.md:64-67` 台账措辞一致 |
| Trace Authority / integration-audit | PASS | `integration-audit.md` GAP 表 owner → S01/S02/S03；Execute 产物与 GAP 路由一致 |
| Trace Authority / plan-doubt-review | PASS（已继承） | Q1–Q5 定案已进入 ENTRY §2、`plan-doubt-review.md`、ADR-031；replay/G5 子集/no DB 无遗漏 |
| Trace Authority / round map | PASS | Wave 4 · 并行轨 0910-B；DCP-07/08 + R3H-05-GATE 阶段外置在 ENTRY、`待修复清单.md`、`PROJECT_IMPLEMENTATION_ROADMAP.md` |
| Trace Authority / source-index | PASS（v4.1 等价） | ENTRY §5.1 登记 14 份 `research/*.md`；`plan-consolidation.md` §5.1 全勾 |
| DOUBT / Red Flags 继承 | PASS | mootdx P0、schema_hash dataset 编码、replay 关 G5、无 evidence_chain DB、不假关全链 — 均已写入 ENTRY/ADR/to-issues/integration-audit |
| GitNexus query | PASS（已执行） | `query({search_query: "layer5 evidence provenance bundle mootdx"})` → 命中 `Layer5LineageBuilder`、`EvidenceFoundationValidator`、`foundation.py`、`lineage.py` 等 |
| GitNexus context | PASS（已执行·索引滞后） | `context({name: "build_source_provenance_from_bundle"})` → not found（新文件未 re-index）；`context({name: "bundle_layer5_provenance"})` → not found（扩展后未 re-index） |
| GitNexus detect_changes | PASS（已执行·低信号） | `detect_changes({scope: "all", worktree: "...-wt-dcp10"})` → `changed_files: 4`, `changed_symbols: 0`, `risk_level: low`（索引滞后） |
| gitnexus-audit-summary.md（Boot #15） | **FAIL** | 任务 `research/` 下无 `gitnexus-audit-summary.md`（7.pre 未产出；全仓仅 archive 任务有范例） |
| validate-plan-freeze | NOTE | exit 1 — 缺 audit-a2/a3/a6/a7 报告登记（Audit 进行中预期；非 A1 实质 scope 缺口） |

### 活卡 / ENTRY / ADR-031 一致性对照（实质）

| 维度 | 活卡（主仓只读） | ENTRY §1 | ADR-031 | 裁决 |
| --- | --- | --- | --- | --- |
| P0 域/源/标的/clean 表 | 一条 P0 竖切（§3 约束） | 四元组明示 | Decision §1 表 | ✅ |
| 三件套绑定 | `source_fetch_id` + hashes（§3） | §2 约束 | §2 映射表 | ✅ |
| 金路径 | raw→clean→Layer5（§4） | §2 金路径 | §3 实现 | ✅ |
| G5 子集 | ACC 承接（§2） | 价值行 | §5 | ✅ |
| 非目标 | §6 四条 | §1 不在范围 | Alternatives | ✅ |
| 参考 L1/L2/L3 | AC §5-④ | — | — | ✅ `reference-adoption-dcp10.md` 含 L1/L2/L3 |

**实质 scope/AC 一致**；缺口在 **活卡路径不可达** 与 **活卡元数据陈旧**（见 findings）。

---

## §维度裁决

**FAIL**

（§计划内 2 行非占位 + §计划外 2 行非占位 → 按 `audit-finding-schema.md` 强制 FAIL）

---

## 计划内问题

| ID | P | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | --- | --- | --- | --- | --- |
| A1-P2-001 | P2 | 活卡路径在 worktree 不可读 | `EXTERNAL-INDEX.md` §A L11 · `task.json` `meta.source_task_card` · `frozen/R3_DCP_10_LAYER5_EVIDENCE_BINDING.md` L6 | 活卡 `docs/implementation_tasks/.../R3_DCP_10_LAYER5_EVIDENCE_BINDING.md` 未进入 feature 分支 worktree；Trace Authority 第二级「原始任务卡」在审计工作目录断裂 | 将活卡 commit 到 `feature/wave4-r3-dcp-10-evidence`；或 Plan Repair 更新 EXTERNAL-INDEX §A 显式声明 v4.1 下 ENTRY+frozen 取代活卡路径（须 ADR/活卡同步） | worktree 内 `Test-Path docs/implementation_tasks/.../R3_DCP_10_LAYER5_EVIDENCE_BINDING.md` → True |
| A1-P3-001 | P3 | 活卡状态与 Execute 进度不一致 | 活卡 L11 `🔴 OPEN · Plan 阶段` vs `EXECUTION_INDEX.md` §1 S00–S03 `[x]` | Plan freeze 后未回写活卡状态字段 | 更新活卡状态为 `in_progress` / Audit 阶段，与 `task.json` `status` 对齐 | 活卡 L11 与 `task.json.status` 一致；frozen 指针 `frozen_at` 可保留 |

---

## 计划外发现

| ID | P | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | --- | --- | --- | --- | --- |
| A1-P2-002 | P2 | 缺 gitnexus-audit-summary.md（Boot 7.pre） | `agents/audit-boot-v4.1.md` Boot #15 | 主会话派发 A1 前未产出 7.pre 摘要；A1 虽独立跑 query/context/detect_changes，但 Bundle 缺机器可读审计基线 | A9 或协调者在 `research/gitnexus-audit-summary.md` 落盘：含本票 query、新符号 context、detect_changes 与 risk | 文件存在；`validate-audit-handoff` 前可被 A9 引用 |
| A1-P3-002 | P3 | GitNexus 索引滞后，detect_changes 低信号 | `gitnexus-summary.md` §detect_changes 基线 · 本审计 `detect_changes` 输出 | Execute 新增/修改符号未 `analyze`；`changed_symbols: 0`  despite 4 changed files | worktree 根执行 `node .gitnexus/run.cjs analyze`（或 `npx gitnexus analyze`） | `context({name: "build_source_provenance_from_bundle"})` 返回符号；`detect_changes` 列出 `provenance.py` 符号 |

已对抗搜索：`backend/app/layer5_evidence/provenance.py`、`docs/implementation_tasks/**/R3_DCP_10*`、`.trellis/tasks/**/gitnexus-audit-summary.md`、`research/plan-doubt-review.md` Q1–Q5、`integration-audit.md` 六类检查、`PROJECT_IMPLEMENTATION_ROADMAP.md` R3-DCP-10 行、`待修复清单.md` ACC G5 行。

---

## A1 checklist 关账

- [x] trellis-check 步骤 1–7 有证据（命令输出或 `file:line`）
- [x] diff vs audit/check manifest（任务工件 manifest 对齐；代码变更见 git status）
- [ ] Trace Authority 已继承或 explicit defer — **活卡路径断裂**（A1-P2-001）
- [x] 无 Plan omission（ENTRY §5.1 / plan-consolidation 全登记；integration-audit GAP 已 owner）
- [x] GitNexus 已查（query + context + detect_changes）；索引滞后已记 A1-P3-002
