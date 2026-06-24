# Adversarial Plan Audit — B-19 staged pilot v2

> **Auditor:** code-reviewer (PROMPT_19 / B-19, READ ONLY)  
> **Branch:** `feature/round3-real-data-staged-pilot-v2`  
> **Date:** 2026-06-24  
> **Baseline pattern:** `archive/2026-06/06-23-round3-020-layer3-loader/MASTER.plan.md`

## Verdict

**PLAN_NEEDS_FIX**

**BLOCKING count:** 5

计划骨架完整（九切片、Tier A/B、AUD-08 摘要、manifest v3），但执行者在仅读 MASTER 时会在 **worktree 文件锁、证据路径、MUT-PROOF 对抗深度、closeout gate 可测性** 四处踩空；`validate-plan-freeze` exit 0 不能掩盖上述缺口。

---

## Findings Table

| ID    | BLOCKING / NON-BLOCKING | Finding                                                                                                                                                                                                                                                                                                                                                       | Section                                                                                                               | Required fix                                                                                                                                                                                                                                      |
| ----- | ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------- | ------------------------------------------------------------- |
| AA-01 | **BLOCKING**            | 缺少 `research/worktree-slices.md`（020 / `round3-wave-a-slice-plans.md` 模式）：`§3.1` 仅写「窄 pilot 所需 `datasources/` / `storage/` 修复」，无 **allowed / forbidden 文件清单、owner、worktree、merge gate**；并行 agent 可误改 `backend/app/datasources/**` 或 registry。                                                                                | §3.1；对比 020 `worktree-slices.md`                                                                                   | 新增 `research/worktree-slices.md`：显式列出 ops 三文件 + tests + task `execute-evidence/`；datasources/storage **白名单路径或「须 RED 暴露后协调者批准」**；禁止 layer2/3/4/5、registry 大规模改写、production DB；并在 `implement.jsonl` 索引。 |
| AA-02 | **BLOCKING**            | `execute-evidence/*` 路径未锚定任务目录。§8 写 `execute-evidence/8.1-green.txt`，v1 证据在 `.trellis/tasks/feature-round3-real-data-staged-pilot/execute-evidence/`；Execute handoff / A5 抽检会找错目录。                                                                                                                                                    | §3.1、§4、§8.0–8.10、AUDIT §2 A5                                                                                      | 全文统一为 `.trellis/tasks/06-24-round3-real-data-staged-pilot-v2/execute-evidence/`（或 §0 冻结单一 `EVIDENCE_ROOT` 常量）；§8 每步 GREEN 列具名 v2 产物完整相对路径。                                                                           |
| AA-03 | **BLOCKING**            | **Closeout 不得仅依赖 `proof_status=VERIFIED`**（AUD-08 #3）：§5.3 / §8.9 仅规划 `test_stagedPilotV2_closeoutMatrix_allSourcesClassified`（per-source 分类）；未要求 closeout / validation payload 含 **`db_hash_unchanged`、`row_counts_unchanged`** 且为 gate 断言。现网 `staged_pilot.py` closeout 仍只写 `mutation_proof_status`（`proof_status` 字段）。 | §0 AUD-08、§2 AC-MUT-001、§5.3、§8.9；`staged_pilot.py:1207-1220`                                                     | §6 冻结 `pilot_v2_closeout.json` schema；§5.3 增 closeout gate 用例（hash∧counts 均为 true 才 PASS；`MUTATION_DETECTED` 时 closeout 失败）；§8.9 要求同步改 closeout 构建逻辑。                                                                   |
| AA-04 | **BLOCKING**            | **R3Y-MUT-PROOF-001 / §8.8 不足以闭合 AUD-04 HIGH**：§5.3 仅 2 条对抗测（hash+count 不变、KEY 表行变）；AUD-04 要求 **非 KEY 表 row-count-only、schema/hash 变而 KEY count 不变** 等情形；`ProofStatus` 现仅 `VERIFIED                                                                                                                                        | INCONCLUSIVE`，计划写 `MUTATION_DETECTED` 但未规定类型与 closeout 联动。AUDIT A8 将缺口推到 Audit，Execute 可能假绿。 | §8.8、§5.3、AUD-04、`mutation_proof.py:11-81`                                                                                                                                                                                                     | §5.3 增 ≥2 条 `tmp_path` DuckDB 对抗用例并映射 §8.8 RED；§8.8「做什么」列明更新 `ProofStatus` Literal；或 §8.8 显式 defer 非 KEY 场景到 A8 并在 §2 AC-MUT-001 标注 **PARTIAL**（不推荐）。 |
| AA-05 | **BLOCKING**            | **工程纪律未进入 Execute 交接清单**：addendum 要求修复后 **完整 pytest**、**不得削弱测试目的**、测试 **中文 purpose/target**；MASTER 仅在 §5.0 / §0.3a 分散提及，**§12 Audit 交接无对应 checkbox**；§0.3a 较 020 缺少「禁止新抽象/新依赖、ponytail self-check 格式」条目。执行者易在 §8.1–8.9 跳过全量回归纪律。                                              | §0.3a、§11、§12；对比 020 §0.3a                                                                                       | §12 增：每步 GREEN 后 incremental pytest 范围、§8.10 前禁止 weakening test purpose、新增测试须中文四元注释；§0.3a 对齐 020 第 3–6 条。                                                                                                            |
| AA-06 | NON-BLOCKING            | **α-1/α-2 符号在仓库中不存在**；波次串行关系仅在 `plan-boot.md` / `round3-wave-a-slice-plans.md`（PROMPT_19 等 AUD-08），**MASTER §1.2 未索引协调者文档**，Execute 只读 MASTER 时不知 wave-B gate。                                                                                                                                                           | §1.2；`plan-boot.md` §前置依赖                                                                                        | MASTER §1.2 增表：PROMPT_18 AUD-08 merged、`round3-wave-a-slice-plans.md` 波次 B 条件；若 α-1/α-2 为外部命名，映射到 PROMPT_14/R3X/PROMPT_18 证据路径。                                                                                           |
| AA-07 | NON-BLOCKING            | **§2.4.2 `ROUND3_BATCH_IMPLEMENTATION_MAP` 缺失**：`source-index.md` §A 已纠偏至 §2.2 + PROMPT_19/R3Y；`PLAN_BOOT.md` 仍引用 §2.4.2。计划可自给，但索引漂移。                                                                                                                                                                                                 | §1.6、`source-index.md` §A                                                                                            | 更新 `PLAN_BOOT.md` 引用；或在 map 补 §2.4.2 PROMPT_19 行（协调者）。                                                                                                                                                                             |
| AA-08 | NON-BLOCKING            | **R3Y-SP2-01..09 证据文件名不完全对齐 §8 GREEN 列**：8.2「manifest v2 文件」未列 `raw_evidence_manifest_v2.json` / `staging_evidence_manifest_v2.json`；8.3 缺 cninfo manifest；8.7 未列 `conflict_check_summary_v2.json`；8.4 taxonomy 路径未写全名。                                                                                                        | §8.2–8.7、`vertical-slices.md`                                                                                        | 每切片 GREEN 证据列 **完整文件名清单**（对齐 R3Y 任务卡 §4）。                                                                                                                                                                                    |
| AA-09 | NON-BLOCKING            | **§5.3 与 R3Y 任务卡测试缺口**：SP2-05 要求 `user-auth-required` route status，§5.3 仅四类；SP2-04 vertical-slices 要求「非 validation op 拒绝」RED，§5.3 未列。                                                                                                                                                                                              | §5.3、§8.4–8.5、`R3Y_real_data_staged_pilot_v2.md` §4                                                                 | §5.3 补用例行或 §8.4/8.5 扩 RED 命令。                                                                                                                                                                                                            |
| AA-10 | NON-BLOCKING            | **staged-only 未在 §8 逐步重复**：依赖 §0/§1.5 全局停损；各切片表无「sandbox-only / no clean write」列。020 同模式，可接受但审计抽检成本高。                                                                                                                                                                                                                  | §8.0、§1.5                                                                                                            | 可选：§8.0 增「sandbox 约束」列或每步「做什么」首句重复 staged-only。                                                                                                                                                                             |
| AA-11 | NON-BLOCKING            | **§6 无 v2 closeout / caps JSON 字段契约**：`sandbox_clean_write_rehearsal`、per-source `expand                                                                                                                                                                                                                                                               | retry                                                                                                                 | re-defer                                                                                                                                                                                                                                          | block` 未冻结 schema（020 有 §6.1 bundle 协议）。                                                                                                                                          | §6、§8.9 | 增 §6.1 `pilot_v2_closeout.json` / caps envelope 最小字段表。 |
| AA-12 | NON-BLOCKING            | **`validate-plan-freeze` 假阴性与 stale 文案**：实测 exit 0；`integration-audit.md` 仍写「exit 0 待跑」；校验器 **不要求** `worktree-slices.md`、不检查 §5 approval（设计如此）。                                                                                                                                                                             | `plan.freeze.md` §3.6、`integration-audit.md` §5                                                                      | 修正 integration-audit 文案；Plan 侧仍须人工补 AA-01/02；可选增强 freeze 校验 worktree-slices。                                                                                                                                                   |

