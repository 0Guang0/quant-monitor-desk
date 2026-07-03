# Audit A3 Report — M-DATA-03 Tier A Live R2（Security）

## 元信息

| 字段   | 值                                                              |
| ------ | --------------------------------------------------------------- |
| 维度   | A3 — audit-security                                             |
| 任务   | `.trellis/tasks/m-data-03-tier-a-live`                          |
| 协议   | `plan_protocol_version: 4.1`                                    |
| 模板   | `agents/security-auditor.md` · `agents/audit-finding-schema.md` |
| 日期   | 2026-07-03                                                      |
| 审计员 | security-auditor 子 agent（独立复验）                           |

---

## 维度证据 §3.3

### Boot / 追溯

| 项                                | 状态 | 证据                                                           |
| --------------------------------- | ---- | -------------------------------------------------------------- |
| `audit-boot-v4.1.md` Boot         | ✓    | 已 Read                                                        |
| `audit-adversarial-authority.md`  | ✓    | 已 Read                                                        |
| `audit-finding-schema.md`         | ✓    | 已 Read                                                        |
| `AUDIT.plan.md` §0.1 + §2 A3      | ✓    | 无 `参考项目` runtime import；隔离 `DATA_ROOT`；live 闸        |
| `00-EXECUTION-ENTRY.md` §2        | ✓    | `QMD_ALLOW_LIVE_FETCH` + 隔离 `DATA_ROOT`（ADR-034 · ADR-027） |
| ADR-027 / ADR-034                 | ✓    | product live env gate · Tier A 隔离验收                        |
| `reference-adoption-m-data-03.md` | ✓    | 借鉴梯仅 `参考项目/**`；forbidden 语义登记                     |
| `gitnexus-audit-summary.md`       | ✓    | 7.pre 已 Read                                                  |

### GitNexus

| 调用                                                                                                     | 结果                                                                                         |
| -------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| `query({repo:"quant-monitor-desk", query:"tier_a_live validate_live_acceptance_env product_live_gate"})` | 返回 live*pilot / production_gate 邻域；**未直接索引** `tier_a_live*\*` 新符号（索引 stale） |
| `context({name:"validate_live_acceptance_env", repo:"quant-monitor-desk"})`                              | Symbol not found                                                                             |

> 静态审计以 **rg + Read + pytest 独立复验** 为准；与 `gitnexus-audit-summary.md` 结论一致。

### 静态命令（A3 基线 + R2 任务面）

```text
# 参考项目 runtime import — backend/scripts
rg "参考项目" backend/ scripts/
→ 0 matches

# tier_a_live 生产面密钥字面量
rg -i "api[_-]?key|secret|token|password" backend/app/ops/tier_a_live*.py scripts/tier_a_live*.py
→ 仅 SOURCE_API_KEY_ENV 槽位名（FRED_API_KEY 等），无硬编码值

# live 闸调用链（dispatch）
rg "assert_product_live_allowed|gate_live_fetch_port" backend/app/ops/tier_a_live_incremental_dispatch.py
→ _sync_fred_live · _run_macro_live · _run_bar_live · _run_port_live 均 assert_product_live_allowed；port 工厂 use_mock=False

# mock env 绕过
rg "QMD_FRED_INCREMENTAL_USE_MOCK|live_acceptance_mock_env_enabled" backend/app/ops/tier_a_live*.py
→ validate_live_acceptance_env L141-145 fail-closed；fred dispatch 硬编码 use_mock=False（不经 data_commands）
```

### 独立 pytest 复验

```bash
uv run pytest tests/test_reference_adoption_guardrails.py tests/test_tier_a_live_harness.py -q
# exit 0（46 passed, 1 skipped）
```

### Checklist 对照（AUDIT.plan §2 A3 + ENTRY §2 + plan-spec）

