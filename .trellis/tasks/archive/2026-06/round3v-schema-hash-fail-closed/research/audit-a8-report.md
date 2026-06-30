# A8 audit-test-gap — B3V-DATA schema_hash fail-closed

> Dimension: A8 (Test Gap) only  
> Task: `round3v-schema-hash-fail-closed` · Playbook `B3V-DATA` / Manifest `B3V-C02`  
> Worktree: `quant-monitor-desk-wt-b3v-data`  
> Skills: `agents/qa-expert.md` · `agents/test-automator.md` · `testing-guidelines`  
> Authority: `agents/audit-adversarial-authority.md` · `AUDIT.plan.md` §1 A8  
> Mode: **只读**（无补测、无代码修复）  
> 日期: **2026-06-28**

---

## Verdict: **PASS**

Post Repair `1bc0260` 后，MASTER §5.3 冻结用例、B02_02 §6 五条测试要求、B3V-AUD-05 负向保全均已落地；G-01/G-03 已 FIX。其余计划外项均按 `zero-open-signoff.md` **RE-DEFER / WONT-FIX / ACCEPTED**，**OPEN = 0**。在设置 `QMD_DATA_ROOT` 且使用仓库根 `.audit-sandbox/pytest` 的前提下，AUDIT.plan 指定 pytest 选择器 **106 passed / exit 0**（本次复验 2026-06-28）。

---

## 1. 必读完成

| 来源                                       | 要点                                                          |
| ------------------------------------------ | ------------------------------------------------------------- |
| `agents/qa-expert.md`                      | A8 追溯 Red Flags；每 Flag 须 test \| defer \| §4.3           |
| `agents/test-automator.md`                 | 五字段 docstring；sandbox `QMD_DATA_ROOT`；Audit `--basetemp` |
| `testing-guidelines`                       | 语义断言、mock 边界、禁止弱唯一断言                           |
| `agents/audit-adversarial-authority.md`    | MASTER §5 仅参考；须对抗搜索计划外缺口                        |
| `AUDIT.plan.md` §1 A8                      | 三文件 pytest 选择器 + `--basetemp=.audit-sandbox/pytest`     |
| `MASTER.plan.md` §5–§7                     | 场景 S1–S5、§5.3 冻结 `test_*` 表、Red Flags                  |
| `B02_02_schema_hash_fail_closed.md` §6–§7  | 任务卡测试要求与验收命令                                      |
| `BATCH_3V_ADVERSARIAL_AUDIT.md` B3V-AUD-05 | 禁止为便利削弱 gate 负向                                      |
| `repair-evidence/zero-open-signoff.md`     | G-01..G-07 disposition；A8 OPEN 归零                          |

---

## 2. Pytest 证据

### 2.1 AUDIT.plan 权威选择器

**命令（与 `AUDIT.plan.md` 一致，审计补充 sandbox）：**

```text
$env:QMD_DATA_ROOT = "<repo>/.audit-sandbox/data"
New-Item -ItemType Directory -Force -Path .audit-sandbox/data, .audit-sandbox/pytest
uv run pytest tests/test_data_adapter_contract.py tests/test_db_validation_gate.py tests/test_adapter_skeletons.py -q --basetemp=.audit-sandbox/pytest
```

**结果（2026-06-28，worktree `quant-monitor-desk-wt-b3v-data`）：**

```text
........................................................................ [ 67%]
..................................                                       [100%]
106 passed
exit 0
```

原始输出：`.trellis/tasks/round3v-schema-hash-fail-closed/research/audit-a8-rerun-2026-06-28.txt`

**环境注记：**

