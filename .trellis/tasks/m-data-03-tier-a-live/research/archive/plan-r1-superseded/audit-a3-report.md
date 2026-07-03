# Audit A3 Report — M-DATA-03 Tier A Live（Security）

## 元信息

| 字段   | 值                                                                                    |
| ------ | ------------------------------------------------------------------------------------- |
| 维度   | A3 — audit-security                                                                   |
| 任务   | `.trellis/tasks/m-data-03-tier-a-live`                                                |
| 协议   | `plan_protocol_version: 4.1`                                                          |
| 模板   | `agents/security-auditor.md` · `agents/sql-pro.md` · `agents/audit-finding-schema.md` |
| 日期   | 2026-07-03                                                                            |
| 审计员 | composer-2.5（只读）                                                                  |

---

## 维度证据 §3.3

### Boot / 追溯

| 项                                | 状态 | 证据                                                        |
| --------------------------------- | ---- | ----------------------------------------------------------- |
| `audit-boot-v4.1.md` Boot         | ✓    | 已 Read                                                     |
| `audit-finding-schema.md`         | ✓    | 已 Read                                                     |
| `AUDIT.plan.md` §0.1 + §2 A3      | ✓    | A3：无 `参考项目` runtime import；live 闸；隔离 `DATA_ROOT` |
| ADR-027 / ADR-034                 | ✓    | 已 Read                                                     |
| `plan-spec.md` Interface Contract | ✓    | live 闸 / exit 码 / 负向「无 silent fallback」              |
| `gitnexus-audit-summary.md`       | ✓    | 7.pre 已 Read                                               |

### GitNexus

| 调用                                                                                                             | 结果                                                                                     |
| ---------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| `query({repo:"quant-monitor-desk", search_query:"tier_a_live_incremental_dispatch product live gate"})`          | 返回 production*gate / live_pilot 流程；**未索引** `tier_a_live*\*` 新符号（索引 stale） |
| `context({name:"run_tier_a_live_incremental", file_path:"backend/app/ops/tier_a_live_incremental_dispatch.py"})` | Symbol not found                                                                         |
| `context({name:"validate_live_acceptance_env", file_path:"backend/app/ops/tier_a_live_acceptance.py"})`          | Symbol not found                                                                         |

> 静态审计以 **rg + Read diff 文件** 为准；建议 Repair 前 `node .gitnexus/run.cjs analyze` 刷新索引。

### 静态命令（A3 基线 + 任务面）

```text
# 参考项目 runtime import — backend/scripts tier_a_live 新增文件
rg "参考项目" backend/app/ops/tier_a_live*.py scripts/tier_a_live*.py
→ 0 matches

# API key / secret / token（tier_a_live 生产面）
rg -i "api[_-]?key|secret|token|password" backend/app/ops/tier_a_live*.py scripts/tier_a_live*.py
→ 仅 SOURCE_API_KEY_ENV 槽位名（FRED_API_KEY 等），无值泄露

# SQL 拼接（新增 dispatch）
rg "execute\(f|f\".*SELECT" backend/app/ops/tier_a_live_incremental_dispatch.py
→ L434,L441: quote_ident(clean_table) + 参数化 WHERE；clean_table 来自 resolve_clean_write_target（registry），非用户输入

# live 闸调用链
rg "gate_live_fetch_port|assert_product_live_allowed" backend/app/ops/tier_a_live_incremental_dispatch.py
→ dispatch 层 assert_product_live_allowed（L94,L135,L172,…）；fetch port 工厂仍调 gate_live_fetch_port
```

### Checklist 对照（AUDIT.plan §2 A3 + plan-spec）

| 威胁面                       | 结论        | 证据摘要                                                                                                                       |
| ---------------------------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------ |
| 无 `参考项目` runtime import | **PASS**    | `backend/` · `scripts/tier_a_live_acceptance.py` 0 命中；`tests/test_bis_incremental_e2e.py` 有 AST 禁止 digital-oracle import |
| Live gate bypass             | **FAIL**    | fred 分支经 `QMD_FRED_INCREMENTAL_USE_MOCK` 可静默 mock（见 A3-P1-01）                                                         |
| API keys 进日志              | **PASS**    | `missing_api_keys_for_sources` 只报 env 名；`print` 仅 source_id + detail                                                      |
| 隔离 `DATA_ROOT` / 无主库写  | **PARTIAL** | `assert_isolated_live_data_root` + 负向测绿；fred sync 路径未绑定 `data_root` 参数（见 A3-P2-01）                              |
| SEC_EDGAR UA                 | **PARTIAL** | port `_sec_user_agent()` 要求 `@`/`contact`；acceptance 仅检查非空（见 A3-P2-02）                                              |
| 无 silent fallback           | **FAIL**    | plan-spec §Testing Negative 明确要求；fred mock env 未拦截                                                                     |

### DOUBT 三类对抗搜索

| 类                 | 范围                        | 结论                                                                                          |
| ------------------ | --------------------------- | --------------------------------------------------------------------------------------------- |
| 硬编码 URL 变体    | `deribit_port.py` live HTTP | 仅 `deribit.com/api/v2/public/*` 固定公网端点；instrument 经 whitelist + `urllib.parse.quote` |
| JWT / API key 模式 | tier_a_live 新增 + dispatch | 无硬编码密钥；env 槽位校验不打印值                                                            |
| SQL 拼接           | `_clean_row_count`          | `quote_ident` + `?` 绑定；表名来自内部 registry，可接受 ponytail                              |

---

## §维度裁决

**FAIL**

（§计划内 ≥1 非占位 finding，含 P1。）

---

## 计划内问题

