# Audit Repair Manifest — R3H-02（零遗留）

> **规则：** 每一项 BLOCKING / NON-BLOCKING / P1 / P2 / debt-lite 均须 **CLOSED** 并记入 `research/audit-repair-evidence.md`。  
> **参照：** R3H-01 `research/audit-repair-evidence.md`  
> **验证门：** `uv run pytest -q` exit 0 · `loop_maintain.py` OK · `validate-execute-handoff` OK · `node .gitnexus/run.cjs analyze`

## A1 / A5 / A8 — 合并门与证据

| ID         | 来源                     | 动作                                                                    | 验收                           |
| ---------- | ------------------------ | ----------------------------------------------------------------------- | ------------------------------ |
| R3H02-R-01 | A1 OOF-A1-01 / A8 P0-01  | `test_catalog.yaml` 登记两模块；`loop_maintain` 全绿                    | `check_test_catalog.py` exit 0 |
| R3H02-R-02 | A1 OOF-A1-02             | 刷新 `execute-evidence/9.8-full.txt` 与 `9.8-green.txt`（真实命令输出） | 与 `pytest -q` + loop 一致     |
| R3H02-R-03 | A1 OOF-A1-03 / A5-GAP-01 | 同步 canonical `execute-evidence/`：9.6-green、9.7-_、9.8-_             | handoff 路径一致               |
| R3H02-R-04 | A1 OOF-A1-04             | `node .gitnexus/run.cjs analyze`；更新 `gitnexus-audit-summary.md`      | 五 port 可 query               |
| R3H02-R-05 | A1 OOB-01 / A5-GAP-02    | §9.4：`adapters/__init__.py` yahoo 指向 port 边界（对齐 frozen）        | 无 skeleton-only 注册          |

## A4 / A8 — 对抗测试与契约

| ID         | 来源                          | 动作                                                                                                                           | 验收                                           |
| ---------- | ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------- |
| R3H02-R-10 | A4 P1-01 / A3 / A8 P1-01      | yahoo/stooq/coingecko `SourceRoutePlanner` validation-only Primary 阻断测（对齐 akshare `test_layer1_ingestion_gates.py:223`） | 3 条新测绿                                     |
| R3H02-R-11 | A4 P1-04 / A8 P1-02           | stooq/yahoo/coingecko cap overflow 负例                                                                                        | 各 1 条                                        |
| R3H02-R-12 | A4 P1-06                      | AV `max_symbols` factory overflow 测                                                                                           | 1 条                                           |
| R3H02-R-13 | A4 P1-02 / A6 NB-1 / A8 P1-03 | `max_window_days` 在 AV/stooq fetch 入口 `reject_over_cap` + window 负例                                                       | 测绿                                           |
| R3H02-R-14 | A4 P1-03 / A8 P1-04           | yahoo option_chain：实现 port 分支 **或** capabilities 收敛至已实现 operation                                                  | yaml↔port 一致                                 |
| R3H02-R-15 | A4 P1-05                      | capabilities 字段分层（`bundle_fields`/`observation_fields`）或 mock 补 `market_cap_usd` + parity 测                           | `test_r3h02_capabilityFields_matchPortOutput`  |
| R3H02-R-16 | A4 P2-01                      | `test_r3h02_marketCaps_matchRegistry` 五源 caps parity                                                                         | 测绿                                           |
| R3H02-R-17 | A4 P2-02 / A8 S-01            | 五源 unknown symbol/instrument 白名单负例                                                                                      | 每源 1 条（可参数化）                          |
| R3H02-R-18 | A4 P2-05                      | `contract_coverage.yaml` 标注 cap/validation route `negative_required: true`                                                   | loop_maintain OK                               |
| R3H02-R-19 | A8 S-03                       | merge gate 显式跑 `test_r3h_source_final_decisions.py` 并记入 9.8 证据                                                         | 文档/证据                                      |
| R3H02-R-21 | A8 G1                         | AV `us_option_chain` / `max_option_strikes` cap overflow 负例                                                                  | 1 条测绿                                       |
| R3H02-R-22 | A8 G2                         | replay bundle 断言 `window_kind == calendar_days`（AV/stooq/yahoo）                                                            | 测绿                                           |
| R3H02-R-23 | A8 G6                         | AV 未授权时 route planner `DISABLED_SOURCE` 负例                                                                               | 1 条                                           |
| R3H02-R-24 | A8 G7                         | crypto Layer4 smoke（deribit/coingecko replay）                                                                                | 1 条                                           |
| R3H02-R-25 | A8 G8                         | yahoo validation 域启用后 READY 正例 route                                                                                     | 1 条                                           |
| R3H02-R-26 | A5 O-04                       | `evidence_index.json` 补 execute/audit 索引（若任务工件要求）                                                                  | 文件非空或 explicit defer 记入 repair-evidence |
| R3H02-R-27 | A5 / A1                       | 弱 green.txt 补 `exit_code: 0` 摘要（9.1/9.2 等 canonical）                                                                    | 证据可读                                       |

## A3 — Registry YAML 歧义

| ID         | 来源                 | 动作                                                                                                 | 验收                             |
| ---------- | -------------------- | ---------------------------------------------------------------------------------------------------- | -------------------------------- |
| R3H02-R-20 | A3-YAHOO / COINGECKO | validation-only 源移出 `domain_roles.primary` 或改为 validation 槽位（yahoo/coingecko/stooq 相关域） | registry 语义一致 + route 测仍绿 |

## A2 — Ponytail debt（用户要求零遗留）

| ID         | 来源  | 动作                                                                                                          | 验收         |
| ---------- | ----- | ------------------------------------------------------------------------------------------------------------- | ------------ |
| R3H02-R-30 | A2 U1 | 删 `write_crypto_market_evidence_bundle` **或** 补 crypto write round-trip 测（与 market 对称，二选一须闭合） | 无 dead API  |
| R3H02-R-31 | A2    | 抽 `evidence_bundle.bundle_layer5_provenance()` 合并三处拷贝                                                  | 测仍绿       |
| R3H02-R-32 | A2    | 删未用常量或接线：`MAX_OPTION_STRIKES`（yahoo）、已接 window cap（R-13）                                      | 无死常量     |
| R3H02-R-33 | A2    | Layer5 smoke 抽 `tests/conftest_layer_smoke.py` helper（不改 purpose）                                        | 测仍绿       |
| R3H02-R-34 | A2    | 合并重复 replay 读路径测（market 双测 `_AV_REPLAY`）                                                          | purpose 不变 |

## A6 — Perf 备忘闭合

| ID         | 来源    | 动作                                                                            | 验收           |
| ---------- | ------- | ------------------------------------------------------------------------------- | -------------- |
| R3H02-R-40 | A6 NB-2 | 由 R-11 覆盖                                                                    | CLOSED-by-test |
| R3H02-R-41 | A6 NB-3 | 在 port 或文档注明 DSS 接入时 ResourceGuard hook（`ponytail:` 注释 + 活卡指针） | 文档闭合       |

## A7 — 运维

| ID         | 来源    | 动作                                                                      | 验收   |
| ---------- | ------- | ------------------------------------------------------------------------- | ------ |
| R3H02-R-50 | A7 NB-5 | 9.8 证据含 `test_PromoteRunner_refusesCanonicalProductionDbPath` 通过记录 | 证据行 |

## 最终门

```bash
uv run pytest -q
uv run python scripts/loop_maintain.py
uv run python .trellis/scripts/task.py validate-execute-handoff .trellis/tasks/06-28-06-28-round3h-r3h02-market-data
node .gitnexus/run.cjs analyze
```
