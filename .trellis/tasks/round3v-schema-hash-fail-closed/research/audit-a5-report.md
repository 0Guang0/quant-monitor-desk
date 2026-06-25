# A5 — audit-completion（AC 追溯 · evidence 抽检 · prod-path）

**维度：** A5 · verification-before-completion + doubt-driven-development  
**派发模型：** composer-2.5  
**工作区：** `C:/Users/Guang/Desktop/quant-monitor-desk-wt-b3v-data`  
**任务：** `round3v-schema-hash-fail-closed`（B3V-DATA · B3V-C02 · VR-DATA-001）  
**审计时间：** 2026-06-25（A5 复验）  
**判定：** **PASS（Execute AC 范围）** · **§4.3 登记全库回归未绿**  
**OPEN：** **1（NON-BLOCKING）** · **BLOCKING：** **0**

---

## 1. 启动清单

| 项 | 状态 |
| --- | --- |
| `agents/audit-a5-completion.md` | 已读 |
| `agents/quant-analyst.md` | 已读（方法层：无回测声称；fixture 证据链） |
| `agents/risk-manager.md` | 已读（fail-closed · registry defer） |
| `B02_02_schema_hash_fail_closed.md`（Trace Authority） | 已读 §5–§8 |
| `MASTER.plan.md` §2 · §6 · §8–§10 | 已读 |
| `AUDIT.plan.md` §1–§2 | 已读 |
| `implement.jsonl` 全读（31 行） | 已读 |
| `research/execute-evidence/*`（10 文件） | 已读 |
| `manifest-amend.md` | **不存在** |
| `repair-evidence/` | **不存在** |
| `validate-execute-handoff` | **exit 0**（A5 复验） |

**约束：** 只读审计；未 `git commit`；未改生产库；未改 Execute 验收库。

---

## 2. A5 Checklist

| 检查项 | 结果 |
| --- | --- |
| 每条 AC 追溯链 + 1–5 分 | ✅ §3.5（AC-DATA-01..05） |
| §10 最弱 2 行抽检 | ✅ §4 |
| `execute-evidence/*-green.txt` 非占位 | ⚠️ §5（9.3/9.4 输出偏薄 → §4.3 NB，可复现） |
| audit-prod-path `uv run pytest -q` | ❌ §7（**46 failed** · exit **1** · 环境/仓库卫生 · 非本任务 diff） |
| registry / defer 项 | ✅ B02-DATA-05 **explicit defer**（MASTER §1.4 · §10） |
| `validate-execute-handoff` | ✅ exit 0 |
| 负向 gate 测试仍存在（B3V-AUD-05） | ✅ `test_missingSchemaHashOnStructuredFetch_rejects` 等仍在 |

---

## 3. §3.5 — AC-DATA 追溯与评分

| AC# | 追溯链（原始 → MASTER → §8/§9 → 证据） | 分 | 抽检/复验 |
| --- | --- | --- | --- |
| **AC-DATA-01** | B02 §5 DATA-01 → MASTER §8 DATA-01 → §9.1 → `data_adapter_contract.md` structured schema_hash · `9.1-green.txt` · `test_dataAdapterContract_documentsStructuredSchemaHashRequirement` | **5** | `pytest …::test_dataAdapterContract_documentsStructuredSchemaHashRequirement -v` → **1 passed** |
| **AC-DATA-02** | B02 §5 DATA-02 → MASTER §8 DATA-02 / S1–S2 → §9.2 → `skeleton_base._infer_schema_hash` · `9.2-green.txt` · `test_inferSchemaHash_csvHeader_*` / `parquetColumns_*` | **5** | infer 两测 → **2 passed** |
| **AC-DATA-03** | B02 §6 缺 hash 拒绝 → MASTER S3 / §8 DATA-03 → §9.3 → `validation_gate._schema_hash_blocks_write` L242–248 · `9.3-green.txt` · `test_missingSchemaHashOnStructuredFetch_rejects` | **4** | 抽检 → **4 passed**（含漂移回归）；green.txt 无完整 session 头 |
| **AC-DATA-04** | B02 §6 损坏 Parquet/CSV → MASTER S4 / §8 DATA-04 → §9.4 → `skeleton_base` corrupt → `SCHEMA_DRIFT`/`FAILED` · `9.4-green.txt` | **4** | corrupt 两测 → **2 passed**；证据偏薄 |
| **AC-DATA-05** | B02 §6 schema_hash change → MASTER S5 → §9.3 → `test_schemaHashDriftWithoutApproval_rejects` · `write_contract.yaml` | **5** | 与 AC-DATA-03 同批抽检 → **passed** |