| ID       | P   | 标题                                                                  | 锚点                                                                                                       | 根因                                                                                                                                                                                                                                                                                                                                                               | 修复方案                                                                                                                                                                                                                                                                                      | 验证                                                                                                                                                                                                                                                                                                                               |
| -------- | --- | --------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A3-P1-01 | P1  | fred live 验收可经 `QMD_FRED_INCREMENTAL_USE_MOCK` 静默退回 mock      | `backend/app/ops/tier_a_live_incremental_dispatch.py:114-120` → `backend/app/cli/data_commands.py:195-232` | fred 分支委托 `_sync_fred_macro_incremental`，其 `use_mock = os.environ.get("QMD_FRED_INCREMENTAL_USE_MOCK", "0") != "0"`；`use_mock=True` 时 `create_fred_fetch_port` 直接返回 `FredMockFetchPort`（**跳过** `gate_live_fetch_port`），在 `QMD_ALLOW_LIVE_FETCH=1` 下仍可被 `tier_a_live_acceptance` 标 pass，违反 ADR-027/034 与 plan-spec「无 silent fallback」 | 在 `validate_live_acceptance_env` 或 fred 分支入口 **fail-closed**：若 `QMD_FRED_INCREMENTAL_USE_MOCK` 为真则 `TierALiveEnvError(code="MOCK_FORBIDDEN_IN_LIVE_ACCEPTANCE")`；或 fred 分支改走与其他 10 源一致的 `_prepare_sandbox` + `use_mock=False` 专用 runner，并 `delenv`/拒绝 mock 开关 | `uv run pytest tests/test_tier_a_live_harness.py -q` 新增负向：`monkeypatch.setenv("QMD_FRED_INCREMENTAL_USE_MOCK","1")` + opt-in → exit 2 或 `TierALiveEnvError`；`QMD_ALLOW_LIVE_FETCH=1 uv run python scripts/tier_a_live_acceptance.py --source-id fred --data-root .audit-sandbox/m-data-03/audit-a3` 在设 mock env 时 exit 2 |
| A3-P2-01 | P2  | fred dispatch 忽略 `data_root` 且跳过 `_prepare_sandbox`              | `tier_a_live_incremental_dispatch.py:111-120` vs 其他源 L134 `_prepare_sandbox(data_root)`                 | fred 仅调 CLI helper，依赖调用方预先设置 `QMD_DATA_ROOT`；`run_tier_a_live_incremental` 的 `data_root` 用于 inspect/clean 计数（L450-452）但与 sync 目标可能不一致，削弱 ADR-034 隔离契约                                                                                                                                                                          | fred 分支与其他源对齐：入口 `os.environ["QMD_DATA_ROOT"]=str(data_root)` + `_prepare_sandbox(data_root)`，或内联 fred incremental runner 显式传入 `data_root`，禁止隐式读全局 env                                                                                                             | 单测：`run_tier_a_live_incremental("fred", isolated_root)` 在 **未** 预设 env 时 sync 与 inspect 使用同一 `isolated_root/duckdb/quant_monitor.duckdb`（mock HTTP）；`assert_isolated_live_data_root` 负向测仍绿                                                                                                                    |
| A3-P2-02 | P2  | `validate_live_acceptance_env` 对 SEC_EDGAR UA 弱于 port 公平访问规则 | `tier_a_live_acceptance.py:84-93` vs `sec_edgar_port.py:65-73`                                             | acceptance 只检查 `SEC_EDGAR_USER_AGENT` 非空；port `_sec_user_agent()` 拒绝无 `@` 且无 `contact` 的 bare UA；验收层可放行非法 UA，后续才在 port fail（exit 1 非 exit 2）                                                                                                                                                                                          | 抽取共享 `validate_sec_edgar_user_agent(raw) -> str \| None`，在 `missing_api_keys_for_sources` 或独立校验中对 `sec_edgar` 复用 port 同等规则                                                                                                                                                 | `uv run pytest tests/test_tier_a_live_harness.py -q` 新增：`SEC_EDGAR_USER_AGENT="QuantMonitor/1.0"`（无 @）→ `TierALiveEnvError` `MISSING_API_KEYS` 或专用 code；`tests/test_sec_edgar_adapter.py` 现有 port 测仍绿                                                                                                               |

---

## 计划外发现

| ID       | P   | 标题                                 | 锚点                                | 根因                                                                                                                     | 修复方案                                                                                           | 验证                                                                                                                 |
| -------- | --- | ------------------------------------ | ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| A3-P3-01 | P3  | acceptance CLI exit 2 不输出失败原因 | `tier_a_live_acceptance.py:239-243` | `run_acceptance` 捕获 `TierALiveEnvError` 直接 `return 2`，不 `print`；仅 `main()` 对外层异常写 stderr，内层校验失败静默 | `return 2` 前 `print(str(exc), file=sys.stderr)` 或让 `TierALiveEnvError` 冒泡至 `main()` 统一打印 | `test_tierALiveAcceptanceCli_exit2WhenEnvInvalid` 断言 stderr 含 `QMD_ALLOW_LIVE_FETCH` 或 `LIVE_FETCH_NOT_OPTED_IN` |

已对抗搜索：`backend/app/ops/tier_a_live*.py` · `scripts/tier_a_live*.py` · `tests/test_tier_a_live*.py` · `tests/*_incremental_support.py`（M-DATA-03 变更）· `backend/app/datasources/fetch_ports/deribit_port.py` · `rg 参考项目 backend/` · `rg QMD_FRED_INCREMENTAL_USE_MOCK` · GitNexus query/context（索引未含新符号）。除上表外未发现额外 P0–P2 威胁面。

[REDACTED]
