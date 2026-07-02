# Audit A4 Report — R3-DCP-08 Layer4 US_EQ Clean Read / Code Quality

## 元信息

| 字段                  | 值                                           |
| --------------------- | -------------------------------------------- |
| 维                    | A4                                           |
| 任务                  | 07-02-wave4-r3-dcp-08-layer4                 |
| plan_protocol_version | 4.1                                          |
| 模板                  | `agents/code-reviewer.md`                    |
| 日期                  | 2026-07-02                                   |
| 审计员                | A4 subagent（独立复验 · 只审 A4）            |
| 工作目录              | `quant-monitor-desk-wt-dcp08`（未提交 diff） |

---

## 维度证据

### 范围与权威

| 来源                                                      | 用途                              |
| --------------------------------------------------------- | --------------------------------- |
| `AUDIT.plan.md` §2 A4                                     | US_EQ breadth 从 Tier A clean     |
| `research/00-EXECUTION-ENTRY.md` §1–§2                    | P0 US_EQ · ADR-033 · tier_a_clean |
| `research/to-issues-slices.md` S08-READ/ADAPTER/BUILD/E2E | 切片 AC · 建议测试                |
| `docs/decisions/ADR-033-dcp08-layer4-us-eq-clean-read.md` | clean read 决策 · mootdx 双轨     |
| `research/layer4-tier-a-research.md`                      | breadth 聚合语义                  |
| `research/plan-doubt-review.md` Cycle 1–4                 | US_EQ 定案 · 无 migration         |
| `agents/audit-adversarial-authority.md`                   | 对抗：错误模型 · 脆弱断言         |

### 审查 diff 范围

| 类别 | 路径                                                                    |
| ---- | ----------------------------------------------------------------------- |
| 新增 | `backend/app/layer4_markets/clean_read.py`                              |
| 新增 | `tests/layer4_clean_e2e_support.py`                                     |
| 新增 | `tests/test_layer4_clean_read.py`                                       |
| 新增 | `tests/test_layer4_us_equity_clean_e2e.py`                              |
| 修改 | `backend/app/layer4_markets/market_structure.py`（`tier_a_clean` 分支） |
| 修改 | `backend/app/cli/data_commands.py`（mootdx dry-run 路由）               |
| 修改 | `tests/test_qmd_data_sync_tier_a_router.py`（mootdx 断言扩展）          |

### 独立 pytest（A4 主范围）

```bash
uv run pytest \
  tests/test_layer4_clean_read.py \
  tests/test_layer4_us_equity_clean_e2e.py \
  tests/test_layer4_market_structure.py \
  -q
```

| 项        | 结果  |
| --------- | ----- |
| exit code | **0** |
| collected | 22    |
| passed    | 22    |
| failed    | 0     |

### 全量回归（A4 交叉引用）

```bash
uv run pytest -q
```

| 项        | 结果  |
| --------- | ----- |
| exit code | **0** |

### §3.4 多轴审查表

| 轴                     | 发现摘要                                                                                    | 证据                                                      |
| ---------------------- | ------------------------------------------------------------------------------------------- | --------------------------------------------------------- |
| 正确性                 | US_EQ clean bar → advancers/decliners/total_amount 聚合与 fixture 一致；staged 022 路径未改 | `test_layer4_clean_read.py` 4 测 + e2e 绿                 |
| 错误处理               | 空 bar 集 fail-closed（`Layer4MarketError`）；Builder 非交易日 US_EQ 拒（staged 已有测）    | `clean_read.py:44-47`；`test_cleanRead_noBars_failClosed` |
| 可读性                 | 新模块 ponytail 注释清晰；测试五字段 docstring 全覆盖                                       | `clean_read.py` · 5 个 `test_*`                           |
| 架构                   | `tier_a_clean` 与 `staged_fixture_only` 并行；lazy import clean_read                        | `market_structure.py:199-207,265-329`                     |
| 安全（局部）           | sandbox tmp_path DB；无密钥进 diff                                                          | `layer4_clean_e2e_support.py`                             |
| 性能                   | `_build_tier_a_clean` 对同日 bar 重复 JOIN 两次                                             | `market_structure.py:288-309`                             |
| 测试质量               | Builder `tier_a_clean` 负向路径、e2e lineage 细粒度、flat bar 语义未测                      | 见 §计划内/计划外                                         |
| mootdx 路由（diff 内） | dry-run JSON 强制覆盖 `selected_source_id`；runtime `__setattr__` 与测试 monkeypatch 并存   | `data_commands.py:543-555`                                |