---

## Adversarial Checklist (1–10)

| #   | 检查项                                                                                    | 结论                                                                                                    |
| --- | ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| 1   | R3Y-SP2-01..09 各有 AC、产物、验证、证据路径？                                            | **部分** — AC/§8 RED/GREEN 齐；GREEN 产物路径多处不具名（AA-08）                                        |
| 2   | R3Y-MUT-PROOF-001 §8.8 足够？AUD-08 控件接入？                                            | **不足** — proof_status 收紧有规划，对抗深度与 closeout 子字段 gate 未闭合（AA-03、AA-04）              |
| 3   | staged-only / no production-live 每切片强制？                                             | **全局强制** — §0/§1.5/§3.3；切片表未逐步重复（AA-10）                                                  |
| 4   | α-1/α-2 合并顺序对执行者可见？                                                            | **弱** — 前置在 plan-boot，MASTER §1.2 未链协调者文档（AA-06）                                          |
| 5   | pilot 测试模块与 Tier A/B 矩阵完整？                                                      | **基本完整** — `test_catalog.yaml` 已登记 `test_staged_pilot.py`；v2 用例为规划态；§5.3 有缺口（AA-09） |
| 6   | ops/ 文件锁 allowed paths 显式？                                                          | **否** — 缺 worktree-slices（AA-01）                                                                    |
| 7   | karpathy / testing / TDD / ponytail / 中文注释 / full pytest / 禁削弱测试目的 在 §0/§12？ | **部分** — §0.3a/§5.0/§11 有；§12 与 020 级纪律不足（AA-05）                                            |
| 8   | Map §2.4.2 缺失计划能否自给？                                                             | **是** — `source-index.md` §A 纠偏 + PROMPT_19/R3Y 足够（AA-07 非阻塞）                                 |
| 9   | Closeout 不单靠 `proof_status=VERIFIED` 可测？                                            | **否** — 测试与 schema 未覆盖（AA-03）                                                                  |
| 10  | `validate-plan-freeze` 假阳性？                                                           | **有盲区** — 通过但缺 worktree-slices / 证据根路径（AA-12）                                             |