| 条件                        | 现象                                                                | 处理                                                                     |
| --------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| 未设 `QMD_DATA_ROOT`        | `test_skeletonAdapterBase_successWritesRawFile` 等 raw 路径断言失败 | 审计命令应显式设 sandbox data root                                       |
| `--basetemp` 父目录不存在   | Windows `FileNotFoundError` setup ERROR                             | 跑前 `mkdir .audit-sandbox/pytest`（须用**仓库根**路径，非 task 子目录） |
| Windows 复用已存在 basetemp | `FileExistsError` / `rm_rf` 警告                                    | 跑前删除 `.audit-sandbox/pytest` 或使用唯一 basetemp                     |

### 2.2 MASTER §5.3 冻结子集 + Repair 增项

**命令：**

```text
uv run pytest \
  tests/test_data_adapter_contract.py::test_dataAdapterContract_documentsStructuredSchemaHashRequirement \
  tests/test_db_validation_gate.py::test_missingSchemaHashOnStructuredFetch_rejects \
  tests/test_db_validation_gate.py::test_missingSchemaHash_registryFallback_rejects \
  tests/test_db_validation_gate.py::test_schemaHashDriftWithoutApproval_rejects \
  tests/test_adapter_skeletons.py::test_inferSchemaHash_csvHeader_producesStableHash \
  tests/test_adapter_skeletons.py::test_inferSchemaHash_parquetColumns_producesHash \
  tests/test_adapter_skeletons.py::test_skeletonFetch_corruptCsv_notSuccessEligible \
  tests/test_adapter_skeletons.py::test_skeletonFetch_corruptParquet_notSuccessEligible \
  -q --basetemp=.audit-sandbox/pytest-frozen
```

**结果（2026-06-28）：** `10 passed` · exit 0  
（§5.3 七项 + `test_missingSchemaHashOnStructuredFetch_rejects` parametrize 额外两实例 + `test_missingSchemaHash_registryFallback_rejects`）

### 2.3 任务卡 §7 邻接文件（非 A8 选择器）

`B02_02` §7 另列 `tests/test_data_quality_validator.py`；AUDIT A8 选择器未包含。现有 `test_schemaHashDriftFlagInQualityFlags_rejects`（gate）与 `test_validateRows_schemaDrift_failedAndManualReview`（validator）提供邻接覆盖，**不记为 A8 阻塞**。

---

## 3. §3.8 Red Flag / 场景映射

| Red Flag / 来源                               | 场景                                  | 覆盖         | 证据                                                                                                                              |
| --------------------------------------------- | ------------------------------------- | ------------ | --------------------------------------------------------------------------------------------------------------------------------- |
| Gate weaken（MASTER §7）                      | 缺 hash / 漂移须 `ValidationRejected` | **测试**     | `test_missingSchemaHashOnStructuredFetch_rejects`（三后缀）；`test_schemaHashDriftWithoutApproval_rejects`                        |
| B3V-AUD-05                                    | 负向不得为过关删除                    | **测试**     | diff 仅 additive；无删除 `assert_can_write` 拒绝分支                                                                              |
| AC-DATA-01 / S1–S2 契约                       | 结构化 SUCCESS 须 schema_hash         | **测试**     | `test_dataAdapterContract_documentsStructuredSchemaHashRequirement`                                                               |
| AC-DATA-02 / S1                               | CSV infer 稳定 hash                   | **测试**     | `test_inferSchemaHash_csvHeader_producesStableHash`                                                                               |
| AC-DATA-02 / S2                               | Parquet infer 非空 hash               | **测试**     | `test_inferSchemaHash_parquetColumns_producesHash`                                                                                |
| AC-DATA-03 / S3                               | Gate 缺 hash fail-closed              | **测试**     | `test_missingSchemaHashOnStructuredFetch_rejects`（`.csv`/`.parquet`/`.json`）；`test_missingSchemaHash_registryFallback_rejects` |
| AC-DATA-04 / S4                               | 损坏 CSV/Parquet 非 SUCCESS           | **测试**     | `test_skeletonFetch_corruptCsv_notSuccessEligible`；`test_skeletonFetch_corruptParquet_notSuccessEligible`                        |
| AC-DATA-05 / S5                               | hash 漂移拒绝                         | **测试**     | `test_schemaHashDriftWithoutApproval_rejects`（回归）                                                                             |
| B02_02 §6「Parquet success 无 hash 拒绝写库」 | Gate 层 Parquet 路径                  | **测试**     | parametrize `suffix=parquet`（G-01 FIX）                                                                                          |
| B02_02 §6「CSV success 无 hash 拒绝写库」     | Gate 层 CSV 路径                      | **测试**     | parametrize `suffix=csv`                                                                                                          |
| 全文件 Parquet 扫描（§7 RF）                  | 有界推导                              | **测试间接** | Parquet 单测用 DuckDB 最小文件；无全量扫描断言                                                                                    |
| registry 并发（§7 RF）                        | Execute 禁止                          | **defer**    | B02-DATA-05 → 主会话                                                                                                              |
| schemaless 豁免（契约）                       | 无 hash 仍允许写                      | **defer**    | G-02 → B02-DATA-05；契约文档含 `schemaless`                                                                                       |
| write_contract `validation_tests`             | YAML 契约 pytest                      | **defer**    | G-07；行为由 gate 单测覆盖                                                                                                        |

