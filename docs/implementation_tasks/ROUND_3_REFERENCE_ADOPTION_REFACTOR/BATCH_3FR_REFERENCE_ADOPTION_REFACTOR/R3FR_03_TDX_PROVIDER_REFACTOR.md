# R3FR-03 — TDX Provider Refactor from EasyXT Reference

> **Batch:** Batch 3F-R — Mature Reference Adoption Refactor  
> **Module movement:** TDX must move from ad hoc manual probe pieces to a QMD-owned disabled/raw-only provider port with explicit authorization and caps.  
> **Execution posture:** disabled by default; raw evidence only; no production clean write; no default live scan.

---

## 1. Purpose

Refactor existing TDX/pytdx probe code so provider lifecycle, connection attempts, request caps, error mapping, and raw evidence output are separated from probe orchestration. This must complete the disabled/raw-only provider shape in this batch; do not split it into repeated “add one host/add one status” tasks.

```yaml
reference_project:
  path: 参考项目/EasyXT/easy_xt/realtime_data/providers/tdx_provider.py
  license: MIT
  allowed_use: direct_adaptation
  qmd_target_files:
    - backend/app/datasources/fetch_ports/tdx_pytdx_port.py
    - backend/app/datasources/normalizers/tdx.py
    - backend/app/ops/interface_probe_fetch_ports.py
  direct_copy_allowed: false
  rewrite_required:
    - remove_runtime_import_from_reference_project
    - remove_auto_server_scan_default
  forbidden_semantics:
    - production_primary
    - auto_login
  attribution_required: true
```

---

## 2. Reference source file

Read and adapt from:

```text
参考项目/EasyXT/easy_xt/realtime_data/providers/tdx_provider.py
```

Useful ideas:

- optional `pytdx` import handling;
- server list / host-port abstraction;
- connection lifecycle separation;
- retry/error classification;
- stock code normalization/parsing ideas;
- daily/index/security-list method separation.

---

## 3. Required rewrites

Do not copy EasyXT provider behavior wholesale. Rewrite as QMD-owned port code:

- no auto server scan by default;
- no default live enablement;
- no silent fallback to another source;
- no QMT/xqshare enablement;
- no trading/account semantics;
- all live attempts require explicit authorization object;
- every fetch must respect caps from capability/contract;
- raw output must be stored as evidence with content/schema hash;
- route status must remain `DISABLED_SOURCE`, `USER_AUTH_REQUIRED`, or raw-only pass until future authorization changes it.

---

## 4. Target QMD files

Create/update:

```text
backend/app/datasources/fetch_ports/tdx_pytdx_port.py
backend/app/datasources/normalizers/tdx.py
backend/app/datasources/adapters/tdx_pytdx.py
backend/app/ops/interface_probe_fetch_ports.py
backend/app/ops/tdx_manual_probe.py
backend/app/ops/tdx_live_manual_probe_gate.py
docs/quality/tdx_pytdx_live_manual_probe_authorization_2026-06-24.md
specs/datasource_registry/source_registry.yaml
specs/datasource_registry/source_capabilities.yaml
tests/test_tdx_pytdx_port.py
tests/test_tdx_manual_probe.py
tests/test_tdx_live_manual_probe_authorization.py
tests/test_reference_adoption_guardrails.py
tests/test_source_capabilities.py
```

If the `fetch_ports/` or `normalizers/` package does not exist, create it with QMD-owned module boundaries.

---

## 5. Required operations and caps

Supported disabled/raw-only operations:

```text
security_list
cn_equity_daily_bar
cn_index_daily_bar
```

Default caps:

```yaml
security_list_max_rows: 20
equity_daily_bar_max_symbols: 3
index_daily_bar_max_symbols: 3
max_network_calls: 5
minute_bars_enabled: false
full_market_scan_enabled: false
```

Any larger scope requires a later task or ADR. Do not add another micro-batch for one more cap unless it moves the provider toward a complete stable form.

### 5.1 Caps authority（R3FR-03 supersedes 018C row caps）

| 字段                             | SSOT 值 | 018C 旧值（须同步） |
| -------------------------------- | ------- | ------------------- |
| equity/index max_rows per symbol | **3**   | 10                  |
| security_list max_rows           | 20      | 20                  |
| max_network_calls                | 5       | 5                   |

