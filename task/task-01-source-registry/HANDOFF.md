# Handoff · 测试资产治理会话 + task-01 指针

> **日期：** 2026-07-12  
> **本文件角色：** 给下一会话 / 新 agent 的交接摘要（读完能续作）。**不是**权威规格 SSOT。  
> **权威：** `MIGRATION_MAP.md` 索引的 `**/design/**` · `AGENTS.md` · `agent-toolchain.md` · testing-guidelines / TEST-EVIDENCE-GOVERNANCE。  
> **原则：** 不复制计划/ADR/票正文；只给加载顺序、本会话做了什么、禁令与指针。  
> **敏感信息：** 无。

---

## 0. 本会话实际做了什么（先读）

本会话**不是**在推进 G1-02 票 08，而是按时间线做 **pytest 测试资产治理**（用户明确：不走完整 completion-check 关账）：

| 约束       | 口径                                                                                                          |
| ---------- | ------------------------------------------------------------------------------------------------------------- |
| 正式实现   | **不改** `backend/`                                                                                           |
| design     | **不改** `**/design/**`（parity 失败只允许 promote design→runtime，本会话未改 design）                        |
| 处置       | 不该进业务 pytest 的 → DELETE 或迁 `phase-scripts/` / 稳定门禁 `scripts/`；正式 runtime/DB/CLI outcome → KEEP |
| 一次性产物 | `.scratch/_batch_*` / `_tmp_*` / `_c_verify` 等盘点验证文件 → **用完即删**；正式 `check_*.py` **保留**        |

### 已完成批次（按 git 首次入库时间）

| 批次   | 时间窗        | 要点                                                                                                        |
| ------ | ------------- | ----------------------------------------------------------------------------------------------------------- |
| 预清理 | 早期          | 删 `test_pytest_slow_tier` / `test_b3f_sh_hard_constraints` → phase-scripts                                 |
| **A**  | ~06-16～06-17 | config/schema/raw_store/port 等 SPLIT；phase-scripts                                                        |
| **B**  | ~06-18～06-19 | reference / data_cli / module_boundaries / datasource_service / platform_matrix → scripts + production_gate |
| **C**  | ~06-20～06-22 | layer1_axis / ops_db_inspector SPLIT；保留 design 点名的 shadow 测                                          |
| **D**  | ~06-23～06-26 | contract_drift → scripts；fred/model_whitelist/tdx caps → phase-scripts                                     |
| **E**  | ~06-27～06-30 | provider_catalog → scripts；web/prediction registry、R3H caps、CN capabilities → phase-scripts              |
| **F**  | ~07-01～07-04 | sync_job_contract → scripts；K1 whitelist、Tier-A health profile → phase-scripts                            |
| **G**  | ~07-07～07-08 | source-route acceptance contract/matrix/honesty SPLIT；bootstrap meta → phase-scripts（Grok 4.5 子代理）    |

### 本会话新建/强化的稳定门禁（`scripts/`，多已接 `production_gate`）

- `check_contract_drift.py`
- `check_provider_catalog.py`
- `check_sync_job_contract.py`
- `check_source_route_db_acceptance_contract.py`
- （既有）`check_reference_adoption_guardrails.py` · `check_platform_source_matrix.py` · `check_datasource_service_boundaries.py` · `check_source_route_db_acceptance_matrix.py` · …

改 `production_gate.main` 前 GitNexus impact = **LOW**；须同步 stub `tests/test_production_gate.py`。

### 本会话新建的阶段性脚本（`phase-scripts/`，中文功能/价值/退役条件）

示例：`check_layer1_k1_whitelist_parity.py` · `check_data_health_tier_a_profile_contract.py` · `check_r3h_resource_caps_parity.py` · `check_model_input_whitelist.py` · `check_source_route_matrix_checker_regression.py` · `check_acceptance_e2e_bootstrap_path.py` · …（完整列表以目录为准）。

### 下一治理刀（若续测债）

- **Batch H+：** ~07-09 起剩余 `tests/test_*.py`（按 git 首次入库日继续）
- 先 `git status`：工作树可能很脏（sandbox / pyc / 未提交治理 diff），分清「本治理改动」再动手
- **不要**把「若干 `--strict` + 子集 pytest 绿」写成模块 R4 / G1-02 关账

---

## 1. task-01-source-registry 产品线状态（并行指针，勿混淆）

本目录票务主线仍是 **G1-02 启用缝**。**测债治理 ≠ 票 08 / G1-02 / R4 完成。**

| 项                   | 状态（以三件套为准，HANDOFF 只摘要）                                                    |
| -------------------- | --------------------------------------------------------------------------------------- |
| 票 01–07             | Execute **CLOSED**（见 `completion-check-execute.md`）                                  |
| Frontier             | 票 **08**（4x bridge）                                                                  |
| G1-02 整包 / 模块 R4 | **仍 OPEN**                                                                             |
| 开放 finding         | F03 余 4x · F06 · F07 · F08 · F09 待复验 · F10–F12 · FRED 合并票 10；**F05-A 测债已关** |

**先扫三件套：** `task_plan.md` · `progress.md` · `findings.md`（以文件正文为准，勿用更旧口头摘要）。