---

## 4. 计划外发现

**对抗搜索声明：** 已检索 `tests/` 中 `schema_hash`、`schemaless`、`missingSchemaHash`、`corruptParquet`、`SCHEMA_DRIFT`；对照 `validation_gate._schema_hash_blocks_write` 全分支、`skeleton_base._fetch_impl` 守卫；审阅 Post Repair `test_db_validation_gate.py` parametrize + registry 回退用例；复跑 A8 三文件 pytest（2026-06-28）。

| ID           | 场景                               | 若只按 MASTER §5.3 测会漏什么          | 严重度       | Post Repair 处置                                            | OPEN?  |
| ------------ | ---------------------------------- | -------------------------------------- | ------------ | ----------------------------------------------------------- | ------ |
| G-01         | Gate 缺 hash 仅 `.csv` 单测        | parquet/json 后缀无独立证据            | NON-BLOCKING | **FIX** — `@pytest.mark.parametrize` 三后缀                 | **否** |
| G-03         | registry 回退无单测                | 无后缀 + file_registry structured 漏拦 | NON-BLOCKING | **FIX** — `test_missingSchemaHash_registryFallback_rejects` | **否** |
| G-02         | schemaless 正向豁免                | 误拒/误放未证明                        | NON-BLOCKING | **RE-DEFER** → B02-DATA-05                                  | **否** |
| G-05 / OP-01 | 非 skeleton 直写 fetch_log         | gate 启发式 fail-open                  | NON-BLOCKING | **RE-DEFER** → B02-DATA-05                                  | **否** |
| G-04         | row_count=0 边界                   | 条件回归无对照测                       | NON-BLOCKING | **WONT-FIX** — `row_count>0` 为设计内                       | **否** |
| G-06         | adapter→gate E2E 正向              | 分层单测未串联                         | NON-BLOCKING | **WONT-FIX** — AC 已满足                                    | **否** |
| G-07         | write_contract 无 validation_tests | YAML 与 pytest 无绑定                  | NON-BLOCKING | **RE-DEFER** — 全局契约策略                                 | **否** |

**A8 OPEN 计数：0**（见 `repair-evidence/zero-open-signoff.md`）

---

## 5. B3V-AUD-05 负向保全

| 检查项                                                                                              | 结果                       |
| --------------------------------------------------------------------------------------------------- | -------------------------- |
| `test_schemaHashDriftWithoutApproval_rejects` 仍存在                                                | PASS（diff 未改动体）      |
| `test_schemaHashDriftFlagInQualityFlags_rejects` 仍存在                                             | PASS                       |
| `test_missingSchemaHashOnStructuredFetch_rejects` 断言 `ValidationRejected` + `match="schema_hash"` | PASS（三后缀 parametrize） |
| `test_missingSchemaHash_registryFallback_rejects` 覆盖 registry 回退                                | PASS                       |
| corrupt 测试断言 `status in ("FAILED","SCHEMA_DRIFT")` 且 `!= "SUCCESS"`                            | PASS                       |
| 为过关删除 gate 拒绝分支                                                                            | **未发现**                 |