### GitNexus

已调用 `query({repo: "quant-monitor-desk", query: "aggregate_breadth_from_bars USEquityCleanMarketAdapter"})`；索引未收录本 worktree 新符号（worktree 未 analyze）。改 symbol 前须 `impact()` + `detect_changes()`。

### DOUBT 对抗搜索声明

已搜索：`clean_read.py` 全文件、`market_structure.py` `_build_tier_a_clean`、`data_commands.py::sync_mootdx_incremental` dry-run 分支、`test_layer4_clean_read.py`、`test_layer4_us_equity_clean_e2e.py`、`test_layer4_market_structure.py`（tier_a_clean 负向）、`test_qmd_data_sync_tier_a_router.py` mootdx 相关、`layer4-tier-a-research.md` 聚合语义、`ADR-033` §5 registry 跟进。

---

## §维度裁决

**FAIL**

（§计划内 + §计划外 findings 表均含非占位行 → 按 `audit-finding-schema.md` 强制 FAIL）

**pytest exit code（A4 主范围 + 全量）：0**

---

## 计划内问题

| ID        | P   | 标题                                       | 锚点                                                                                                | 根因                                                                                                                                                                                        | 修复方案                                                                                                                                                                               | 验证                                                                                            |
| --------- | --- | ------------------------------------------ | --------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| A4-P2-001 | P2  | Builder `tier_a_clean` 负向路径无 pytest   | `market_structure.py:275-280`；`tests/test_layer4_market_structure.py`（无对应用例）                | `market_id != US_EQ` 与 `clean_con is None` 均有 `Layer4MarketError`，但无测证明 fail-closed；回归可 silent 放宽门禁                                                                        | 在 `test_layer4_market_structure.py` 或 `test_layer4_clean_read.py` 新增两测：`tier_a_clean` + `CN_A` → `Layer4MarketError`；`tier_a_clean` + `clean_con=None` → `Layer4MarketError`   | `uv run pytest tests/test_layer4_clean_read.py tests/test_layer4_market_structure.py -q` exit 0 |
| A4-P2-002 | P2  | e2e lineage 断言过弱                       | `test_layer4_us_equity_clean_e2e.py:38`；`collect_clean_lineage_provenance` `clean_read.py:100-133` | AC 要求 lineage 绑定 clean 表；当前仅 `assert "security_bar_1d" in "".join(source_dataset_ids)`，未断言 `source_fetch_ids` 含 fixture `batch_id`、未断言 `content_hashes` 长度与 bar 数一致 | 扩展 e2e：`assert len(result.lineage_envelope.source_content_hashes) == 3`；`assert any("batch-AAPL" in fid for fid in result.lineage_envelope.source_fetch_ids)`（或等价 batch 前缀） | `uv run pytest tests/test_layer4_us_equity_clean_e2e.py -q` exit 0                              |
| A4-P3-001 | P3  | flat bar（close==pre_close）聚合语义无单测 | `clean_read.py:55-58`；`layer4-tier-a-research.md:13-14`                                            | 调研写明 advancers=count(close>pre_close)、decliners=count(close<pre_close)；flat 不计入任一侧，但无测锁定；未来改 `>=`/`<=` 可假绿                                                         | 在 `test_layer4_clean_read.py` 种子 1 条 flat bar（close==pre_close），断言 advancers/decliners 不变且 total_amount 仍累加                                                             | `uv run pytest tests/test_layer4_clean_read.py -q` exit 0                                       |

---

## 计划外发现

