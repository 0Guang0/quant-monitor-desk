# Audit A4 Report — Five-Axis Clean E2E Assertability / Code Quality

## 元信息

| 字段                  | 值                              |
| --------------------- | ------------------------------- |
| 维                    | A4                              |
| 任务                  | wave4-r3-dcp-06-five-axis-clean |
| plan_protocol_version | 4.1                             |
| 模板                  | `agents/code-reviewer.md`       |
| 日期                  | 2026-07-02                      |
| 审计员                | A4 subagent（独立复验）         |

---

## 维度证据

### 范围与权威

| 来源                                    | 用途                                                    |
| --------------------------------------- | ------------------------------------------------------- |
| `research/plan-spec.md` FR-4/FR-5       | 每轴 clean→feature→interpretation 可断言；ResourceGuard |
| `research/to-issues-slices.md` S00–S06  | 切片 AC、测试模块名                                     |
| `AUDIT.plan.md` §2 A4                   | 五轴 clean e2e 可断言                                   |
| `agents/audit-adversarial-authority.md` | 对抗性：目的 vs 实现、脆弱断言                          |
| ADR-029                                 | P0 绑定、流动性 ponytail                                |

### 独立 pytest（A4 范围）

```text
uv run pytest \
  tests/test_layer1_clean_reader.py \
  tests/test_layer1_environment_clean_e2e.py \
  tests/test_layer1_credit_stress_clean_e2e.py \
  tests/test_layer1_risk_appetite_clean_e2e.py \
  tests/test_layer1_liquidity_clean_e2e.py \
  tests/test_layer1_sentiment_clean_e2e.py \
  tests/test_layer1_five_axis_panel_clean_smoke.py \
  -q
```

| 项        | 结果  |
| --------- | ----- |
| exit code | **0** |
| collected | 16    |
| passed    | 16    |
| failed    | 0     |

### §3.4 多轴审查表

| 轴            | 发现摘要                                                                                                                                                                    | 证据                                                                  |
| ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| 正确性        | 五轴垂直链（读→特征→解读）在隔离库可跑通；S06 panel 含 LIQ 解读（S07 修复后）                                                                                               | 16/16 pytest 绿；`test_layer1_five_axis_panel_clean_smoke.py:116-129` |
| 可读性        | 全部 `test_*` 含五字段中文 docstring；共享 `layer1_clean_e2e_support.py` 种子清晰                                                                                           | 各 e2e 模块 docstring                                                 |
| 架构          | `clean_observation_reader.py` 与 staged 桥并行；ponytail cap 常量在 reader                                                                                                  | ADR-029 §1–3                                                          |
| 安全（局部）  | macro/bar `staged_fixture` 拒绝有实现；macro 有单测，bar 无                                                                                                                 | `clean_observation_reader.py:96-98,192-196`                           |
| 性能/资源     | row_cap 行为有 macro/bar 证明；cap 数值与 YAML 无程序化对账                                                                                                                 | `test_layer1_clean_reader.py:97-131`                                  |
| 测试质量      | FR-4 单轴解读断言不一致（CREDIT/LIQ 弱于 ENV/RISK/SEN）；ResourceGuard「真库」测近乎 tautological                                                                           | 见 §计划内问题                                                        |
| K1/A4/L1 交叉 | panel 含 `test_dcp06K1_whitelistAlignsP0CleanBindings`、MagicMock HARD_STOP、window_len≤cap；L1 `clean_replay_proven` 在 `test_model_input_whitelist.py`（A4 范围外但存在） | panel smoke 5 测                                                      |

### FR-4 逐轴断言对照

