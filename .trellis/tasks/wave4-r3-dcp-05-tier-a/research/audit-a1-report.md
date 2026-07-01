# Audit A1 — audit-spec（链 A · 下沉丢失）

## 元信息

| 字段                    | 值                                                            |
| ----------------------- | ------------------------------------------------------------- |
| 维度                    | A1 audit-spec                                                 |
| 任务                    | `wave4-r3-dcp-05-tier-a`                                      |
| `plan_protocol_version` | `4.1`                                                         |
| 分支                    | `feature/wave4-r3-dcp-05-tier-a`                              |
| 模板                    | `agents/audit-a1-spec.md`                                     |
| 审计日期                | 2026-07-02                                                    |
| 焦点                    | 活卡 / ENTRY / ADR-028 一致性 · chain A gaps（AUDIT.plan §2） |

---

## 维度证据 §3.1

| 检查项                             | 结果            | 证据                                                                                                                                                                                                                 |
| ---------------------------------- | --------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| trellis-check 步骤 1 变更范围      | PASS            | `git diff master...HEAD --name-only` → 93 已提交路径；`git status --porcelain` → 7 修改 + 5 未跟踪（含 `tier_a_sync_router.py`、`test_qmd_data_sync_tier_a_router.py`、s12/s13-green、gitnexus-audit-summary）       |
| trellis-check 步骤 2 任务工件      | PASS            | `prd.md`（薄索引）· `frozen/R3_DCP_05_TIER_A_INCREMENTAL.md` · `research/00-EXECUTION-ENTRY.md` · `research/to-issues-slices.md` 已 Read                                                                             |
| trellis-check 步骤 3 包上下文      | PASS            | `python ./.trellis/scripts/get_context.py --mode packages` → `Single-repo project` · `Spec layers: backend`                                                                                                          |
| trellis-check 步骤 5 pytest spot   | PASS            | `uv run pytest tests/test_qmd_data_sync_tier_a_router.py tests/test_tierA_incremental_registry.py -q` → exit 0（36 passed）                                                                                          |
| diff vs audit/check manifest       | PASS            | `check.jsonl` 2 行（frozen + INDEX）均在 diff 集内；`audit.jsonl` 3 行均为任务包内路径                                                                                                                               |
| GitNexus ≥1 调用                   | PASS            | `query(repo=quant-monitor-desk, "Tier A incremental sync clean write")` → 命中 `DataSyncOrchestrator.run_incremental` 等；`context(resolve_clean_write_target)` → index stale（与 `gitnexus-audit-summary.md` 一致） |
| 活卡 §5 AC → slices/INDEX          | PASS（部分）    | 活卡 §5 九项中八项可映射 S00–S13 / ENTRY §3；reference-adoption 仅有文件无切片 AC 行（非阻断，见对账备注）                                                                                                           |
| 活卡 §3 约束 → ENTRY §2            | **FAIL**        | 活卡 L32「主库禁止 silent 写 canonical `data/duckdb/`」；ENTRY §2 约束表（L24–30）无对应行；`DEBT.plan.md` L53 有、ENTRY 无                                                                                          |
| ADR-028 11 源矩阵 → Bundle         | PASS            | ADR-028 L17–29 表；`to-issues-slices.md` S00 AC；ENTRY §4 ADR 索引；`plan-spec.md` L52–58 ASSUMPTIONS 一致                                                                                                           |
| 非目标 explicit defer              | PASS            | 活卡 §6 FRED live primary → ENTRY §1「不在范围」· AUDIT.plan §3 `B2.5-O-05` 不关 · S02 AC「live primary 仍 open」                                                                                                    |
| EXTERNAL §A ↔ ENTRY §5.2           | **FAIL**        | EXTERNAL §A L9–18 列 8 项包外开工必读；ENTRY §5.2 L78–82 仅 5 项（缺 wave index、roadmap、orchestrator §13.4.2、guardrails.yaml、待修复清单、ops 文档）                                                              |
| AUDIT.plan §0.1 Trace Authority    | **FAIL**        | 本任务 `AUDIT.plan.md` 无 §0.1（对照 archive `06-29-round3h-r3h06-clean-schema/AUDIT.plan.md` L13–24）；`audit.jsonl` 仅 3 条 manifest，无 omission-check / integration-audit 等追溯行                               |
| `to-issues-slices` 依赖图 ↔ 切片表 | **FAIL**        | 依赖图 L21–23：`S08(cninfo)∥S09(mootdx)` → `S10–S12(sec/alpha/deribit)` → `S13`；切片表 L39–45：`S07–S11` 为 cninfo→deribit，`S12=CLI-ROUTER`，`S13=REGISTRY`；**S12 CLI 路由在依赖图中缺失**                        |
| integration-audit 闭环             | PASS（Plan 期） | `integration-audit.md` L23–29 对抗项 PASS；Execute GAP 已路由至 S00–S13（`plan-consolidation.md` L46–54）                                                                                                            |

### 活卡 AC 对账（链 A 摘要）

