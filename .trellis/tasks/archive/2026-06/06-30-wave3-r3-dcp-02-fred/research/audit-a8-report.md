# Audit A8 — Test Gap / QA

> **维：** A8 (audit-test-gap)  
> **任务：** `.trellis/tasks/06-30-wave3-r3-dcp-02-fred`  
> **协议：** debt-lite Phase 8D  
> **Worktree：** `../quant-monitor-desk-wt-dcp02` · branch `feature/wave3-r3-dcp-02-fred`  
> **审计日期：** 2026-06-30  
> **模型：** composer-2.5

---

## 维度证据

### AUDIT.plan §2 A8 验证矩阵对照

| 检查项                           | 命令 / 锚点                                                | 结果          | 证据                                                                                       |
| -------------------------------- | ---------------------------------------------------------- | ------------- | ------------------------------------------------------------------------------------------ |
| **空表 watermark**               | `test_fredWatermark_emptyTable_returnsCappedColdStart`     | PASS          | `uv run pytest tests/test_fred_macro_incremental_watermark.py -q -k emptyTable` → 1 passed |
| **多 series 独立 watermark**     | `test_fredWatermark_multiSeries_independentWatermarks`     | PASS          | `-k multiSeries` → 1 passed；DGS10 since=次日、VIXCLS 冷启动 cap                           |
| **无 key 负例**                  | `test_fredPort_live_rejectsWithoutApiKey`                  | PASS          | `-k rejectsWithoutApiKey` → `PortError.status == USER_AUTH_REQUIRED`；无 silent mock 回退  |
| **幂等 re-run**                  | `test_fredIncremental_idempotent_secondRun_rowCountStable` | PASS          | `-k idempotent` → 两次跑后 `COUNT(*)` 相等且 `>= 1`                                        |
| **隔离 pytest（audit-sandbox）** | 四模块定向套件 + `--basetemp`                              | PASS          | 见下「隔离 pytest 复跑」                                                                   |
| **五字段 docstring**             | 14 个 `test_*`                                             | PASS          | AST 扫描 14/14 含 覆盖范围·测试对象·目的/目标·验证点·失败含义                              |
| **test_catalog 登记**            | `tests/test_catalog.yaml`                                  | **N/A（P7）** | 用户注记：登记已 revert，由 P7 coordinator 承接；**不计入本维 finding**                    |

### 隔离 pytest 复跑（2026-06-30）

```powershell
New-Item -ItemType Directory -Force -Path ".trellis/tasks/06-30-wave3-r3-dcp-02-fred/.audit-sandbox/pytest"
uv run pytest tests/test_fred_macro_incremental_watermark.py `
  tests/test_fred_macro_incremental_port.py `
  tests/test_fred_macro_incremental_e2e.py `
  tests/test_fred_macro_incremental_cli.py -q `
  --basetemp=".trellis/tasks/06-30-wave3-r3-dcp-02-fred/.audit-sandbox/pytest"
# → 13 passed, 1 skipped (live_smoke 无 FRED_API_KEY)；exit 0
```

首次未 `mkdir` 父目录时 3 个 `tmp_path` 用例 **ERROR**（WinError 3）；创建 `.audit-sandbox/pytest` 后复跑全绿——属审计环境前置，非产品缺陷。

### 五字段 docstring 抽检

| 模块                                       | test 数 | 五字段    |
| ------------------------------------------ | ------- | --------- |
| `test_fred_macro_incremental_watermark.py` | 3       | 3/3       |
| `test_fred_macro_incremental_port.py`      | 4       | 4/4       |
| `test_fred_macro_incremental_e2e.py`       | 3       | 3/3       |
| `test_fred_macro_incremental_cli.py`       | 4       | 4/4       |
| **合计**                                   | **14**  | **14/14** |

机械校验：`uv run python` AST + `_missing_fields` 逻辑（同 `test_docstring_quadruple_coverage.py`）→ `gaps none`。

