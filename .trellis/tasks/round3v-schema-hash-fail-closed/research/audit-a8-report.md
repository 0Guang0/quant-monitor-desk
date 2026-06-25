# A8 audit-test-gap — B3V-DATA schema_hash fail-closed

> Dimension: A8 (Test Gap) only  
> Task: `round3v-schema-hash-fail-closed` · Playbook `B3V-DATA` / Manifest `B3V-C02`  
> Worktree: `../quant-monitor-desk-wt-b3v-data`  
> Skills: `agents/qa-expert.md` · `agents/test-automator.md` · `testing-guidelines`  
> Authority: `agents/audit-adversarial-authority.md` · `AUDIT.plan.md` §1 A8  
> Mode: **只读**（无补测、无代码修复）

---

## Verdict: **PASS_WITH_NON_BLOCKING_GAPS**

MASTER §5.1–§5.3 冻结用例与 B02_02 §6 核心负向均已落地；`B3V-AUD-05` 负向断言未被削弱。在设置 `QMD_DATA_ROOT` 且清理 `--basetemp` 的前提下，AUDIT.plan 指定 pytest 选择器 **103 passed / exit 0**。存在若干计划外边界未单测覆盖（见 §4），均标 NON-BLOCKING，不阻塞本任务 Execute 交接；建议在 B02-DATA-05 registry 闭合或主会话 follow-up 中补齐 defense-in-depth 用例。

---

## 1. 必读完成

| 来源 | 要点 |
|------|------|
| `agents/qa-expert.md` | A8 追溯 Red Flags；每 Flag 须 test \| defer \| §4.3 |
| `agents/test-automator.md` | 五字段 docstring；sandbox `QMD_DATA_ROOT`；Audit `--basetemp` |
| `testing-guidelines` | 语义断言、mock 边界、禁止弱唯一断言 |
| `agents/audit-adversarial-authority.md` | MASTER §5 仅参考；须对抗搜索计划外缺口 |
| `AUDIT.plan.md` §1 A8 | 三文件 pytest 选择器 + `--basetemp=.audit-sandbox/pytest` |
| `MASTER.plan.md` §5–§7 | 场景 S1–S5、§5.3 冻结 `test_*` 表、Red Flags |
| `B02_02_schema_hash_fail_closed.md` §6–§7 | 任务卡测试要求与验收命令 |
| `BATCH_3V_ADVERSARIAL_AUDIT.md` B3V-AUD-05 | 禁止为便利削弱 gate 负向 |
| `research/audit-a4-report.md` OP-01/OP-02 | Gate 启发式 fail-open 窗口（交叉引用） |

---

## 2. Pytest 证据

### 2.1 AUDIT.plan 权威选择器

**命令（与 `AUDIT.plan.md` 一致，审计时补充 sandbox）：**

```text
$env:QMD_DATA_ROOT = "<task>/.audit-sandbox/data"
uv run pytest tests/test_data_adapter_contract.py tests/test_db_validation_gate.py tests/test_adapter_skeletons.py -q --basetemp=.audit-sandbox/pytest
```

**结果（2026-06-25，worktree `fix/round3v-schema-hash-fail-closed`）：**

```text
........................................................................ [ 69%]
...............................                                          [100%]
103 passed
exit 0
```

**环境注记：**

| 条件 | 现象 | 处理 |
|------|------|------|
| 未设 `QMD_DATA_ROOT` | `test_skeletonAdapterBase_successWritesRawFile` 等 raw 路径断言失败 | 审计命令应显式设 sandbox data root |
| Windows 复用已存在 `--basetemp` | `FileExistsError` / `rm_rf` 警告 | 跑前删除 `.audit-sandbox/pytest` 或使用唯一 basetemp |

### 2.2 MASTER §5.3 冻结子集（7 用例）

**命令：**

```text
uv run pytest \
  tests/test_data_adapter_contract.py::test_dataAdapterContract_documentsStructuredSchemaHashRequirement \
  tests/test_db_validation_gate.py::test_missingSchemaHashOnStructuredFetch_rejects \
  tests/test_db_validation_gate.py::test_schemaHashDriftWithoutApproval_rejects \
  tests/test_adapter_skeletons.py::test_inferSchemaHash_csvHeader_producesStableHash \
  tests/test_adapter_skeletons.py::test_inferSchemaHash_parquetColumns_producesHash \
  tests/test_adapter_skeletons.py::test_skeletonFetch_corruptCsv_notSuccessEligible \
  tests/test_adapter_skeletons.py::test_skeletonFetch_corruptParquet_notSuccessEligible \
  -q
```