| 轴            | 读               | 特征                    | 解读                           | 备注                  |
| ------------- | ---------------- | ----------------------- | ------------------------------ | --------------------- |
| ENVIRONMENT   | ✓ fred / spec id | ✓ z_score, state_bucket | ✓ boundary_reminder            | S01 完整              |
| CREDIT_STRESS | ✓                | ✓                       | △ 无 boundary_reminder         | 仅否定 买入/卖出      |
| RISK_APPETITE | ✓                | ✓                       | ✓ boundary + level 含 id       | S03 完整              |
| LIQUIDITY     | ✓ alpha_vantage  | ✓                       | △ 仅 level_label==state_bucket | S06 panel 补 boundary |
| SENTIMENT     | ✓ cftc_cot       | ✓                       | ✓ boundary_reminder            | S05 完整              |

### DOUBT 对抗搜索声明

已搜索：`clean_observation_reader.py`、`layer1_clean_e2e_support.py`、六组 e2e + panel smoke、`layer1_source_whitelist.yaml` P0 行、`test_model_input_whitelist.py::test_layer1_p0_dcp06_cleanReplayProven`（范围外交叉引用）。重点：测试目的 vs 断言强度、cap 漂移假绿、ResourceGuard 接线、bar fail-closed 缺口。

---

## §维度裁决

**FAIL**

（§计划内 + §计划外 findings 表均含非占位行 → 按 `audit-finding-schema.md` 强制 FAIL）

**pytest exit code（A4 范围）：0**

---

## 计划内问题

| ID        | P   | 标题                                                  | 锚点                                                                                      | 根因                                                                                                                                                                                                 | 修复方案                                                                                                                                                                                                      | 验证                                                                                                                           |
| --------- | --- | ----------------------------------------------------- | ----------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| A4-P2-001 | P2  | Reader cap 常量与 K1 YAML 无程序化对账                | `clean_observation_reader.py:31-45`；`test_layer1_five_axis_panel_clean_smoke.py:192-194` | `P0_ROW_CAPS`/`P0_WINDOW_CAPS` 手写镜像 whitelist；K1 测仅断言 YAML 有 cap，未 `assert resolve_read_limit(spec)==yaml_row_cap`                                                                       | 在 panel 或 reader 测试中：对 DCP-06 五 spec 解析 `layer1_source_whitelist.yaml` 的 `row_cap`/`window_cap`（去 `d`/`w` 后缀），与 `resolve_read_limit`/`resolve_window_cap` 逐项相等                          | `uv run pytest tests/test_layer1_five_axis_panel_clean_smoke.py::test_dcp06K1_whitelistAlignsP0CleanBindings -q` 扩展后 exit 0 |
| A4-P2-002 | P2  | Bar clean 读路径缺 staged_fixture 拒绝单测            | `clean_observation_reader.py:192-196`；`test_layer1_clean_reader.py`（无对称用例）        | macro 有 `test_layer1CleanReader_rejectsStagedFixtureSourceUsed`，bar 守卫同构但未测；回归可 silently 移除 bar 守卫                                                                                  | 新增 `test_layer1CleanReader_rejectsStagedFixtureBarSource`：`seed_spy_bars` 后 `UPDATE source_used='staged_fixture'` → `pytest.raises(CleanObservationFallbackForbiddenError)`                               | `uv run pytest tests/test_layer1_clean_reader.py -q` exit 0                                                                    |
| A4-P2-003 | P2  | Panel ResourceGuard「真库」测未证明特征链 fail-closed | `test_layer1_five_axis_panel_clean_smoke.py:197-209` vs `87-129`                          | `resourceGuardOnMigratedDb` 仅调用孤立 `ResourceGuard(con).check()`，断言 `decision ∈ {OK,PAUSE,HARD_STOP}` 覆盖枚举全集；panel smoke 内 `AxisFeatureEngine()` 用默认无 `con` 的 guard，与迁移库无关 | 方案 A：panel smoke 构造 `AxisFeatureEngine(resource_guard=ResourceGuard(con=con), …)` 并断言 `check` 被调用；或方案 B：注入可强制 HARD_STOP 的 guard stub 且传入 panel 循环。保留现有 MagicMock HARD_STOP 测 | `uv run pytest tests/test_layer1_five_axis_panel_clean_smoke.py -q` exit 0                                                     |
| A4-P3-001 | P3  | S04 LIQ 单轴 FR-4 解读断言薄于它轴                    | `test_layer1_liquidity_clean_e2e.py:51-56`                                                | 目的 docstring 写「贯通特征与解读」，但仅 `level_label==state_bucket`；无 `boundary_reminder`/`generated_by`（ENV/RISK/SEN 有）                                                                      | 对齐 S01：`assert interp_rows[0].boundary_reminder == "不构成交易动作"`（及可选 `generated_by`）                                                                                                              | `uv run pytest tests/test_layer1_liquidity_clean_e2e.py -q` exit 0                                                             |