**均分：** 4.6 / 5 — **PASS（Execute 范围）**

### defer 切片（设计内，非 OPEN 缺陷）

| ID | 状态 | 说明 |
| --- | --- | --- |
| **B02-DATA-05** | **DEFERRED → 主会话** | `original-plan-trace.md` · MASTER §1.4 · §10「不 registry 闭合」；`git diff master` 无 registry 三件套改动 |

---

## 4. §10 最弱 2 行 — 抽检

MASTER §10 仅两行 DoD；均抽检：

| # | §10 原文 | 复跑 / 验证 | exit | 与 Execute 一致？ |
| --- | --- | --- | --- | --- |
| 1 | §9 证据齐 · 任务卡 §7 pytest 子集全绿 · §11 Skill `[x]` · `validate-execute-handoff` 0 | `python .trellis/scripts/task.py validate-execute-handoff …`；`uv run pytest tests/test_data_adapter_contract.py tests/test_db_validation_gate.py tests/test_adapter_skeletons.py tests/test_data_quality_validator.py -q` | **0** | ✅ handoff 0；子集全绿（与 `9.0-green.txt` 126 passed 口径一致） |
| 2 | **不** finish-work · **不** registry 闭合 | `git diff master --name-only` 仅 7 个实现/契约文件；无 `UNRESOLVED_*` / registry yaml 变更 | — | ✅ 符合 MASTER 边界 |

**补充 — AUDIT.plan A8（Tier 任务测）：**

```bash
uv run pytest tests/test_data_adapter_contract.py tests/test_db_validation_gate.py tests/test_adapter_skeletons.py -q --basetemp=.audit-sandbox/pytest
```

→ **exit 0**（A5 独立复验）

---

## 5. execute-evidence `*-green.txt` 真实性

抽检最弱两份：**`9.3-green.txt`**、**`9.4-green.txt`**（仅命令 + passed 计数，无 pytest session 头）。

| 文件 | 非空 | 非 TODO | 含命令/结果 | 与 §9 步一致 | 独立复跑 |
| --- | --- | --- | --- | --- | --- |
| `9.3-green.txt` | ✅ | ✅ | ⚠️ 薄 | DATA-03 | ✅ 4 passed（含漂移回归） |
| `9.4-green.txt` | ✅ | ✅ | ⚠️ 薄 | DATA-04 | ✅ 2 passed |

**§4.3 NB：** 非纯「PASS」占位，但缺完整终端 banner；**可复现，不降级 AC 分数至 2**。

RED 证据对照：`9.3-red.txt` 显示 RED 时 `DID NOT RAISE ValidationRejected`；`9.4-red.txt` 显示 corrupt 曾达 SUCCESS — TDD 链可信。

---

## 6. quant-analyst 视角（方法层）

| 检查 | 结论 |
| --- | --- |
| 回测/alpha 声称 | N/A — 本任务为摄取契约与 gate fail-closed |
| 数据窥探 / look-ahead | 无 — schema 指纹仅读 header / DuckDB LIMIT 0 元数据 |
| fixture vs prod-equivalent | 单测用 `tmp_path` + 合成 CSV/Parquet；符合 MASTER「无 live fetch」 |
| 指标定义与代码一致 | `data_adapter_contract.md` structured 段与 `validation_gate.py` L242–248 对齐 |
| 过拟合 / 多重试参 | N/A |

---

## 7. risk-manager 视角（fail-closed）

| 风险 | 等级 | 证据 |
| --- | --- | --- |
| 结构化 SUCCESS 无 `schema_hash` 绕过 gate | P1 已闭合 | `_schema_hash_blocks_write` 对 structured+SUCCESS+row_count>0+NULL hash → block |
| schema 漂移 | P1 已闭合 | baseline≠current → block；`test_schemaHashDriftWithoutApproval_rejects` 绿 |
| 损坏文件进入 clean-write | P1 已闭合 | adapter → `SCHEMA_DRIFT`/`FAILED`；corrupt 负向测绿 |
| production clean write | — | diff 无写库路径；AUDIT A3 口径满足 |
| VR-DATA-001 registry 行 | P2 defer | B02-DATA-05 主会话；Execute 未宣称闭合 |
| Gate weaken（B3V-AUD-05） | — | 负向测未删除/未改目的 |