---

## Post-audit fixes (2026-06-24)

| ID        | Status                                                                                 |
| --------- | -------------------------------------------------------------------------------------- |
| AA-01..05 | **FIXED** — `worktree-slices.md`、EVIDENCE_ROOT、§6.1 closeout、§5.3 MUT 测、§0.3b/§12 |
| Verdict   | **PLAN_READY**                                                                         |

- 九垂直切片与 `/to-issues` 对齐，`vertical-slices.md` + §8.0 依赖图清晰，防「单脚本冒充」。
- AUD-08 控件在 §0 表格化，与 `R3Y-AUD-08-go-no-go.md` 一致；`grill-me-session.md` 吸收 red flags。
- Tier A/B 分离明确（全库 pytest 仅 §8.10），优于许多 legacy 计划。
- `implement.jsonl` 44 行、manifest v3、`integration-ledger.md` ≥5 行，`validate-plan-freeze` 实测 exit 0。

---

## Verification Story

| 项                     | 结果                                                                                                                      |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| Tests reviewed         | 是 — 对照 `tests/test_staged_pilot.py` 现网 26 测；§5.3 v2 用例均为规划名                                                 |
| Build verified         | 否 — Plan-only audit                                                                                                      |
| Security checked       | 是 — AUD-04/08 只读对照；staged sandbox 边界在现网代码中成立，gate 语义为缺口                                             |
| `validate-plan-freeze` | `python .trellis/scripts/task.py validate-plan-freeze .trellis/tasks/06-24-round3-real-data-staged-pilot-v2` → **exit 0** |

---

## Top Gaps (执行前必改)

1. **无 `worktree-slices.md`** — ops/datasources/storage 文件锁不明确（AA-01）。
2. **`execute-evidence` 根路径歧义** — handoff / Audit 抽检会失败（AA-02）。
3. **Closeout gate 不可测试** — AUD-08「不得仅 VERIFIED」未落入 §5.3/§8.9（AA-03）。
4. **MUT-PROOF-001 对抗覆盖不足** — AUD-04 非 KEY / hash-only 场景未规划（AA-04）。
5. **§12 缺工程纪律交接** — 完整 pytest / 禁削弱测试目的未冻结（AA-05）。