### DEBT 切片 S02-01..05 测试映射

| Slice              | 建议测                                         | 实测模块                                      | 判定                   |
| ------------------ | ---------------------------------------------- | --------------------------------------------- | ---------------------- |
| S02-01 watermark   | `test_fred_macro_incremental_watermark.py`     | 空表 / 有观测 / 多 series                     | PASS                   |
| S02-02 port window | `test_fred_macro_incremental_port.py`          | start_time、cold cap、filter、no-key          | PASS                   |
| S02-03 e2e replay  | `test_fred_macro_incremental_e2e.py -k replay` | mock + `run_incremental` → `axis_observation` | PASS                   |
| S02-04 live + 幂等 | e2e live_smoke + idempotent                    | 见 §计划内 finding（live 弱断言）             | PARTIAL                |
| S02-05 CLI         | `test_fred_macro_incremental_cli.py`           | dry-run、live gate、mock 真跑、help           | PARTIAL（help 弱断言） |

### Red Flag / 参考采纳（A8 横切）

| Red Flag / 契约                                 | 测试覆盖                                                                      | 判定                                         |
| ----------------------------------------------- | ----------------------------------------------------------------------------- | -------------------------------------------- |
| 空表冷启动 capped 窗                            | `test_fredWatermark_emptyTable_*` + `test_fredPort_coldStart_*`               | PASS                                         |
| per-series watermark                            | `test_fredWatermark_multiSeries_*`                                            | PASS（单元；无多 series e2e 编排，见计划外） |
| 无 `FRED_API_KEY` fail-closed                   | `test_fredPort_live_rejectsWithoutApiKey`                                     | PASS                                         |
| EasyXT forbidden（silent 回退）                 | port 负例 docstring 明示；断言 `USER_AUTH_REQUIRED`                           | PASS（port 层）                              |
| env-gated live                                  | `test_fredIncremental_live_smoke_*`（skip 无 key）+ CLI `LIVE_FETCH_REJECTED` | PARTIAL                                      |
| 幂等 upsert                                     | `test_fredIncremental_idempotent_*`                                           | PASS                                         |
| `reference-adoption-dcp02.md` L3 多 series 编排 | 仅 watermark 单测；e2e 恒 `series_ids=("DGS10",)`                             | 见计划外                                     |

### GitNexus

| 动作                                                                         | 结果                                          |
| ---------------------------------------------------------------------------- | --------------------------------------------- |
| `query("fred macro incremental watermark axis_observation run_incremental")` | 索引偏旧；未命中 `fred_incremental_*` 新符号  |
| `context("run_fred_macro_incremental")`                                      | Symbol not found（worktree 新文件未 analyze） |
| 任务内 `research/gitnexus-execute-summary.md`                                | 已 Read；Execute 阶段风险 LOW                 |

**注：** 新 ops 符号需 `node .gitnexus/run.cjs analyze` 后复索引；本维以 **代码 Read + pytest 复跑** 为准。

### §3.8 Red Flag 追溯表

| Red Flag                   | 覆盖                                                       | 补测/证据                      |
| -------------------------- | ---------------------------------------------------------- | ------------------------------ |
| 空表 watermark             | `test_fredWatermark_emptyTable_returnsCappedColdStart`     | 定向 pytest 绿                 |
| 多 series watermark        | `test_fredWatermark_multiSeries_independentWatermarks`     | 定向 pytest 绿                 |
| 无 API key                 | `test_fredPort_live_rejectsWithoutApiKey`                  | 定向 pytest 绿                 |
| 幂等 re-run                | `test_fredIncremental_idempotent_secondRun_rowCountStable` | 定向 pytest 绿                 |
| live env gate              | CLI 负例 + live_smoke（条件 skip）                         | live_smoke 断言偏弱（finding） |
| EMPTY_RESPONSE（水位追上） | **无** 专用 replay 测                                      | 计划外 finding                 |
| test_catalog 注册          | P7 coordinator                                             | 本维 N/A                       |