---

## 计划外发现

| ID        | P   | 标题                                             | 锚点                                           | 根因                                                                                    | 修复方案                                                                                                | 验证                                                                   |
| --------- | --- | ------------------------------------------------ | ---------------------------------------------- | --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| A4-P3-002 | P3  | CREDIT 单轴解读缺 boundary_reminder 断言         | `test_layer1_credit_stress_clean_e2e.py:64-69` | 仅检查 summary 不含买卖词，未锁定合规边界文案                                           | 增加 `assert interp.boundary_reminder == "不构成交易动作"`                                              | `uv run pytest tests/test_layer1_credit_stress_clean_e2e.py -q` exit 0 |
| A4-P3-003 | P3  | `as_of_end` 时间窗过滤无 reader 单测             | `clean_observation_reader.py:131-133`          | 种子可构造 as_of 之后 publish 行；无测证明过滤生效，未来 ORDER/LIMIT 改动可假绿         | 种子 40 行 + 1 行 `publish_timestamp > AS_OF`；断言读结果不含未来行且末行正确                           | `uv run pytest tests/test_layer1_clean_reader.py -q` exit 0            |
| A4-P3-004 | P3  | `macro_supplementary` 前缀禁止未在 reader 测覆盖 | `clean_observation_reader.py:16`               | `FORBIDDEN_FALLBACK_SOURCE_PREFIXES` 含 `macro_supplementary`，仅 `staged_fixture` 有测 | 新增 macro/bar 各一测：`source_used='macro_supplementary:…'` → `CleanObservationFallbackForbiddenError` | `uv run pytest tests/test_layer1_clean_reader.py -q` exit 0            |

已对抗搜索：`clean_observation_reader` fail-closed 分支、五轴 e2e 解读断言对称性、K1 cap 对账、ResourceGuard 与 panel 特征链接线、`as_of_end` 与 forbidden 前缀边界。

---

## 做得好的地方

- **S00 契约扎实**：空库 fail-closed、staged_fixture 拒绝、Amihud bar 路径、macro/bar row_cap 行为均有独立证明（`test_layer1_clean_reader.py` 六测）。
- **五字段 docstring 全覆盖**：A4 范围 16 个 `test_*` 均含覆盖范围/对象/目的/验证点/失败含义，符合 `testing-guidelines` §9.1。
- **S06 panel 集成**：五轴同库 smoke + K1 绑定对账 + LIQ 解读 `boundary_reminder`（S07 修复）+ MagicMock HARD_STOP，满足 G12 硬门禁主路径。
- **ponytail 标注清晰**：reader 模块注释标明 cap 镜像 K1、升级路径加载 YAML，符合 ADR-029 流动性 ponytail 政策。

---

## Verification Story

| 项               | 结果                                                                                |
| ---------------- | ----------------------------------------------------------------------------------- |
| Tests reviewed   | 是 — 16 测全文 + `clean_observation_reader.py` + `layer1_clean_e2e_support.py`      |
| Build verified   | 是 — A4 范围 pytest exit 0                                                          |
| Security checked | 局部 — fail-closed/staged 守卫有实现；bar/macro_supplementary 测缺口已记入 findings |