**同步文件（9.4 + 9.6 同一 GREEN，未同步不得宣称 Step 9.4 GREEN）：** `tdx_live_manual_probe_gate.py` · 授权 MD · `tdx_manual_probe.py` · `source_capabilities.yaml` `tdx_pytdx.resource_caps`。

---

## 6. Tests / gates

Required verification:

```bash
uv run pytest tests/test_tdx_manual_probe.py tests/test_tdx_live_manual_probe_authorization.py -q
uv run pytest tests/test_reference_adoption_guardrails.py tests/test_source_capabilities.py -q
```

Tests must prove:

- missing `pytdx` returns disabled/source error, not crash;
- live path requires explicit authorization;
- default path is mocked/disabled raw-only;
- full-market/minute/default scan is rejected;
- source route/fetch result records disabled/user-auth status;
- no runtime import from `参考项目/**`;
- EasyXT auto-login/account/trading semantics are absent.

---

## 7. Done criteria

R3FR-03 is done when TDX has a complete disabled/raw-only QMD-owned provider port shape for the supported operations above. It must be strong enough for Round 3G audit to reason about TDX as excluded/disabled, not as a loose probe wrapper.

---

## 8. 边界约束 / 停止条件

| #   | 禁止 / 停止条件                                    | 动作                                          |
| --- | -------------------------------------------------- | --------------------------------------------- |
| 1   | production clean write、默认 live enablement       | 立即停止                                      |
| 2   | runtime import `参考项目/**`                       | 立即停止                                      |
| 3   | 改 `data_health.py` 主体（属 R3FR-02）             | 立即停止                                      |
| 4   | 在 `TdxPytdxProbeFetchPort` 继续堆 downloader 逻辑 | 回 Plan；改走 `fetch_ports/tdx_pytdx_port.py` |
| 5   | 全市场扫描 / 分钟线默认开启                        | 拒绝请求                                      |
| 6   | silent fallback 到其他源                           | 拒绝                                          |
| 7   | 未经批准的 caps 扩大                               | `RESOURCE_GUARD_PAUSED`                       |
| 8   | 未同步 gate + 授权 MD caps 却宣称 9.4 GREEN        | 停止；回 9.4                                  |
| 9   | R3FR-05 并行修改 `tdx_pytdx` registry caps 行      | 停止；由 coordinator 串行合并                 |
| 10  | 直调 `TdxPytdxFetchPort` 绕过 live gate            | 测试/门禁 FAIL                                |

---

## 9. 实现步骤（垂直切片 TDX-R3FR-01..07）

### 9.0 Boot

- Read `EXECUTION_INDEX.md` + `implement.jsonl` 每条 + `context_pack.json` + `trellis-execute/SKILL.md`
- 复跑 `context_router.py`；读完 §3 manifest

### 9.1 Provider port 包骨架（TDX-R3FR-01）

- 新建 `backend/app/datasources/fetch_ports/tdx_pytdx_port.py`（MIT 归因注释，无 runtime import 参考项目）
- 扩展 `fetch_port.py` `PortErrorStatus`：`DISABLED_SOURCE` · `USER_AUTH_REQUIRED`
- optional `pytdx` import；缺包 → `DISABLED_SOURCE`
- 新测：`test_tdxPytdxPort_missingPytdx_returnsDisabledSource`

### 9.2 Normalizers（TDX-R3FR-02）

- 新建 `backend/app/datasources/normalizers/tdx.py`（MIT 归因注释）
- 三操作 raw → manifest；`adapters/tdx_pytdx.py` 委托 normalizer
- 新测：`test_tdxNormalizer_equityManifest_hasRequiredFieldsAndHash`

### 9.3 三操作 + caps 拒绝（TDX-R3FR-03）

- `security_list` / `cn_equity_daily_bar` / `cn_index_daily_bar`
- 拒绝 minute、full-market、超 cap
- 新测：`test_tdxPytdxPort_rejectsMinuteBars` · `rejectsFullMarketScan` · `rejectsOverCap`

### 9.4 授权与 live 门（TDX-R3FR-04）

- port 要求显式 authorization；无授权 → `USER_AUTH_REQUIRED`
- 更新 `tdx_live_manual_probe_gate.py` caps（equity/index max_rows=**3**）
- 同步 `docs/quality/tdx_pytdx_live_manual_probe_authorization_2026-06-24.md` §Per-request
- enforce `FORBIDDEN_LIVE_ENTRYPOINTS`（含新 port FQN）；新测 `test_tdxLiveGate_forbiddenDirectPortInvocation`
- 新测：`test_tdxPytdxPort_withoutAuth_raisesUserAuthRequired`