---

## 6. 测试质量（testing-guidelines）

| 检查项                                             | schema_hash 相关用例 | 备注                                                             |
| -------------------------------------------------- | -------------------- | ---------------------------------------------------------------- |
| 五字段 docstring（覆盖/对象/目的/验证点/失败含义） | PASS                 | 对齐 `ROUND3_TEST_DOCSTRING_HYGIENE`                             |
| 语义断言（非仅 not None / no throw）               | PASS                 | hash 长度/相等、异常类型+message、status 枚举                    |
| Mock 仅外部 I/O                                    | PASS                 | corrupt 用 `StubFetchPort`；gate 用 sandbox DB                   |
| 弱断言                                             | 无阻塞               | `assert result.status != "SUCCESS"` 在 `in (...)` 后冗余，信息性 |
| 确定性                                             | PASS                 | CSV/Parquet fixture 固定；Parquet 用 tmp_path 生成               |
| test catalog                                       | PASS                 | 三文件均在仓库 test catalog 内（无新增 orphan 模块）             |

**附加覆盖（非 §5.3 冻结，加分项）：**

- `test_inferSchemaHash_detectsNestedStructureDrift` — JSON 嵌套键漂移
- `test_inferSchemaHash_detectsTypeDrift` — 同键类型漂移
- `test_payloadSchemaHash_propagatesToFetchResultAndFetchLog` — hash 写入 fetch_log 传播

---

## 7. DOUBT（A8）

| Claim                                | 攻击                                       | 结论                                                   |
| ------------------------------------ | ------------------------------------------ | ------------------------------------------------------ |
| 「每个原始 Red Flag 有测试或 defer」 | §3.8 表逐项映射                            | **成立**                                               |
| 「B02_02 §6 五条测试要求全覆盖」     | Parquet/CSV gate + corrupt + drift 均有测  | **成立**（Post G-01 FIX）                              |
| 「只跑 §5.3 即可防生产 bypass」      | OP-01/G-05：非 skeleton + 无后缀 gate 窗口 | **不成立为完备** — 已 RE-DEFER B02-DATA-05，与 A4 一致 |
| 「AUDIT 选择器绿 = A8 过」           | 依赖 `QMD_DATA_ROOT` + basetemp 父目录存在 | **成立**（满足 AUDIT.plan 环境时）                     |

---

## 8. 后续 follow-up（非 A8 阻塞）

1. **G-02** — registry schemaless 标记后 `SUCCESS`+`row_count>0`+`schema_hash=NULL` 应 **允许** `assert_can_write`（B02-DATA-05）。
2. **G-05** — 多写入路径 integration：非 skeleton 直写 fetch_log + 无结构化线索（B02-DATA-05）。
3. **G-07** — 若项目统一 `write_contract.yaml` validation_tests，可补 YAML↔pytest 绑定。

---

## 9. A8 维度结论

| 项                                 | 状态                                         |
| ---------------------------------- | -------------------------------------------- |
| AUDIT.plan pytest 选择器           | PASS（106 passed，sandbox 前提下）           |
| MASTER §5.3 冻结用例 + Repair 增项 | PASS（10/10 点名子集）                       |
| B02_02 §6 五条要求                 | PASS                                         |
| B3V-AUD-05 负向保全                | PASS                                         |
| 计划外缺口 disposition             | 7 项均已 FIX / RE-DEFER / WONT-FIX；OPEN = 0 |
| **A8 总判定**                      | **PASS**                                     |