**结果：** `7 passed` · exit 0

### 2.3 任务卡 §7 邻接文件（非 A8 选择器）

`B02_02` §7 另列 `tests/test_data_quality_validator.py`；AUDIT A8 选择器未包含。现有 `test_schemaHashDriftFlagInQualityFlags_rejects`（gate）与 validator 内 `SCHEMA_DRIFT` 断言提供邻接覆盖，**不记为 A8 阻塞**。

---

## 3. §3.8 Red Flag / 场景映射

| Red Flag / 来源 | 场景 | 覆盖 | 证据 |
|-----------------|------|------|------|
| Gate weaken（MASTER §7） | 缺 hash / 漂移须 `ValidationRejected` | **测试** | `test_missingSchemaHashOnStructuredFetch_rejects`；既有 `test_schemaHashDriftWithoutApproval_rejects` 未改 |
| B3V-AUD-05 | 负向不得为过关删除 | **测试** | diff 仅新增 gate 负向；无删除 `assert_can_write` 拒绝分支 |
| AC-DATA-01 / S1–S2 契约 | 结构化 SUCCESS 须 schema_hash | **测试** | `test_dataAdapterContract_documentsStructuredSchemaHashRequirement` |
| AC-DATA-02 / S1 | CSV infer 稳定 hash | **测试** | `test_inferSchemaHash_csvHeader_producesStableHash` |
| AC-DATA-02 / S2 | Parquet infer 非空 hash | **测试** | `test_inferSchemaHash_parquetColumns_producesHash` |
| AC-DATA-03 / S3 | Gate 缺 hash fail-closed | **测试** | `test_missingSchemaHashOnStructuredFetch_rejects`（`.csv` 后缀路径） |
| AC-DATA-04 / S4 | 损坏 CSV/Parquet 非 SUCCESS | **测试** | `test_skeletonFetch_corruptCsv_notSuccessEligible`；`test_skeletonFetch_corruptParquet_notSuccessEligible` |
| AC-DATA-05 / S5 | hash 漂移拒绝 | **测试** | `test_schemaHashDriftWithoutApproval_rejects`（回归） |
| 全文件 Parquet 扫描（§7 RF） | 有界推导 | **测试间接** | Parquet 单测用 DuckDB 最小文件；无全量扫描断言 |
| registry 并发（§7 RF） | Execute 禁止 | **defer** | B02-DATA-05 → 主会话 |
| B02_02 §6「Parquet success 无 hash 拒绝写库」 | Gate 层 Parquet 路径 | **部分** | 与 CSV 共用 `_raw_paths_indicate_structured`；**无独立 `.parquet` gate 用例**（见 G-01） |
| B02_02 §6「CSV success 无 hash 拒绝写库」 | Gate 层 CSV 路径 | **测试** | `test_missingSchemaHashOnStructuredFetch_rejects` |
| schemaless 豁免（契约） | 无 hash 仍允许写 | **defer** | 契约文档断言含 `schemaless`；无正向 gate 单测（见 G-02） |
| write_contract `validation_tests` | YAML 契约 pytest | **defer** | `write_contract.yaml` 无 `validation_tests` 段；行为由 gate 单测覆盖 |

---

## 4. 计划外发现

| ID | 场景 | 若只按 MASTER §5.3 测会漏什么 | 严重度 | §4.3 建议 |
|----|------|----------------------------------|--------|-----------|
| G-01 | Gate 缺 hash：仅 `.csv` raw 路径受测 | `.parquet` / `.json` 后缀同代码路径但未独立证据 | NON-BLOCKING | 主会话可加参数化：`raw_file_paths` 三后缀各一例 |
| G-02 | schemaless source 注册后 `SUCCESS`+`row_count>0`+`schema_hash=NULL` | 无法证明豁免路径不误拒 / 非 schemaless 误放行 | NON-BLOCKING | defer 至 B02-DATA-05 registry 闭合后补正向用例 |
| G-03 | `raw_file_paths` 空 + `file_registry` 有 structured `file_type` 回退 | `_fetch_log_is_structured` registry 分支无单测 | NON-BLOCKING | `test_db_validation_gate` 增「无后缀 + registry 回退」用例 |
| G-04 | `SUCCESS`+`row_count=0`+`schema_hash=NULL`+结构化路径 | Gate 条件 `row_count>0` 故意不拦；无边界单测 | NON-BLOCKING | 文档化或加「允许写」负向对照（防回归改条件） |
| G-05 | 非 skeleton 写入路径直写 `fetch_log`（OP-01 / A4-01） | 无后缀且无 registry 时 gate fail-open | NON-BLOCKING | registry / 多写入路径闭合后补 integration |
| G-06 | Adapter infer 成功 → Gate `assert_can_write` 正向 E2E | 仅单元分层；未证明「合法 hash 整条链路可写」 | NON-BLOCKING | 可选：stub fetch 写 log + gate 放行单测 |
| G-07 | `write_contract.yaml` 无 `validation_tests` | 契约 YAML 与 pytest 无显式绑定 | NON-BLOCKING | 与项目其他 contract 策略一致时可 defer |