**本地票：** `.scratch/task-01-g1-02-enable-seam/` Frontier≈08。

---

## 2. 上下文加载顺序（context-engineering）

### 若续 **测试资产治理**

| 序  | 加载什么                                                                                            |
| --- | --------------------------------------------------------------------------------------------------- |
| 1   | `AGENTS.md` · `agent-toolchain.md` · project-global / ponytail                                      |
| 2   | `completion-check/references/TEST-EVIDENCE-GOVERNANCE.md`（准入/处置阶梯）                          |
| 3   | 本 `HANDOFF.md` §0（已完成批次 + 禁令）                                                             |
| 4   | `scripts/production_gate.py` + 已有 `scripts/check_*.py` / `phase-scripts/check_*.py`（勿重复造轮） |
| 5   | 下一批 `tests/test_*.py`（按入库日）+ 同类已迁脚本 pattern                                          |
| 6   | 失败时只贴失败断言/栈                                                                               |

### 若续 **G1-02 票 08**

| 序  | 加载什么                                                                               |
| --- | -------------------------------------------------------------------------------------- |
| 1   | 同上规则                                                                               |
| 2   | [`EXECUTION-DOC-INDEX.md`](EXECUTION-DOC-INDEX.md)                                     |
| 3   | `.scratch/.../issues/08-*.md` · [`g1-02-execution-brief.md`](g1-02-execution-brief.md) |
| 4   | [`note.md`](note.md) · [`findings.md`](findings.md)                                    |
| 5   | design 只读：ADR-017/018 · `docs/modules/design/data_sources.md` §5.2.1                |
| 6   | 已落地：`activation_overlay` · `ask_activation` · `plan(con=)` · `enable_source_route` |
| 7   | 正式代码 **TDD**；改 symbol 前 GitNexus `impact`                                       |

**冲突裁决：** design > brief（G1-02）> task_plan > inventory。  
**不要加载当开工 SSOT：** [`归档/`](归档/README.md)。

---

## 3. 硬禁令（两线共用）

- 禁止改 `backend/`（测债治理线）/ 禁止未审阅改 `**/design/**`
- 禁止为绿改测试**目的**；禁止假完成（缩验证、跳约定 pytest）
- 禁止未迁调用方就删 ESR 根；禁止只清 fred 漏 else（G1-02）
- 禁止用 sandbox READY 升格「产品已默认启用」
- 阶段性代码只放 `phase-scripts/`（中文：功能 / 业务价值 / 退役条件）
- 阶段外置须双登记：`docs/quality/待修复清单.md` + `PROJECT_IMPLEMENTATION_ROADMAP.md`
- 正式关票须 `/completion-check`；**本测债会话未宣称 task 关账**

---

## 4. 验证速查

**测债回归（示例，按触及面加减）：**

```text
uv run python scripts/check_contract_drift.py --strict
uv run python scripts/check_provider_catalog.py --strict
uv run python scripts/check_sync_job_contract.py --strict
uv run python scripts/check_source_route_db_acceptance_contract.py --strict
uv run python phase-scripts/check_layer1_k1_whitelist_parity.py --strict
uv run python phase-scripts/check_data_health_tier_a_profile_contract.py --strict
uv run pytest -q tests/test_production_gate.py
```

**G1-02 06∥07 回归（≠ G1-02 关账）：**

```text
uv run pytest -q tests/test_g1_02_incremental_route_activation.py tests/test_g1_02_gold_path_overlay.py
uv run python phase-scripts/check_g1_02_esr_fixture_hygiene.py --strict
```

---

## 5. Suggested skills（下一会话按需 @）

| 时机                                 | Skill                                                                                |
| ------------------------------------ | ------------------------------------------------------------------------------------ |
| 续测债批次                           | `testing-guidelines` · TEST-EVIDENCE-GOVERNANCE · `ponytail` · `karpathy-guidelines` |
| 开写 / 改正式代码                    | `agent-toolchain` → 定分支；`test-driven-development`                                |
| 改 production_gate / 共享 check 脚本 | `gitnexus-impact-analysis`                                                           |
| 查调用链                             | `gitnexus-exploring`                                                                 |
| 正式关票 08 / Execute                | `completion-check`（追加既有 `completion-check-execute.md`）                         |
| 目标/边界不清                        | `grilling` / grill-me（**停猜**）                                                    |
| 收尾瘦身                             | `ponytail-review` / `code-simplification`（只动本 diff）                             |
| 新会话续作                           | **先读本 `HANDOFF.md`**；测债看 §0；票务看 §1 + `EXECUTION-DOC-INDEX.md`             |

---

## 6. 给下一 agent 的第一句话（可复制）

> 读 `task/task-01-source-registry/HANDOFF.md`。上一会话已完成 **测试资产治理 Batch A–G**（不改 backend/design；meta/YAML parity 迁 scripts|phase-scripts；一次性 scratch 已清）。下一刀若续测债：按入库日开 **Batch H+**，先列清单再 SPLIT，复用已有 `check_*.py`，验证后删 `_tmp/_batch` scratch。若续产品：G1-02 Frontier=**票 08**；01–07 Execute CLOSED ≠ G1-02/R4；债见 `findings.md`。先 `git status`。不要加载 `归档/`。

_本 handoff 不含密钥。_