| ID        | P   | 标题                                                         | 锚点                                                                                       | 根因                                                                                                                                                                   | 修复方案                                                                                                                                                                                                                                            | 验证                                                                                                 |
| --------- | --- | ------------------------------------------------------------ | ------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| A4-P2-003 | P2  | `_build_tier_a_clean` 对同日 bar 重复 SQL                    | `market_structure.py:288-309`；`clean_read.py:33-43` vs `107-118`                          | `adapter.load_breadth` 与 `collect_clean_lineage_provenance` 各执行相同 `security_bar_1d` JOIN；大库热路径双倍 I/O                                                     | ponytail 可接受则加注释说明；或让 `load_breadth` 返回 provenance 元组一次查询复用（最小 diff：内部 helper `_fetch_clean_bars_for_day`）                                                                                                             | `uv run pytest tests/test_layer4_us_equity_clean_e2e.py tests/test_layer4_clean_read.py -q` exit 0   |
| A4-P2-004 | P2  | mootdx dry-run 强制覆盖 `selected_source_id`                 | `data_commands.py:549-555`                                                                 | `preview_route` 结果写入 `preview` 后，若 `route_status==READY` 无条件 `preview["selected_source_id"]="mootdx"`；dry-run JSON 不再反映路由器真实决策，路由回归可被掩盖 | 方案 A：registry apply 后依赖真实 routing，删除覆盖；方案 B：保留覆盖但新增负向测——mock `preview_route` 返回 `baostock` 且 READY，断言 dry-run 仍 fail-closed（或文档化「effective primary overlay」并测 overlay 前原始值记入 `route_preview_raw`） | `uv run pytest tests/test_qmd_data_sync_tier_a_router.py -k mootdx -q` exit 0                        |
| A4-P2-005 | P2  | mootdx `validation_only` runtime hack 未按 ADR 移除          | `data_commands.py:543`；`test_qmd_data_sync_tier_a_router.py:76-88`；`ADR-033` §Decision 5 | ADR/registry delta 要求 registry apply 后移除 `object.__setattr__`；当前 Execute 仍 runtime 变异 + 测试 monkeypatch 镜像，双轨语义未落 registry SSOT                   | 主会话 merge `registry_proposed_delta.yaml` 后删除 `data_commands.py:543` 与 `_patch_mootdx_registry_validation_only`；dry-run 靠 registry `validation_only: false` 自然 routing                                                                    | `uv run pytest tests/test_qmd_data_sync_tier_a_router.py -k mootdx -q` exit 0（无 monkeypatch 仍绿） |
| A4-P3-002 | P3  | `build_calendar_row` 不校验 `market_id`                      | `clean_read.py:80-97`                                                                      | 公开函数接受任意 `market_id` 但始终调用 US `is_trading_day`；误传 `CN_A` 会产出错误 calendar 行                                                                        | 在 `build_calendar_row` 入口 `if market_id != US_EQ_MARKET_ID: raise Layer4MarketError(...)`，或收窄为模块内私有                                                                                                                                    | `uv run pytest tests/test_layer4_clean_read.py -q` exit 0                                            |
| A4-P3-003 | P3  | `collect_clean_lineage_provenance` 空 bar fail-closed 无单测 | `clean_read.py:119-122`                                                                    | 与 `aggregate_breadth_from_bars` 对称的空集守卫未独立证明                                                                                                              | 复用 `test_cleanRead_noBars_failClosed` 模式，对 `collect_clean_lineage_provenance` 断言 `no clean rows for lineage`                                                                                                                                | `uv run pytest tests/test_layer4_clean_read.py -q` exit 0                                            |
| A4-P3-004 | P3  | NULL `pre_close` 抛 `TypeError` 非 `Layer4MarketError`       | `clean_read.py:52-54`                                                                      | `float(pre_close_raw)` 在 NULL 时抛未包装异常，与 Layer4 fail-closed 错误模型不一致                                                                                    | 在循环内检测 `pre_close_raw is None`（或 close 缺失）→ `Layer4MarketError("missing pre_close for breadth aggregation")`                                                                                                                             | 新增单测：INSERT bar `pre_close=NULL` → `pytest.raises(Layer4MarketError)`                           |

已对抗搜索：`clean_read.py` 全部分支、`sync_mootdx_incremental` dry-run/live 分叉、registry proposed delta 与 runtime 一致性、tier_a_clean Builder 负向、lineage 断言强度、flat/NULL bar 边界。

---

## 做得好的地方

- **S08-READ/ADAPTER 契约扎实**：已知 bar 集聚合、calendar SSOT、adapter 封装、空 bar fail-closed 均有独立单测（`test_layer4_clean_read.py` 四测）。
- **五字段 docstring 全覆盖**：A4 范围 5 个 `test_*` 均含覆盖范围/对象/目的/验证点/失败含义。
- **staged 路径隔离**：`tier_a_clean` 新分支未动 manifest gate；022 staged 测仍绿（22/22）。
- **ponytail 标注**：mootdx `__setattr__`、breadth 聚合范围均有 `ponytail:` + 升级路径注释，符合 ADR-033。

---

## Verification Story

| 命令                                                                                                                              | 结果               |
| --------------------------------------------------------------------------------------------------------------------------------- | ------------------ |
| `uv run pytest tests/test_layer4_clean_read.py tests/test_layer4_us_equity_clean_e2e.py tests/test_layer4_market_structure.py -q` | exit 0 · 22 passed |
| `uv run pytest -q`                                                                                                                | exit 0 · 全绿      |