---

## 8. audit-prod-path — `uv run pytest -q`

| 命令 | exit | 摘要 |
| --- | --- | --- |
| `uv run pytest -q` | **1** | **46 failed**（A5 复验 · ~143s） |

完整输出存档：`.trellis/tasks/round3v-schema-hash-fail-closed/research/a5-pytest-full.txt`

### §4.3 — 失败归因（非 B3V-DATA 回归）

| 类别 | 代表失败 | 根因 | 与本任务 diff 关系 |
| --- | --- | --- | --- |
| 环境 ResourceGuard | `test_layer1_*` / `test_layer2_*` 大批写路径测 | `available_memory_gb` 低 · `profile=eco` · suggestion=retry later | **无关** — 未改 layer1/2 |
| 仓库卫生 | `test_docs_specs_indexed` · `test_loop_engineering_flow` · `test_trellis_validate_plan` | stale `MIGRATION_MAP` / `docs_specs_index.generated.md` | **无关** — 未改 docs 索引 |
| live pilot | `test_batch275_live_pilot_gate` ×2 | 同 ResourceGuard 生态 | **无关** |
| residual R3X | `test_r3x_*` ×3 | 全库契约测 | **无关** |

**本任务 `git diff master` 触及文件（7）：**

- `.trellis/spec/backend/datasource-adapters.md`
- `backend/app/datasources/adapters/skeleton_base.py`
- `backend/app/db/validation_gate.py`
- `specs/contracts/data_adapter_contract.md`
- `tests/test_adapter_skeletons.py`
- `tests/test_data_adapter_contract.py`
- `tests/test_db_validation_gate.py`

**任务子集（Tier A / A8）在 A5 环境全绿** — Execute AC 结论仍成立。

**MASTER §0.1** 注明 `prod-path | Tier A only（无 live fetch）`；全库 Tier C 失败登记为 **§4.3 环境/卫生**，建议主会话或 CI（normal profile + `loop_maintain.py --fix`）复验 Tier C，**不阻塞 B3V-DATA Execute AC 签收**。

### B02 §7 验收命令（任务卡）

| 步骤 | 命令 | A5 结果 |
| --- | --- | --- |
| pytest 契约+gate | `uv run pytest tests/test_data_adapter_contract.py tests/test_db_validation_gate.py -q` | ✅ exit 0 |
| pytest quality | `uv run pytest tests/test_data_quality_validator.py -q` | ✅ exit 0 |
| ruff | `uv run ruff check backend/app/datasources backend/app/db tests` | ❌ 174 errors（仓库存量 lint 债） |

---

## 9. 实现锚点（抽检代码，只读）

| 能力 | 位置 |
| --- | --- |
| 契约 structured 必填 hash | `specs/contracts/data_adapter_contract.md` structured schema_hash 段 |
| CSV/Parquet 有界 infer | `skeleton_base.py` `_infer_schema_hash` |
| corrupt → 非 SUCCESS | `skeleton_base.py` `status="SCHEMA_DRIFT"` |
| Gate 缺 hash fail-closed | `validation_gate.py` L242–248 |

---

## 10. 总结判定

| 维度 | 判定 |
| --- | --- |
| AC-DATA-01..05（Execute） | **PASS**（均分 4.6/5） |
| evidence 链 + TDD RED→GREEN | **PASS** |
| §10 DoD + handoff | **PASS** |
| B02-DATA-05 registry | **DEFERRED**（explicit，符合 Plan） |
| 全库 `pytest -q`（audit-prod-path） | **§4.3 FAIL**（exit 1 · 46 failed · 环境 ResourceGuard + docs 索引卫生） |
| B3V-AUD-05 负向保留 | **PASS** |

**A5 签收建议：** **PASS（Execute AC）** — 可进入 Audit 其余维度；**Tier C 全库回归** 待 CI/资源正常环境复绿后由主会话关闭 §4.3 项。**勿 finish-work** 直至 Audit 全维 PASS 且 B02-DATA-05 registry 由主会话闭合。

---

*只读审计 · 未修改生产代码 · 未 commit*