### 9.5 Probe 编排瘦身（TDX-R3FR-05）

- `tdx_manual_probe.py` 调 port；`TdxPytdxProbeFetchPort` 瘦身为委托
- 编排内不得直连 `TdxHq_API`

### 9.6 Registry caps（TDX-R3FR-06）

- 更新 `source_registry.yaml` / `source_capabilities.yaml` `tdx_pytdx` 行 + `resource_caps` 块
- 新测：`test_tdxPytdx_capsMatchTaskCard` · `test_tdxRoute_tdxPytdx_disabledByDefault`
- **R3FR-03 独占 `tdx_pytdx` 行**；R3FR-05 不得改 caps

### 9.7 Guardrails 收尾（TDX-R3FR-07）

- `test_reference_adoption_guardrails.py` 绿；Tier A/B pytest
- `uv run python scripts/loop_maintain.py --fix`（新包 + `test_tdx_pytdx_port.py` catalog）

---

## 10. 测试要求

| 文件                                                | 目的                        | 成功         | 失败意味着                 |
| --------------------------------------------------- | --------------------------- | ------------ | -------------------------- |
| `tests/test_tdx_manual_probe.py`                    | mocked/disabled 路径与 caps | 全绿         | probe 可默认 live 或超 cap |
| `tests/test_tdx_live_manual_probe_authorization.py` | live 授权 fail-closed       | 全绿         | 无授权可联网               |
| `tests/test_reference_adoption_guardrails.py`       | 无参考 runtime import       | 全绿         | 采纳红线破裂               |
| `tests/test_source_capabilities.py`                 | registry caps               | `tdx` 相关绿 | caps 与任务卡不一致        |

测试 docstring 须五字段（GLOBAL_TESTING_POLICY）；TDD RED→GREEN 每步。

---

## 11. 验收命令

```bash
uv run pytest tests/test_tdx_manual_probe.py tests/test_tdx_live_manual_probe_authorization.py -q
uv run pytest tests/test_reference_adoption_guardrails.py tests/test_source_capabilities.py -q
uv run pytest -q
```

---

## 12. 完成标准

- §7 Done criteria 满足
- `EXECUTION_INDEX.md` §2 全部 AC-TDX-\* 有证据
- `validate-execute-handoff` exit 0；Audit PASS 后 `finish-work`
- **不闭合** `UNRESOLVED` B01-C03 live `PROBE_REDEFERRED`（host 占位）；仅强化 provider port

---

## 13. Red Flags

- 声称 TDX production-primary 或默认 live
- 复制 EasyXT auto-login / trading 语义
- 弱化测试 purpose 以通过 caps 变更
- 单 PR 水平实现全部切片无分步 evidence
- caps 权威冲突未同步 gate/授权 MD/registry
- `FORBIDDEN_LIVE_ENTRYPOINTS` 未 enforce
- R3FR-05 与 R3FR-03 并发改 `tdx_pytdx` registry caps
- 直调新 port 绕过 `validate_tdx_live_manual_probe_authorization`

---

## 14. Execute Skill 冻结

| Skill                      | 本任务 | 绑定 Step     | 触发                         |
| -------------------------- | ------ | ------------- | ---------------------------- |
| test-driven-development    | 必做   | 每 §9.x       | 每步                         |
| karpathy-guidelines        | 必做   | 每 §9.x       | 每步                         |
| testing-guidelines         | 必做   | 每 §9.x       | 每步                         |
| incremental-implementation | 必做   | 每步 GREEN 后 | 自动                         |
| gitnexus-impact-analysis   | 必做   | 改 symbol 前  | `impact()`                   |
| ponytail                   | 必做   | 全程          | `.cursor/rules/ponytail.mdc` |

---

## 15. Rollback plan（Playbook §4）

1. `git revert` 本分支 R3FR-03 commits 或 reset 至 `master` 合并点前
2. 恢复 `TdxPytdxProbeFetchPort` 内联 pytdx 路径（若已瘦身）
3. 回退 `source_registry` / `source_capabilities` `tdx_pytdx` 行与 `resource_caps`
4. 回退 gate / 授权 MD caps 至 018C 行（仅当未单独 merge caps ADR）
5. `uv run pytest -q` 全绿后方可宣称回滚完成
