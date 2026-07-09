# ADR-016：22 源矩阵验收诚实关账（无资格暴露 · 外部失败 · 禁止假绿）

- **状态：** 已接受（2026-07-07 修订 — `sec_edgar` 列入 external_deferred）
- **日期：** 2026-07-07
- **背景：** Task-01 将 `SourceRouteDbAcceptanceSpine` 扩展到 `docs/modules/data_sources.md` §5.9.1 全部 22 个数据源。用户在隔离 `data_root` 下以 `QMD_ALLOW_LIVE_FETCH=1` 跑 production-equivalent 全矩阵 live 验收时，出现三类**必须诚实保留**的结果，不能与「为了 closure PASS 而 mock / 藏失败」混为一谈：
  1. **长期无资格源** — `qmt_xtdata`、`ths_ifind` 当前拿不到本机终端授权或商业牌照 artifact；矩阵行应为 `failure_class=BLOCKED`，且**故意暴露**「当前没有使用资格」。
  2. **外部网络失败** — `sec_edgar` 在部分环境访问 `https://data.sec.gov` 时出现 `NETWORK_ERROR`（如 SSL EOF）；不得用 replay/mock 冒充 live PASS；**矩阵行须诚实 `FAIL_EXTERNAL`，但登记为 `external_deferred_sources` 时不阻断 Slice 10 closure**（见 §4）。
  3. **探针与活市场不一致** — 曾用 replay 固定符号（如 Deribit 过期期权名）跑 live 矩阵导致 `rows_written=0` 假失败；与「源未接入」不同，属符号 SSOT 问题（已由契约 `live_vs_replay_probe` 约束）。
     既有 ADR-015 已规定隔离沙箱、禁止 mock 冒充 live、允许 `FAIL_EXTERNAL` 并保留证据，但未区分 **矩阵 closure** 下「必须 PASS 的源」与「允许无资格 BLOCKED 的源」。全矩阵 `--live-authorized` checker 若一律把任意 `BLOCKED` 当 closure FAIL，会把用户**主动选择暂不提供的资格缺口**误判为产品假红。

- **SSOT 契约:** `specs/contracts/source_route_db_acceptance_contract.yaml` → `matrix_closure`、`qualification_deferred_sources`、`external_deferred_sources`、`live_vs_replay_probe`

## 决策

### 1. 两种显式 closure 模式（Slice 10 与中间态分离）

| `closure_mode`                | 何时用                                                                    | `BLOCKED` 行 closure 规则                                                                                                                                                                   |
| ----------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `**dry_run`\*\*               | `live_authorized=false`；开发期矩阵、诚实暴露资格缺口                     | 缺 `QMD_ALLOW_LIVE_FETCH`（live authorization missing）或 `qualification_deferred_sources` 缺终端/牌照 → **PASS**；其余 BLOCKED → FAIL                                                      |
| `**final_live_authorized`\*\* | `--live-authorized` checker；用户已 `QMD_ALLOW_LIVE_FETCH=1` 跑 live 矩阵 | `qualification_deferred_sources` 缺终端/牌照 → **PASS**；`external_deferred_sources` 诚实 `FAIL_EXTERNAL` → **PASS**；**其他** `BLOCKED` / `FAIL_EXTERNAL` / `FAIL_CONTRACT` → 阻断 closure |

`qualification_deferred_sources`（`qmt_xtdata`、`ths_ifind`）在两种模式下均可把诚实 terminal/license `BLOCKED` 计为 closure PASS。**除这些预期无资格外，不得出现其它失败行。**

矩阵报告须带 `closure_mode`；`--live-authorized` checker 要求 `live_authorized=true` 且 `closure_mode=final_live_authorized`。

### 2. 三层验收结论（业务词汇 · 矩阵行诚实度）

| 层                        | 问什么                         | 典型行状态                         | `final_live_authorized` closure                                                          |
| ------------------------- | ------------------------------ | ---------------------------------- | ---------------------------------------------------------------------------------------- |
| **A. 无资格（资格延期）** | 用户当前能否合法使用该源？     | `BLOCKED`（缺终端/牌照 env）       | **PASS** — 诚实暴露无资格；dry_run 与 final 均适用                                       |
| **B. 有能力须证明**       | 有资格时，隔离库全链路是否通？ | `PASS` 或 `FAIL` / `FAIL_EXTERNAL` | 未登记延期须 `PASS`；登记 `external_deferred` 可 honest `FAIL_EXTERNAL` + closure PASS   |
| **C. 外部客观失败**       | 上游网络/限流/SSL 等？         | `FAIL_EXTERNAL`                    | 默认阻断；`**external_deferred_sources`** 矩阵行红、closure **PASS\*\*（禁止 mock 修行） |

**不在资格延期列的 `BLOCKED`**（如缺 `FRED_API_KEY`）在两种模式下对 final gate 均为 **FAIL**。

### 3. 矩阵行 vs closure 行（禁止混淆）