---

## §维度裁决

**FAIL**

（§计划内 + §计划外 findings 表均有非占位行；按 `audit-finding-schema.md` 须 FAIL。）

---

## 计划内问题

| ID        | P   | 标题                                | 锚点                                                                                              | 根因                                                                                                                                         | 修复方案                                                                                                                                              | 验证                                                                                                                 |
| --------- | --- | ----------------------------------- | ------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| A8-P2-001 | P2  | live_smoke 验证点与断言不一致且过宽 | `tests/test_fred_macro_incremental_e2e.py::test_fredIncremental_live_smoke_envGated` L150-180     | docstring 验证点写 `COMPLETED` 或 `EMPTY_RESPONSE`；代码断言 `in {"COMPLETED", "FAILED_FINAL"}`——`FAILED_FINAL` 既不在验证点，也会放过真失败 | 断言改为 `status in {"COMPLETED", "EMPTY_RESPONSE"}`；若需容忍网络 flake，用 `pytest.mark.flaky` + 重试或拆成 opt-in 手册测，勿用 `FAILED_FINAL` 绿过 | 有 `FRED_API_KEY` 时 `uv run pytest tests/test_fred_macro_incremental_e2e.py -q -k live_smoke`；无 key 时 skip 仍 OK |
| A8-P3-001 | P3  | CLI help 测未兑现 docstring 验证点  | `tests/test_fred_macro_incremental_cli.py::test_fredIncrementalCli_help_showsSourceIdFlag` L75-90 | 验证点声称 help 含 `macro_series` 示例域；仅断言 `--source-id`，未检查 `macro_series` 字符串                                                 | 增加 `assert "macro_series" in proc.stdout`（或修正 docstring 若 help 本无示例域）                                                                    | `uv run pytest tests/test_fred_macro_incremental_cli.py -q -k help`                                                  |

---

## 计划外发现

| ID        | P   | 标题                                | 锚点                                                          | 根因                                                                                                                 | 修复方案                                                                                                | 验证                                                                          |
| --------- | --- | ----------------------------------- | ------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| A8-P3-002 | P3  | EMPTY_RESPONSE 水位追上无 replay 测 | `backend/app/ops/fred_incremental_run.py` L112-121 · e2e 套件 | staging adapter 在 watermark 过滤后零行时返回 `EMPTY_RESPONSE`；14 条 fred 增量测无一构造「since 已最新」replay 场景 | 新增 e2e：seed 最新观测 + mock 仅旧点 → 断言 `series_results[0]["status"]=="EMPTY_RESPONSE"` 且行数不变 | `uv run pytest tests/test_fred_macro_incremental_e2e.py -q -k empty_response` |
| A8-P3-003 | P3  | 多 series 编排仅 watermark 单测     | `run_fred_macro_incremental` L296-345 · e2e 恒单 series       | L3 编排 loop 未在 e2e 用 `series_ids=("DGS10","VIXCLS")` 证明两路均 `COMPLETED`                                      | 可选：e2e mock 双 series + 断言 `len(series_results)==2` 且各行 `COMPLETED`                             | `uv run pytest tests/test_fred_macro_incremental_e2e.py -q -k multi_series`   |

已对抗搜索：`tests/test_fred_macro_incremental*.py` 全文 · `tests/fred_macro_incremental_support.py` · `rg EMPTY_RESPONSE\|multiSeries\|FRED_API_KEY` 于 `tests/` · `reference-adoption-dcp02.md` §4 L3 行 · DEBT S02-01..05 表 · GitNexus query/context（索引未含新符号）。

---

## 本维未纳入（显式排除）

- **`tests/test_catalog.yaml` 登记**：用户注记 revert + P7 coordinator；非 A8 测试缺口。
- **全库 `uv run pytest -q`**：属 A5 completion；本维仅定向四模块 + audit-sandbox basetemp。
- **代码 ponytail / 重复 helper**：属 A2；本维不修代码。
