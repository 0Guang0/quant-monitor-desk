# ADR-016：22 源矩阵验收诚实关账（无资格暴露 · 外部失败 · 禁止假绿）

- **Status:** Accepted
- **Date:** 2026-07-07
- **Context:** Task-01 将 `SourceRouteDbAcceptanceSpine` 扩展到 `docs/modules/data_sources.md` §5.9.1 全部 22 个数据源。用户在隔离 `data_root` 下以 `QMD_ALLOW_LIVE_FETCH=1` 跑 production-equivalent 全矩阵 live 验收时，出现三类**必须诚实保留**的结果，不能与「为了 closure PASS 而 mock / 藏失败」混为一谈：

  1. **长期无资格源** — `qmt_xtdata`、`ths_ifind` 当前拿不到本机终端授权或商业牌照 artifact；矩阵行应为 `failure_class=BLOCKED`，且**故意暴露**「当前没有使用资格」。
  2. **外部网络失败** — `sec_edgar` 在部分环境访问 `https://data.sec.gov` 时出现 `NETWORK_ERROR`（如 SSL EOF）；不得用 replay/mock 冒充 live PASS。
  3. **探针与活市场不一致** — 曾用 replay 固定符号（如 Deribit 过期期权名）跑 live 矩阵导致 `rows_written=0` 假失败；与「源未接入」不同，属符号 SSOT 问题（已由契约 `live_vs_replay_probe` 约束）。

  既有 ADR-015 已规定隔离沙箱、禁止 mock 冒充 live、允许 `FAIL_EXTERNAL` 并保留证据，但未区分 **矩阵 closure** 下「必须 PASS 的源」与「允许无资格 BLOCKED 的源」。全矩阵 `--live-authorized` checker 若一律把任意 `BLOCKED` 当 closure FAIL，会把用户**主动选择暂不提供的资格缺口**误判为产品假红。

- **Extends:** [ADR-015](ADR-015-tier-a-live-acceptance-sandbox.md)（隔离 production-equivalent DB、诚实 `implementation_mode`、允许 `FAIL_EXTERNAL`）
- **Extends:** [ADR-008](ADR-008-product-live-env-gate.md)（`QMD_ALLOW_LIVE_FETCH` 总闸）
- **SSOT 契约:** `specs/contracts/source_route_db_acceptance_contract.yaml` → `matrix_closure`、`qualification_deferred_sources`、`live_vs_replay_probe`

## Decision

### 1. 三层验收结论（业务词汇）

| 层                        | 问什么                         | 典型行状态                         | closure 当 `live_authorized=true`                                                           |
| ------------------------- | ------------------------------ | ---------------------------------- | ------------------------------------------------------------------------------------------- |
| **A. 无资格（资格延期）** | 用户当前能否合法使用该源？     | `BLOCKED`（缺终端/牌照 env）       | **`closure_outcome=PASS`** — 诚实暴露无资格，不算产品假绿                                   |
| **B. 有能力须证明**       | 有资格时，隔离库全链路是否通？ | `PASS` 或 `FAIL` / `FAIL_EXTERNAL` | 须 `PASS` 或登记的外部失败（见下）                                                          |
| **C. 外部客观失败**       | 上游网络/限流/SSL 等？         | `FAIL_EXTERNAL`                    | **`closure_outcome=FAIL_EXTERNAL`** — 保留在报告与 checker violation 中，**禁止 mock 修绿** |

**资格延期源（当前绑定）：** `qmt_xtdata`、`ths_ifind`（`qualification_deferred_sources`）。  
**不在此列的 `BLOCKED`**（如缺 `FRED_API_KEY`、`ALPHA_VANTAGE_API_KEY`）仍为 closure **FAIL** — 用户应提供的 API 凭证缺口不得冒充「长期无资格」。

### 2. 矩阵行 vs closure 行（禁止混淆）

- **矩阵行 `status`** 必须诚实：`BLOCKED` / `FAIL` / `PASS` 如实反映单次 execute 结果。
- **closure 行 `closure_outcome`** 是关账规则：在 `live_authorized=true` 下判断该行是否阻碍「本政策下的矩阵关账」。
- **禁止：** 为让 `status=PASS` 而注入假数据、假授权 env、或把 live handler 改回 mock/replay。
- **禁止：** 为让 `closure_outcome=PASS` 而把 `FAIL_EXTERNAL`（如 SEC `NETWORK_ERROR`）静默改为 `PASS` 或吞掉错误。

### 3. 外部失败（以 SEC EDGAR 为当前样例）

当 `sec_edgar` live 路径在隔离库中走完整 incremental 金路径，但 `_fetch_sec_submissions_json` 因 SSL/网络失败返回 `NETWORK_ERROR`：

1. 报告必须保留 `failure_class=FAIL_EXTERNAL`、`errors` 含网络摘要。
2. **不得**用 replay fixture、空 filings bundle 或跳过 fetch 让矩阵行 `PASS`。
3. **不得**在 closure 汇总里把 `FAIL_EXTERNAL` 计为 `PASS`。
4. 环境恢复连通后须**重跑**同一矩阵命令验证；关账证据以重跑报告为准。

当前实测（2026-07-07）：全矩阵 22 源中 **21 行 closure PASS + 1 行 SEC `FAIL_EXTERNAL`**；QMT/iFinD 为 `status=FAIL` + `BLOCKED` 但 `closure_outcome=PASS`。

