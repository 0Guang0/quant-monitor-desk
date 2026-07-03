# Audit A6 — K1 Model Input Whitelist（wave4-r3-dcp-06-five-axis-clean）

> **维：** A6 K1 whitelist（AUDIT.plan §2 主会话覆写；非 performance SKIP）  
> **协议：** plan_protocol_version 4.1  
> **日期：** 2026-07-02  
> **焦点：** FR-6 · ADR-029 §K1 · DCP-06 五轴 P0 `clean_replay_proven` 绑定

---

## 维度证据

### Boot / 范围

| 项                        | 证据                                                                  |
| ------------------------- | --------------------------------------------------------------------- |
| AUDIT.plan §2 A6          | K1 whitelist（主会话）                                                |
| plan-spec FR-6            | K1 P0 rows reflect `clean_replay_proven`（not production-live ready） |
| ADR-029 §Consequences L35 | P0 readiness 可从 `sandbox_candidate` → `clean_replay_proven`         |
| 活卡 / ENTRY              | 五轴 Tier A clean 读路径；`B2.5-O-05` 仍开放                          |

### ADR-029 P0 锚点 ↔ K1 白名单对账

| axis_id       | indicator_id (ADR-029)       | whitelist input_id | series | source_id     | readiness           | 裁决 |
| ------------- | ---------------------------- | ------------------ | ------ | ------------- | ------------------- | ---- |
| ENVIRONMENT   | ENV-E1-DGS10                 | L1-ENV-DGS10       | DGS10  | fred          | clean_replay_proven | OK   |
| CREDIT_STRESS | CRD.CS1.BAA10Y               | L1-CRD-BAA10Y      | BAA10Y | fred          | clean_replay_proven | OK   |
| RISK_APPETITE | RA.R1.VIXCLS_30D_IMPLIED_VOL | L1-RA-VIXCLS       | VIXCLS | fred          | clean_replay_proven | OK   |
| LIQUIDITY     | LIQ.B-I1.AMIHUD_ILLIQ        | L1-LIQ-AMIHUD-SPY  | SPY    | alpha_vantage | clean_replay_proven | OK   |
| SENTIMENT     | SEN-S1-COT_LF_NET            | L1-SEN-COT-LF-NET  | 088691 | cftc_cot      | clean_replay_proven | OK   |

- 五行 `forbidden_claims` 均含 `production-live ready`；全文件无 `readiness: production_candidate`
- `L1-LIQ-AMIHUD-SPY` notes 标注 ADR-029 ponytail；`forbidden_claims` 含 tiingo primary substitute guard

### 非 P0 / macro_supplementary 抽检

| 类别                | 行                                   | readiness / role                              | 裁决 |
| ------------------- | ------------------------------------ | --------------------------------------------- | ---- |
| B01-FRED 未 proven  | T10Y3M, SP500, DFII10                | sandbox_candidate · primary_candidate         | OK   |
| 非 P0 宏观          | EFFR, WRESBAL, M2SL                  | deferred · role=deferred                      | OK   |
| macro_supplementary | L1-MACRO-SUPP-VALIDATION             | validation_only · akshare · sandbox_candidate | OK   |
| 禁止替代 FRED P0    | macro_supplementary forbidden_claims | 含 `primary_candidate for FRED P0 series`     | OK   |

### docs/quality/model_input_readiness_matrix.md

- Legend 新增 `clean_replay_proven`（明确 **not** production-live）
- Layer1 表含五行 DCP-06 proven + 三行 B01 sandbox + macro_supplementary validation_only
- 脚注：`macro_supplementary` 不得替代 FRED P0（`B2.5-O-05`）

### 测试（独立复验）

```text
uv run pytest tests/test_model_input_whitelist.py -q
→ 25 passed, exit 0

uv run pytest tests/test_layer1_five_axis_panel_clean_smoke.py::test_dcp06K1_whitelistAlignsP0CleanBindings -q
→ 1 passed, exit 0
```

| 测试                                                 | 证明点                                              |
| ---------------------------------------------------- | --------------------------------------------------- |
| `test_layer1_p0_dcp06_cleanReplayProven`             | DGS10/BAA10Y/VIXCLS/SPY/088691 readiness + caps     |
| `test_layer1_p0_fred_macro_series_sandbox_candidate` | T10Y3M/SP500/DFII10 仍为 sandbox_candidate          |
| `test_layer1_macro_supplementary_not_fred_primary`   | akshare 非 primary                                  |
| `test_layer1_non_p0_indicators_deferred_or_p2`       | 非 P0 无 production_candidate；DCP-06 proven 行允许 |
| `test_readiness_matrix_documents_layers`             | 矩阵含 `clean_replay_proven` 语义                   |
| `test_dcp06K1_whitelistAlignsP0CleanBindings`        | runtime P0_BINDINGS ↔ whitelist source/series 对账  |

### 分支 diff 抽检备注（非 finding）

- `L1-ENV-DGS10` / `L1-RA-VIXCLS` 的 `closure_test` 仍写 B01-FRED sandbox 文案，较 BAA10Y/SPY/088691 少显式「DCP-06 clean replay e2e」子句；`readiness` 与 matrix `Next gate` 已正确，机器测试未覆盖 `closure_test` 文案一致性。

---

## §维度裁决

**PASS**

---

## 计划内问题

| ID  | P   | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| —   | —   | 无   | —    | —    | —        | —    |

---

## 计划外发现

| ID  | P   | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| —   | —   | 无   | —    | —    | —        | —    |

已对抗搜索：`specs/model_inputs/layer1_source_whitelist.yaml` 全行 · `docs/quality/model_input_readiness_matrix.md` Layer1 · ADR-029 P0 表 · `tests/test_model_input_whitelist.py` FR-6 相关用例 · `tests/test_layer1_five_axis_panel_clean_smoke.py` `test_dcp06K1_*` · `production_candidate` / `macro_supplementary` grep。