| 活卡 §5 项                  | Bundle 落点                                | 判定                           |
| --------------------------- | ------------------------------------------ | ------------------------------ |
| migration 015               | S00 · INDEX §2                             | OK                             |
| clean_write_targets 11 源   | S00 · ADR-028                              | OK                             |
| baostock live               | S01                                        | OK                             |
| 11× watermark + e2e clean   | S01–S11 建议测试列                         | OK                             |
| 11× dry-run sync            | S12                                        | OK                             |
| reference-adoption L1/L2/L3 | `reference-adoption-dcp05.md` · ENTRY §5.1 | OK（无切片 AC 归属，已文档化） |
| 东财 SSOT                   | S13                                        | OK                             |
| validate-plan-freeze        | ENTRY §3 L40                               | OK                             |
| pytest -q                   | ENTRY §3 · INDEX §2                        | OK                             |

---

## §维度裁决

**FAIL**

（§计划内问题 4 条非占位 finding）

---

## 计划内问题

| ID        | P   | 标题                                        | 锚点                                                                                 | 根因                                                                                                                                  | 修复方案                                                                                                                               | 验证                                                                                                                                                                                          |
| --------- | --- | ------------------------------------------- | ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A1-P2-001 | P2  | AUDIT.plan 缺 §0.1 Trace Authority Set      | `AUDIT.plan.md`（全文仅 §1–§3）· `audit.jsonl`（3 行）                               | Plan/Audit 冻结未按 v4.1 Boot 模板补齐 Trace Authority 表；审计倒查源未机器可读登记                                                   | 在 `AUDIT.plan.md` 新增 §0.1（活卡、ADR-028、INDEX、frozen、integration-audit、EXTERNAL §A 等）；同步扩展 `audit.jsonl` 首条后的追溯行 | `grep "§0.1 Trace Authority" .trellis/tasks/wave4-r3-dcp-05-tier-a/AUDIT.plan.md` 命中；`python .trellis/scripts/task.py validate-audit-handoff .trellis/tasks/wave4-r3-dcp-05-tier-a` exit 0 |
| A1-P2-002 | P2  | 切片依赖图与切片表 S07–S13 编号/语义漂移    | `to-issues-slices.md` L19–23 vs L39–45                                               | 依赖图未纳入 S12-CLI-ROUTER，且 cninfo/mootdx/sec/alpha/deribit 编号比切片表整体 +1；`S02–S07` 标注「macro×5+fred」与 S07=CNINFO 冲突 | 以切片总表为 SSOT 重写依赖图：S02–S06 macro+fred → 并行 S07–S11 源片 → **S12 CLI** → S13；删除错误 `S08–S12` 旧编号                    | 人工对读：依赖图每一 ID 与切片表「Slice」列一一对应；`grep "S12-CLI-ROUTER" to-issues-slices.md` 在依赖图与表中均出现                                                                         |
| A1-P2-003 | P2  | 活卡「主库 silent 写」禁令未下沉至 ENTRY §2 | 活卡 `R3_DCP_05_TIER_A_INCREMENTAL.md` L32 · ENTRY `00-EXECUTION-ENTRY.md` §2 L24–30 | 链 A 下沉丢失：铁律仅在活卡与 `DEBT.plan.md` L53，Execute 首读 ENTRY §2 缺显式约束                                                    | 在 ENTRY §2 约束表增行：`主库` · `禁止 silent 写 canonical data/duckdb/` · 详述 `DEBT.plan` production boundary / ADR-027              | `grep -n "silent" .trellis/tasks/wave4-r3-dcp-05-tier-a/research/00-EXECUTION-ENTRY.md` 命中 §2                                                                                               |
| A1-P2-004 | P2  | EXTERNAL §A 开工必读与 ENTRY §5.2 不一致    | `EXTERNAL-INDEX.md` §A L9–18 · ENTRY §5.2 L78–82                                     | §A 声明 8 项包外必读，§5.2 仅列 5 项；wave index / roadmap / orchestrator / guardrails / 待修复清单 / ops 文档未进入 Execute 开工清单 | 方案 A：扩充 ENTRY §5.2 与 §A 对齐；或方案 B：在 §5.2 增「其余见 EXTERNAL-INDEX §A」并确保 §A 为 SSOT 超集                             | `diff` 或人工表：§A 每一 path 在 §5.2 或 §5.2 显式 defer 指针中可解析                                                                                                                         |

---

## 计划外发现

| ID  | P   | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| —   | —   | 无   | —    | —    | —        | —    |

已对抗搜索：活卡 §3–§6 全约束 · ADR-028 全文 · ENTRY/EXTERNAL/slices/AUDIT/DEBT/plan-boot/plan-spec/integration-audit/plan-doubt-review · `git diff master...HEAD` 93 文件 + 未提交 S12/S13 · GitNexus query · pytest spot check。除 §计划内问题 已列链 A 缺口外，未发现需单独登记的 plan外 spec 漂移（如 staging-only 放行、FRED live primary 误关账等）。