### 4. Live 探针：验收单 vs 活市场

- **验收单（replay fixture）：** 测试/offline 用固定符号，可含已过期合约；仅用于 mock、`tests/fixtures`、确定性单测。
- **活市场（live matrix）：** execute 时必须对齐 API 当前可见标的（SSOT helper 或 `resolve_*_live_instrument`）；staging 按 `instrument_id` 过滤时，不得使用与 bundle 不一致的过期 seed。
- **Deribit：** replay seed `BTC-28JUN24-65000-C` ≠ live 矩阵 `instrument_id`；live 须 `resolve_matrix_deribit_live_instrument()`。

### 5. 测试与 `.env` 隔离（pytest 卫生）

- **矩阵 live / 产品路径：** 允许 `.env` 中开启 `QMD_ALLOW_LIVE_FETCH`；QMT/iFinD 无 env 时**必须** `BLOCKED`。
- **单测「默认未授权」负例：** 须在测试开头用 `monkeypatch.delenv` 清除 `QMT_XTDATA_AUTHORIZED`、`THS_IFIND_LICENSE_ARTIFACT` 等，避免 `.env` 污染导致「默认应拦截」用例假失败。  
  实现：`tests/test_cn_market_adapters.py` → `_clear_license_gate_env()`。
- **二者不矛盾：** 矩阵暴露真实资格状态；单测证明代码默认会拦。

### 6. 关账命令与通过条件（本 ADR 口径）

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

**在本 ADR 政策下，honest close 当且仅当：**

1. 所有**非资格延期**、**非 validation-only 定位**的主档源在 `live_authorized=true` 下 `closure_outcome=PASS`（或合法的 validation/manual_review PASS 语义）。
2. `qualification_deferred_sources` 可为 `BLOCKED` 且 `closure_outcome=PASS`。
3. 剩余 `FAIL_EXTERNAL` 行有完整 `errors` / `failure_class` 证据，且**未**用 mock 替代。
4. 无 `FAIL_CONTRACT`、无「缺 live 授权却混在已授权报告里」的 metadata violation。
5. `uv run pytest -q` 全绿（含授权门默认负例与矩阵 closure 单测）。

**明确：SEC 仍 `FAIL_EXTERNAL` 时 checker exit 1 是正确行为**，不是实现缺陷。

## Alternatives Considered

| Alternative                                         | Rejected because                                                               |
| --------------------------------------------------- | ------------------------------------------------------------------------------ |
| 全矩阵任意 `BLOCKED` 一律 closure FAIL              | 把 QMT/iFinD「当前无资格」与「产品坏了」混为一谈；逼迫假授权或删源             |
| 为 SEC 在 live handler 内 fallback 到 replay bundle | 违反 ADR-015「mock 不能冒充 live success」；掩盖 SSL/网络根因                  |
| 资格延期源从矩阵删除                                | 违背 5.9.1 全覆盖；失去「源在册但无资格」的可审计状态                          |
| closure PASS = 所有行 `status=PASS`                 | 与 validation-only、资格延期语义冲突；报告无法同时诚实又关账                   |
| 在 CI 默认跑全矩阵 live                             | 慢、脆、依赖密钥与网络；默认 `pytest` 仍 replay/network-marked 分离（ADR-015） |

## Consequences

- **代码：** `evaluate_matrix_row_closure` 对 `QUALIFICATION_DEFERRED_SOURCE_IDS` 在 `live_authorized=true` 且 gate `BLOCKED` 时返回 `PASS`；`FAIL_EXTERNAL` 仍阻断 closure。
- **契约：** `source_route_db_acceptance_contract.yaml` 已登记 `qualification_deferred_sources`、`live_vs_replay_probe`。
- **文档：** 本 ADR 为 task-01 Slice 10 矩阵关账的权威「为什么可以 21/22 closure PASS 而 SEC 仍红」说明。
- **运维：** 用户若日后取得 QMT/iFinD 资格，须重跑矩阵；预期该行从 `BLOCKED` 变为 live `PASS`，closure 仍 PASS。
- **风险登记：** SEC SSL 问题记入报告即可；修复路径为网络/客户端/环境，非 acceptance 语义放宽。

## Glossary（domain-modeling · 业务词，非实现）

| 术语                                    | 含义                                                                      |
| --------------------------------------- | ------------------------------------------------------------------------- |
| **production-equivalent acceptance DB** | 与主库同 schema/migration 的隔离 DuckDB；不写 canonical 主库              |
| **资格延期（qualification deferred）**  | 源在册，但用户长期无法提供终端/牌照；允许 `BLOCKED` 且 closure 通过       |
| **必须 PASS 的源**                      | 有资格且定位要求 live 证明的主档源；`FAIL` / `FAIL_EXTERNAL` 阻断 closure |
| **FAIL_EXTERNAL**                       | 链路已接、上游客观失败；保留证据，禁止 mock 修绿                          |
| **假绿**                                | `status` 或 `closure_outcome` 为 PASS，但依赖 mock、假授权或吞异常        |

## Binding

- Task: `task/task-01-source-route and DB acceptance spine`
- Slices: Slice 10（Real Authorized Source-Matrix Acceptance）
- Checkers: `scripts/check_source_route_db_acceptance_matrix.py --live-authorized`
- Reports: `.audit-sandbox/source-route-db-full-live-v2/reports/source-matrix-acceptance.json`（2026-07-07 证据样例）