- **矩阵行 `status`** 必须诚实：`BLOCKED` / `FAIL` / `PASS` 如实反映单次 execute 结果。
- **closure 行 `closure_outcome`** 是关账规则：在 `closure_mode=final_live_authorized` 下判断该行是否阻碍 Slice 10 关账。
- **禁止：** 为让 `status=PASS` 而注入假数据、假授权 env、或把 live handler 改回 mock/replay。
- **禁止：** 为让 `closure_outcome=PASS` 而把矩阵行 `FAIL_EXTERNAL` 改成 `status=PASS`、注入 replay/mock，或吞掉 `errors`。
- **允许（Slice 10）：** 对 `external_deferred_sources` 中已登记的源，矩阵行保持 `failure_class=FAIL_EXTERNAL`，`closure_outcome=PASS` —— **诚实暴露环境/上游问题，不假装 live 成功，也不因此无限期阻塞 task-01 关账**。

### 4. 外部失败（SEC EDGAR · 环境延期登记）

当 `sec_edgar` live 路径在隔离库中走完整 incremental 金路径，但 `_fetch_sec_submissions_json` 因 SSL/网络失败返回 `NETWORK_ERROR`：

1. **矩阵行必须诚实：** 保留 `status=FAIL`、`failure_class=FAIL_EXTERNAL`、`errors` 含网络摘要（如 `SSL EOF`、`NETWORK_ERROR`）。
2. **禁止假绿：** 不得用 replay fixture、空 filings bundle 或跳过 fetch 让矩阵行 `PASS`。
3. **Slice 10 closure 不阻断：** `sec_edgar` 列入 `external_deferred_sources`（见契约 YAML）。在 `final_live_authorized` 下，诚实 `FAIL_EXTERNAL` → `**closure_outcome=PASS`\*\*，全矩阵 checker 可关账。
4. **不等于「问题不存在」：** 报告与 ADR 须保留 SEC 红行证据；环境恢复连通后**应重跑**验证 live `PASS`；后续 slice 可收紧登记或移除延期（须改 ADR + 契约，不得静默改语义）。
5. **登记边界：** 仅适用于**已接入 live handler、链路正确、失败来自上游客观环境**的 `FAIL_EXTERNAL`；`FAIL_CONTRACT`、缺 `SEC_EDGAR_USER_AGENT` 的 `BLOCKED`、未接 handler 的 `NOT_IMPLEMENTED` **仍阻断** closure。

当前实测（2026-07-07）：用户 live 授权下，**预期** QMT/iFinD `BLOCKED` closure PASS；**SEC `FAIL_EXTERNAL` 矩阵行红、closure PASS**，不阻塞 Slice 10 honest close。

### 5. Live 探针：验收单 vs 活市场

- **验收单（replay fixture）：** 测试/offline 用固定符号，可含已过期合约；仅用于 mock、`tests/fixtures`、确定性单测。
- **活市场（live matrix）：** execute 时必须对齐 API 当前可见标的（SSOT helper 或 `resolve_*_live_instrument`）；staging 按 `instrument_id` 过滤时，不得使用与 bundle 不一致的过期 seed。
- **Deribit：** replay seed `BTC-28JUN24-65000-C` ≠ live 矩阵 `instrument_id`；live 须 `resolve_matrix_deribit_live_instrument()`。

### 6. 测试与 `.env` 隔离（pytest 卫生）

- **矩阵 live / 产品路径：** 允许 `.env` 中开启 `QMD_ALLOW_LIVE_FETCH`；QMT/iFinD 无 env 时**必须** `BLOCKED`。
- **单测「默认未授权」负例：** 须在测试开头用 `monkeypatch.delenv` 清除 `QMT_XTDATA_AUTHORIZED`、`THS_IFIND_LICENSE_ARTIFACT` 等，避免 `.env` 污染导致「默认应拦截」用例假失败。  
  实现：`tests/test_cn_market_adapters.py` → `_clear_license_gate_env()`。
- **二者不矛盾：** 矩阵暴露真实资格状态；单测证明代码默认会拦。

### 7. 关账命令与通过条件（本 ADR 口径）

```powershell
# 隔离根示例
uv run qmd-ops accept-source-route-db `
  --all-documented-sources `
  --data-root .audit-sandbox/source-route-db-full-live-v2 `
  --report .audit-sandbox/source-route-db-full-live-v2/reports/source-matrix-acceptance.json `
  --allow-live-fetch

uv run python scripts/check_source_route_db_acceptance_matrix.py `
  --strict --live-authorized `
  --report .audit-sandbox/source-route-db-full-live-v2/reports/source-matrix-acceptance.json
```

**在本 ADR 政策下，honest close（`final_live_authorized`）当且仅当：**