**对抗搜索声明：** 已检索 `tests/` 中 `schema_hash`、`schemaless`、`missingSchemaHash`、`corruptParquet`、`SCHEMA_DRIFT`；对照 `validation_gate._schema_hash_blocks_write` 全分支、`skeleton_base._fetch_impl` 守卫；审阅相对 `master` 的三测试文件 diff（仅 additive，无削弱既有负向）。

---

## 5. B3V-AUD-05 负向保全

| 检查项 | 结果 |
|--------|------|
| `test_schemaHashDriftWithoutApproval_rejects` 仍存在 | PASS（diff 未改动体） |
| `test_schemaHashDriftFlagInQualityFlags_rejects` 仍存在 | PASS |
| 新增 `test_missingSchemaHashOnStructuredFetch_rejects` 断言 `ValidationRejected` + `match="schema_hash"` | PASS（语义断言，非弱断言） |
| corrupt 测试断言 `status in ("FAILED","SCHEMA_DRIFT")` 且 `!= "SUCCESS"` | PASS（略宽但覆盖 fail-closed；adapter 实现固定 `SCHEMA_DRIFT`） |
| 为过关删除 gate 拒绝分支 | **未发现** |

---

## 6. 测试质量（testing-guidelines）

| 检查项 | 新增 7 用例 | 备注 |
|--------|-------------|------|
| 五字段 docstring（覆盖/对象/目的/验证点/失败含义） | PASS | 对齐 `ROUND3_TEST_DOCSTRING_HYGIENE` |
| 语义断言（非仅 not None / no throw） | PASS | hash 长度/相等、异常类型+message、status 枚举 |
| Mock 仅外部 I/O | PASS | corrupt 用 `StubFetchPort`；gate 用 sandbox DB |
| 弱断言 | 无阻塞 | `assert result.status != "SUCCESS"` 在 `in (...)` 后冗余，信息性 |
| 确定性 | PASS | CSV/Parquet fixture 固定；Parquet 用 tmp_path 生成 |

---

## 7. DOUBT（A8）

| Claim | 攻击 | 结论 |
|-------|------|------|
| 「每个原始 Red Flag 有测试或 defer」 | §3.8 表逐项映射 | **成立** |
| 「B02_02 §6 五条测试要求全覆盖」 | Parquet gate 路径仅逻辑覆盖、无独立用例 | **部分成立** — G-01 NON-BLOCKING |
| 「只跑 §5.3 即可防生产 bypass」 | OP-01/G-05：非 skeleton + 无后缀 gate 窗口 | **不成立为完备** — 已知 defer，与 A4 一致 |
| 「AUDIT 选择器绿 = A8 过」 | 依赖 `QMD_DATA_ROOT` + basetemp 卫生 | **成立**（满足 AUDIT.plan 环境时） |

---

## 8. 建议补测（主会话 / post-registry，本 Audit 不实施）

1. **G-01** — `@pytest.mark.parametrize("suffix", [".csv", ".parquet", ".json"])` 扩展 `test_missingSchemaHashOnStructuredFetch_rejects`。
2. **G-03** — `raw_file_paths='[]'` + `file_registry` 插入 `file_type='parquet'` → 缺 hash 仍 `ValidationRejected`。
3. **G-02** — registry schemaless 标记后同条件应 **允许** `assert_can_write`（需 B02-DATA-05 数据面）。

---

## 9. A8 维度结论

| 项 | 状态 |
|----|------|
| AUDIT.plan pytest 选择器 | PASS（103 passed，sandbox 前提下） |
| MASTER §5.3 冻结用例 | PASS（7/7） |
| B3V-AUD-05 负向保全 | PASS |
| 计划外缺口 | 7 项 NON-BLOCKING，已列 §4 |
| **A8 总判定** | **PASS_WITH_NON_BLOCKING_GAPS** |