| 威胁面                       | 结论     | 证据摘要                                                                                                                                                                                                                                                              |
| ---------------------------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 无 `参考项目` runtime import | **PASS** | `backend/` · `scripts/` 0 命中；`test_noReferenceProjectRuntimeImport` 绿（AST + sys.path + 参考项目 子串扫描）                                                                                                                                                       |
| `QMD_ALLOW_LIVE_FETCH` 门禁  | **PASS** | `is_product_live_fetch_allowed()` · `validate_live_acceptance_env` → `LIVE_FETCH_NOT_OPTED_IN`；dispatch 各路径 `assert_product_live_allowed`；`test_validateLiveAcceptanceEnv_rejectsWithoutLiveFetchOptIn` · `test_livePort_noSilentFallbackToMock` · CLI exit 2 绿 |
| 无 silent mock fallback      | **PASS** | `live_acceptance_mock_env_enabled()` 在 env 层拒绝 `QMD_FRED_INCREMENTAL_USE_MOCK`；fred `_sync_fred_live` 不经 `data_commands._sync_fred_macro_incremental`；`test_validateLiveAcceptanceEnv_rejectsFredMockEnv` 绿                                                  |
| 隔离 `DATA_ROOT` / 无主库写  | **PASS** | `assert_isolated_live_data_root` 拒绝 canonical main DB/data root；要求路径含 `.audit-sandbox/m-data-03`；`resolve()` 规范化后复检；harness 负向测绿                                                                                                                  |
| 无密钥泄漏                   | **PASS** | `missing_api_keys_for_sources` 仅报 env **名**；manifest/report 无 env 值字段；`fred_port` 错误消息不含 key 值；CI workflow 用 `secrets.*` 注入                                                                                                                       |
| SEC_EDGAR UA 公平访问        | **PASS** | 共享 `validate_sec_edgar_user_agent`（`@` 或 `contact`）；`test_validateLiveAcceptanceEnv_rejectsBareSecEdgarUa` 绿                                                                                                                                                   |
| CLI exit 2 可观测            | **PASS** | `run_acceptance` / `run_acceptance_report` 在 `return 2` 前 `print(str(exc), stderr)`；`test_tierALiveAcceptanceCli_exit2WhenEnvInvalid` 断言 stderr 含闸信息                                                                                                         |

### R1 → R2 修复核对（历史 finding 关账）

| 历史 ID  | R1 问题                      | R2 状态    | 证据                                                               |
| -------- | ---------------------------- | ---------- | ------------------------------------------------------------------ |
| A3-P1-01 | fred mock env 静默 bypass    | **已消除** | `validate_live_acceptance_env` + `_sync_fred_live(use_mock=False)` |
| A3-P2-01 | fred dispatch 忽略 data_root | **已消除** | `_sync_fred_live` 调用 `_prepare_sandbox(data_root)`               |
| A3-P2-02 | SEC UA 弱校验                | **已消除** | `validate_sec_edgar_user_agent` 与 port 同构                       |
| A3-P3-01 | exit 2 静默                  | **已消除** | `print(str(exc), file=sys.stderr)`                                 |

### 对抗性搜索（计划外）

| 类                  | 范围                                                             | 结论                                                                                                                                        |
| ------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| 程序化 API 旁路     | `run_source_live_acceptance` 不经 `validate_live_acceptance_env` | dispatch 层 `assert_product_live_allowed` + port `gate_live_fetch_port` 仍 fail-closed；fred 硬编码 `use_mock=False`；**不构成 false pass** |
| 路径穿越 / 符号链接 | `assert_isolated_live_data_root` + `resolve()`                   | canonical main 路径经 `is_canonical_main_db_path` / `is_canonical_main_data_root` 拒绝                                                      |
| JWT / 硬编码密钥    | tier_a_live + fetch_ports                                        | 无硬编码；env 槽位 only                                                                                                                     |
| CI artifact 泄漏    | `.github/workflows/tier-a-live.yml`                              | secrets 经 GitHub Secrets；failure artifact 仅 report/manifest JSON（无 env 值字段）                                                        |
| SQL 注入            | `_clean_row_count`                                               | `quote_ident(clean_table)` + 参数化 `source_used`；表名来自 registry                                                                        |

---

## §维度裁决

**PASS**

（§计划内 + §计划外 findings 表均为占位行；checklist 满足 AUDIT.plan §2 A3。）

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

已对抗搜索：`backend/app/ops/tier_a_live*.py` · `scripts/tier_a_live_acceptance.py` · `backend/app/ops/tier_a_live_incremental_dispatch.py` · `backend/app/datasources/product_live_gate.py` · `backend/app/datasources/fetch_ports/*`（tier A 11 源）· `tests/test_tier_a_live_harness.py` · `tests/test_reference_adoption_guardrails.py` · `.github/workflows/tier-a-live.yml` · `rg 参考项目 backend/ scripts/` · `rg QMD_FRED_INCREMENTAL_USE_MOCK` · GitNexus `query` + `context`（索引 stale，以代码为准）。除上表外未发现可 exploit 的 P0–P3 威胁面。