1. 所有非资格延期、非 external-deferred、非 validation-only 定位的主档源 `closure_outcome=PASS`（或合法 non-primary PASS）。
2. `qualification_deferred_sources` 可为诚实 `BLOCKED` 且 `closure_outcome=PASS`。
3. `external_deferred_sources` 可为诚实 `FAIL_EXTERNAL` 且 `closure_outcome=PASS`（矩阵行仍 FAIL，禁止 mock 修绿）。
4. **除上述登记预期外**，无其它 `BLOCKED`、`FAIL_EXTERNAL`、`FAIL_CONTRACT` 行。
5. 报告 `live_authorized=true` 且 `closure_mode=final_live_authorized`。
6. `uv run pytest -q` 全绿。

`**dry_run` closure PASS\*\* 不能代替 final 报告；final 仍允许资格延期 `BLOCKED` 与 external 延期 `FAIL_EXTERNAL`（行诚实、closure PASS）。

**明确：SEC 矩阵行仍 `FAIL_EXTERNAL` 是正确诚实暴露**；Slice 10 不因该登记源 closure FAIL。其它未登记源的 `FAIL_EXTERNAL` 仍阻断 checker。

## 曾考虑的替代方案

| 替代方案                                             | 拒绝原因                                                                       |
| ---------------------------------------------------- | ------------------------------------------------------------------------------ |
| 全矩阵任意 `BLOCKED` 一律 closure FAIL（final 模式） | Slice 10 要求用户全授权；dry_run 另设模式暴露无资格                            |
| 为 SEC 在 live handler 内 fallback 到 replay bundle  | 违反 ADR-015「mock 不能冒充 live success」；掩盖 SSL/网络根因                  |
| SEC FAIL_EXTERNAL 永久阻断 Slice 10                  | 部分环境 SSL/网络不可在 acceptance 代码内修复；应诚实登记 external_deferred    |
| 资格延期源从矩阵删除                                 | 违背 5.9.1 全覆盖；失去「源在册但无资格」的可审计状态                          |
| final 模式仍豁免 QMT/iFinD `BLOCKED`                 | 与 ADR 资格延期语义一致；仅非延期源与其它失败类阻断                            |
| closure PASS = 所有行 `status=PASS`                  | 与 validation-only 语义冲突；报告无法同时诚实又关账                            |
| 在 CI 默认跑全矩阵 live                              | 慢、脆、依赖密钥与网络；默认 `pytest` 仍 replay/network-marked 分离（ADR-015） |

## 后果

- **代码：** `evaluate_matrix_row_closure` 按 `closure_mode` 分支；`qualification_deferred` 与 `external_deferred` 在 final 可 PASS；其它 `BLOCKED` / `FAIL_EXTERNAL` / `FAIL_CONTRACT` 阻断 final closure。
- **契约：** `source_route_db_acceptance_contract.yaml` 已登记 `qualification_deferred_sources`、`external_deferred_sources`、`live_vs_replay_probe`。
- **文档：** 本 ADR 为 task-01 Slice 10 矩阵关账的权威说明：**QMT/iFinD 无资格 BLOCKED、SEC 环境 FAIL_EXTERNAL 可 closure PASS，矩阵行仍诚实红**。
- **运维：** 用户若日后取得 QMT/iFinD 资格，须重跑矩阵；SEC 连通恢复后应重跑以争取 live 行 PASS。
- **风险登记：** SEC SSL/网络问题保留在报告 `errors`；修复路径为网络/客户端/环境；**不**用 mock 修绿，**不**无限期阻塞 Slice 10。

## 术语表（domain-modeling · 业务词，非实现）

| 术语                                    | 含义                                                                                          |
| --------------------------------------- | --------------------------------------------------------------------------------------------- |
| **production-equivalent acceptance DB** | 与主库同 schema/migration 的隔离 DuckDB；不写 canonical 主库                                  |
| **资格延期（qualification deferred）**  | 源在册但缺终端/牌照；`BLOCKED` 且 closure PASS（dry_run 与 final）                            |
| **环境延期（external deferred）**       | 源 live 链路已接但上游客观 `FAIL_EXTERNAL`；矩阵行红、closure PASS（final）；当前 `sec_edgar` |
| **必须 PASS 的源**                      | 有资格且未登记延期的主档源；`FAIL` / 未登记 `FAIL_EXTERNAL` 阻断 closure                      |
| **FAIL_EXTERNAL**                       | 链路已接、上游客观失败；保留证据，禁止 mock 修绿                                              |
| **假绿**                                | `status` 或 `closure_outcome` 为 PASS，但依赖 mock、假授权或吞异常                            |

## 绑定

- **任务：** `task/task-01-source-route and DB acceptance spine`
- **切片：** Slice 10（Real Authorized Source-Matrix Acceptance）
- **检查器：** `scripts/check_source_route_db_acceptance_matrix.py --live-authorized`
- **PR 门：** `python scripts/production_gate.py`（dry-run 矩阵关账；接线于 `.github/workflows/ci.yml`）
- **发布门：** `python scripts/production_gate.py --live-authorized --source-matrix-report <path>`
- **手动 live 工作流：** `.github/workflows/source-matrix-live-acceptance.yml`
